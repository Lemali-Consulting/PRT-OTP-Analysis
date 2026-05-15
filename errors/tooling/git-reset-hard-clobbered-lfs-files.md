---
title: git reset --hard clobbered LFS files
date: 2026-05-15T17:54:36Z
---

## What happened

`git-lfs` is not installed on this machine, but `data/prt.db` and
`data/GTFS/stop_times.txt` are tracked via Git LFS (see `.gitattributes`).
Running `git reset --hard origin/main` to sync a diverged local branch
overwrote both files with their 133-byte LFS *pointer* text instead of the
real content (61 MB database, 65 MB CSV). Without git-lfs, the smudge filter
never runs, so git treats the pointer blob as the file's true content.

Any analysis or pipeline step touching `prt.db` immediately failed with
`sqlite3.DatabaseError: file is not a database`.

## How it was discovered

A sanity-check query against `prt.db` (`SELECT name FROM sqlite_master`)
raised `file is not a database` right after the reset. Inspecting the file
showed it was 133 bytes of `version https://git-lfs.github.com/spec/v1` text.

## What was done

1. Installed the `git-lfs` v3.5.1 binary into `~/.local/bin` (no sudo needed)
   from the official GitHub release tarball.
2. Ran `git lfs install --local` then `git lfs pull`, which fetched the real
   LFS objects from the remote and restored both files.
3. Deleted the stale `prt.db-shm` / `prt.db-wal` sidecar files left over from
   the pre-reset database so SQLite would not see a mismatched WAL.

Prevention: before any `git reset --hard`, `checkout`, or branch switch in a
repo whose `.gitattributes` declares `filter=lfs`, confirm `git lfs` is
installed (`git lfs version`). If it is not, the operation will silently
replace LFS files with pointers. Recovery requires git-lfs and network access
to the LFS remote. A `## Mistakes` entry was added to project `CLAUDE.md`.

## Relevant commits

- Recovery used no commits — `git lfs pull` restores working-tree files only.
- `analysis-46-wip` (local branch, commit `95ddb1e`) holds the superseded
  duplicate analysis work; it does not touch the LFS files.
