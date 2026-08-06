"""Mandate issuance, presentation checking, and constraint evaluation.

A mandate is not a common-envelope object: it carries a single `proof` member
rather than a signatures array. The bytes the proof covers are the canonical
bytes of the document with `proof` removed, computed by the same
canonicalization the envelope uses, so an implementation that already has one
canonicalizer needs no second one.

Evaluation follows section 6 of commercial-mandate-v0.1.md in the order that
document states, and returns one decision of `allow`, `deny`, or
`require_approval` together with the registered reason codes behind it.
Arithmetic over money, percentages, and quantities is decimal. No language
model is consulted, and no network call is made: the status endpoint is
resolved by the caller and its result is presented here, because a mandate
whose status this process cannot see is a mandate this process must deny.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from a202_reference.canonical import content_hash
from a202_reference.emission import make_object, new_id
from a202_reference.signing import sign_object, verify_signature

from . import gate
from .state import KeyMisbound

STATUS_CACHE_SECONDS = 60
"""The pilot cap on cached status freshness, from section 9 of the mandate
document. A result older than this is treated as no result."""

MANDATE_PROOF_PURPOSE = "mandate_issuance"

_ACTIVE = "active"


class Refused(Exception):
    """An act or a document was refused, with the registered codes that refused it.

    Every refusal in this package carries codes rather than prose, so a caller
    branches on the reason instead of parsing a sentence. `detail` carries the
    prose, including any message the published schema produced, and nothing in
    it is a code.
    """

    def __init__(self, codes: list[str], detail: list[str] | str | None = None) -> None:
        super().__init__("; ".join(codes))
        self.codes = codes
        if isinstance(detail, list):
            detail = "; ".join(detail)
        self.detail = detail


class MandateRefused(Refused):
    """A mandate was refused at issue."""


class ApprovalRefused(Refused):
    """An approval was refused at issue."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value) -> datetime:
    """Parse an RFC 3339 instant, or raise ValueError.

    A value that is not a string raises the same error a malformed string
    does. A presented mandate is a counterparty's document, so every member of
    it is of whatever type the counterparty sent, and a type error escaping
    from here would leave the caller with a traceback instead of a refusal.
    """
    if not isinstance(value, str):
        raise ValueError(f"not an RFC 3339 instant: {type(value).__name__}")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _signing_view(mandate: dict) -> dict:
    """The document the proof covers: everything except the proof itself."""
    return {key: value for key, value in mandate.items() if key != "proof"}


def _proof_entry(proof: dict) -> dict:
    """The proof read as a signature entry, so that one verifier serves both.

    `created_at` on a proof is the `signed_at` of a signature entry. The
    member is renamed and nothing else about it changes, so the bytes covered
    are the same bytes in both directions.
    """
    return {
        "key_id": proof.get("key_id"),
        "algorithm": proof.get("algorithm"),
        "signature": proof.get("signature"),
        "signed_at": proof.get("created_at"),
        "purpose": proof.get("purpose"),
    }


def spending_limit_constraints(limit: dict) -> list[dict]:
    """The two constraints a stated spending limit means.

    A ceiling on an amount says nothing without the currency it is expressed
    in, so a limit of 4000 with no currency constraint is satisfied by 4000 of
    any currency. Both constraints are emitted, and both appear in the audit
    record and in any later delegation-narrowing check.
    """
    return [
        {
            "id": "c_total_amount",
            "type": "commercial.decimal",
            "path": "$.proposed_terms.core.total.amount",
            "operator": "maximum",
            "value": limit["amount"],
            "on_failure": "deny",
        },
        {
            "id": "c_total_currency",
            "type": "commercial.string",
            "path": "$.proposed_terms.core.total.currency",
            "operator": "equals",
            "value": limit["currency"],
            "on_failure": "deny",
        },
    ]


