"""Construction of shared objects on the common envelope.

Identifiers are opaque and type prefixed per canonical model section 3. The
envelope is completed, the content hash computed over the canonical bytes,
and only then is the object signed, so the signature always covers the bytes
a counterparty will verify.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from .canonical import content_hash

SPEC_VERSION = "a202-commercial/0.1"

# The registered prefix table of canonical model section 3. Object types with
# no registered prefix are deliberately absent: minting an identifier for one
# would choose a prefix the specification has not chosen.
PREFIXES = {
    "organization": "org_",
    "agent": "agt_",
    "principal": "prn_",
    "commercial_mandate": "mnd_",
    "capability": "cap_",
    "intent": "int_",
    "counterparty_invitation": "inv_",
    "invitation_acceptance": "ina_",
    "action_envelope": "act_",
    "offer": "off_",
    "acceptance": "acc_",
    "agreement": "agr_",
    "commitment": "cmt_",
    "obligation": "obl_",
    "obligation_response": "obr_",
    "performance_event": "prf_",
    "exception": "exc_",
    "dispute": "dsp_",
    "determination": "det_",
    "evidence": "evd_",
    "transaction_event": "evt_",
    "policy_decision": "pol_",
    "approval": "apr_",
    "settlement_instruction": "stl_",
    "adapter_receipt": "adp_",
}


def new_id(object_type: str) -> str:
    """A fresh opaque identifier under the registered prefix for the type.

    No legal name, email, employee number, or secret is encoded: the suffix
    is random. An unregistered type is refused rather than given an invented
    prefix, because a prefix minted here would diverge from the one a later
    proposal registers.
    """
    prefix = PREFIXES.get(object_type)
    if prefix is None:
        raise ValueError(f"no registered identifier prefix for object type {object_type}")
    return prefix + secrets.token_hex(12)


def make_object(
    object_type: str,
    payload: dict,
    created_by: dict,
    transaction_id: str | None,
    object_id: str | None = None,
    created_at: str | None = None,
    previous_version_id: str | None = None,
    version: int = 1,
) -> dict:
    """A complete unsigned shared object with its content hash set.

    The caller signs it with signing.sign_object and appends the entries to
    the signatures array. The returned object carries an empty signatures
    array rather than omitting the field, because the field is required by
    the envelope and its absence would validate nothing.
    """
    obj = {
        "spec_version": SPEC_VERSION,
        "id": object_id or new_id(object_type),
        "object_type": object_type,
        "version": version,
        "created_at": created_at
        or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "created_by": created_by,
        "transaction_id": transaction_id,
        "previous_version_id": previous_version_id,
        "signatures": [],
        "payload": payload,
    }
    obj["content_hash"] = content_hash(obj)
    return obj
