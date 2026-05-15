---
title: SOURCES.yaml files entries as bare strings break website build
date: 2026-05-15T17:12:59Z
---

## What happened

The `files:` key in `analyses/42_allegheny_go_equity/SOURCES.yaml` and
`analyses/43_allegheny_go_growth/SOURCES.yaml` was hand-written as a list of
bare path strings:

```yaml
files:
- data/allegheny-go/tract_reach.csv
```

The website generator (`products/website/main.py`, `page_sources()`) expects
each `files` entry to be a dict with `path`/`description` keys — the format
produced by `products/website/generate_manifests.py`. Iterating the string
list raised `AttributeError: 'str' object has no attribute 'get'` and aborted
the whole site build. As a result, analyses 42 and 43 (and anything after
them) never got an `index.html` generated, so the site had been un-buildable
since those analyses were committed in `ca57201`.

## How it was discovered

While adding analysis 44 (service productivity), running
`uv run python products/website/main.py` to regenerate the site crashed at
`page_sources`. The traceback pointed at the `files` loop; inspecting the
SOURCES.yaml files for the most recently added analyses revealed the bare
string format.

## What was done

Converted the `files:` entries in both SOURCES.yaml files to the expected
dict form (`- path: ... \n  description: ...`). The canonical format is the
one emitted by `generate_manifests.py`. The website then built cleanly.
No change to the website code was needed, though `page_sources()` could be
made tolerant of bare strings as a future hardening.

## Relevant commits

<template-instructions>List commit hashes and their one-line summaries.</template-instructions>