def issue_mandate(
    state,
    issuer: dict,
    subject: dict,
    represented_organization_id: str,
    valid_from: str,
    valid_until: str,
    status_endpoint: str,
    actions: list,
    scope: dict,
    spending_limit: dict | None = None,
    constraints: list | None = None,
    approval_rules: list | None = None,
    delegation: dict | None = None,
    evidence_refs: list | None = None,
    parent_mandate_id: str | None = None,
    mandate_id: str | None = None,
) -> dict:
    """Issue and sign one commercial mandate.

    The document is checked against the published schema and against the
    checks the schema cannot perform before it is signed, so a refused mandate
    is never given a signature that would make it look issued.
    """
    mandate = {
        "spec_version": gate.MANDATE_SPEC_VERSION,
        "id": mandate_id or new_id("commercial_mandate"),
        "issuer": dict(issuer),
        "subject": dict(subject),
        "represented_organization_id": represented_organization_id,
        "parent_mandate_id": parent_mandate_id,
        "valid_from": valid_from,
        "valid_until": valid_until,
        "status_endpoint": status_endpoint,
        "actions": list(actions),
        "scope": dict(scope),
        "constraints": (spending_limit_constraints(spending_limit) if spending_limit else [])
        + list(constraints or []),
        "approval_rules": list(approval_rules or []),
        "delegation": dict(delegation or {"allowed": False, "maximum_depth": 0}),
        "evidence_refs": list(evidence_refs or []),
    }

    codes, errors = gate.mandate_refusals(dict(mandate, proof=_placeholder_proof(issuer)))
    if codes:
        raise MandateRefused(codes, errors)

    # The mandate is where a key first becomes an agent's key or a principal's.
    # Learning both here is what lets a later approval refuse a key that
    # belongs to the acting agent.
    try:
        state.bind_principal_key(issuer["principal_id"], issuer["key_id"])
        if subject.get("agent_id"):
            state.bind_agent_key(subject["agent_id"], subject["key_id"])
        elif subject.get("principal_id"):
            state.bind_principal_key(subject["principal_id"], subject["key_id"])
    except KeyMisbound as misbound:
        raise MandateRefused(["A202-POLICY-DENIED"], str(misbound))

    key_id = issuer["key_id"]
    entry = sign_object(
        _signing_view(mandate),
        state.signing_key(key_id),
        key_id,
        MANDATE_PROOF_PURPOSE,
    )
    mandate["proof"] = {
        "key_id": entry["key_id"],
        "algorithm": entry["algorithm"],
        "created_at": entry["signed_at"],
        "purpose": entry["purpose"],
        "signature": entry["signature"],
    }
    state.put_mandate(mandate)
    return mandate


def action_hash_of(proposed_action: dict) -> str:
    """The hash of the exact act an approval and a decision bind.

    It is the canonical hash of the proposed action document, so changing one
    byte of the act changes the hash, and neither an approval nor a policy
    decision issued over the old bytes covers the new ones.
    """
    return content_hash(proposed_action)


def act_document(
    action_type: str,
    transaction_id: str,
    counterparty_organization_id: str | None = None,
    proposed_terms: dict | None = None,
    references: dict | None = None,
) -> dict:
    """The document one act is evaluated as, and hashed as.

    A recording tool builds this from its own arguments and requires the
    decision it was handed to carry this hash, so the act that was evaluated
    and the act that is recorded are the same act rather than two acts with
    the same description. A member whose value is absent is omitted rather
    than carried as null, so the same act always produces the same bytes.
    """
    document = {"action_type": action_type, "transaction_id": transaction_id}
    if counterparty_organization_id is not None:
        document["counterparty_organization_id"] = counterparty_organization_id
    if proposed_terms is not None:
        document["proposed_terms"] = proposed_terms
    for name, value in sorted((references or {}).items()):
        if value is not None:
            document[name] = value
    return document


