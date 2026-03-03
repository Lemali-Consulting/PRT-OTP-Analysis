"""Auto-generate SOURCES.yaml for analyses by scanning each main.py file."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ANALYSES_DIR = PROJECT_ROOT / "analyses"

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


def extract_tables(code: str) -> list[str]:
    """Extract likely table names from SQL snippets in the script text."""
    patterns = [
        r"\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        r"\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        r"\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)",
    ]
    found: set[str] = set()
    for pattern in patterns:
        for match in re.findall(pattern, code, flags=re.IGNORECASE):
            table = match.strip()
            if table.lower() in {"select", "where", "group", "order", "on"}:
                continue
            found.add(table)
    return sorted(found)


def extract_file_inputs(code: str) -> list[dict[str, str]]:
    """Extract explicit data path references from script text."""
    files = []
    for match in re.findall(r"data/[\w\-./()]+", code):
        files.append({"path": match, "description": "Referenced directly in analysis script."})
    unique = {(f["path"], f["description"]): f for f in files}
    return sorted(unique.values(), key=lambda x: x["path"])


def build_manifest(analysis_dir: Path) -> dict:
    """Build a manifest payload for one analysis directory."""
    number = int(analysis_dir.name.split("_", 1)[0])
    code = (analysis_dir / "main.py").read_text(encoding="utf-8")
    readme_title = (analysis_dir / "README.md").read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()

    return {
        "kind": "analysis",
        "title": readme_title or analysis_dir.name,
        "group": group_for(number),
        "tables": extract_tables(code),
        "files": extract_file_inputs(code),
        "analyses": [],
    }


def main() -> None:
    """Generate SOURCES.yaml files for all analyses missing one."""
    written = 0
    for analysis_dir in sorted(ANALYSES_DIR.glob("[0-9][0-9]_*")):
        manifest_path = analysis_dir / "SOURCES.yaml"
        if manifest_path.exists():
            continue
        payload = build_manifest(analysis_dir)
        manifest_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        written += 1
        print(f"Wrote {manifest_path.relative_to(PROJECT_ROOT)}")
    print(f"Done. Wrote {written} manifests.")


if __name__ == "__main__":
    main()
