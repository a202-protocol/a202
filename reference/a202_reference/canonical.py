"""RFC 8785 canonicalization for the JSON subset the kernel emits.

The specification carries money, percentages, and quantities as base-10
strings, so the only numbers that legitimately appear in a shared object are
integers such as version and sequence counters. A non-integer number in an
object is therefore refused here rather than serialized: accepting one would
canonicalize a value the specification never permits, and the two encoders
that disagree about its digits would produce two different signatures over
what a reader believes is one object.

Object members are ordered by the UTF-16 code units of their names, which is
the RFC 8785 rule. Sorting the UTF-16BE encoding of each name gives exactly
that order, including for names containing supplementary-plane characters,
where Python's native string order would differ.
"""

from __future__ import annotations

import hashlib

# Fields excluded from the hashed bytes, per canonical model section 4. The
# hash covers the object's content, never the framing around it, so a
# control-plane annotation attached after signing can never become load
# bearing and a signature never covers its own value.
EXCLUDED_TOP_LEVEL_FIELDS = ("content_hash", "signatures", "kernel_annotations")

_ESCAPES = {
    '"': '\\"',
    "\\": "\\\\",
    "\b": "\\b",
    "\f": "\\f",
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}


def _serialize_string(value: str) -> str:
    out = ['"']
    for ch in value:
        if ch in _ESCAPES:
            out.append(_ESCAPES[ch])
        elif ord(ch) < 0x20:
            out.append("\\u%04x" % ord(ch))
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _serialize(value) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return _serialize_string(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        raise ValueError(
            "non-integer number in a shared object; the specification carries "
            "decimal values as base-10 strings"
        )
    if isinstance(value, list):
        return "[" + ",".join(_serialize(item) for item in value) + "]"
    if isinstance(value, dict):
        members = []
        for key in sorted(value.keys(), key=lambda k: k.encode("utf-16-be")):
            if not isinstance(key, str):
                raise ValueError("object member names must be strings")
            members.append(_serialize_string(key) + ":" + _serialize(value[key]))
        return "{" + ",".join(members) + "}"
    raise ValueError(f"unserializable type in a shared object: {type(value).__name__}")


def canonicalize(value) -> str:
    """Serialize a JSON value under RFC 8785 for the kernel's JSON subset."""
    return _serialize(value)


def canonical_bytes(obj: dict) -> bytes:
    """The bytes an object's content hash and signatures cover.

    content_hash, signatures, and kernel_annotations are omitted at the top
    level, exactly as the conformance runner and canonical model section 4
    require.
    """
    stripped = {
        key: value
        for key, value in obj.items()
        if key not in EXCLUDED_TOP_LEVEL_FIELDS
    }
    return canonicalize(stripped).encode("utf-8")


def content_hash(obj: dict) -> str:
    """Lowercase hexadecimal SHA-256 over the canonical bytes."""
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()
