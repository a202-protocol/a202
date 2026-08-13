#!/usr/bin/env python3
"""Check that the npm placeholder package states the identifiers this tree defines.

`packages/a202-protocol/` is the source of the package published to npm as
`a202-protocol`. The JavaScript SDK does not exist yet, so the package carries
no implementation: it holds the name and exports the protocol identifiers, and
the whole of its value is that those identifiers are correct. A published
package that names a specification version the specification no longer uses is
worse than an unpublished one, because an implementer who reads it is told
something false by an artifact that looks authoritative.

TRADEMARK.md, under Nominative use, lists the specification version string
among the identifiers an implementation has to reproduce in order to
interoperate. That makes it a controlled value rather than incidental text, and
a copy of a controlled value needs something holding it to the original. This
script is that something. It reports three kinds of defect:

    drift       an identifier in the package that disagrees with the tree
    missing     an identifier the package is expected to export and does not
    shape       a package.json field that would publish the wrong thing

The normative source for the version string is the `spec_version` const in
schemas/v0.1/commercial-kernel.schema.json, which the digest file covers. A
version bump therefore fails here until the package is updated with it.

This script does not publish and does not check the registry. Whether the
published tarball matches this directory is a question about a release, and
RELEASES.md is where that belongs; this only keeps the source honest.

Exits 1 if any defect is found, 0 otherwise.
"""

import json
import os
import re
import subprocess
import sys

PACKAGE = "packages/a202-protocol"
KERNEL = "schemas/v0.1/commercial-kernel.schema.json"

# The identifiers index.js exports, and where each one's truth lives. The
# homepage and schema host are the deployed locations named across the tree;
# the repository is the one the specification is published from.
EXPECTED = {
    "name": "A202",
    "homepage": "https://a202.org",
    "repository": "https://github.com/a202-protocol/a202",
    "schemas": "https://schemas.a202.org",
}

EXPORT = re.compile(r"""^\s*(\w+)\s*:\s*["']([^"']*)["']\s*,?\s*$""", re.M)


def repo_root():
    return subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def spec_version(root):
    """The specification version string the kernel schema requires."""
    with open(os.path.join(root, KERNEL), encoding="utf-8") as handle:
        schema = json.load(handle)
    return schema["properties"]["spec_version"]["const"]


def exports(root):
    """The string-valued fields index.js exports, as a dict."""
    with open(os.path.join(root, PACKAGE, "index.js"), encoding="utf-8") as handle:
        return dict(EXPORT.findall(handle.read()))


def main():
    root = repo_root()
    defects = []

    found = exports(root)
    expected = dict(EXPECTED, specVersion=spec_version(root))

    for key, want in expected.items():
        got = found.get(key)
        if got is None:
            defects.append((f"{PACKAGE}/index.js", f"missing: {key} is not exported"))
        elif got != want:
            defects.append(
                (
                    f"{PACKAGE}/index.js",
                    f"drift: {key} is {got!r}, the tree says {want!r}",
                )
            )

    with open(os.path.join(root, PACKAGE, "package.json"), encoding="utf-8") as handle:
        manifest = json.load(handle)

    # A wrong name publishes under a name the project does not hold, and a
    # wrong entry point publishes a package that does not load. Both are
    # unrecoverable once released, because a version is never republished.
    if manifest.get("name") != "a202-protocol":
        defects.append((f"{PACKAGE}/package.json", f"shape: name is {manifest.get('name')!r}"))
    if manifest.get("license") != "Apache-2.0":
        defects.append(
            (f"{PACKAGE}/package.json", f"shape: license is {manifest.get('license')!r}")
        )
    main_file = manifest.get("main", "index.js")
    if not os.path.exists(os.path.join(root, PACKAGE, main_file)):
        defects.append((f"{PACKAGE}/package.json", f"shape: main {main_file!r} does not exist"))
    for name in manifest.get("files", []):
        if not os.path.exists(os.path.join(root, PACKAGE, name)):
            defects.append(
                (f"{PACKAGE}/package.json", f"shape: files names {name!r}, which does not exist")
            )
    if main_file not in manifest.get("files", [main_file]):
        defects.append(
            (f"{PACKAGE}/package.json", f"shape: files omits main {main_file!r}")
        )

    for source, defect in defects:
        print(f"{source}: {defect}")

    print(
        f"\n{len(expected)} identifiers checked in {PACKAGE}, {len(defects)} defective"
    )
    return 1 if defects else 0


if __name__ == "__main__":
    sys.exit(main())
