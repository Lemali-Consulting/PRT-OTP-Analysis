"""Check that SOURCES.yaml provenance metadata is complete for all analyses and pipelines."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANALYSES_DIR = PROJECT_ROOT / "analyses"
PIPELINE_DIR = PROJECT_ROOT / "pipeline"

# Files in output/ that are not analysis artifacts
IGNORED_OUTPUT_FILES = {"__pycache__", ".gitkeep", "README.md"}

ANALYSIS_REQUIRED_FIELDS = {"kind", "title", "description", "group"}
PIPELINE_REQUIRED_FIELDS = {"kind", "title", "description"}

# Pattern matching SQL string literals (triple-quoted or single-quoted strings containing SQL)
_SQL_STRING_PATTERN = re.compile(
    r'(?:r|f|rf|fr)?(?:"""|\'\'\')(.*?)(?:"""|\'\'\')', re.DOTALL
)


def _has_sql_queries(code: str) -> bool:
    """Return True if the code contains SQL query strings (not just Python keywords)."""
    for match in _SQL_STRING_PATTERN.finditer(code):
        text = match.group(1).upper()
        if any(kw in text for kw in ["SELECT ", "FROM ", "JOIN "]):
            return True
    return False


@dataclass
class ValidationResult:
    """Holds errors and warnings for a single directory."""

    directory: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _load_sources(directory: Path) -> dict | None:
    """Load and return SOURCES.yaml as a dict, or None if missing/invalid."""
    path = directory / "SOURCES.yaml"
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def validate_analysis(directory: Path) -> ValidationResult:
    """Validate provenance completeness for a single analysis directory."""
    result = ValidationResult(directory=directory.name)
    sources = _load_sources(directory)

    if sources is None:
        result.errors.append("SOURCES.yaml missing or not a valid mapping")
        return result

    # Required top-level fields
    for field_name in ANALYSIS_REQUIRED_FIELDS:
        if not sources.get(field_name):
            result.errors.append(f"missing required field '{field_name}'")

    # Outputs declared
    outputs = sources.get("outputs")
    if not outputs:
        result.errors.append("missing or empty 'outputs' field")
    elif isinstance(outputs, list):
        for i, entry in enumerate(outputs, 1):
            if not isinstance(entry, dict):
                result.errors.append(f"outputs[{i}] must be a dict, got {type(entry).__name__}")
                continue
            if not entry.get("path"):
                result.errors.append(f"outputs[{i}] missing 'path'")
            if not entry.get("kind"):
                result.errors.append(f"outputs[{i}] missing 'kind'")
            if not entry.get("description"):
                result.errors.append(f"outputs[{i}] missing 'description'")

        # Cross-check: declared vs actual files
        declared_paths = {e["path"] for e in outputs if isinstance(e, dict) and e.get("path")}
        output_dir = directory / "output"
        if output_dir.is_dir():
            actual_files = {
                p.name
                for p in output_dir.iterdir()
                if p.is_file() and p.name not in IGNORED_OUTPUT_FILES
            }
            undeclared = actual_files - declared_paths
            for name in sorted(undeclared):
                result.errors.append(f"output file '{name}' exists but is not declared in outputs")
            missing = declared_paths - actual_files
            for name in sorted(missing):
                result.errors.append(f"output '{name}' declared but file does not exist")

    # Cross-references (analyses field)
    xrefs = sources.get("analyses", [])
    if isinstance(xrefs, list):
        for i, entry in enumerate(xrefs, 1):
            if not isinstance(entry, dict):
                result.errors.append(
                    f"analyses[{i}] must be a dict (mapping with id/relationship), "
                    f"got {type(entry).__name__}"
                )
                continue
            if "id" not in entry:
                result.errors.append(f"analyses[{i}] missing 'id'")
            if not entry.get("relationship"):
                result.errors.append(f"analyses[{i}] missing 'relationship'")

    # Warnings for likely-incomplete auto-generated fields
    main_py = directory / "main.py"
    code = main_py.read_text(encoding="utf-8") if main_py.exists() else ""

    tables = sources.get("tables", [])
    if not tables and _has_sql_queries(code):
        result.warnings.append("main.py contains SQL but 'tables' is empty")

    deps = sources.get("dependencies", [])
    if not deps and "import " in code:
        result.warnings.append("main.py has imports but 'dependencies' is empty")

    return result


def validate_pipeline(directory: Path) -> ValidationResult:
    """Validate provenance completeness for a single pipeline directory."""
    result = ValidationResult(directory=directory.name)
    sources = _load_sources(directory)

    if sources is None:
        result.errors.append("SOURCES.yaml missing or not a valid mapping")
        return result

    # Required top-level fields
    for field_name in PIPELINE_REQUIRED_FIELDS:
        if not sources.get(field_name):
            result.errors.append(f"missing required field '{field_name}'")

    # tables_produced validation
    tables_produced = sources.get("tables_produced")
    if not tables_produced:
        result.errors.append("missing or empty 'tables_produced'")
    elif isinstance(tables_produced, list):
        for i, entry in enumerate(tables_produced, 1):
            if not isinstance(entry, dict):
                result.errors.append(
                    f"tables_produced[{i}] must be a dict, got {type(entry).__name__}"
                )
                continue
            if not entry.get("name"):
                result.errors.append(f"tables_produced[{i}] missing 'name'")
            if not entry.get("description"):
                result.errors.append(f"tables_produced[{i}] missing 'description'")

    # files should have descriptions
    files = sources.get("files", [])
    if isinstance(files, list):
        for i, entry in enumerate(files, 1):
            if isinstance(entry, dict) and not entry.get("description"):
                result.warnings.append(f"files[{i}] missing 'description'")

    return result


def main() -> int:
    """Validate all analyses and pipelines, print report, return exit code."""
    all_results: list[ValidationResult] = []

    for d in sorted(ANALYSES_DIR.glob("[0-9][0-9]_*")):
        if d.is_dir():
            all_results.append(validate_analysis(d))

    if PIPELINE_DIR.is_dir():
        for d in sorted(PIPELINE_DIR.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                all_results.append(validate_pipeline(d))

    total_errors = 0
    total_warnings = 0
    for r in all_results:
        if r.errors or r.warnings:
            print(f"\n{r.directory}:")
            for e in r.errors:
                print(f"  ERROR: {e}")
                total_errors += 1
            for w in r.warnings:
                print(f"  WARN:  {w}")
                total_warnings += 1

    print(f"\n{'=' * 50}")
    print(f"Checked {len(all_results)} directories")
    print(f"Errors:   {total_errors}")
    print(f"Warnings: {total_warnings}")

    if total_errors == 0 and total_warnings == 0:
        print("All provenance metadata is complete.")

    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
