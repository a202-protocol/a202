"""Minimal reference implementation of the A202 wire.

Emission, validation, canonicalization, signatures, evidence verification,
and carrier extension declaration handling. No operator logic, no network.
The specification documents in this repository are the definition; where this
package and a document disagree, the document governs.
"""

from .canonical import canonical_bytes, canonicalize, content_hash
from .emission import PREFIXES, make_object, new_id
from .extension import (
    A202_EXTENSION_UNSUPPORTED,
    COMMERCIAL_EXTENSION_URI,
    build_declaration,
    check_counterparty,
)
from .schemas import SchemaSet
from .signing import (
    SYNTHETIC_SIGNATURE_VALUE,
    generate_key,
    public_key_of,
    sign_object,
    verify_signature,
)
from .verifier import Check, VerificationReport, verify_bundle

__all__ = [
    "A202_EXTENSION_UNSUPPORTED",
    "COMMERCIAL_EXTENSION_URI",
    "Check",
    "PREFIXES",
    "SchemaSet",
    "SYNTHETIC_SIGNATURE_VALUE",
    "VerificationReport",
    "build_declaration",
    "canonical_bytes",
    "canonicalize",
    "check_counterparty",
    "content_hash",
    "generate_key",
    "make_object",
    "new_id",
    "public_key_of",
    "sign_object",
    "verify_bundle",
    "verify_signature",
]
