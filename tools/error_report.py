"""CLI tool for logging errors, bugs, and mistakes into the errors/ directory."""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ERRORS_DIR = Path(__file__).resolve().parent.parent / "errors"


def slugify(text: str) -> str:
    """Convert a short title to a filename-safe slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def cmd_list(args):
    """List all existing error classes (subdirectories of errors/)."""
    classes = sorted(
        d.name for d in ERRORS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")
    )
    if not classes:
        print("No error classes yet.")
        return
    for c in classes:
        print(c)


def cmd_add(args):
    """Create a new error report markdown file."""
    error_class = slugify(args.error_class)
    title = args.title
    slug = slugify(title)

    if not slug:
        print("Error: title produced an empty slug.", file=sys.stderr)
        sys.exit(1)

    class_dir = ERRORS_DIR / error_class
    class_dir.mkdir(parents=True, exist_ok=True)

    filepath = class_dir / f"{slug}.md"
    if filepath.exists():
        print(f"Error: {filepath} already exists.", file=sys.stderr)
        sys.exit(1)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    content = f"""---
title: {title}
date: {now}
---

## What happened

<template-instructions>Describe the error. What was wrong, and what effect did it have on results or code?</template-instructions>

## How it was discovered

<template-instructions>What made you notice the error? A surprising result, a failing test, a code review?</template-instructions>

## What was done

<template-instructions>How was it fixed? List the key changes, files modified, or processes updated.</template-instructions>

## Relevant commits

<template-instructions>List commit hashes and their one-line summaries, e.g. `a0c4f5f` — Fix variable mapping</template-instructions>
"""
    filepath.write_text(content)
    print(filepath)


def main():
    parser = argparse.ArgumentParser(description="Error reporting tool")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List all error classes")

    add_parser = sub.add_parser("add", help="Add a new error report")
    add_parser.add_argument("error_class", help="Error class (subdirectory name)")
    add_parser.add_argument("title", help="Short descriptive title for the error")

    args = parser.parse_args()
    if args.command == "list":
        cmd_list(args)
    elif args.command == "add":
        cmd_add(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
