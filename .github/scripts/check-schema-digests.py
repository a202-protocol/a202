#!/usr/bin/env python3
"""Check that schemas/digests-v0.1.json describes the schemas in the tree.

RELEASES.md section 3.2 requires a release to carry a digest for every schema
file, so that an implementer can verify that the schema it validates against
is the schema that was released. A digest file that is written once and then
drifts from the schemas beside it is worse than none, because it states
something false with the authority of a hash.

This script is what stops the drift. It reports four kinds of defect:

    missing     a schema file in the tree that the digest file does not name
    unknown     a path the digest file names that is not in the tree
    mismatch    a digest that is not the digest of the file's bytes
    id          a recorded $id that is not the schema's own $id

The digest covers the bytes of the file on disk, whole and unmodified. It is
not the canonical form of canonical-commercial-model-v0.1.md section 4, which
covers commercial objects and omits fields a schema document does not carry.

The conformance manifest is checked the same way, under RELEASES.md
section 3.3, so that the fixture set a release names is as verifiable as the
schemas.

Regenerate the digest file after any schema or manifest change:

    python3 .github/scripts/check-schema-digests.py --write

Exits 1 if any defect is found, 0 otherwise.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys

DIGESTS = "schemas/digests-v0.1.json"
MANIFEST = "conformance/manifest-v0.1.json"


def repo_root():
    return subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def digest_of(root, rel):
    with open(os.path.join(root, rel), "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def schema_files(root):
    """Every JSON Schema file git knows about, as paths relative to the root."""
    out = subprocess.run(
        ["git", "-C", root, "ls-files", "-z", "schemas/**/*.schema.json"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return sorted(p for p in out.split("\0") if p)


def schema_id(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as handle:
        return json.load(handle).get("$id")


def build(root):
    existing = {}
    path = os.path.join(root, DIGESTS)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            existing = json.load(handle)
    return {
        "spec_version": existing.get("spec_version", "a202-commercial/0.1"),
        "release": existing.get("release", "v0.1.0"),
        "algorithm": "sha-256",
        "encoding": "hex-lower",
        "covers": existing.get("covers", ""),
        "description": existing.get("description", ""),
        "schemas": [
            {
                "path": rel,
                "id": schema_id(root, rel),
                "digest": digest_of(root, rel),
            }
            for rel in schema_files(root)
        ],
        "conformance_manifest": {
            "path": MANIFEST,
            "digest": digest_of(root, MANIFEST),
            "note": existing.get("conformance_manifest", {}).get("note", ""),
        },
    }


def check(root):
    with open(os.path.join(root, DIGESTS), encoding="utf-8") as handle:
        recorded = json.load(handle)

    if recorded.get("algorithm") != "sha-256":
        print("algorithm: only sha-256 is defined for v0.1", file=sys.stderr)
        return 1

    by_path = {entry["path"]: entry for entry in recorded["schemas"]}
    on_disk = schema_files(root)
    defects = []

    for rel in on_disk:
        if rel not in by_path:
            defects.append(f"missing   {rel}: in the tree, not in {DIGESTS}")
            continue
        entry = by_path[rel]
        actual = digest_of(root, rel)
        if entry["digest"] != actual:
            defects.append(
                f"mismatch  {rel}: recorded {entry['digest']}, actual {actual}"
            )
        declared = schema_id(root, rel)
        if entry.get("id") != declared:
            defects.append(
                f"id        {rel}: recorded {entry.get('id')}, declared {declared}"
            )

    for rel in by_path:
        if rel not in on_disk:
            defects.append(f"unknown   {rel}: in {DIGESTS}, not in the tree")

    manifest = recorded.get("conformance_manifest", {})
    actual = digest_of(root, MANIFEST)
    if manifest.get("digest") != actual:
        defects.append(
            f"mismatch  {MANIFEST}: recorded {manifest.get('digest')}, actual {actual}"
        )

    if defects:
        for defect in defects:
            print(defect, file=sys.stderr)
        print(
            f"\n{len(defects)} defect(s). Regenerate with: "
            "python3 .github/scripts/check-schema-digests.py --write",
            file=sys.stderr,
        )
        return 1

    print(
        f"{len(on_disk)} schema files and the conformance manifest match "
        f"the digests recorded in {DIGESTS}"
    )
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="rewrite the digest file from the tree instead of checking it",
    )
    args = parser.parse_args()
    root = repo_root()

    if args.write:
        built = build(root)
        with open(os.path.join(root, DIGESTS), "w", encoding="utf-8") as handle:
            json.dump(built, handle, indent=2)
            handle.write("\n")
        print(f"wrote {len(built['schemas'])} schema digests to {DIGESTS}")
        return 0

    return check(root)


if __name__ == "__main__":
    sys.exit(main())
