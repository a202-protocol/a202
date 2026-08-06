"""Carrier extension declaration handling.

Pure functions over declaration documents, per the carrier binding,
bindings/a2a-binding-v0.1.md sections 2 to 4. There is no network access
here: retrieving a counterparty's capability surface is the caller's
concern, and an unretrievable surface is passed in as None.

Every failure mode returns the single refusal A202-EXTENSION-UNSUPPORTED.
The four conditions have exactly one correct outcome, and a caller handed
four codes that must be handled identically will eventually handle one
differently, so the code does not vary. The check runs before any
commercial object is transmitted, and there is no downgrade path to a bare
carrier exchange.
"""

from __future__ import annotations

import re

COMMERCIAL_EXTENSION_URI = "https://schemas.a202.org/a2a-ext/commercial/0.1"
A202_EXTENSION_UNSUPPORTED = "A202-EXTENSION-UNSUPPORTED"

_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+$")


def build_declaration(
    read_versions: list[str],
    write_version: str,
    required: bool = True,
    description: str = "Exchanges A202 commercial objects.",
) -> dict:
    """One entry for the extension array of a capability declaration.

    read_versions and write_version have the meanings of the release policy
    section 4; a party never writes a version it cannot read, and that rule
    is enforced here at construction rather than discovered by a
    counterparty.
    """
    for value in [write_version, *read_versions]:
        if not _VERSION_PATTERN.match(value):
            raise ValueError(f"version {value!r} is not of the form MAJOR.MINOR")
    if not read_versions:
        raise ValueError("read_versions must carry at least one entry")
    if write_version not in read_versions:
        raise ValueError("a party never writes a version it cannot read")
    return {
        "uri": COMMERCIAL_EXTENSION_URI,
        "description": description,
        "required": required,
        "params": {
            "read_versions": list(read_versions),
            "write_version": write_version,
        },
    }


def _parse_params(entry: dict) -> tuple[list[str], str] | None:
    params = entry.get("params")
    if not isinstance(params, dict):
        return None
    read_versions = params.get("read_versions")
    write_version = params.get("write_version")
    if not isinstance(read_versions, list) or not read_versions:
        return None
    if not isinstance(write_version, str):
        return None
    for value in read_versions + [write_version]:
        if not isinstance(value, str) or not _VERSION_PATTERN.match(value):
            return None
    return read_versions, write_version


def check_counterparty(
    own_declaration: dict,
    counterparty_extensions: list[dict] | None,
) -> str | None:
    """Evaluate a counterparty's declared extensions against our own entry.

    Returns None when the exchange may proceed, and the refusal code
    otherwise. counterparty_extensions is the counterparty's extension
    array, or None when its capability surface could not be retrieved at
    all. Unavailability is not permission: a party that cannot be checked
    has not passed the check.
    """
    own = _parse_params(own_declaration)
    if own is None or own_declaration.get("uri") != COMMERCIAL_EXTENSION_URI:
        raise ValueError("own declaration is not a valid extension entry")
    own_read, own_write = own

    if counterparty_extensions is None:
        return A202_EXTENSION_UNSUPPORTED

    entry = next(
        (
            item
            for item in counterparty_extensions
            if isinstance(item, dict) and item.get("uri") == COMMERCIAL_EXTENSION_URI
        ),
        None,
    )
    if entry is None:
        return A202_EXTENSION_UNSUPPORTED

    parsed = _parse_params(entry)
    if parsed is None:
        return A202_EXTENSION_UNSUPPORTED
    their_read, their_write = parsed

    # Mismatch fails closed in both directions: no nearest version, no
    # fallback to an earlier extension URI, no partial match.
    if their_write not in own_read or own_write not in their_read:
        return A202_EXTENSION_UNSUPPORTED
    return None
