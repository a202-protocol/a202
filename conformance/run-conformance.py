#!/usr/bin/env python3
"""A202 v0.1 conformance runner.

Validates every fixture named in manifest-v0.1.json against the pilot schemas,
then applies the invariants that JSON Schema cannot express and that the
specifications therefore require an implementation to enforce.

The runner exists because schema validation alone is not conformance. Several
rules in canonical-commercial-model-v0.1.md and commercial-mandate-v0.1.md are
cross-field or registry-dependent. If those rules live only in prose, an
implementation can pass the schemas and still violate the specification.

Fixture kinds
-------------

``kernel``
    One shared object, validated against commercial-kernel.schema.json and then
    against the normative checks that apply to its object type.

``mandate``
    One mandate, validated against commercial-mandate.schema.json and then
    against the mandate interval rule.

``mandate_chain``
    A parent mandate and a child mandate delegated from it, each validated
    against commercial-mandate.schema.json, then checked for monotonic
    narrowing on every axis of commercial-mandate-v0.1.md section 7:
    validity interval, actions, scope, retained deny constraints, numeric
    limits under decimal comparison, and delegation depth. Every failure is
    A202-MANDATE-DELEGATION-WIDENING, which is the code section 7 names.

``grade``
    A conformance grade, validated against conformance-grade.schema.json and
    then against the role scope rules of
    conformance/conformance-role-scopes-v0.1.md sections 3.2 and 6.3: the
    named role scope resolves in the registry, exactly one is named, and every
    fixture family a band or a held-out coverage claim was established from
    lies inside the scope named. A grade is a standalone signed document rather
    than a common-envelope object, on the same footing as a mandate.

``declaration``
    A carrier capability declaration rather than a commercial object. The
    fixture carries the counterparty's declared extension entries and the local
    party's own version declaration. The runner checks that an entry for the
    A202 commercial extension URI is present, that it carries a required flag,
    that its read_versions and write_version parse, and that the two
    declarations are compatible in both directions. Every failure returns
    A202-EXTENSION-UNSUPPORTED, because the conditions have one correct outcome
    and a caller handed several codes that must be handled identically will
    eventually handle one of them differently.

``bundle``
    A set of objects plus a context, so that the rules which hold between
    objects are executable: content hash recomputation, signature purpose and
    count, version chain gaps and forks, per-stream continuity and the refusal
    to expect continuity across streams, replay of guarded transitions against
    the rules version in force at append time, the checks that make a
    determination follow from its rules and inputs, obligation response binding
    and remainder, settlement trigger resolution, disclosure completeness, and
    the three-valued verification report rules.

    Content hashes are recomputed only for objects carried in a bundle. Those
    objects carry hashes computed over their own canonical bytes. The
    single-object fixtures predate the cross-object checks and carry synthetic
    hash values, so they are not hash-recomputed; nothing about their existing
    behaviour changes.

Usage:
    python3 run-conformance.py            # run everything
    python3 run-conformance.py --verbose  # include per-fixture detail

Requires: jsonschema >= 4.18 (for the referencing registry API).
Exit code 0 when every fixture behaves as the manifest declares.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource
except ImportError:  # pragma: no cover
    sys.exit("install jsonschema>=4.18 first:  pip install jsonschema")

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "schemas" / "v0.1"
PROFILES = SCHEMAS / "profiles"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "v0.1"
MANIFEST = Path(__file__).resolve().parent / "manifest-v0.1.json"


def load_reference_canonical_bytes():
    """Load the repository's canonicalizer without importing package extras."""
    path = ROOT / "reference" / "a202_reference" / "canonical.py"
    spec = importlib.util.spec_from_file_location("a202_reference_canonical", path)
    if spec is None or spec.loader is None:  # pragma: no cover - import machinery
        raise RuntimeError(f"cannot load canonicalizer from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.canonical_bytes


canonical_bytes = load_reference_canonical_bytes()


def load(path: Path) -> dict:
    with path.open() as handle:
        return json.load(handle)


def build_registry() -> Registry:
    """Resolve the schemas' absolute $id values to the local files."""
    registry = Registry()
    for path in list(SCHEMAS.glob("*.json")) + list(PROFILES.glob("*.json")):
        schema = load(path)
        registry = registry.with_resource(
            schema["$id"], Resource.from_contents(schema)
        )
    return registry


def profile_registry() -> dict[str, dict]:
    """Map a transaction profile identifier to its schema.

    An identifier that is absent from this map fails closed. The kernel never
    special-cases a profile; it only checks that one resolves.
    """
    registry: dict[str, dict] = {}
    for path in PROFILES.glob("*.schema.json"):
        schema = load(path)
        stem = path.name.removesuffix(".schema.json")  # calibration-service-0.1
        name, _, version = stem.rpartition("-")
        registry[f"a202-profile/{name}/{version}"] = schema
    return registry


def rfc3339(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def content_hash_of(obj: dict) -> str:
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()


# --- registries that fail closed ----------------------------------------------

# Every registry below is closed in v0.1 and is enforced here as well as in the
# schema. Both layers must fail closed on their own: adding a member to a schema
# enum without an evaluator that knows what the member means must not cause an
# object to be treated as valid, and the reverse must not either.

REGISTERED_EVIDENCE_TYPES = {
    "attestation",
    "third_party_certificate",
    "inspection_result",
    "delivery_confirmation",
    "measurement_record",
    "adapter_receipt",
    "verification_report",
    "signed_document",
}

REGISTERED_DUE_CONDITION_TYPES = {
    "due_at_time",
    "due_on_event",
    "due_on_discharge",
    "all_of",
}

DUE_CONDITION_FIELDS = {
    "due_at_time": {"type", "at", "business_days"},
    "due_on_event": {"type", "act_ref", "evidence_type"},
    "due_on_discharge": {"type", "obligation_id"},
    "all_of": {"type", "conditions"},
}

REGISTERED_REJECTION_REASONS = {
    "evidence_insufficient",
    "evidence_unverified",
    "quantity_short",
    "subject_not_as_agreed",
    "due_condition_not_met",
    "assertion_unauthorized",
}

REGISTERED_DISPUTE_GROUNDS = {
    "authority_absent",
    "authority_exceeded",
    "state_transition_invalid",
    "obligation_not_performed",
    "obligation_wrongly_rejected",
    "evidence_unverified",
    "disclosure_breach",
    "refusal_incorrect",
    "rule_misapplied",
}

REGISTERED_APPEAL_GROUNDS = {
    "rule_misapplied",
    "input_did_not_exercise_invariant",
    "wrong_scope",
    "wrong_rule_version",
}

REGISTERED_SUPERSESSION_REASONS = {
    "appeal_outcome",
    "corrected_input",
    "rule_misapplication",
}

# The mandate constraint vocabulary is closed in v0.1, per
# commercial-mandate-v0.1.md section 4. The schema enforces these as an enum;
# the evaluator enforces them again here, because the specification requires both
# layers to fail closed on their own: adding a member to the schema enum without
# an evaluator that knows what it means MUST NOT let an act through, and the
# reverse must not either. This is the second layer for the mandate.
REGISTERED_CONSTRAINT_TYPES = {
    "commercial.decimal",
    "commercial.integer",
    "commercial.string",
    "commercial.boolean",
    "commercial.timestamp",
    "commercial.set",
    "disclosure.path",
    "evidence.reference",
    "counterparty.reference",
    "geography.reference",
}

REGISTERED_CONSTRAINT_OPERATORS = {
    "equals",
    "not_equals",
    "one_of",
    "none_of",
    "minimum",
    "maximum",
    "matches",
    "present",
    "absent",
    "before",
    "after",
    "evidence_verified",
}

# Numeric operators whose limit a child mandate may tighten but never loosen,
# per commercial-mandate-v0.1.md section 7. A maximum may only fall, a minimum
# may only rise.
NUMERIC_CONSTRAINT_OPERATORS = {"minimum", "maximum"}

# The settlement rail registry is fail-closed and holds only what an
# implementation has deliberately registered. One synthetic identifier is
# registered here so that the allow direction is testable. An unregistered value
# is refused rather than routed to a default adapter: the unchecked value would
# select who receives money.
REGISTERED_SETTLEMENT_RAILS = {"rail_test_sandbox"}

# The commercial layer holds no funds. An instruction naming a commercial-layer
# organization as payee for onward transmission is refused.
COMMERCIAL_LAYER_ORGANIZATIONS = {"org_a202_operator"}

# Deletion is not a defined operation anywhere in the set. Naming one in an
# event is refused, which is what makes the absence testable rather than
# asserted.
UNDEFINED_EVENT_TYPES = {
    "determination.deleted",
    "dispute.deleted",
    "obligation.deleted",
    "evidence.deleted",
}

# The purpose a signature was issued for is part of what makes it a signature
# for this act. A signature valid over the bytes and issued for another purpose
# does not count, and this map is what a verifier checks at step 2.
SIGNATURE_PURPOSES = {
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

MINIMUM_SIGNATURES = {
    "agreement": 2,
    "invitation_acceptance": 2,
}

# Object types whose signature count is already decided by a rule that names
# which signatures must be present rather than how many. An invitation
# acceptance carries the claimant's attestation and the operator's issuance
# signature, and the absence of either is refused with
# A202-INVITATION-CLAIM-UNSIGNED; raising a second, weaker code for the same
# absence would make one offence look like two.
SIGNATURE_COUNT_RULED_BY_PURPOSE = {"invitation_acceptance"}

# The stream kinds this specification version defines. A stream kind outside
# this set is an event format v0.1 does not define, refused under
# negotiation/auction-event-semantics-v0.1.md section 9 rather than
# approximated: an approximated event is one whose fairness cannot be proven.
REGISTERED_STREAM_KINDS = {"transaction", "session"}

# Member names through which a claim secret would travel in the clear. The
# secret is a bearer credential: a shared object carries `claim_secret_hash`
# and never the value, per discovery/counterparty-invitation-v0.1.md section 7.
# Matched on the member name exactly, at any depth, so that the hash member is
# untouched and a nested copy is not missed.
CLAIM_SECRET_MEMBER_NAMES = {"claim_secret", "claim_secret_value", "secret"}

# Member names through which a bid would name an award unit. v0.1 defines a
# single award unit per event and no award-unit object, so no such reference
# resolves and every one of them fails closed with A202-LOT-UNKNOWN, per
# negotiation/auction-event-semantics-v0.1.md sections 8.1 and 9. Silently
# dropping the member would submit the bid against the wrong award unit.
AWARD_UNIT_MEMBER_NAMES = {"lot_id", "award_unit_id"}

# The carrier capability declaration. The URI is defined by the binding, carries
# the specification minor version, and resolves on a reserved domain so that the
# placeholder cannot point at a host anyone controls.
COMMERCIAL_EXTENSION_URI = "https://schemas.a202.org/a2a-ext/commercial/0.1"
SPEC_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+$")

# Rule sets in force. A window, an available effect, an appeal route, and the
# set of transitions that were legal are all read from a rule set version, never
# restated by the object that references one. Several versions are registered so
# that a transition legal under a later version and not under the version in
# force at append time is distinguishable. Every version other than the newest
# is immutable: a record replays against the set that was in force when it
# appended, never against the current one.
PILOT_TRANSITIONS_1_0 = {
    ("draft", "request.published", "published"),
    ("published", "qualification.started", "qualifying"),
    ("qualifying", "negotiation.opened", "negotiating"),
    ("negotiating", "offer.selected", "agreement_pending"),
    ("agreement_pending", "approval.rejected", "negotiating"),
    ("agreement_pending", "acceptance.withdrawn", "negotiating"),
    ("agreement_pending", "agreement.committed", "committed"),
    ("committed", "obligation.activated", "in_performance"),
    ("in_performance", "performance.declared", "acceptance_pending"),
    ("acceptance_pending", "acceptance.rejected", "in_performance"),
    ("acceptance_pending", "acceptance.granted", "settlement_pending"),
    ("settlement_pending", "settlement.instructed", "settlement_pending"),
    ("settlement_pending", "transaction.completed", "completed"),
    ("committed", "exception.opened", "exception_open"),
    ("in_performance", "exception.opened", "exception_open"),
    ("acceptance_pending", "exception.opened", "exception_open"),
    ("settlement_pending", "exception.opened", "exception_open"),
    ("exception_open", "remediation.accepted", "in_performance"),
    ("exception_open", "exception.resolved", "settlement_pending"),
    ("exception_open", "transaction.terminated", "terminated"),
    ("opened", "offer.submitted", "active"),
    ("active", "offer.submitted", "active"),
    ("active", "clarification.sent", "active"),
    ("active", "approval.requested", "paused_for_approval"),
    ("paused_for_approval", "approval.granted", "active"),
    ("paused_for_approval", "approval.rejected", "active"),
    ("active", "offer.accepted", "accepted"),
    ("active", "offer.withdrawn", "withdrawn"),
    ("active", "deadline.elapsed", "expired"),
    ("accepted", "session.closed", "closed"),
}
for _pre_commit in ("draft", "published", "qualifying", "negotiating", "agreement_pending"):
    PILOT_TRANSITIONS_1_0.add((_pre_commit, "transaction.cancelled", "cancelled"))
    PILOT_TRANSITIONS_1_0.add((_pre_commit, "deadline.elapsed", "expired"))

PILOT_TRANSITIONS_1_1 = PILOT_TRANSITIONS_1_0 | {
    ("exception_open", "transaction.completed", "completed"),
}

# Version 1.2 registers the consensual-close and amendment transitions adopted
# after the review: termination.agreed ends a committed transaction by a
# termination record both parties signed, agreement.amended records a
# superseding agreement version reached through a fresh offer and acceptance
# without moving aggregate state, and obligation.released is the
# obligation-level counterpart of an authorized termination. Earlier versions
# are immutable: a record made under 1.0 or 1.1 replays against the set in
# force when it appended.
PILOT_TRANSITIONS_1_2 = PILOT_TRANSITIONS_1_1 | {
    ("committed", "termination.agreed", "terminated"),
    ("in_performance", "termination.agreed", "terminated"),
    ("acceptance_pending", "termination.agreed", "terminated"),
    ("settlement_pending", "termination.agreed", "terminated"),
    ("exception_open", "termination.agreed", "terminated"),
    ("committed", "agreement.amended", "committed"),
    ("in_performance", "agreement.amended", "in_performance"),
}

# Version 1.3 registers the direct bilateral formation path adopted after the
# specification review of 30 July 2026: agreement.direct moves a transaction from draft straight
# to agreement_pending, so that two parties who already found each other reach
# an agreement without a publication, a qualification round, or a negotiation
# room. Versions 1.0 to 1.2 stay immutable, so a record made under any of them
# replays against the set that was in force when it appended and the direct
# transition is illegal there.
PILOT_TRANSITIONS_1_3 = PILOT_TRANSITIONS_1_2 | {
    ("draft", "agreement.direct", "agreement_pending"),
}

PILOT_RULE_IDS = {
    "a202-rules/pilot#dispute.window",
    "a202-rules/pilot#appeal.window",
    "a202-rules/pilot#appeal.route",
    "a202-rules/pilot#determiner.authority",
    "a202-rules/pilot#determination.effect",
    "a202-rules/pilot#obligation.acceptance-binds-assertion",
    "a202-rules/pilot#obligation.remainder-required",
    "a202-rules/pilot#state.transition-legality",
    "a202-rules/pilot#disclosure.session-isolation",
}

RULE_SETS = {
    ("a202-rules/pilot", "1.0"): {
        "rules_hash": "11a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f80",
        "rules": PILOT_RULE_IDS,
        # The effect a determination may claim, by question class. A class that
        # is absent grants no effect, and absence resolves downward to advisory
        # rather than upward to anything.
        "effect_grants": {
            "act": "binding",
            "obligation_state": "presumptive",
            "determination": "binding",
        },
        "dispute_window_hours": 168,
        "appeal_window_hours": 336,
        "transitions": PILOT_TRANSITIONS_1_0,
    },
    ("a202-rules/pilot", "1.1"): {
        "rules_hash": "22b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f8091",
        "rules": PILOT_RULE_IDS,
        "effect_grants": {
            "act": "binding",
            "obligation_state": "presumptive",
            "determination": "binding",
        },
        "dispute_window_hours": 168,
        "appeal_window_hours": 336,
        "transitions": PILOT_TRANSITIONS_1_1,
    },
    ("a202-rules/pilot", "1.2"): {
        "rules_hash": "33c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f8091a2",
        "rules": PILOT_RULE_IDS,
        "effect_grants": {
            "act": "binding",
            "obligation_state": "presumptive",
            "determination": "binding",
        },
        "dispute_window_hours": 168,
        "appeal_window_hours": 336,
        "transitions": PILOT_TRANSITIONS_1_2,
    },
    ("a202-rules/pilot", "1.3"): {
        "rules_hash": "44d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3",
        "rules": PILOT_RULE_IDS,
        "effect_grants": {
            "act": "binding",
            "obligation_state": "presumptive",
            "determination": "binding",
        },
        "dispute_window_hours": 168,
        "appeal_window_hours": 336,
        "transitions": PILOT_TRANSITIONS_1_3,
    },
}

EFFECT_ORDER = {"advisory": 0, "presumptive": 1, "binding": 2}

# The registered state vocabularies. A determination's state_result may name
# only a state one of the specification's machines defines; a state outside
# every vocabulary is a transition to nowhere and fails closed.
AGGREGATE_STATES = {
    "draft", "published", "qualifying", "negotiating", "agreement_pending",
    "committed", "in_performance", "acceptance_pending", "settlement_pending",
    "completed", "exception_open", "cancelled", "expired", "terminated",
}
SESSION_STATES = {
    "opened", "active", "paused_for_approval", "accepted", "rejected",
    "withdrawn", "expired", "closed",
}
OBLIGATION_STATES = {
    "pending", "due", "asserted", "accepted", "rejected", "disputed",
    "discharged", "waived", "expired", "released",
}
REGISTERED_RESULT_STATES = AGGREGATE_STATES | SESSION_STATES | OBLIGATION_STATES

# The role scope registry of conformance-role-scopes-v0.1.md section 3.1. It is
# closed in v0.1, and an identifier that does not resolve here is refused rather
# than read as the nearest registered scope or dropped for an unscoped reading.
REGISTERED_ROLE_SCOPES = {
    "a202-scope/bilateral/0.1",
    "a202-scope/operated/0.1",
}

# The fixture families each role scope contains, as the Family column of
# conformance-role-scopes-v0.1.md sections 4.3 and 5.3 names them, lowercased
# with spaces replaced by hyphens. A grade's bands and its held-out coverage
# name the families they were established from, and a family outside the named
# scope is the overclaim of section 6.3 item 3. The two sets are the two halves
# of a partition that document states is total and disjoint over the fixtures on
# disk; the conformance-grade family appears in both because each scope holds
# grade fixtures of its own, exactly as the conformance-grades document's
# sections appear in both scope tables.
BILATERAL_FIXTURE_FAMILIES = {
    "mandate",
    "delegation-chain",
    "offer",
    "agreement",
    "obligation",
    "evidence-and-verification",
    "dispute-and-determination",
    "settlement",
    "termination",
    "carrier-declaration",
    "key-record",
    "approval",
    "party-family",
    "envelope-annotation",
    "policy-decision",
    "conformance-grade",
}
OPERATED_FIXTURE_FAMILIES = {
    "invitation",
    "session-event",
    "auction",
    "stream-disclosure",
    "annotated-offer",
    "direct-formation-contention",
    "appeal",
    "conformance-grade",
}
SCOPE_FIXTURE_FAMILIES = {
    "a202-scope/bilateral/0.1": BILATERAL_FIXTURE_FAMILIES,
    "a202-scope/operated/0.1": OPERATED_FIXTURE_FAMILIES,
}


def resolve_rules(ref: dict | None) -> dict | None:
    """Resolve a rules reference to an exact, hash-addressed rule set version.

    A reference whose hash does not match the registered one does not resolve.
    Unavailability is not permission: every caller of this function treats None
    as a refusal rather than as an absent constraint.
    """
    if not isinstance(ref, dict):
        return None
    entry = RULE_SETS.get((ref.get("rule_set_id"), ref.get("version")))
    if entry is None:
        return None
    if ref.get("rules_hash") != entry["rules_hash"]:
        return None
    return entry


# --- invariants that JSON Schema cannot express -------------------------------

# Substrings that must never appear in a key of a session-stream event's `data`.
# A losing bidder's close reason may state that it lost. It may not state what it
# lost to, to whom, or against how many. See test 16 in
# negotiation/pilot-transaction-state-machine-v0.1.md section 11 and the
# disclosure rules in negotiation/auction-event-semantics-v0.1.md.
#
# Every event is now constrained at the schema layer by an allowlist:
# sessionCloseData on terminal session events, sessionEventData on the rest of
# the session lifecycle, and transactionEventData on the aggregate lifecycle.
# An allowlist is the real protection, because it refuses free-text keys a
# denylist would never anticipate.
#
# This denylist is the second, independent layer, kept because both layers must
# fail closed on their own: widening either allowlist without updating this list,
# or vice versa, must not let a leak through. It is applied to every stream kind
# and at every nesting depth.
RIVAL_DISCLOSING_KEY_PARTS = (
    "competing",
    "rival",
    "other_bid",
    "bid_count",
    "bidder_count",
    "session_count",
    "participant_count",
    "winning_price",
    "best_price",
    "best_bid",
    "rank",
)

# Reason codes whose mere return to the acting party discloses aggregate state
# the actor is not entitled to. `A202-BID-NO-IMPROVEMENT` tells a bidder that a
# standing better bid exists, which is exactly what a sealed event withholds.
# Private visibility does not help: the leak is to the actor, not to a rival.
#
# These are permitted only under a declared disclosure policy that allows them.
# The v0.1 kernel has no disclosure policy object, so they fail closed.
# A202-LOT-ALREADY-AWARDED is on the list for the same reason as
# A202-BID-NO-IMPROVEMENT: returned to a bidder it discloses that an award
# happened, which is aggregate state a sealed event withholds until the
# neutral close reason delivers it symmetrically.
DISCLOSURE_BEARING_REASON_CODES = {
    "A202-BID-NO-IMPROVEMENT",
    "A202-LOT-ALREADY-AWARDED",
}

# A dispute description is untrusted free text that nothing in the protocol
# reads meaning out of, and the disclosure rules apply to it unchanged. A field
# through which anything can travel is the field a rival's price travels
# through, so free text carrying a party identifier that is not a party to the
# dispute, or a money-shaped token, is refused.
MONEY_IN_FREE_TEXT = re.compile(
    r"\b[A-Z]{3}\s?[0-9]+(?:[.,][0-9]+)?\b|\b[0-9]+(?:[.,][0-9]{2})\s?[A-Z]{3}\b"
)
PARTY_IN_FREE_TEXT = re.compile(r"\b(?:org|agt|off|acc)_[A-Za-z0-9][A-Za-z0-9_-]{2,127}\b")

# A locator hint is an ordinary field of a shared object. It never establishes
# anything, and it carries no secret, bearer token, credential, or personal
# data.
SECRET_IN_HINT = re.compile(
    r"(?i)\b(bearer|authorization|api[_-]?key|access[_-]?token|secret|password)\b"
)


def _data_keys(value):
    """Every member name in an event's data object, at any depth."""
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key
            yield from _data_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _data_keys(item)


def evidence_reference_failures(ref, seen_object_form: bool = True) -> list[str]:
    """Check one evidence reference in either accepted form."""
    failures: list[str] = []

    if isinstance(ref, str):
        # The identifier-only short form remains valid in v0.1. It carries no
        # content hash, so a verifier resolves it or reports it as not
        # checkable. It is never reported as verified on the strength of the
        # identifier alone, and it is not a failure either.
        return failures

    if not isinstance(ref, dict):
        return ["A202-EVIDENCE-HASH-MISMATCH"]

    digest = ref.get("content_hash")
    if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
        # A reference with a locator hint and no usable content hash would make
        # retrieval the only check, which puts whoever controls the location in
        # control of the evidence.
        if digest is None:
            failures.append("A202-EVIDENCE-HASH-MISMATCH")
        else:
            failures.append("A202-HASH-FORMAT-INVALID")

    if ref.get("evidence_type") not in REGISTERED_EVIDENCE_TYPES:
        failures.append("A202-EVIDENCE-TYPE-UNKNOWN")

    hint = ref.get("locator_hint")
    if isinstance(hint, str) and SECRET_IN_HINT.search(hint):
        failures.append("A202-DISCLOSURE-DENIED")

    return failures


def collect_evidence_refs(payload: dict) -> list:
    refs: list = []
    for key in ("evidence_refs", "assurance_evidence_refs"):
        value = payload.get(key)
        if isinstance(value, list):
            refs.extend(value)
    outcome = payload.get("outcome")
    if isinstance(outcome, dict) and isinstance(outcome.get("evidence_relied_on"), list):
        refs.extend(outcome["evidence_relied_on"])
    return refs


def due_condition_failures(condition, depth: int = 0) -> list[str]:
    """The due condition registry is closed and fails closed at evaluation.

    A registry enforced only at validation would let a member added to a schema
    enum, with no evaluator that knows what it means, make an obligation become
    due.
    """
    failures: list[str] = []
    if not isinstance(condition, dict):
        return ["A202-OBLIGATION-CONDITION-UNKNOWN"]

    kind = condition.get("type")
    if kind not in REGISTERED_DUE_CONDITION_TYPES:
        return ["A202-OBLIGATION-CONDITION-UNKNOWN"]

    # A registered type wearing another type's fields is not that type.
    if set(condition) - DUE_CONDITION_FIELDS[kind]:
        failures.append("A202-OBLIGATION-CONDITION-UNKNOWN")

    if kind == "all_of":
        if depth > 0:
            # A nested conjunction is a flat conjunction written twice.
            failures.append("A202-OBLIGATION-CONDITION-UNKNOWN")
        entries = condition.get("conditions")
        if not isinstance(entries, list) or len(entries) < 2:
            failures.append("A202-OBLIGATION-CONDITION-UNKNOWN")
        else:
            for entry in entries:
                failures.extend(due_condition_failures(entry, depth + 1))

    if kind == "due_at_time":
        business = condition.get("business_days")
        if isinstance(business, dict) and not business.get("calendar"):
            # A duration in business days with no named calendar is not a term.
            failures.append("A202-TERMS-INVALID")

    if kind == "due_on_event":
        evidence_type = condition.get("evidence_type")
        if evidence_type is not None and evidence_type not in REGISTERED_EVIDENCE_TYPES:
            failures.append("A202-EVIDENCE-TYPE-UNKNOWN")

    return failures


def due_on_discharge_edges(obligation: dict) -> list[str]:
    """The obligation identifiers this obligation's discharge condition waits on."""
    payload = obligation.get("payload", {})
    condition = payload.get("due_condition")
    entries = [condition]
    if isinstance(condition, dict) and condition.get("type") == "all_of":
        entries = condition.get("conditions") or []
    targets = []
    for entry in entries:
        if isinstance(entry, dict) and entry.get("type") == "due_on_discharge":
            target = entry.get("obligation_id")
            if isinstance(target, str):
                targets.append(target)
    return targets


def mandate_checks(doc: dict) -> list[str]:
    """The mandate rules of commercial-mandate-v0.1.md that the schema also
    expresses, enforced independently here so that each of the two layers
    fails closed on its own, plus the interval rule the schema cannot express.

    Each check returns the reason code an implementation must produce for the
    failure, which is what lets the runner assert that a negative fixture is
    refused for its declared reason rather than for an incidental one.
    """
    failures: list[str] = []

    try:
        if rfc3339(doc["valid_from"]) >= rfc3339(doc["valid_until"]):
            failures.append("A202-MANDATE-INTERVAL-INVALID")
    except (KeyError, ValueError):
        failures.append("A202-MANDATE-INTERVAL-INVALID")

    # An empty constraints array confers unbounded authority within the
    # allowed actions. Deliberate absence of a limit is an explicit permissive
    # constraint, so that it appears in the audit record.
    if not doc.get("constraints"):
        failures.append("A202-MANDATE-UNBOUNDED")

    # Scope must be bounded by transaction or category. Geography and
    # counterparty narrow an existing boundary; they cannot establish one.
    scope = doc.get("scope") or {}
    if not scope.get("transaction_ids") and not scope.get("categories"):
        failures.append("A202-MANDATE-SCOPE-TOO-BROAD")

    # Cached status is the only channel by which a revocation reaches a
    # relying party. Status served over plain HTTP is forgeable in transit.
    endpoint = doc.get("status_endpoint")
    if isinstance(endpoint, str) and not endpoint.startswith("https://"):
        failures.append("A202-MANDATE-STATUS-INSECURE")

    # Both registries are closed in v0.1. The schema refuses these too; this
    # layer refuses them at evaluation so that widening the enum alone cannot
    # let an act through.
    for constraint in doc.get("constraints") or []:
        if not isinstance(constraint, dict):
            failures.append("A202-MANDATE-CONSTRAINT-UNKNOWN")
            continue
        if constraint.get("type") not in REGISTERED_CONSTRAINT_TYPES:
            failures.append("A202-MANDATE-CONSTRAINT-UNKNOWN")
        if constraint.get("operator") not in REGISTERED_CONSTRAINT_OPERATORS:
            failures.append("A202-MANDATE-CONSTRAINT-UNKNOWN")

    # Exactly one of an agent or a delegated principal. A mandate naming both
    # is ambiguous about who acts under it, and is rejected rather than read
    # charitably.
    subject = doc.get("subject") or {}
    if ("agent_id" in subject) == ("principal_id" in subject):
        failures.append("A202-MANDATE-SUBJECT-AMBIGUOUS")

    # allowed: false requires depth 0, allowed: true requires depth >= 1. An
    # incoherent pair is rejected rather than interpreted.
    delegation = doc.get("delegation") or {}
    allowed = delegation.get("allowed")
    depth = delegation.get("maximum_depth")
    if allowed is False and depth != 0:
        failures.append("A202-MANDATE-DELEGATION-INCOHERENT")
    if allowed is True and isinstance(depth, int) and depth < 1:
        failures.append("A202-MANDATE-DELEGATION-INCOHERENT")

    return failures


def delegation_checks(doc: dict) -> list[str]:
    """Monotonic narrowing along the delegation chain, per
    commercial-mandate-v0.1.md section 7.

    The fixture carries a parent mandate and a child mandate. The child must
    be equal to or narrower than the parent on every axis: it references the
    parent, fits inside its validity interval, carries a subset of its
    actions, narrows its scope, retains every parent deny constraint,
    tightens but never loosens a numeric limit, and reduces delegation depth.
    Numeric comparison is decimal, never binary floating point. Every failure
    is A202-MANDATE-DELEGATION-WIDENING, the code section 7 names.
    """
    failures: list[str] = []
    parent = doc.get("parent")
    child = doc.get("child")
    if not isinstance(parent, dict) or not isinstance(child, dict):
        return ["A202-MANDATE-DELEGATION-WIDENING"]

    if child.get("parent_mandate_id") != parent.get("id"):
        failures.append("A202-MANDATE-DELEGATION-WIDENING")

    try:
        if rfc3339(child["valid_from"]) < rfc3339(parent["valid_from"]) or (
            rfc3339(child["valid_until"]) > rfc3339(parent["valid_until"])
        ):
            failures.append("A202-MANDATE-DELEGATION-WIDENING")
    except (KeyError, ValueError):
        failures.append("A202-MANDATE-DELEGATION-WIDENING")

    if not set(child.get("actions") or []) <= set(parent.get("actions") or []):
        failures.append("A202-MANDATE-DELEGATION-WIDENING")

    # On every axis the parent declares, the child declares an equal or
    # narrower set. An axis the parent does not declare may be added by the
    # child, because adding an axis narrows.
    parent_scope = parent.get("scope") or {}
    child_scope = child.get("scope") or {}
    for axis in (
        "transaction_ids",
        "categories",
        "counterparty_organization_ids",
        "geographies",
    ):
        if axis not in parent_scope:
            continue
        child_axis = child_scope.get(axis)
        if not isinstance(child_axis, list) or not child_axis:
            failures.append("A202-MANDATE-DELEGATION-WIDENING")
        elif not set(child_axis) <= set(parent_scope[axis]):
            failures.append("A202-MANDATE-DELEGATION-WIDENING")

    # Every parent deny constraint is retained, matched on type, path, and
    # operator. A numeric limit may tighten and may never loosen.
    child_constraints = {
        (c.get("type"), c.get("path"), c.get("operator")): c
        for c in child.get("constraints") or []
        if isinstance(c, dict)
    }
    for constraint in parent.get("constraints") or []:
        if not isinstance(constraint, dict) or constraint.get("on_failure") != "deny":
            continue
        key = (constraint.get("type"), constraint.get("path"), constraint.get("operator"))
        counterpart = child_constraints.get(key)
        if counterpart is None:
            failures.append("A202-MANDATE-DELEGATION-WIDENING")
            continue
        if constraint.get("operator") in NUMERIC_CONSTRAINT_OPERATORS:
            try:
                parent_value = Decimal(str(constraint.get("value")))
                child_value = Decimal(str(counterpart.get("value")))
            except InvalidOperation:
                failures.append("A202-MANDATE-DELEGATION-WIDENING")
                continue
            if constraint["operator"] == "maximum" and child_value > parent_value:
                failures.append("A202-MANDATE-DELEGATION-WIDENING")
            if constraint["operator"] == "minimum" and child_value < parent_value:
                failures.append("A202-MANDATE-DELEGATION-WIDENING")

    # A child exists one hop below its parent, so the parent must permit
    # delegation at all, and the child's remaining depth must be strictly
    # less than the parent's.
    parent_delegation = parent.get("delegation") or {}
    child_delegation = child.get("delegation") or {}
    if not parent_delegation.get("allowed"):
        failures.append("A202-MANDATE-DELEGATION-WIDENING")
    else:
        parent_depth = parent_delegation.get("maximum_depth") or 0
        child_depth = child_delegation.get("maximum_depth") or 0
        if child_depth > parent_depth - 1:
            failures.append("A202-MANDATE-DELEGATION-WIDENING")

    return failures


def normative_checks(
    doc: dict,
    kind: str,
    profiles: dict,
    registry: Registry,
    context: dict | None = None,
) -> list[str]:
    """Return the reason codes an implementation must raise for this document.

    These are normative specification checks that JSON Schema cannot express.
    They are counterparty-visible rules, not the proprietary policy evaluator.

    `context` carries the other objects a bundle disclosed, keyed by identifier
    and by declared content hash, plus whatever the bundle stated about the
    record around them. A check that needs another object runs only when the
    bundle disclosed one, so that a single-object fixture is never failed for
    the absence of something it was never given.
    """
    failures: list[str] = []
    context = context or {}
    by_id = context.get("objects_by_id", {})
    by_hash = context.get("objects_by_hash", {})
    stated = context.get("stated", {})

    if kind == "mandate":
        failures.extend(mandate_checks(doc))
        return failures

    if kind == "grade":
        failures.extend(grade_checks(doc))
        return failures

    payload = doc.get("payload", {})
    object_type = doc.get("object_type")
    payload_members = set(_data_keys(payload))

    # An act that requires two signatures is not the act until both are on it.
    # MINIMUM_SIGNATURES was applied in bundle_checks alone until 30 July 2026,
    # so a single object carrying an agreement with one signature was refused by
    # the schema's minItems and by nothing that returns a reason code. Section
    # 10 of canonical-commercial-model-v0.1.md requires both parties' signatures
    # over the same agreement bytes, and section 10 of
    # pilot-transaction-state-machine-v0.1.md gives the code for a required
    # signature that is absent.
    minimum = MINIMUM_SIGNATURES.get(object_type)
    if minimum is not None and object_type not in SIGNATURE_COUNT_RULED_BY_PURPOSE:
        if len(doc.get("signatures") or []) < minimum:
            failures.append("A202-EVIDENCE-SIGNATURE-INVALID")

    # `kernel_annotations` are control-plane metadata attached after signing,
    # and section 3 of canonical-commercial-model-v0.1.md states that an
    # agent-authored `action_envelope` MUST NOT carry them. An envelope is the
    # agent's own submission to the kernel and so precedes the minting in step 4
    # of section 9 that writes annotations at all, which is why annotations on
    # one were written by somebody other than the control plane.
    if object_type == "action_envelope" and "kernel_annotations" in doc:
        failures.append("A202-ANNOTATION-FORGED")

    # A claim secret is a bearer credential. Section 7 of
    # counterparty-invitation-v0.1.md requires a shared object to carry its hash
    # and never its value, and the scan runs on every object type because the
    # rule is about the secret rather than about the invitation.
    if CLAIM_SECRET_MEMBER_NAMES & payload_members:
        failures.append("A202-INVITATION-SECRET-DISCLOSED")

    # v0.1 defines a single award unit per event and no award-unit object, so a
    # reference to one resolves nowhere. Sections 8.1 and 9 of
    # auction-event-semantics-v0.1.md require the bid to be refused rather than
    # accepted against the wrong award unit.
    if AWARD_UNIT_MEMBER_NAMES & payload_members:
        failures.append("A202-LOT-UNKNOWN")

    # A declared endpoint other than a mandate status endpoint is forgeable in
    # transit for the same reason a status endpoint is, and section 10 of
    # pilot-transaction-state-machine-v0.1.md gives it its own code.
    if object_type == "agent":
        endpoint = payload.get("endpoint")
        if isinstance(endpoint, str) and not endpoint.startswith("https://"):
            failures.append("A202-ENDPOINT-INSECURE")

    if object_type == "offer":
        try:
            if rfc3339(payload["valid_until"]) <= rfc3339(doc["created_at"]):
                failures.append("A202-OFFER-EXPIRED")
        except (KeyError, ValueError):
            failures.append("A202-OFFER-EXPIRED")

        terms = payload.get("terms", {})
        profile_id = terms.get("profile")
        profile_schema = profiles.get(profile_id)
        if profile_schema is None:
            failures.append("A202-PROFILE-UNKNOWN")
        else:
            validator = Draft202012Validator(
                profile_schema, registry=registry, format_checker=FormatChecker()
            )
            if list(validator.iter_errors(terms.get("profile_terms", {}))):
                failures.append("A202-PROFILE-TERMS-INVALID")

    if object_type == "policy_decision":
        if payload.get("decision") == "deny":
            if payload.get("visibility") not in {"private_to_actor", "operator_only"}:
                failures.append("A202-DISCLOSURE-DENIED")
            if payload.get("stream", {}).get("kind") != "private":
                failures.append("A202-DISCLOSURE-DENIED")

        if DISCLOSURE_BEARING_REASON_CODES & set(payload.get("reason_codes", [])):
            failures.append("A202-DISCLOSURE-POLICY-VIOLATION")

    if object_type == "transaction_event":
        # v0.1 defines two stream kinds. An event on any other stream is an
        # event format this specification version does not define, and section 9
        # of auction-event-semantics-v0.1.md requires an implementation to
        # refuse it rather than approximate it: an approximated event is one
        # whose fairness cannot be proven, which removes the reason to run it
        # under this specification at all.
        if payload.get("stream", {}).get("kind") not in REGISTERED_STREAM_KINDS:
            failures.append("A202-AUCTION-FORMAT-UNSUPPORTED")

        # The denylist applies to every stream kind, not only to session
        # streams. Post-commit the winning counterparty reads the transaction
        # stream, so rival-disclosing keys there leak exactly as they would on
        # a session stream. The scan is recursive because an open `data`
        # object can nest the same key one level down.
        for key in _data_keys(payload.get("data", {})):
            if any(part in key.lower() for part in RIVAL_DISCLOSING_KEY_PARTS):
                failures.append("A202-DISCLOSURE-POLICY-VIOLATION")
                break

        # Deletion is not a defined operation. There is no protocol operation
        # that removes a determination, and an implementation must not provide
        # one, so an event naming one is refused rather than ignored.
        if payload.get("event_type") in UNDEFINED_EVENT_TYPES:
            failures.append("A202-STATE-TRANSITION-DENIED")

    if object_type == "counterparty_invitation":
        try:
            if rfc3339(payload["expires_at"]) <= rfc3339(doc["created_at"]):
                failures.append("A202-INVITATION-EXPIRED")
        except (KeyError, ValueError):
            failures.append("A202-INVITATION-EXPIRED")

        # A grant must name exactly the transaction it was issued against. A
        # party that has received one invitation has demonstrated nothing
        # beyond that transaction, so a wider grant is standing market access
        # obtained for free.
        granted = payload.get("granted_scope", {}).get("transaction_ids", [])
        if granted != [doc.get("transaction_id")]:
            failures.append("A202-INVITATION-SCOPE-EXCEEDED")

    # Assurance is reported, never inferred. The invariant in section 12 of
    # canonical-commercial-model-v0.1.md is stated over a declared assurance
    # level rather than over one object type, so it is enforced that way here. A
    # party that declares its own level above `self_asserted` has declared one
    # with nothing behind it, which is why the organization payload has no
    # assurance member at all: a second home for assurance would be a second
    # answer to how strongly a counterparty is known.
    assurance = payload.get("assurance")
    if object_type == "invitation_acceptance" or assurance is not None:
        if assurance != "self_asserted":
            supporting = payload.get("assurance_evidence_refs") or payload.get(
                "identity_evidence_refs"
            )
            if not supporting:
                failures.append("A202-ASSURANCE-UNSUPPORTED")

    if object_type == "invitation_acceptance":
        # An operator-custodied key may not act without a named principal's
        # approval bound to the exact hash. The schema expresses this too;
        # both layers are required so that neither alone can allow it.
        if payload.get("key_custody") == "operator_custodied":
            if not payload.get("issuance_approval_id"):
                failures.append("A202-CUSTODY-APPROVAL-REQUIRED")

        # Operator authorship alone is not an onboarding record.
        purposes = {sig.get("purpose") for sig in doc.get("signatures", [])}
        if not {"invitation_claim", "object_issuance"} <= purposes:
            failures.append("A202-INVITATION-CLAIM-UNSIGNED")

    # --- evidence references, wherever they appear ----------------------------

    for ref in collect_evidence_refs(payload):
        failures.extend(evidence_reference_failures(ref))

    # --- obligation ----------------------------------------------------------

    if object_type == "obligation":
        failures.extend(due_condition_failures(payload.get("due_condition")))

        subject = payload.get("subject")
        if not isinstance(subject, dict):
            failures.append("A202-OBLIGATION-SUBJECT-UNREFERENCED")
        else:
            # The subject names the owed term. It never restates it: a restated
            # term can drift from the agreement while both copies stay validly
            # signed.
            if set(subject) - {"agreement_id", "terms_hash", "profile", "term_path"}:
                failures.append("A202-OBLIGATION-SUBJECT-UNREFERENCED")
            if subject.get("agreement_id") != payload.get("agreement_id"):
                failures.append("A202-OBLIGATION-SUBJECT-UNREFERENCED")
            path = subject.get("term_path")
            if not isinstance(path, str) or not path.startswith(
                ("$.terms.core", "$.terms.profile_terms")
            ):
                failures.append("A202-OBLIGATION-SUBJECT-UNREFERENCED")

            agreement = by_id.get(subject.get("agreement_id"))
            if agreement is not None:
                agreement_payload = agreement.get("payload", {})
                if subject.get("terms_hash") != agreement_payload.get("terms_hash"):
                    failures.append("A202-OBLIGATION-SUBJECT-UNREFERENCED")
                if subject.get("profile") != agreement_payload.get("terms", {}).get(
                    "profile"
                ):
                    failures.append("A202-OBLIGATION-SUBJECT-UNREFERENCED")
                parties = {
                    agreement_payload.get("buyer", {}).get("organization_id"),
                    agreement_payload.get("supplier", {}).get("organization_id"),
                }
                for role in ("obligor", "obligee"):
                    party = payload.get(role, {})
                    if party.get("organization_id") not in parties:
                        failures.append("A202-OBLIGATION-SUBJECT-UNREFERENCED")

        consideration = payload.get("consideration")
        if isinstance(consideration, dict):
            amount = consideration.get("amount")
            if not isinstance(amount, str) or not re.fullmatch(
                r"(0|[1-9][0-9]*)(\.[0-9]{1,18})?", amount
            ):
                # Consideration reuses the money type. A negative amount, or a
                # binary floating-point one, is a parallel representation.
                failures.append("A202-TERMS-INVALID")

    if object_type == "performance_event":
        refs = payload.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            failures.append("A202-OBLIGATION-ASSERTION-UNEVIDENCED")
        obligation = by_id.get(payload.get("obligation_id"))
        if obligation is not None:
            if payload.get("unit_code") != obligation["payload"].get("unit_code"):
                failures.append("A202-OBLIGATION-TERMS-MUTATED")

    if object_type == "obligation_response":
        # No response mutates the obligation. Changed terms are a new obligation
        # under an amended agreement, never a new version of this one.
        mutating = {
            "subject",
            "due_condition",
            "quantity",
            "unit_code",
            "consideration",
        } & set(payload)
        if mutating:
            failures.append("A202-OBLIGATION-TERMS-MUTATED")

        if payload.get("response_type") == "reject":
            if payload.get("reason_code") not in REGISTERED_REJECTION_REASONS:
                failures.append("A202-OBLIGATION-REJECTION-REASON-UNKNOWN")

        obligation = by_id.get(payload.get("obligation_id"))
        if obligation is not None:
            obligee = obligation["payload"].get("obligee", {})
            actor = doc.get("created_by", {}).get("organization_id")
            # Acceptance is a distinct signed act by the obligee. This holds for
            # a waiver as much as for an acceptance, and a waiver names no
            # assertion, so a check written only against assertion_id misses it.
            if actor != obligee.get("organization_id"):
                failures.append("A202-OBLIGATION-RESPONSE-UNAUTHORIZED")

            if payload.get("response_type") == "accept":
                owed = obligation["payload"].get("quantity")
                accepted = payload.get("accepted_quantity")
                # Decimal, never binary floating point: at float precision a
                # one-unit shortfall above 2**53 compares equal and the
                # remainder requirement silently disappears. An unparseable
                # quantity fails closed rather than reading as not-short.
                try:
                    short = Decimal(str(accepted)) < Decimal(str(owed))
                except InvalidOperation:
                    short = False
                    failures.append("A202-TERMS-INVALID")
                if short and not payload.get("remainder_obligation_id"):
                    # The shortfall would otherwise disappear from the record.
                    failures.append("A202-OBLIGATION-REMAINDER-MISSING")

        assertion = by_id.get(payload.get("assertion_id"))
        if assertion is not None:
            if payload.get("assertion_hash") != assertion.get("content_hash"):
                failures.append("A202-OBLIGATION-RESPONSE-HASH-MISMATCH")
        elif payload.get("assertion_id") and by_id:
            if payload.get("assertion_id") not in stated.get("stated_gaps", []):
                failures.append("A202-EVIDENCE-DISCLOSURE-INCOMPLETE")

    # --- dispute and determination -------------------------------------------

    if object_type == "dispute":
        grounds = payload.get("grounds")
        if not isinstance(grounds, list) or not grounds:
            failures.append("A202-DISPUTE-GROUNDS-UNKNOWN")
        else:
            permitted = (
                REGISTERED_APPEAL_GROUNDS
                if payload.get("subject_type") == "determination"
                else REGISTERED_DISPUTE_GROUNDS
            )
            unregistered = [g for g in grounds if g not in permitted]
            if unregistered:
                if payload.get("subject_type") == "determination":
                    # Disagreement with the rule itself is not a ground of
                    # appeal. A party that thinks the rule is wrong is asking
                    # for the rule to change, which is a change proposal.
                    failures.append("A202-APPEAL-GROUNDS-UNKNOWN")
                else:
                    failures.append("A202-DISPUTE-GROUNDS-UNKNOWN")

        if not payload.get("subject_hash"):
            # A dispute about an object that can change is a dispute about
            # nothing fixed.
            failures.append("A202-DISPUTE-SUBJECT-UNREFERENCED")
        elif by_hash and payload["subject_hash"] not in by_hash:
            if payload["subject_hash"] not in stated.get("resolvable_hashes", []):
                failures.append("A202-DISPUTE-SUBJECT-UNREFERENCED")

        if not payload.get("evidence_refs"):
            failures.append("A202-EVIDENCE-UNVERIFIED")

        description = payload.get("description")
        if isinstance(description, str):
            parties = {
                payload.get("raising_party", {}).get("organization_id"),
                payload.get("raising_party", {}).get("agent_id"),
                payload.get("respondent_party", {}).get("organization_id"),
                payload.get("respondent_party", {}).get("agent_id"),
            }
            named = set(PARTY_IN_FREE_TEXT.findall(description)) - parties
            leaks = bool(named) or bool(MONEY_IN_FREE_TEXT.search(description))
            leaks = leaks or any(
                part in description.lower() for part in RIVAL_DISCLOSING_KEY_PARTS
            )
            if leaks:
                failures.append("A202-DISCLOSURE-POLICY-VIOLATION")

        rules = resolve_rules(payload.get("rules_ref"))
        if rules is None:
            # A window that cannot be resolved cannot be shown to have been met,
            # and unavailability is not permission.
            failures.append("A202-DISPUTE-OUT-OF-WINDOW")
        else:
            subject_at = stated.get("subject_act_at")
            window = rules["dispute_window_hours"]
            if payload.get("subject_type") == "determination":
                window = rules["appeal_window_hours"]
            if subject_at:
                try:
                    if rfc3339(doc["created_at"]) > rfc3339(subject_at) + timedelta(
                        hours=window
                    ):
                        failures.append("A202-DISPUTE-OUT-OF-WINDOW")
                except (KeyError, ValueError):
                    failures.append("A202-DISPUTE-OUT-OF-WINDOW")

    if object_type == "determination":
        question = payload.get("question", {})
        outcome = payload.get("outcome", {})

        # There is no enumerated verdict. A verdict says which way a question
        # went and nothing about why, which leaves nothing to point at on
        # appeal and nothing for a third party to replay.
        if not isinstance(outcome, dict) or set(outcome) - {
            "finding",
            "rules_applied",
            "evidence_relied_on",
            "inputs_hash",
            "state_result",
        }:
            failures.append("A202-DETERMINATION-NOT-FOLLOWING")

        rules = resolve_rules(question.get("rules_ref"))
        if rules is None:
            failures.append("A202-DETERMINATION-NOT-FOLLOWING")
        else:
            applied = outcome.get("rules_applied") or []
            if not applied or any(rule not in rules["rules"] for rule in applied):
                failures.append("A202-DETERMINATION-NOT-FOLLOWING")
            if not outcome.get("evidence_relied_on") or not outcome.get("inputs_hash"):
                failures.append("A202-DETERMINATION-NOT-FOLLOWING")

            granted = rules["effect_grants"].get(question.get("subject_type"))
            claimed = payload.get("effect")
            if granted is None:
                if claimed != "advisory":
                    # Absence is not permission and is never inferred upward.
                    failures.append("A202-DETERMINATION-EFFECT-OVERCLAIM")
            elif EFFECT_ORDER.get(claimed, 3) > EFFECT_ORDER[granted]:
                failures.append("A202-DETERMINATION-EFFECT-OVERCLAIM")

            in_force = stated.get("rules_version_in_force")
            if in_force and question.get("rules_ref", {}).get("version") != in_force:
                # The version in force at the time of the subject act governs.
                # If a later version governed, changing the rules would change
                # the answer to a question that was already asked.
                failures.append("A202-DETERMINATION-NOT-FOLLOWING")

        # state_result is the only field through which a determination touches
        # state, and it is inert unless the rules granted a binding effect. Its
        # shape is closed at the schema layer; here the vocabulary is enforced:
        # it names the determined subject and a registered state, never an
        # arbitrary bag of transitions.
        state_result = outcome.get("state_result") if isinstance(outcome, dict) else None
        if isinstance(state_result, dict):
            if payload.get("effect") != "binding":
                failures.append("A202-DETERMINATION-EFFECT-OVERCLAIM")
            if state_result.get("subject_id") != question.get("subject_id"):
                failures.append("A202-DISPUTE-SUBJECT-UNREFERENCED")
            if state_result.get("state") not in REGISTERED_RESULT_STATES:
                failures.append("A202-STATE-TRANSITION-DENIED")

        dispute = by_id.get(payload.get("dispute_id"))
        if dispute is not None:
            for field in ("subject_type", "subject_hash", "subject_id"):
                if question.get(field) != dispute["payload"].get(field):
                    failures.append("A202-DISPUTE-SUBJECT-UNREFERENCED")
                    break
        elif payload.get("dispute_id") and by_id:
            if payload["dispute_id"] not in stated.get("stated_gaps", []):
                failures.append("A202-EVIDENCE-DISCLOSURE-INCOMPLETE")

        supersedes = payload.get("supersedes")
        if isinstance(supersedes, dict):
            if supersedes.get("reason") not in REGISTERED_SUPERSESSION_REASONS:
                # A record that changes for reasons it does not give is a record
                # whose changes cannot be audited.
                failures.append("A202-DETERMINATION-SUPERSESSION-UNREASONED")
            target = by_id.get(supersedes.get("determination_id"))
            if target is not None:
                if supersedes.get("determination_hash") != target.get("content_hash"):
                    failures.append("A202-EVIDENCE-HASH-MISMATCH")
                # A superseding determination names the same question as the one
                # it replaces. On the appeal path the question is the earlier
                # determination itself, so its own content hash is the other
                # accepted value; a determination on any third question is a
                # separate determination rather than a replacement.
                same_question = question.get("subject_hash") in (
                    target["payload"].get("question", {}).get("subject_hash"),
                    target.get("content_hash"),
                )
                if not same_question:
                    failures.append("A202-DISPUTE-SUBJECT-UNREFERENCED")
                # The chain is linear. A fork means two determinations claim to
                # be current on one question.
                already = [
                    other
                    for other in by_id.values()
                    if other is not doc
                    and other.get("object_type") == "determination"
                    and other is not target
                    and isinstance(other["payload"].get("supersedes"), dict)
                    and other["payload"]["supersedes"].get("determination_id")
                    == supersedes.get("determination_id")
                ]
                if already:
                    failures.append("A202-DETERMINATION-SUPERSESSION-FORKED")

    # --- agreement and acceptance hashes ---------------------------------------

    if object_type == "agreement":
        # terms_hash is recomputed, never trusted. An agreement whose
        # terms_hash does not equal the hash of its own terms is an agreement
        # whose signed summary and signed content disagree, which is exactly
        # the drift the hash exists to make impossible.
        terms = payload.get("terms")
        if isinstance(terms, dict) and payload.get("terms_hash") != content_hash_of(terms):
            failures.append("A202-AGREEMENT-HASH-MISMATCH")

        offer = by_id.get(payload.get("accepted_offer_id"))
        if offer is not None and payload.get("accepted_offer_hash") != offer.get(
            "content_hash"
        ):
            failures.append("A202-AGREEMENT-HASH-MISMATCH")

        # An amendment is a superseding agreement version reached through a
        # fresh offer and acceptance. A later version that names the same
        # acceptance or the same accepted offer as its predecessor is a
        # unilateral restatement wearing an amendment's shape.
        previous = by_id.get(doc.get("previous_version_id"))
        if previous is not None and previous.get("object_type") == "agreement":
            previous_payload = previous.get("payload", {})
            if payload.get("acceptance_id") == previous_payload.get("acceptance_id"):
                failures.append("A202-AGREEMENT-AMENDMENT-UNACCEPTED")
            if payload.get("accepted_offer_id") == previous_payload.get(
                "accepted_offer_id"
            ):
                failures.append("A202-AGREEMENT-AMENDMENT-UNACCEPTED")

    if object_type == "acceptance":
        offer = by_id.get(payload.get("offer_id"))
        if offer is not None and payload.get("offer_hash") != offer.get("content_hash"):
            failures.append("A202-AGREEMENT-HASH-MISMATCH")

    # --- settlement handoff ---------------------------------------------------

    if object_type == "settlement_instruction":
        if payload.get("rail") not in REGISTERED_SETTLEMENT_RAILS:
            # An unregistered rail is refused rather than routed to a default
            # adapter or dropped: the unchecked value selects who receives
            # money.
            failures.append("A202-SETTLEMENT-RAIL-UNKNOWN")

        trigger = payload.get("trigger")
        if not isinstance(trigger, dict) or not trigger.get("accepting_act_hash"):
            failures.append("A202-SETTLEMENT-TRIGGER-ABSENT")
        elif by_hash and trigger["accepting_act_hash"] not in by_hash:
            if trigger["accepting_act_hash"] not in stated.get("resolvable_hashes", []):
                failures.append("A202-SETTLEMENT-TRIGGER-ABSENT")

        payee = payload.get("payee_organization_id")
        if payee in COMMERCIAL_LAYER_ORGANIZATIONS:
            # The commercial layer never holds funds. Custody is a rail
            # property, and a layer that held funds would acquire an interest in
            # the outcome of the disputes it also records.
            failures.append("A202-SETTLEMENT-CUSTODY-REFUSED")
        if payee is not None and payee == payload.get("payer_organization_id"):
            failures.append("A202-SETTLEMENT-CUSTODY-REFUSED")

    return failures


# --- conformance grades -------------------------------------------------------


def grade_checks(doc: dict) -> list[str]:
    """The role scope rules of conformance-role-scopes-v0.1.md, enforced on a
    grade rather than asserted about one.

    The document states three refusals and, until this evaluator existed,
    nothing raised any of them: a grade naming an unregistered scope, a grade
    naming none or two, and a grade reporting a band established from fixtures
    outside the scope it names. Each is a refusal of the grade under section 8
    of that document, never a band 0, because an unreadable grade is an absence
    of assessment rather than a failed one.

    The shape rules of section 4 of conformance-grades-v0.1.md are in
    conformance-grade.schema.json. The rules here are the ones a schema cannot
    express: registry membership, a cardinality that has to fail with a reason
    code rather than as a missing member, and a coverage claim resolved against
    a partition held in another document.
    """
    failures: list[str] = []

    scope = doc.get("scope")
    named = scope.get("role_scopes") if isinstance(scope, dict) else None
    if not isinstance(named, list):
        named = []

    # Section 3.2 item 2. No fallback to the other registered scope, to a
    # nearest match, or to an unscoped reading.
    unregistered = [
        identifier for identifier in named if identifier not in REGISTERED_ROLE_SCOPES
    ]
    if unregistered:
        failures.append("A202-GRADE-SCOPE-UNKNOWN")

    # Section 3.2 items 1 and 3. Naming none and naming two are one refusal,
    # because a grade that covers both scopes is two grades and a grade that
    # covers neither states nothing a consumer can resolve.
    if len(named) != 1:
        failures.append("A202-GRADE-SCOPE-INVALID")

    # Section 6.3 items 3 and 4. A band is established only from the sections
    # and fixtures the named scope contains, and coverage in one scope is not
    # coverage in the other. The check runs only where exactly one registered
    # scope was named, because with no resolved scope there is nothing to read
    # the coverage against, and refusing twice for one unreadable field would
    # report one defect as two.
    if len(named) == 1 and not unregistered:
        covered = SCOPE_FIXTURE_FAMILIES[named[0]]
        claimed: list[str] = []
        dimensions = doc.get("dimensions")
        if isinstance(dimensions, dict):
            for result in dimensions.values():
                if isinstance(result, dict) and isinstance(
                    result.get("established_from"), list
                ):
                    claimed.extend(result["established_from"])
        held_out = doc.get("held_out_coverage")
        if isinstance(held_out, dict) and isinstance(held_out.get("families"), list):
            claimed.extend(held_out["families"])
        if any(family not in covered for family in claimed):
            failures.append("A202-GRADE-SCOPE-OVERCLAIM")

    return failures


# --- carrier capability declarations ------------------------------------------


def parse_version_declaration(params) -> bool:
    """A declaration parses when both fields are present and well formed."""
    if not isinstance(params, dict):
        return False
    read_versions = params.get("read_versions")
    write_version = params.get("write_version")
    if not isinstance(read_versions, list) or not read_versions:
        return False
    if any(
        not isinstance(value, str) or not SPEC_VERSION_PATTERN.fullmatch(value)
        for value in read_versions
    ):
        return False
    if not isinstance(write_version, str) or not SPEC_VERSION_PATTERN.fullmatch(
        write_version
    ):
        return False
    return True


def declaration_checks(doc: dict) -> list[str]:
    """Check a carrier capability declaration.

    The four failure conditions are not distinguished on the wire. They have
    exactly one correct outcome, and a caller handed four codes that must all be
    handled identically will eventually handle one of them differently, which is
    how a fail-closed path acquires a branch that fails open.
    """
    local = doc.get("local_party", {})
    counterparty = doc.get("counterparty_declaration")

    if not isinstance(counterparty, dict):
        # An unretrievable capability surface is a failure on the standing rule
        # that unavailability is not permission.
        return ["A202-EXTENSION-UNSUPPORTED"]

    entries = [
        entry
        for entry in counterparty.get("extensions", [])
        if isinstance(entry, dict) and entry.get("uri") == COMMERCIAL_EXTENSION_URI
    ]
    if len(entries) != 1:
        return ["A202-EXTENSION-UNSUPPORTED"]

    entry = entries[0]
    if not isinstance(entry.get("required"), bool):
        return ["A202-EXTENSION-UNSUPPORTED"]
    if not parse_version_declaration(entry.get("params")):
        return ["A202-EXTENSION-UNSUPPORTED"]
    if not parse_version_declaration(local):
        return ["A202-EXTENSION-UNSUPPORTED"]

    remote = entry["params"]
    # Each party checks that the counterparty writes a version it reads, and
    # that the counterparty reads the version it writes. There is no nearest
    # version and no fallback to an earlier extension URI: a version an
    # implementation did not declare is a version it did not commit to reading.
    if remote["write_version"] not in local["read_versions"]:
        return ["A202-EXTENSION-UNSUPPORTED"]
    if local["write_version"] not in remote["read_versions"]:
        return ["A202-EXTENSION-UNSUPPORTED"]

    return []


# --- bundles ------------------------------------------------------------------


def verification_report_failures(report) -> list[str]:
    """The three-valued output rules.

    A gap never reads as verified, the three outcomes are never collapsed to a
    boolean, and a report over a subset states its scope. Reporting a gap as a
    failure makes ordinary partial disclosure look like misconduct; reporting it
    as a pass makes an absence look like proof.
    """
    failures: list[str] = []
    if not isinstance(report, dict):
        return failures

    scope = report.get("scope")
    if not isinstance(scope, dict) or not scope.get("streams_in_scope"):
        # A report that does not state its scope is a report whose silence is
        # indistinguishable from completeness.
        failures.append("A202-EVIDENCE-REPORT-INVALID")

    checks = report.get("checks")
    if not isinstance(checks, list) or not checks:
        failures.append("A202-EVIDENCE-REPORT-INVALID")
        return failures

    undisclosed = set(scope.get("undisclosed_streams", []) if isinstance(scope, dict) else [])
    for check in checks:
        if not isinstance(check, dict):
            failures.append("A202-EVIDENCE-REPORT-INVALID")
            continue
        result = check.get("result")
        if result not in ("verified", "failed", "not_checkable"):
            # A per-check result reduced to a boolean has discarded the not
            # checkable set, which is the set a relying party most needs.
            failures.append("A202-EVIDENCE-REPORT-INVALID")
            continue
        if check.get("stream") in undisclosed and result != "not_checkable":
            failures.append("A202-EVIDENCE-REPORT-INVALID")

    if isinstance(scope, dict):
        for stream in undisclosed:
            named = any(
                isinstance(check, dict) and check.get("stream") == stream
                for check in checks
            )
            if not named:
                failures.append("A202-EVIDENCE-REPORT-INVALID")

    if any(
        isinstance(check, dict) and check.get("result") == "failed" for check in checks
    ) and report.get("overall") == "passing":
        failures.append("A202-EVIDENCE-REPORT-INVALID")

    return failures


def bundle_checks(fixture: dict, objects: list[dict]) -> list[str]:
    """Cross-object checks, in the order of the verification procedure."""
    failures: list[str] = []
    stated = fixture.get("context", {})

    # Step 1: recompute content hashes over the canonical bytes.
    for obj in objects:
        if obj.get("content_hash") != content_hash_of(obj):
            failures.append("A202-EVIDENCE-HASH-MISMATCH")

    # Step 2: signature purpose and required signature counts.
    for obj in objects:
        expected = SIGNATURE_PURPOSES.get(obj.get("object_type"))
        signatures = obj.get("signatures", [])
        if expected is not None:
            for signature in signatures:
                if signature.get("purpose") not in expected:
                    # A signature valid over the bytes and issued for a
                    # different purpose is not a signature for this act.
                    failures.append("A202-EVIDENCE-SIGNATURE-INVALID")
        minimum = MINIMUM_SIGNATURES.get(obj.get("object_type"))
        if minimum is not None and len(signatures) < minimum:
            failures.append("A202-EVIDENCE-SIGNATURE-INVALID")

    # A cycle among due_on_discharge conditions is refused. No obligation in a
    # cycle can ever become due, so accepting one would create an obligation set
    # that is permanently unsatisfiable and silently so.
    obligations = {
        obj.get("id"): obj for obj in objects if obj.get("object_type") == "obligation"
    }
    visiting: set[str] = set()
    settled: set[str] = set()

    def reaches_cycle(node: str) -> bool:
        if node in visiting:
            return True
        if node in settled or node not in obligations:
            return False
        visiting.add(node)
        found = any(
            reaches_cycle(target) for target in due_on_discharge_edges(obligations[node])
        )
        visiting.discard(node)
        settled.add(node)
        return found

    if any(reaches_cycle(node) for node in list(obligations)):
        failures.append("A202-OBLIGATION-CONDITION-CYCLIC")

    # Step 3: version chains are linear, start at 1, and do not fork.
    predecessors: dict[str, int] = {}
    for obj in objects:
        previous = obj.get("previous_version_id")
        if obj.get("version") == 1 and previous is not None:
            failures.append("A202-EVIDENCE-CHAIN-GAP")
        if previous is None:
            continue
        predecessors[previous] = predecessors.get(previous, 0) + 1
        earlier = next((o for o in objects if o.get("id") == previous), None)
        if earlier is not None and obj.get("version") != earlier.get("version", 0) + 1:
            failures.append("A202-EVIDENCE-CHAIN-GAP")
    if any(count > 1 for count in predecessors.values()):
        # Two successors to one version is a fork, and a fork means two objects
        # claim to be current.
        failures.append("A202-EVIDENCE-CHAIN-GAP")

    # Step 4: per-stream continuity, and no continuity across streams.
    events = [obj for obj in objects if obj.get("object_type") == "transaction_event"]
    by_hash = {obj.get("content_hash"): obj for obj in objects}
    streams: dict[str, list[dict]] = {}
    for event in events:
        stream = event["payload"].get("stream", {})
        streams.setdefault(stream.get("id"), []).append(event)
    for stream_id, members in streams.items():
        members.sort(key=lambda e: e["payload"].get("sequence", 0))
        for index, event in enumerate(members):
            previous_hash = event["payload"].get("previous_event_hash")
            if index > 0:
                expected_sequence = members[index - 1]["payload"]["sequence"] + 1
                if event["payload"].get("sequence") != expected_sequence:
                    failures.append("A202-EVIDENCE-CHAIN-GAP")
                # previous_event_hash names the content hash of the
                # immediately preceding event in the same stream, not merely
                # some earlier event. A chain that skips over an event has a
                # link nobody can replay through.
                if previous_hash != members[index - 1].get("content_hash"):
                    failures.append("A202-EVIDENCE-CHAIN-GAP")
                continue
            if previous_hash is None:
                continue
            predecessor = by_hash.get(previous_hash)
            if predecessor is None:
                # A first disclosed event naming a predecessor the verifier does
                # not hold is a stated boundary, not a gap.
                continue
            other_stream = predecessor["payload"].get("stream", {}).get("id")
            if other_stream != stream_id:
                # Sequence numbers are per stream. A verifier that expected
                # continuity across streams would be reading a covert channel as
                # a correctness property.
                failures.append("A202-EVIDENCE-CHAIN-GAP")

    # Step 5: replay guarded transitions against the rules version in force at
    # the time the event appended, never against the current one.
    in_force_versions = stated.get("event_rules_in_force", {})
    default_version = stated.get("rules_version_in_force", "1.0")
    for event in events:
        payload = event["payload"]
        if payload.get("event_type") in UNDEFINED_EVENT_TYPES:
            continue
        transition = (
            payload.get("from_state"),
            payload.get("event_type"),
            payload.get("to_state"),
        )
        in_force = in_force_versions.get(event.get("id"), default_version)
        governing = RULE_SETS.get(("a202-rules/pilot", in_force))
        if governing is None:
            failures.append("A202-EVIDENCE-TRANSITION-ILLEGAL")
            continue
        if transition not in governing["transitions"]:
            # A transition legal under a later rules version, or under no
            # version at all, is illegal here. A verifier that replayed an old
            # record against today's rules would report failures on a record
            # that was correct when it was made, and one that replayed a new
            # record against a version that never permitted the transition
            # would accept a move nobody agreed to.
            failures.append("A202-EVIDENCE-TRANSITION-ILLEGAL")

    # Step 5, the direct-formation guard. `agreement.direct` exists because two
    # parties who already found each other need no publication, no
    # qualification, and no negotiation room. Where a session stream exists on
    # the transaction, an operator opened a negotiation, offers are contending
    # in it, and a party that entered at `agreement.direct` would be selecting
    # itself out of a contest the other participants are still in. The guard is
    # checked rather than asserted, because a guard nothing evaluates is a
    # sentence rather than a rule.
    if any(event["payload"].get("event_type") == "agreement.direct" for event in events):
        if any(
            event["payload"].get("stream", {}).get("kind") == "session"
            for event in events
        ):
            failures.append("A202-EVIDENCE-TRANSITION-ILLEGAL")

    # Step 7: state every gap, and never let a gap read as a pass.
    failures.extend(verification_report_failures(stated.get("verification_report")))

    return failures


def bundle_errors(
    fixture: dict, profiles: dict, registry: Registry, kernel
) -> tuple[list, list[str]]:
    objects = [obj for obj in fixture.get("objects", []) if isinstance(obj, dict)]
    schema_errors: list = []
    for obj in objects:
        schema_errors.extend(kernel.iter_errors(obj))

    context = {
        "objects_by_id": {obj.get("id"): obj for obj in objects},
        "objects_by_hash": {obj.get("content_hash"): obj for obj in objects},
        "stated": fixture.get("context", {}),
    }

    rule_failures: list[str] = []
    for obj in objects:
        rule_failures.extend(
            normative_checks(obj, "kernel", profiles, registry, context)
        )
    rule_failures.extend(bundle_checks(fixture, objects))
    return schema_errors, rule_failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    registry = build_registry()
    profiles = profile_registry()
    manifest = load(MANIFEST)

    validators = {
        "kernel": Draft202012Validator(
            load(SCHEMAS / "commercial-kernel.schema.json"),
            registry=registry,
            format_checker=FormatChecker(),
        ),
        "mandate": Draft202012Validator(
            load(SCHEMAS / "commercial-mandate.schema.json"),
            registry=registry,
            format_checker=FormatChecker(),
        ),
        "grade": Draft202012Validator(
            load(SCHEMAS / "conformance-grade.schema.json"),
            registry=registry,
            format_checker=FormatChecker(),
        ),
    }

    print(f"profiles registered: {', '.join(sorted(profiles)) or 'none'}")
    print(f"settlement rails registered: {', '.join(sorted(REGISTERED_SETTLEMENT_RAILS))}")
    passed = failed = 0

    for expected_valid, entries in (
        (True, manifest["positive"]),
        (False, manifest["negative"]),
    ):
        for entry in entries:
            path = FIXTURES / entry["fixture"]
            doc = load(path)
            kind = entry["kind"]
            if kind in validators:
                schema_errors = list(validators[kind].iter_errors(doc))
                rule_failures = normative_checks(doc, kind, profiles, registry)
            elif kind == "mandate_chain":
                schema_errors = []
                for part in ("parent", "child"):
                    schema_errors.extend(
                        validators["mandate"].iter_errors(doc.get(part, {}))
                    )
                rule_failures = delegation_checks(doc)
            elif kind == "declaration":
                schema_errors = []
                rule_failures = declaration_checks(doc)
            elif kind == "bundle":
                schema_errors, rule_failures = bundle_errors(
                    doc, profiles, registry, validators["kernel"]
                )
            else:
                schema_errors = []
                rule_failures = [f"A202-FIXTURE-KIND-UNKNOWN:{kind}"]
            is_valid = not schema_errors and not rule_failures

            # A negative fixture must be refused for its declared reason, not
            # for an incidental one. Where the normative layer raised any code
            # at all, the declared code must be among them; a fixture the
            # schema alone refuses is legitimate, because the declared code
            # names what an implementation must return and the static schema
            # layer reports shape errors rather than reason codes.
            #
            # A negative entry that declares no code at all is declaring the
            # case section 5.4 of bindings/a2a-binding-v0.1.md describes: the
            # refusal is a kernel validation refusal and no code is defined for
            # it, because the closed envelope and payload shapes are the rule.
            # The runner asserts that the schema layer did refuse it, so that a
            # missing declaration cannot silently cover a fixture nothing
            # refuses at all.
            declared = entry.get("reason_code")
            reason_ok = True
            if not expected_valid and declared and rule_failures:
                reason_ok = declared in rule_failures
            if not expected_valid and not declared:
                reason_ok = bool(schema_errors)

            if is_valid == expected_valid and reason_ok:
                passed += 1
                status = "ok"
            else:
                failed += 1
                status = "FAIL"

            if args.verbose or status == "FAIL":
                caught = "schema" if schema_errors else ("normative" if rule_failures else "-")
                print(f"  [{status}] {entry['fixture']}  caught_by={caught}")
                if status == "FAIL":
                    if not reason_ok and declared:
                        print(f"          declared reason {declared} not among raised codes")
                    elif not reason_ok:
                        print("          entry declares no reason code and no schema error refused it")
                    for err in schema_errors[:2]:
                        print(f"          schema: {list(err.path)}: {err.message[:120]}")
                    for code in rule_failures:
                        print(f"          rule:   {code}")

    print(f"\n{passed} passed, {failed} failed "
          f"({len(manifest['positive'])} positive, {len(manifest['negative'])} negative)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