def issue_approval(
    state,
    transaction_id: str,
    action_hash: str,
    requested_by: dict,
    approver: dict,
    decision: str = "approved",
    expires_after_seconds: int = 3600,
    expires_at: str | None = None,
    conditions: list | None = None,
) -> dict:
    """Record one human approval bound to one exact action hash.

    The approval is signed by the approving principal's own key, and the key
    is bound to that principal before it signs. Without the binding the
    control is decorative: an agent presenting its own key under a director's
    name approves its own act, and the signature verifies because the key is
    one this process holds. A key that has already signed an act as an agent
    on this transaction is refused for the same reason.

    The expiry is stated absolutely when the caller gives one, and otherwise
    computed from now. A caller evaluating against a stated clock supplies the
    instant, so that the approval and the evaluation agree about the time.
    """
    key_id = approver["key_id"]
    owner = state.agent_for_key(key_id)
    if owner is not None or key_id in state.agent_keys(transaction_id):
        raise ApprovalRefused(
            ["A202-APPROVAL-REQUIRED"],
            f"{key_id} is an agent's signing key, so an approval under it is "
            "the acting agent approving itself",
        )
    try:
        state.bind_principal_key(approver["principal_id"], key_id)
    except KeyMisbound as misbound:
        raise ApprovalRefused(["A202-APPROVAL-REQUIRED"], str(misbound))

    approval = make_object(
        "approval",
        {
            "action_hash": action_hash,
            "approver": {
                "organization_id": requested_by["organization_id"],
                "principal_id": approver["principal_id"],
                "role": approver["role"],
            },
            "decision": decision,
            "expires_at": expires_at
            or (_now() + timedelta(seconds=expires_after_seconds)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "conditions": list(conditions or []),
        },
        {
            "organization_id": requested_by["organization_id"],
            "agent_id": requested_by["agent_id"],
            "mandate_id": requested_by["mandate_id"],
        },
        transaction_id,
    )
    approval["signatures"].append(
        sign_object(approval, state.signing_key(key_id), key_id, "object_issuance")
    )
    codes, errors = gate.kernel_refusals(approval)
    if codes:
        raise ApprovalRefused(codes, errors)
    state.put_object(approval)
    return approval


def _placeholder_proof(issuer: dict) -> dict:
    """A proof-shaped member so the document can be schema-checked before it
    is signed. It is never stored and never returned."""
    return {
        "key_id": issuer["key_id"],
        "algorithm": "ES256",
        "created_at": _now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "purpose": MANDATE_PROOF_PURPOSE,
        "signature": "0" * 64,
    }


# --- path addressing ----------------------------------------------------------

_MISSING = object()


def resolve_path(document: dict, path: str):
    """Resolve `$.a.b.c` against a document, or return the missing marker.

    The same addressing serves a mandate constraint and an obligation's
    `term_path`, so a term a mandate constrains and a term an obligation owes
    are named the same way.
    """
    if not isinstance(path, str) or not path.startswith("$."):
        return _MISSING
    cursor = document
    for segment in path[2:].split("."):
        if not isinstance(cursor, dict) or segment not in cursor:
            return _MISSING
        cursor = cursor[segment]
    return cursor


def _decimal(value):
    """A finite decimal, or None where the value is not one.

    A non-finite value is refused rather than returned. `Decimal("NaN")`
    parses and then raises on every comparison, so a counterparty writing NaN
    into a proposed amount would throw an exception out of the evaluator
    instead of being denied. Infinity parses and compares, and an infinite
    amount is not a price.
    """
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return parsed if parsed.is_finite() else None


def _evidence_verified(state, value) -> bool:
    """Every referenced evidence object resolves and reports `verified`.

    Verification status is reported, never inferred: evidence this party does
    not hold is not verified evidence.
    """
    refs = value if isinstance(value, list) else [value]
    if not refs:
        return False
    for ref in refs:
        evidence_id = ref.get("evidence_id") if isinstance(ref, dict) else ref
        evidence = state.get_object(evidence_id) if isinstance(evidence_id, str) else None
        if evidence is None:
            return False
        if evidence["payload"].get("verification", {}).get("status") != "verified":
            return False
    return True


class Unevaluable(Exception):
    """A registered operator could not be executed as written.

    Section 4 of the mandate document requires an unevaluable constraint to
    deny rather than to pass, so this is raised rather than returned as False:
    a False is a constraint that was evaluated and not satisfied, and the two
    are different facts about the same act.
    """


def evaluate_predicate(state, predicate: dict, action: dict) -> bool:
    """Evaluate one registered operator over one path.

    Unregistered operators do not reach here: the caller refuses them before
    evaluating. An operator that is registered but cannot be executed against
    the values presented raises Unevaluable.
    """
    operator = predicate.get("operator")
    expected = predicate.get("value")
    actual = resolve_path(action, predicate.get("path"))

    if operator == "present":
        return actual is not _MISSING
    if operator == "absent":
        return actual is _MISSING
    if actual is _MISSING:
        # A path that does not resolve satisfies only the two operators above
        # and `none_of`, where nothing present cannot be in a denied set.
        # Every other operator fails closed rather than reading absence as
        # agreement.
        return operator == "none_of"
    if operator == "equals":
        return _compare_equal(actual, expected)
    if operator == "not_equals":
        return not _compare_equal(actual, expected)
    if operator == "one_of":
        return isinstance(expected, list) and any(
            _compare_equal(actual, item) for item in expected
        )
    if operator == "none_of":
        return isinstance(expected, list) and not any(
            _compare_equal(actual, item) for item in expected
        )
    if operator in ("minimum", "maximum"):
        left, right = _decimal(actual), _decimal(expected)
        if left is None or right is None:
            # A limit that is not a number, or a value that is not one, is a
            # comparison nobody can make. It denies rather than passing.
            raise Unevaluable(f"{operator} over a value that is not a finite decimal")
        return left >= right if operator == "minimum" else left <= right
    if operator == "matches":
        try:
            pattern = re.compile(str(expected))
        except re.error as broken:
            raise Unevaluable(f"the constraint's expression does not compile: {broken}")
        return isinstance(actual, str) and pattern.search(actual) is not None
    if operator in ("before", "after"):
        try:
            left, right = _timestamp(actual), _timestamp(expected)
        except ValueError as unparsed:
            raise Unevaluable(str(unparsed))
        return left < right if operator == "before" else left > right
    if operator == "evidence_verified":
        return _evidence_verified(state, actual)
    return False


def _compare_equal(actual, expected) -> bool:
    """Numeric strings compare as decimals so that "20" and "20.00" are one
    value, and everything else compares as it is written."""
    left, right = _decimal(actual), _decimal(expected)
    if left is not None and right is not None:
        return left == right
    return actual == expected


# --- presentation and evaluation ----------------------------------------------

def verify_mandate(
    state,
    mandate: dict,
    at: str | None = None,
    status: dict | None = None,
    proposed_action: dict | None = None,
    approval: dict | None = None,
) -> dict:
    """Check a presented mandate and, where one is supplied, an act under it.

    `status` is what the caller retrieved from the mandate's status endpoint,
    as `{"status": ..., "retrieved_at": ...}`. This process makes no network
    call, so an absent or stale status result is an unresolved status and the
    decision is `deny`. Unavailability is not permission.

    Where a constraint or an approval rule holds the act, `approval` is the
    approval object that releases it. The approval must bind the exact action
    hash this call reports, must not have expired, and must carry the decision
    of a named principal of the acting organisation. An approval never
    releases a `deny`: a denied constraint is not approvable.
    """
    checked_at = _timestamp(at) if at else _now()
    refusals, schema_errors = gate.mandate_refusals(mandate)
    reason_codes: list[str] = []
    decision = "allow"

    def refuse(code: str) -> None:
        nonlocal decision
        decision = "deny"
        if code not in reason_codes:
            reason_codes.append(code)

    def hold(code: str) -> None:
        nonlocal decision
        if decision == "allow":
            decision = "require_approval"
        if code not in reason_codes:
            reason_codes.append(code)

    for code in refusals:
        # A document the published gate refuses is not a mandate this party
        # acts on, whichever layer refused it. The codes are the gate's, and
        # the schema's own messages stay out of them.
        refuse(code)

    proof_result = "not_checkable"
    proof = mandate.get("proof")
    if isinstance(proof, dict):
        key = state.public_keys().get(proof.get("key_id"))
        proof_result = verify_signature(
            _signing_view(mandate),
            _proof_entry(proof),
            key,
            {MANDATE_PROOF_PURPOSE},
        )
    if proof_result != "verified":
        refuse("A202-EVIDENCE-SIGNATURE-INVALID")

    try:
        within_interval = (
            _timestamp(mandate["valid_from"]) <= checked_at < _timestamp(mandate["valid_until"])
        )
    except (KeyError, TypeError, ValueError):
        # A presented mandate carries whatever a counterparty put in it. An
        # interval that cannot be read is an interval that does not hold.
        within_interval = False
    if not within_interval:
        refuse("A202-MANDATE-INACTIVE")

    status_result = _check_status(status, checked_at)
    if status_result is not None:
        refuse(status_result)

    evaluated: list[dict] = []
    hash_of_action = None
    matched_rules: list[str] = []
    if proposed_action is not None:
        hash_of_action = action_hash_of(proposed_action)
        for code in _scope_refusals(mandate, proposed_action):
            refuse(code)
        for outcome in _constraint_outcomes(state, mandate, proposed_action):
            evaluated.append(outcome)
            if outcome["result"] == "satisfied":
                continue
            if outcome["code"] == "A202-MANDATE-CONSTRAINT-UNKNOWN":
                refuse(outcome["code"])
            elif outcome["on_failure"] == "deny":
                refuse("A202-POLICY-DENIED")
            else:
                hold("A202-APPROVAL-REQUIRED")
        for rule in mandate.get("approval_rules") or []:
            try:
                matched = evaluate_predicate(state, rule.get("when", {}), proposed_action)
            except Unevaluable:
                # A rule that cannot be evaluated holds the act rather than
                # letting it through, on the same rule as a constraint.
                matched = True
            if matched:
                matched_rules.append(rule.get("id"))
                hold("A202-APPROVAL-REQUIRED")

    approval_result = "not_presented" if approval is None else "failed"
    if decision == "require_approval" and approval is not None:
        codes = _approval_refusals(state, approval, mandate, matched_rules,
                                   hash_of_action, checked_at, proposed_action)
        if codes:
            approval_result = "failed"
            for code in codes:
                if code not in reason_codes:
                    reason_codes.append(code)
        else:
            # The hold is released, and only the hold. A denied constraint
            # never reaches here, because deny is not approvable.
            approval_result = "verified"
            decision = "allow"
            reason_codes = [
                code for code in reason_codes if code != "A202-APPROVAL-REQUIRED"
            ]

    return {
        "mandate_id": mandate.get("id"),
        "refusals": refusals,
        "schema_errors": schema_errors,
        "proof": proof_result,
        "validity_interval": "verified" if within_interval else "failed",
        "status": "verified" if status_result is None else "failed",
        "constraints": evaluated,
        "approval_rules_matched": matched_rules,
        "approval": approval_result,
        "action_hash": hash_of_action,
        "decision": decision,
        "reason_codes": reason_codes,
        "checked_at": checked_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def held_approval(state, document: dict) -> dict | None:
    """An approval this party holds that binds this exact act, or None.

    A recording tool is handed a decision and not the approval behind it, so
    the approval is found the same way the decision found it: by the action
    hash it binds and the transaction it was issued on.
    """
    wanted = action_hash_of(document)
    for held in state.objects_for(document.get("transaction_id")):
        if held.get("object_type") != "approval":
            continue
        if held["payload"].get("action_hash") == wanted:
            return held
    return None


def rederive_decision(state, mandate: dict, document: dict, presented: dict) -> dict:
    """Evaluate one act again, from the mandate and the act alone.

    A decision presented to a recording tool is an unsigned document written
    by the party the mandate constrains, so it is evidence of what that party
    says it decided and of nothing else. The verdict is therefore recomputed
    here rather than read, using the same evaluation the original call ran.

    One input is taken from the presented decision and only one: whether the
    status endpoint resolved. This process makes no network call, so that fact
    is the caller's to supply in either direction, and taking it here gives a
    caller nothing it did not already have when it called verify_mandate.
    Everything the mandate itself decides, the scope, the constraints, the
    approval rules, and the validity interval, is derived from the mandate.
    """
    status = None
    if presented.get("status") == "verified":
        status = {"status": _ACTIVE, "retrieved_at": presented.get("checked_at")}
    try:
        at = _timestamp(presented.get("checked_at")).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        at = None
    return verify_mandate(
        state,
        mandate,
        at=at,
        status=status,
        proposed_action=document,
        approval=held_approval(state, document),
    )


def _approval_refusals(
    state,
    approval: dict,
    mandate: dict,
    matched_rules: list,
    hash_of_action: str | None,
    checked_at: datetime,
    proposed_action: dict | None,
) -> list[str]:
    """Why a presented approval does not release the hold, or an empty list.

    Section 8 of the mandate document: an approval binds an exact action hash,
    a transaction, an approver identity and role, a decision, and an expiry.
    Changing one byte of the action invalidates it, and it cannot be reused
    across actions or transactions.
    """
    codes: list[str] = []
    payload = approval.get("payload", {})
    approver = payload.get("approver", {})

    # The signature must be the approving principal's own. A signature under
    # any key this process happens to hold proves only that this process holds
    # a key, and the agent's key is one of those.
    bound_key = state.key_for_principal(approver.get("principal_id"))
    keys = state.public_keys()
    verified = any(
        entry.get("key_id") == bound_key
        and verify_signature(
            approval, entry, keys.get(entry.get("key_id")), {"object_issuance"}
        ) == "verified"
        for entry in (approval.get("signatures") or [])
    )
    if not verified:
        codes.append("A202-EVIDENCE-SIGNATURE-INVALID")

    if payload.get("action_hash") != hash_of_action:
        codes.append("A202-APPROVAL-HASH-MISMATCH")

    # An approval cannot be reused across transactions. Without this the same
    # approval releases every act of the same shape on every other deal.
    acting_transaction = (proposed_action or {}).get("transaction_id")
    if approval.get("transaction_id") != acting_transaction:
        codes.append("A202-STREAM-MISMATCH")

    if payload.get("decision") != "approved":
        codes.append("A202-APPROVAL-REQUIRED")

    try:
        if _timestamp(payload.get("expires_at")) <= checked_at:
            codes.append("A202-APPROVAL-REQUIRED")
    except ValueError:
        codes.append("A202-APPROVAL-REQUIRED")

    # The approver must be of the acting organisation whatever held the act.
    # A hold raised by a constraint matches no approval rule, so a check that
    # ran only over matched rules ran over nothing and let any approver
    # release it.
    if approver.get("organization_id") != mandate.get("represented_organization_id"):
        codes.append("A202-APPROVAL-REQUIRED")

    # Where a rule raised the hold, the approver must also hold the role the
    # rule named.
    rules = {rule.get("id"): rule for rule in mandate.get("approval_rules") or []}
    for rule_id in matched_rules:
        named = rules.get(rule_id, {}).get("approver", {})
        if named.get("organization_id") != approver.get("organization_id"):
            codes.append("A202-APPROVAL-REQUIRED")
        elif named.get("role") != approver.get("role"):
            codes.append("A202-APPROVAL-REQUIRED")

    return sorted(set(codes))


def _check_status(status: dict | None, checked_at: datetime) -> str | None:
    """The reason a presented status result does not support acting, or None.

    The freshness bound is two sided. A one-sided check passes a result
    retrieved a year from now, which is the easiest possible way to present a
    status nobody retrieved.
    """
    if not isinstance(status, dict):
        return "A202-MANDATE-STATUS-UNRESOLVED"
    try:
        stamp = _timestamp(status.get("retrieved_at"))
    except ValueError:
        return "A202-MANDATE-STATUS-UNRESOLVED"
    if abs(checked_at - stamp) > timedelta(seconds=STATUS_CACHE_SECONDS):
        return "A202-MANDATE-STATUS-UNRESOLVED"
    if status.get("status") != _ACTIVE:
        return "A202-MANDATE-INACTIVE"
    return None


def _scope_refusals(mandate: dict, action: dict) -> list[str]:
    """Action membership and the four scope axes.

    Actions are deny by default: an omitted action is not allowed. A stated
    scope axis binds, and an act that names no value on a stated axis is
    refused rather than read as unrestricted on it.
    """
    codes: list[str] = []
    if action.get("action_type") not in (mandate.get("actions") or []):
        codes.append("A202-POLICY-DENIED")
    scope = mandate.get("scope") or {}
    axes = (
        ("transaction_ids", "transaction_id"),
        ("categories", "category"),
        ("counterparty_organization_ids", "counterparty_organization_id"),
        ("geographies", "geography"),
    )
    for scope_key, action_key in axes:
        permitted = scope.get(scope_key)
        if not permitted:
            continue
        if action.get(action_key) not in permitted:
            codes.append("A202-POLICY-DENIED")
    return codes


def _constraint_outcomes(state, mandate: dict, action: dict) -> list[dict]:
    """Every constraint, in the order the mandate states them.

    Order is stable so that two evaluators reading one mandate produce one
    sequence of outcomes. An unregistered type or operator is denied here as
    well as at schema validation, so widening the enum alone cannot let an act
    through.
    """
    outcomes = []
    registered_types = gate.runner.REGISTERED_CONSTRAINT_TYPES
    registered_operators = gate.runner.REGISTERED_CONSTRAINT_OPERATORS
    for constraint in mandate.get("constraints") or []:
        entry = {
            "id": constraint.get("id"),
            "path": constraint.get("path"),
            "on_failure": constraint.get("on_failure"),
            "result": "satisfied",
            "code": None,
        }
        if (
            constraint.get("type") not in registered_types
            or constraint.get("operator") not in registered_operators
        ):
            entry["result"] = "unevaluable"
            entry["code"] = "A202-MANDATE-CONSTRAINT-UNKNOWN"
            outcomes.append(entry)
            continue
        try:
            satisfied = evaluate_predicate(state, constraint, action)
        except Unevaluable as broken:
            # A constraint that cannot be executed as written is not a
            # constraint that passed. It denies, and it says why.
            entry["result"] = "unevaluable"
            entry["code"] = "A202-MANDATE-CONSTRAINT-UNKNOWN"
            entry["detail"] = str(broken)
            outcomes.append(entry)
            continue
        if not satisfied:
            entry["result"] = "unsatisfied"
            entry["code"] = (
                "A202-POLICY-DENIED"
                if constraint.get("on_failure") == "deny"
                else "A202-APPROVAL-REQUIRED"
            )
        outcomes.append(entry)
    return outcomes
