#!/usr/bin/env python3
"""
Safe workspace cleanup utility.
- Removes common cache/build/OS junk files and folders.
- Skips critical state (e.g., Terraform tfstate).
- Dry-run by default; use --apply to actually delete.
- Optional --include-venv to remove virtualenv folders.
"""
from __future__ import annotations
import argparse
import fnmatch
import os
import shutil
from dataclasses import dataclass
from typing import Iterable, List, Tuple

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

DIR_PATTERNS = [
    '**/__pycache__',
    '**/.pytest_cache',
    '**/.mypy_cache',
    '**/.ipynb_checkpoints',
    '**/.ruff_cache',
    '**/.cache',
    '**/.terraform',  # safe; contains plugin cache; not state
    '**/.terraform/modules',
]

FILE_PATTERNS = [
    '*.pyc', '*.pyo', '*.pyd',
    '.DS_Store', 'Thumbs.db', 'ehthumbs.db',
    '*.swp', '*.swo', '*~',
    'crash.log', 'crash.*.log',
    # Logs are usually disposable; keep this conservative
    '*.log',
]

# Explicitly DO NOT delete: terraform.tfstate, terraform.tfstate.*
SKIP_FILE_PATTERNS = [
    'terraform.tfstate', 'terraform.tfstate.*', '.terraform.lock.hcl'
]

# Virtualenv patterns (optional)
VENV_DIR_PATTERNS = ['**/.venv', '**/venv', '**/env', '**/ENV', '**/env.bak', '**/venv.bak']

@dataclass
class RemovalPlan:
    files: List[str]
    dirs: List[str]


def _glob_walk(root: str) -> Iterable[str]:
    for dirpath, dirnames, filenames in os.walk(root):
        # yield dirs with trailing slash marker for matching convenience
        for d in dirnames:
            yield os.path.join(dirpath, d)
        for f in filenames:
            yield os.path.join(dirpath, f)


def _match_any(path: str, patterns: Iterable[str]) -> bool:
    name = os.path.basename(path)
    # Skip Windows reserved device names that can break relpath
    reserved = {"con", "prn", "aux", "nul", "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9", "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9"}
    if name.lower() in reserved or path.lower().startswith('\\\\.\\'):
        return False
    try:
        rel = os.path.relpath(path, ROOT)
    except Exception:
        rel = name
    for pat in patterns:
        if fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(path, pat):
            return True
    return False


def build_plan(include_venv: bool = False) -> RemovalPlan:
    files: List[str] = []
    dirs: List[str] = []

    dir_patterns = DIR_PATTERNS + (VENV_DIR_PATTERNS if include_venv else [])

    # First collect directories to remove entirely
    for path in _glob_walk(ROOT):
        if os.path.isdir(path):
            if _match_any(path, dir_patterns):
                dirs.append(path)
        else:
            # file
            if _match_any(path, SKIP_FILE_PATTERNS):
                continue
            if _match_any(path, FILE_PATTERNS):
                files.append(path)

    # De-duplicate and sort longest path first for dirs (to remove nested first)
    dirs = sorted(set(dirs), key=lambda p: (-len(p), p))
    files = sorted(set(files))

    # Safety: don't include ROOT itself
    dirs = [d for d in dirs if os.path.abspath(d) != ROOT]

    return RemovalPlan(files=files, dirs=dirs)


def apply_plan(plan: RemovalPlan) -> Tuple[int, int]:
    removed_files = 0
    removed_dirs = 0

    # Remove files first
    for f in plan.files:
        try:
            if os.path.exists(f) and os.path.isfile(f):
                os.remove(f)
                removed_files += 1
        except Exception:
            pass

    # Remove directories
    for d in plan.dirs:
        try:
            if os.path.exists(d) and os.path.isdir(d):
                shutil.rmtree(d, ignore_errors=True)
                removed_dirs += 1
        except Exception:
            pass

    return removed_files, removed_dirs


def human_count(n: int, word: str) -> str:
    return f"{n} {word}{'' if n==1 else 's'}"


def main():
    ap = argparse.ArgumentParser(description='Clean workspace junk safely')
    ap.add_argument('--apply', action='store_true', help='Actually delete files (default is dry-run)')
    ap.add_argument('--include-venv', action='store_true', help='Also remove virtualenv folders (.venv/venv/env)')
    args = ap.parse_args()

    plan = build_plan(include_venv=args.include_venv)

    print(f"Workspace: {ROOT}")
    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print(f"Include venv: {'YES' if args.include_venv else 'no'}")

    print('\nPlanned directory removals:')
    for d in plan.dirs:
        print('  [DIR] ', os.path.relpath(d, ROOT))

    print('\nPlanned file removals:')
    for f in plan.files[:200]:
        print('  [FILE]', os.path.relpath(f, ROOT))
    if len(plan.files) > 200:
        print(f"  ... and {len(plan.files)-200} more files")

    if args.apply:
        files_removed, dirs_removed = apply_plan(plan)
        print(f"\nRemoved {human_count(files_removed, 'file')} and {human_count(dirs_removed, 'directory')}.")
    else:
        print(f"\nDry-run only. Use --apply to delete these items.")

if __name__ == '__main__':
    main()
