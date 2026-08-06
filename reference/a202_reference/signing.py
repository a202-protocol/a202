"""ES256 signature creation and verification over canonical bytes plus the
signature's own protected members.

The signature value is the JOSE raw form, the 64-byte concatenation of r and
s, base64url encoded without padding. The bytes signed are the canonical
bytes of canonical.py, a `.` separator, and the canonical serialization of
the signature entry's own key_id, algorithm, purpose, and signed_at members,
per canonical model section 4.

The protected members are covered because an uncovered signature entry is
relabelable: a signature over the content alone stays cryptographically
valid when its purpose is rewritten to a different act, or when its signed
time is backdated to before a key's revocation. Covering the members makes
either change a verification failure rather than an undetectable edit. The
signature still never covers its own value, the signatures array, or any
carrier framing.

The published fixtures carry the literal placeholder string
"synthetic-placeholder-signature-value" instead of a cryptographic value. A
verifier reports such a signature as not checkable, never as verified and
never as failed: the fixture demonstrates a shape, and treating its
placeholder as either outcome would make an absence of cryptography read as
evidence about it.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature,
    encode_dss_signature,
)

from .canonical import canonical_bytes, canonicalize

SYNTHETIC_SIGNATURE_VALUE = "synthetic-placeholder-signature-value"

# The purpose a signature was issued for is part of what makes it a signature
# for this act. A signature valid over the bytes and issued for another
# purpose does not count, which is step 2 item 2 of the verification
# procedure. This map mirrors the one the conformance runner checks.
EXPECTED_PURPOSES = {
    "offer": {"offer_submission", "object_issuance"},
    "acceptance": {"offer_acceptance", "object_issuance"},
    "agreement": {"agreement_commitment", "object_issuance"},
    "transaction_event": {"event_append"},
    "policy_decision": {"policy_decision"},
    "action_envelope": {"action_submission"},
    "counterparty_invitation": {"invitation_issuance", "object_issuance"},
    "invitation_acceptance": {"invitation_claim", "object_issuance"},
    "adapter_receipt": {"adapter_receipt", "object_issuance"},
    "obligation": {"object_issuance"},
    "performance_event": {"object_issuance"},
    "obligation_response": {"object_issuance"},
    "dispute": {"object_issuance"},
    "determination": {"object_issuance"},
    "settlement_instruction": {"object_issuance"},
    "approval": {"object_issuance"},
    "commitment": {"object_issuance"},
    "evidence": {"object_issuance"},
    "revocation_record": {"object_issuance"},
    "key_record": {"object_issuance"},
}

# An agreement exists only when both parties sign the same canonical hash,
# and an invitation acceptance carries both the claimant's attestation and
# the operator's issuance signature.
MINIMUM_SIGNATURES = {"agreement": 2, "invitation_acceptance": 2}


def generate_key() -> ec.EllipticCurvePrivateKey:
    """A P-256 private key, for tests and examples. Keys live in memory only."""
    return ec.generate_private_key(ec.SECP256R1())


def public_key_of(private_key: ec.EllipticCurvePrivateKey) -> ec.EllipticCurvePublicKey:
    return private_key.public_key()


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _unb64url(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _signed_bytes(obj: dict, key_id: str, algorithm: str, purpose: str, signed_at: str) -> bytes:
    """The bytes a signature covers: canonical object content, a separator,
    and the entry's own protected members in canonical order. Rewriting any
    protected member afterwards changes these bytes and fails verification."""
    protected = {
        "algorithm": algorithm,
        "key_id": key_id,
        "purpose": purpose,
        "signed_at": signed_at,
    }
    return canonical_bytes(obj) + b"." + canonicalize(protected).encode("utf-8")


def sign_object(
    obj: dict,
    private_key: ec.EllipticCurvePrivateKey,
    key_id: str,
    purpose: str,
    signed_at: str | None = None,
) -> dict:
    """Return the signature entry for obj, without mutating it.

    The caller appends the entry to the object's signatures array. Signing
    happens after content_hash is set, and neither the hash nor the
    signatures array is inside the signed bytes, so appending a signature
    never invalidates an earlier one. The entry's own key_id, algorithm,
    purpose, and signed_at are inside the signed bytes, so none of them can
    be rewritten after the fact.
    """
    stamped = signed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    der = private_key.sign(
        _signed_bytes(obj, key_id, "ES256", purpose, stamped),
        ec.ECDSA(hashes.SHA256()),
    )
    r, s = decode_dss_signature(der)
    raw = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    return {
        "key_id": key_id,
        "algorithm": "ES256",
        "signature": _b64url(raw),
        "signed_at": stamped,
        "purpose": purpose,
    }


def verify_signature(
    obj: dict,
    signature_entry: dict,
    public_key: ec.EllipticCurvePublicKey | None,
    expected_purposes: set[str] | None = None,
) -> str:
    """Verify one signature entry. Returns verified, failed, or not_checkable.

    A synthetic placeholder is not checkable. An unresolvable key is not
    checkable, and the signature is not thereby verified. A signature whose
    purpose is outside the expected set for the act is failed even when the
    cryptography verifies, because purpose is part of what was signed for.
    """
    value = signature_entry.get("signature", "")
    if value == SYNTHETIC_SIGNATURE_VALUE:
        return "not_checkable"
    if expected_purposes is not None:
        if signature_entry.get("purpose") not in expected_purposes:
            return "failed"
    if public_key is None:
        return "not_checkable"
    if signature_entry.get("algorithm") != "ES256":
        return "failed"
    try:
        raw = _unb64url(value)
        if len(raw) != 64:
            return "failed"
        der = encode_dss_signature(
            int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big")
        )
        covered = _signed_bytes(
            obj,
            str(signature_entry.get("key_id")),
            str(signature_entry.get("algorithm")),
            str(signature_entry.get("purpose")),
            str(signature_entry.get("signed_at")),
        )
        public_key.verify(der, covered, ec.ECDSA(hashes.SHA256()))
        return "verified"
    except (InvalidSignature, ValueError):
        return "failed"
