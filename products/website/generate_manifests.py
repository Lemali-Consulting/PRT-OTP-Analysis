"""Auto-generate SOURCES.yaml for analyses by scanning each main.py file."""

from __future__ import annotations

import ast
import re
import sqlite3
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ANALYSES_DIR = PROJECT_ROOT / "analyses"
DB_PATH = PROJECT_ROOT / "data" / "prt.db"
LOCAL_PACKAGES = {"prt_otp_analysis", "analyses", "pipeline", "products"}

GROUP_MAP = {
    range(1, 10): "Core OTP Patterns",
    range(10, 20): "Route and Service Drivers",
    range(20, 30): "Ridership and External Factors",
    range(30, 40): "Equity and Strategic Planning",
}


def group_for(number: int) -> str:
    """Map analysis number to a display group."""
    for rng, label in GROUP_MAP.items():
        if number in rng:
            return label
    return "Other"


def extract_sql_strings(code: str) -> list[str]:
    """Extract likely SQL string payloads from source code."""
    patterns = [
        r'(?s)(?:r|f|rf|fr)?"""(.*?)"""',
        r"(?s)(?:r|f|rf|fr)?'''(.*?)'''",
        r'(?s)(?:r|f|rf|fr)?"(SELECT.+?)"',
        r"(?s)(?:r|f|rf|fr)?'(SELECT.+?)'",
    ]
    sql_strings: list[str] = []
    for pattern in patterns:
        for match in re.findall(pattern, code, flags=re.IGNORECASE):
            if any(token in match.upper() for token in ["SELECT ", "FROM ", "JOIN ", "UPDATE ", "INSERT "]):
                sql_strings.append(match)
    return sql_strings


def known_db_tables() -> set[str]:
    """Return actual table names from project SQLite DB when available."""
    if not DB_PATH.exists():
        return set()
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        return {row[0] for row in rows}
    finally:
        conn.close()


def extract_tables(code: str, valid_tables: set[str]) -> list[str]:
    """Extract table names from SQL snippets; optionally validate against DB schema."""
    patterns = [
        r"\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        r"\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        r"\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        r"\bINTO\s+([a-zA-Z_][a-zA-Z0-9_]*)",
    ]
    found: set[str] = set()
    for sql in extract_sql_strings(code):
        for pattern in patterns:
            for match in re.findall(pattern, sql, flags=re.IGNORECASE):
                table = match.strip().lower()
                if table in {"select", "where", "group", "order", "on"}:
                    continue
                if valid_tables and table not in valid_tables:
                    continue
                found.add(table)
    return sorted(found)


def extract_file_inputs(code: str) -> list[dict[str, str]]:
    """Extract data file inputs from direct and composed path references."""
    files = []
    # Direct literal paths like "data/foo/bar.csv"
    for match in re.findall(r"data/[\w\-./()]+", code):
        files.append({"path": match, "description": "Referenced directly in analysis script."})

    # Composed paths like DATA_DIR / "foo" / "bar.csv"
    for match in re.finditer(r"DATA_DIR(?P<parts>(?:\s*/\s*['\"][^'\"]+['\"])+)", code):
        parts = re.findall(r"['\"]([^'\"]+)['\"]", match.group("parts"))
        if parts:
            files.append(
                {
                    "path": "data/" + "/".join(parts),
                    "description": "Referenced via DATA_DIR path composition in analysis script.",
                }
            )

    # Composed paths like PROJECT_ROOT / "data" / "foo" / "bar.csv"
    for match in re.finditer(
        r"PROJECT_ROOT\s*/\s*['\"]data['\"](?P<parts>(?:\s*/\s*['\"][^'\"]+['\"])+)",
        code,
    ):
        parts = re.findall(r"['\"]([^'\"]+)['\"]", match.group("parts"))
        if parts:
            files.append(
                {
                    "path": "data/" + "/".join(parts),
                    "description": "Referenced via PROJECT_ROOT/data path composition in analysis script.",
                }
            )

    unique = {(f["path"], f["description"]): f for f in files}
    return sorted(unique.values(), key=lambda x: x["path"])


def extract_dependencies(code: str) -> list[str]:
    """Extract imported third-party dependency names from python AST."""
    stdlib = set(getattr(sys, "stdlib_module_names", set()))
    deps: set[str] = set()
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root and root not in stdlib and root not in LOCAL_PACKAGES:
                    deps.add(root)
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            root = node.module.split(".", 1)[0]
            if root and root not in stdlib and root not in LOCAL_PACKAGES:
                deps.add(root)
    return sorted(deps)


def one_sentence_summary(readme_path: Path) -> str:
    """Extract a one-sentence summary from README body text."""
    text = readme_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines()]
    body = [line for line in lines if line and not line.startswith("#")]
    if not body:
        return "Summary pending."
    first_para = []
    for line in body:
        if not line:
            break
        first_para.append(line)
    candidate = " ".join(first_para).strip()
    match = re.match(r"^(.+?[.!?])(\s|$)", candidate)
    if match:
        return match.group(1).strip()
    return candidate


def build_manifest(analysis_dir: Path) -> dict:
    """Build a manifest payload for one analysis directory."""
    number = int(analysis_dir.name.split("_", 1)[0])
    code = (analysis_dir / "main.py").read_text(encoding="utf-8")
    readme_path = analysis_dir / "README.md"
    readme_title = readme_path.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
    valid_tables = known_db_tables()

    return {
        "kind": "analysis",
        "title": readme_title or analysis_dir.name,
        "description": one_sentence_summary(readme_path),
        "group": group_for(number),
        "tables": extract_tables(code, valid_tables),
        "dependencies": extract_dependencies(code),
        "files": extract_file_inputs(code),
        "analyses": [],
    }


def main() -> None:
    """Generate or update SOURCES.yaml files for analyses."""
    written = 0
    for analysis_dir in sorted(ANALYSES_DIR.glob("[0-9][0-9]_*")):
        manifest_path = analysis_dir / "SOURCES.yaml"
        auto_payload = build_manifest(analysis_dir)
        if manifest_path.exists():
            existing = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
            for key in ["kind", "title", "group", "tables", "dependencies", "files", "analyses"]:
                if key not in existing:
                    existing[key] = auto_payload[key]
            existing["tables"] = auto_payload["tables"]
            existing["dependencies"] = auto_payload["dependencies"]
            existing["files"] = auto_payload["files"]
            existing["description"] = auto_payload["description"]
            payload = existing
        else:
            payload = auto_payload
        new_text = yaml.safe_dump(payload, sort_keys=False)
        old_text = manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else ""
        if new_text != old_text:
            manifest_path.write_text(new_text, encoding="utf-8")
            written += 1
            print(f"Updated {manifest_path.relative_to(PROJECT_ROOT)}")
    print(f"Done. Updated {written} manifests.")


if __name__ == "__main__":
    main()
