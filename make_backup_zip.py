#!/usr/bin/env python3
"""Create a backup zip of this project.

Usage:
    python make_backup_zip.py                 # light zip (source only, default)
    python make_backup_zip.py --mode full     # full offline zip (deps + builds + models)
    python make_backup_zip.py --out PATH      # custom output path
    python make_backup_zip.py --out -         # write zip to stdout (pipe it)
    python make_backup_zip.py --mode full --out D:\\backups\\proj.zip

Modes:
  light (default)  Source/config files only. Excludes venvs, node_modules,
                   build outputs, model binaries, caches, logs and .env secrets.
                   Small (~15 MB) — good for sharing or storing in git-adjacent storage.
  full             Everything needed to run offline: node_modules, .venv, backend/venv,
                   whisper.cpp build artifacts and models. Excludes only .git,
                   .freebuff session files, .uv-cache2, __pycache__ and *.pyc junk.
                   Very large (multi-GB) — use for machine-to-machine transfers.

Notes:
  - stdout mode ("--out -") is for piping, e.g.:
        python make_backup_zip.py --out - > backup.zip
  - the script never follows symlinks/junctions; unreadable paths are skipped
    and reported at the end.
  - Windows long paths (>260 chars) are supported via backslash-\\?\\ prefixes.
"""

import argparse
import os
import stat
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(ROOT)

TOP_LEVEL = [
    ".gitignore",
    "backend_launch.log",
    "backend_launch_err.log",
    "docker-compose.yml",
    "netlify.toml",
    "README.md",
    "backend",
    "frontend",
    "whisper.cpp",
]

EXTRA_TOP_LEVEL_FULL = [".venv"]  # only added in full mode

# ---------------------------------------------------------------- light mode
EXCLUDE_DIRS_LIGHT = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    ".venv-canary",
    ".uv-cache2",
    ".uv-cache",
    "node_modules",
    "build",
    "dist",
    ".next",
    ".nemo-src",
    ".freebuff",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".turbo",
    ".cache",
}
# Path-specific exclusions (relative POSIX paths, prefix-matched):
# whisper.cpp/models holds multi-GB downloaded ggml binaries. Note: backend/app/models
# is SOURCE CODE and must never be excluded.
EXCLUDE_PATHS_LIGHT = {
    "whisper.cpp/models",
}
EXCLUDE_FILES_LIGHT = {".DS_Store"}
EXCLUDE_SUFFIXES_LIGHT = (".pyc", ".pyo", ".log", ".env")

# ------------------------------------------------------------------ full mode
EXCLUDE_DIRS_FULL = {
    ".git",
    ".freebuff",
    ".uv-cache2",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
EXCLUDE_FILES_FULL = {".DS_Store"}
EXCLUDE_SUFFIXES_FULL = (".pyc", ".pyo")

LIGHT = {
    "dirs": EXCLUDE_DIRS_LIGHT,
    "files": EXCLUDE_FILES_LIGHT,
    "suffixes": EXCLUDE_SUFFIXES_LIGHT,
    "paths": EXCLUDE_PATHS_LIGHT,
}
FULL = {
    "dirs": EXCLUDE_DIRS_FULL,
    "files": EXCLUDE_FILES_FULL,
    "suffixes": EXCLUDE_SUFFIXES_FULL,
    "paths": set(),
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Create a backup zip of this project.")
    p.add_argument(
        "--mode",
        choices=("light", "full"),
        default="light",
        help="light = source only (default); full = include deps/builds/models",
    )
    p.add_argument(
        "--out",
        default=None,
        help="output zip path (default: ../project-backup.zip or ../project-full-backup.zip); '-' for stdout",
    )
    return p.parse_args()


def make_writer(out_path: str):
    """Return (context-manager zip writer, closer)."""
    if out_path == "-":
        sys.stdout.reconfigure(write_through=True)
        return zipfile.ZipFile(
            sys.stdout.buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True
        )
    return zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True)


def is_junction_or_symlink(path: str) -> bool:
    try:
        st = os.lstat(path)
        return stat.S_ISLNK(st.st_mode)
    except OSError:
        return True  # unreadable -> treat as excluded


def collect(include_entries, rules, pref_root: str):
    """Yield (abs_path, arcname) pairs for every file to zip."""
    for entry in include_entries:
        src = os.path.join(pref_root, entry)
        if os.path.isfile(src):
            yield src, entry
            continue
        for dp, dns, fns in os.walk(src):
            rel_dir = os.path.relpath(dp, pref_root).replace("\\", "/")
            if rel_dir == ".":
                rel_dir = ""
            dns[:] = sorted(
                d
                for d in dns
                if d not in rules["dirs"]
                and f"{rel_dir}/{d}".lstrip("/") not in rules["paths"]
                and not is_junction_or_symlink(os.path.join(dp, d))
            )
            for fn in sorted(fns):
                if fn in rules["files"] or fn.lower().endswith(rules["suffixes"]):
                    continue
                full = os.path.join(dp, fn)
                yield full, os.path.relpath(full, pref_root)


def main() -> int:
    args = parse_args()
    mode = args.mode
    rules = LIGHT if mode == "light" else FULL

    include = list(TOP_LEVEL)
    if mode == "full":
        include += EXTRA_TOP_LEVEL_FULL

    if args.out == "-":
        out_path = "-"
    elif args.out:
        out_path = os.path.abspath(args.out)
    else:
        out_path = os.path.join(PARENT, "project-full-backup.zip" if mode == "full" else "project-backup.zip")

    pref_root = "\\\\?\\" + os.path.normpath(ROOT)

    file_count = 0
    byte_count = 0
    skipped = []

    with make_writer(out_path) as zf:
        for abs_path, arcname in collect(include, rules, pref_root):
            try:
                zf.write(abs_path, arcname)
                file_count += 1
                byte_count += os.path.getsize(abs_path)
            except (OSError, ValueError) as exc:
                skipped.append((arcname, str(exc)))

    if out_path == "-":
        # no console summary on stdout; summary goes to stderr
        print(f"files={file_count} skipped={len(skipped)}", file=sys.stderr)
    else:
        size_mb = os.path.getsize(out_path) / (1024 * 1024)
        print(f"ZIP created: {out_path}")
        print(
            f"files={file_count}  skipped={len(skipped)}  "
            f"uncompressed={byte_count/1024/1024:.1f}MB  zip={size_mb:.1f}MB"
        )

    for arcname, err in skipped[:20]:
        print(f"SKIP {arcname}: {err}", file=sys.stderr)
    if len(skipped) > 20:
        print(f"... and {len(skipped)-20} more skipped", file=sys.stderr)

    return 0 if not skipped else 2  # exit 2 = partial (some files skipped)


if __name__ == "__main__":
    sys.exit(main())
