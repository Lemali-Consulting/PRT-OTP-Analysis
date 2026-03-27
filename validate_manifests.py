"""Validate that all pipeline and analysis directories have the required files and content."""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
PIPELINE_DIR = PROJECT_ROOT / "pipeline"
ANALYSES_DIR = PROJECT_ROOT / "analyses"

REQUIRED_FILES = ["README.md", "METHODS.md", "FINDINGS.md", "SOURCES.yaml", "main.py"]
METHODS_SECTIONS = ["Question", "Approach", "Data", "Output"]
SOURCES_REQUIRED_FIELDS = {"kind", "title"}


def _heading_texts(text: str) -> list[str]:
    """Return lowercased ## heading texts from markdown."""
    return [m.group(1).strip().lower() for m in re.finditer(r"^##\s+(.+)$", text, re.MULTILINE)]


def validate_directory(d: Path, kind: str) -> list[str]:
    """Return a list of error strings for a single pipeline/analysis directory."""
    errors: list[str] = []
    label = f"{kind} {d.name}"
    manifest = None

    # Required files
    for fname in REQUIRED_FILES:
        if not (d / fname).exists():
            errors.append(f"{label}: missing {fname}")

    # output/ directory
    if not (d / "output").is_dir():
        errors.append(f"{label}: missing output/ directory")

    # SOURCES.yaml content
    sources_path = d / "SOURCES.yaml"
    if sources_path.exists():
        import yaml

        with open(sources_path, encoding="utf-8") as f:
            manifest = yaml.safe_load(f)
        if not isinstance(manifest, dict):
            errors.append(f"{label}: SOURCES.yaml is not a valid YAML mapping")
        else:
            for field in SOURCES_REQUIRED_FIELDS:
                if field not in manifest:
                    errors.append(f"{label}: SOURCES.yaml missing required field '{field}'")
            if manifest.get("kind") != kind:
                errors.append(
                    f"{label}: SOURCES.yaml kind is '{manifest.get('kind')}', expected '{kind}'"
                )

    # METHODS.md sections
    methods_path = d / "METHODS.md"
    if methods_path.exists():
        headings = _heading_texts(methods_path.read_text(encoding="utf-8"))
        for section in METHODS_SECTIONS:
            if section.lower() not in headings:
                errors.append(f"{label}: METHODS.md missing '## {section}' section")

    # main.py docstring
    main_path = d / "main.py"
    if main_path.exists():
        first_line = main_path.read_text(encoding="utf-8").lstrip().split("\n", 1)[0]
        if not (first_line.startswith('"""') or first_line.startswith("'''")):
            errors.append(f"{label}: main.py missing docstring")

    return errors


def main() -> int:
    all_errors: list[str] = []

    if PIPELINE_DIR.is_dir():
        for d in sorted(PIPELINE_DIR.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                all_errors.extend(validate_directory(d, "pipeline"))

    for d in sorted(ANALYSES_DIR.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            all_errors.extend(validate_directory(d, "analysis"))

    if all_errors:
        print(f"Found {len(all_errors)} issue(s):\n")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    print("All manifests valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
