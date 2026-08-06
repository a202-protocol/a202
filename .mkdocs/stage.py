#!/usr/bin/env python3
"""Assemble the MkDocs docs directory from the tracked tree.

The specification sources stay where they are; this script mirrors every
tracked file into `.mkdocs/stage/`, which `mkdocs.yml` uses as its docs
directory. Mirroring the whole tree, not just the markdown, keeps every
relative link in the documents resolving on the site exactly as it resolves
in the repository: a link to a fixture, the manifest, or the runner serves
the file itself.

Two kinds of content are treated specially:

- `docs/` holds the pages authored for the site: the landing page, the
  introduction, and the topic pages. They are promoted to the root of the
  stage so they publish at the site root. Because that promotion moves them
  up one directory level, exactly one leading `../` is stripped from every
  relative markdown link they carry. In the repository the links resolve
  from `docs/`; on the site they resolve from the root; both are checked,
  the first by `.github/scripts/check-links.py` and the second by the
  MkDocs build.
- The repository `README.md` is not mirrored. It is the repository's front
  door; the site's front door is `docs/index.md`.

Also excluded from the mirror: repository machinery that is not part of
the specification set (`.github/`, the MkDocs configuration itself, and
the editor and git configuration files). `.mkdocs/assets/` is copied into
the stage so the theme can reference the favicon and stylesheet.

Run from the repository root:

    python3 .mkdocs/stage.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGE = ROOT / ".mkdocs" / "stage"
ASSETS = ROOT / ".mkdocs" / "assets"
DOCS = "docs/"

EXCLUDED_PREFIXES = (".github/", ".mkdocs/")
EXCLUDED_FILES = {
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "README.md",
    "mkdocs.yml",
    "requirements-docs.txt",
}


def tracked_files() -> list:
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    return [line for line in out.splitlines() if line]


def promote(rel: str) -> None:
    """Copy a docs/ page to the stage root, stripping one ../ per link."""
    src = ROOT / rel
    dest = STAGE / rel[len(DOCS):]
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix == ".md":
        text = src.read_text(encoding="utf-8")
        dest.write_text(text.replace("](../", "]("), encoding="utf-8")
    else:
        shutil.copy2(src, dest)


def main() -> int:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)

    mirrored = 0
    promoted = 0
    for rel in tracked_files():
        if rel in EXCLUDED_FILES or rel.startswith(EXCLUDED_PREFIXES):
            continue
        if rel.startswith(DOCS):
            promote(rel)
            promoted += 1
            continue
        src = ROOT / rel
        dest = STAGE / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        mirrored += 1

    if ASSETS.is_dir():
        shutil.copytree(ASSETS, STAGE / "assets", dirs_exist_ok=True)

    print(
        f"staged {mirrored} tracked files and {promoted} site pages "
        f"into {STAGE.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
