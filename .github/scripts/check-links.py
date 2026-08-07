#!/usr/bin/env python3
"""Check that every markdown link in this repository resolves inside the tree.

CONTRIBUTING.md rule 5 states that no path or link leaves this repository, and that
every relative link and every referenced path must resolve inside this tree.
The rule was stated in prose with nothing checking it. This script checks it.

It reads every tracked markdown file, extracts inline links, images, and
reference-style link definitions, and reports three kinds of defect:

    missing     a relative target that does not exist on disk
    escaping    a relative target that resolves outside the repository root
    external    a target carrying a URL scheme, which leaves the tree by
                definition. `mailto:` is allowed, because an address is a
                correspondence route rather than a path out of the tree.
                In `docs/` — the pages authored for the site, informative
                in full — an `https:` link is also allowed: a site page
                that describes other projects cites their published
                documents, and a citation is a reference to a source, not
                a dependency of the specification. Specification documents
                keep the absolute rule

Links inside fenced code blocks and inline code spans are skipped: a link in an
example is a sample of what an implementation would emit, not a reference this
repository makes. Fragments are stripped before resolution and the headings
they name are not checked.

Exits 1 if any defect is found, 0 otherwise.
"""

import os
import re
import subprocess
import sys

INLINE_LINK = re.compile(
    r"""!?\[[^\]]*\]\(\s*(<[^>\n]*>|[^)\s]+)(?:\s+["'][^"'\n]*["'])?\s*\)"""
)
REFERENCE_DEF = re.compile(r"""^[ ]{0,3}\[[^\]^][^\]]*\]:\s*(<[^>\n]*>|\S+)""", re.M)
FENCE = re.compile(r"^[ ]{0,3}(`{3,}|~{3,}).*$")
INLINE_CODE = re.compile(r"(`+)(?:.|\n)*?\1")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")


def tracked_markdown(root):
    """Every markdown file git knows about, as paths relative to the root."""
    out = subprocess.run(
        ["git", "-C", root, "ls-files", "-z", "*.md"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return sorted(p for p in out.split("\0") if p)


def strip_code(text):
    """Blank out fenced blocks and inline code spans, preserving line numbers."""
    lines = text.split("\n")
    kept = []
    fence = None
    for line in lines:
        match = FENCE.match(line)
        if fence is None and match:
            fence = match.group(1)[0] * 3
            kept.append("")
            continue
        if fence is not None:
            if match and match.group(1)[0] * 3 == fence:
                fence = None
            kept.append("")
            continue
        kept.append(line)
    joined = "\n".join(kept)
    return INLINE_CODE.sub(lambda m: " " * len(m.group(0)), joined)


def targets(text):
    """Yield (line number, raw target) for every link in the stripped text."""
    for pattern in (INLINE_LINK, REFERENCE_DEF):
        for match in pattern.finditer(text):
            target = match.group(1)
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            yield text.count("\n", 0, match.start()) + 1, target


def classify(root, source, target):
    """Return a defect string for this target, or None if it resolves."""
    target = target.strip()
    if not target or target.startswith("#"):
        return None
    if SCHEME.match(target):
        if target.lower().startswith("mailto:"):
            return None
        if source.startswith("docs/") and target.lower().startswith("https:"):
            return None
        return "external: leaves the repository"
    path = target.split("#", 1)[0].split("?", 1)[0]
    if not path:
        return None
    path = path.replace("%20", " ")
    if path.startswith("/"):
        return "escaping: absolute path, which does not resolve inside the tree"
    base = os.path.dirname(os.path.join(root, source))
    resolved = os.path.normpath(os.path.join(base, path))
    inside = os.path.commonpath([os.path.realpath(root), os.path.realpath(resolved)])
    if inside != os.path.realpath(root):
        return "escaping: resolves outside the repository root"
    if not os.path.exists(resolved):
        return "missing: no such file or directory"
    return None


def main():
    root = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    files = tracked_markdown(root)
    defects = []
    links = 0

    for source in files:
        with open(os.path.join(root, source), encoding="utf-8") as handle:
            text = strip_code(handle.read())
        for line, target in targets(text):
            links += 1
            defect = classify(root, source, target)
            if defect:
                defects.append((source, line, target, defect))

    for source, line, target, defect in defects:
        print(f"{source}:{line}: {target}  {defect}")

    print(
        f"\n{links} links checked across {len(files)} markdown files, "
        f"{len(defects)} defective"
    )
    return 1 if defects else 0


if __name__ == "__main__":
    sys.exit(main())
