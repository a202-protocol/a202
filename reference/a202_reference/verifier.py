"""The seven-step verification procedure of evidence-verification-v0.1.md.

Executed over the set of objects the caller holds, with no operator access.
Every check produces one of three results, verified, failed, or
not_checkable, and the report never collapses them: there is deliberately no
overall boolean anywhere on the report type. A failing step does not stop
the run, so the report states everything that is wrong rather than the first
thing.

The caller supplies what a real verifier holds: the bundle, optionally a map
of key identifiers to public keys, and optionally a rules resolver. A rules
reference that does not resolve yields not_checkable for everything read
from it, never verified, because unavailability is not permission in either
direction.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .canonical import content_hash
from .signing import EXPECTED_PURPOSES, MINIMUM_SIGNATURES, verify_signature

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

EFFECT_ORDER = {"advisory": 0, "presumptive": 1, "binding": 2}


@dataclass
class Check:
    """One executed or attempted check. result is verified, failed, or
    not_checkable, and a refusal code accompanies failed results only: a
    check that could not be executed produces no code, per section 8."""

    step: int
    name: str
    subject: str
    result: str
    code: str | None = None
    detail: str = ""


@dataclass
class VerificationReport:
    """Per-check results plus the stated scope. No overall boolean exists on
    this type, and none should be added: a report reduced to a boolean
    discards the not_checkable set, which is the refusal
    A202-EVIDENCE-REPORT-INVALID."""

    checks: list[Check] = field(default_factory=list)
    objects_in_scope: list[str] = field(default_factory=list)
    streams_disclosed: list[str] = field(default_factory=list)
    undisclosed_streams: list[str] = field(default_factory=list)
    unresolved_references: list[str] = field(default_factory=list)
    unreferenced_evidence: list[str] = field(default_factory=list)

    def results(self) -> dict[str, int]:
        counts = {"verified": 0, "failed": 0, "not_checkable": 0}
        for check in self.checks:
            counts[check.result] += 1
        return counts


def _payload(obj: dict) -> dict:
    payload = obj.get("payload")
    return payload if isinstance(payload, dict) else {}


def _stream_key(obj: dict) -> str:
    """One key per stream, from the stream's own identifier. Two session
    streams on one transaction are two streams: keying them by transaction
    would merge rival sessions and make the verifier expect continuity across
    a boundary the specification forbids it to look across."""
    stream = _payload(obj).get("stream", {})
    return f"{stream.get('kind', 'unknown')}:{stream.get('id', obj.get('transaction_id'))}"


def _collect_evidence_refs(payload) -> list:
    refs = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in ("evidence_refs", "assurance_evidence_refs", "evidence_relied_on"):
                if isinstance(value, list):
                    refs.extend(value)
            else:
                refs.extend(_collect_evidence_refs(value))
    elif isinstance(payload, list):
        for item in payload:
            refs.extend(_collect_evidence_refs(item))
    return refs


def verify_bundle(
    objects: list[dict],
    keys: dict | None = None,
    rules_resolver=None,
) -> VerificationReport:
    """Execute steps 1 to 7 over the objects the caller holds.

    keys maps a key_id to a cryptography EC public key; an absent entry is
    an unresolvable key status. rules_resolver maps a rules reference dict
    to a rule set description carrying rules identifiers, a transitions set
    of (from_state, event_type, to_state) triples, and effect_grants by
    question class; None, or a resolver returning None, is an unresolvable
    rule set version.
    """
    keys = keys or {}
    report = VerificationReport()
    by_id = {obj.get("id"): obj for obj in objects if obj.get("id")}
    by_hash = {}
    report.objects_in_scope = sorted(by_id)

    # Step 1: canonicalise and check content hashes, including every hash
    # the bundle asserts between objects it holds.
    for obj in objects:
        oid = obj.get("id", "?")
        declared = obj.get("content_hash")
        if not declared:
            report.checks.append(Check(1, "content_hash_present", oid, "failed",
                                       "A202-EVIDENCE-HASH-MISMATCH", "no declared hash"))
            continue
        recomputed = content_hash(obj)
        if recomputed == declared:
            report.checks.append(Check(1, "content_hash", oid, "verified"))
        else:
            report.checks.append(Check(1, "content_hash", oid, "failed",
                                       "A202-EVIDENCE-HASH-MISMATCH",
                                       f"declared {declared[:12]} recomputed {recomputed[:12]}"))
        by_hash[declared] = obj

    for obj in objects:
        oid = obj.get("id", "?")
        payload = _payload(obj)
        if obj.get("object_type") == "agreement":
            terms = payload.get("terms")
            if isinstance(terms, dict):
                if payload.get("terms_hash") == content_hash(terms):
                    report.checks.append(Check(1, "terms_hash", oid, "verified"))
                else:
                    report.checks.append(Check(1, "terms_hash", oid, "failed",
                                               "A202-AGREEMENT-HASH-MISMATCH",
                                               "terms_hash is not the hash of the terms"))
            offer = by_id.get(payload.get("accepted_offer_id"))
            if offer is not None:
                if payload.get("accepted_offer_hash") == offer.get("content_hash"):
                    report.checks.append(Check(1, "accepted_offer_hash", oid, "verified"))
                else:
                    report.checks.append(Check(1, "accepted_offer_hash", oid, "failed",
                                               "A202-AGREEMENT-HASH-MISMATCH"))
            elif payload.get("accepted_offer_id"):
                report.checks.append(Check(1, "accepted_offer_hash", oid, "not_checkable",
                                           detail=f"{payload.get('accepted_offer_id')} not in bundle"))
                report.unresolved_references.append(str(payload.get("accepted_offer_id")))
        if obj.get("object_type") == "acceptance":
            offer = by_id.get(payload.get("offer_id"))
            if offer is not None:
                if payload.get("offer_hash") == offer.get("content_hash"):
                    report.checks.append(Check(1, "offer_hash_binding", oid, "verified"))
                else:
                    report.checks.append(Check(1, "offer_hash_binding", oid, "failed",
                                               "A202-AGREEMENT-HASH-MISMATCH"))
            elif payload.get("offer_id"):
                report.checks.append(Check(1, "offer_hash_binding", oid, "not_checkable",
                                           detail=f"{payload.get('offer_id')} not in bundle"))
                report.unresolved_references.append(str(payload.get("offer_id")))
        if obj.get("object_type") == "obligation_response":
            assertion_id = payload.get("assertion_id")
            assertion = by_id.get(assertion_id) if assertion_id else None
            if assertion is not None:
                if payload.get("assertion_hash") == assertion.get("content_hash"):
                    report.checks.append(Check(1, "assertion_hash_binding", oid, "verified"))
                else:
                    report.checks.append(Check(1, "assertion_hash_binding", oid, "failed",
                                               "A202-EVIDENCE-HASH-MISMATCH"))
            elif assertion_id:
                report.checks.append(Check(1, "assertion_hash_binding", oid, "not_checkable",
                                           detail=f"{assertion_id} not in bundle"))
                report.unresolved_references.append(assertion_id)
        if obj.get("object_type") == "determination":
            dispute = by_id.get(payload.get("dispute_id"))
            question = payload.get("question", {})
            if dispute is not None:
                if question.get("subject_hash") == _payload(dispute).get("subject_hash"):
                    report.checks.append(Check(1, "question_matches_dispute", oid, "verified"))
                else:
                    report.checks.append(Check(1, "question_matches_dispute", oid, "failed",
                                               "A202-DISPUTE-SUBJECT-UNREFERENCED"))

    # Step 2: verify every signature against declared key and purpose, and
    # check the minimum signature counts.
    for obj in objects:
        oid = obj.get("id", "?")
        object_type = obj.get("object_type", "")
        expected = EXPECTED_PURPOSES.get(object_type)
        signatures = obj.get("signatures", [])
        minimum = MINIMUM_SIGNATURES.get(object_type, 1)
        if len(signatures) < minimum:
            report.checks.append(Check(2, "signature_count", oid, "failed",
                                       "A202-EVIDENCE-SIGNATURE-INVALID",
                                       f"{len(signatures)} of {minimum} required"))
        for index, entry in enumerate(signatures):
            key = keys.get(entry.get("key_id"))
            result = verify_signature(obj, entry, key, expected)
            code = "A202-EVIDENCE-SIGNATURE-INVALID" if result == "failed" else None
            if result == "not_checkable" and entry.get("key_id") not in keys:
                report.unresolved_references.append(str(entry.get("key_id")))
            report.checks.append(Check(2, f"signature[{index}]", oid, result, code))

    # Step 3: version chains. A fork means two objects claim to be current.
    children: dict[str, list[dict]] = {}
    for obj in objects:
        previous = obj.get("previous_version_id")
        if previous:
            children.setdefault(previous, []).append(obj)
    for previous, successors in children.items():
        if len(successors) > 1:
            for successor in successors:
                report.checks.append(Check(3, "version_chain_fork", successor.get("id", "?"),
                                           "failed", "A202-EVIDENCE-CHAIN-GAP",
                                           f"two successors to {previous}"))
        else:
            successor = successors[0]
            parent = by_id.get(previous)
            if parent is None:
                report.checks.append(Check(3, "version_chain", successor.get("id", "?"),
                                           "not_checkable", detail=f"{previous} not in bundle"))
                report.unresolved_references.append(previous)
            elif successor.get("version", 0) != parent.get("version", 0) + 1:
                report.checks.append(Check(3, "version_chain", successor.get("id", "?"),
                                           "failed", "A202-EVIDENCE-CHAIN-GAP",
                                           "version does not increase by one"))
            else:
                report.checks.append(Check(3, "version_chain", successor.get("id", "?"),
                                           "verified"))

    # Determination supersession chains follow the same no-forks rule.
    superseded: dict[str, list[dict]] = {}
    for obj in objects:
        if obj.get("object_type") == "determination":
            supersedes = _payload(obj).get("supersedes")
            if isinstance(supersedes, dict):
                target = supersedes.get("determination_id", "?")
                superseded.setdefault(target, []).append(obj)
    for target, supersessors in superseded.items():
        if len(supersessors) > 1:
            for det in supersessors:
                report.checks.append(Check(3, "supersession_fork", det.get("id", "?"),
                                           "failed", "A202-EVIDENCE-CHAIN-GAP",
                                           f"two supersessions of {target}"))

    # Step 4: per-stream sequence continuity, within each disclosed stream
    # and only within it. A first event naming a predecessor the verifier
    # does not hold is a disclosed boundary, not a gap.
    streams: dict[str, list[dict]] = {}
    for obj in objects:
        if obj.get("object_type") == "transaction_event":
            streams.setdefault(_stream_key(obj), []).append(obj)
    report.streams_disclosed = sorted(streams)
    for stream_key, events in streams.items():
        events.sort(key=lambda event: _payload(event).get("sequence", 0))
        first = events[0]
        first_previous = _payload(first).get("previous_event_hash")
        if first_previous is not None and first_previous not in by_hash:
            report.checks.append(Check(4, "stream_boundary", stream_key, "not_checkable",
                                       detail="disclosed from mid stream; stated boundary"))
        for earlier, later in zip(events, events[1:]):
            earlier_payload, later_payload = _payload(earlier), _payload(later)
            if later_payload.get("sequence") != earlier_payload.get("sequence", 0) + 1:
                report.checks.append(Check(4, "sequence_continuity", stream_key, "failed",
                                           "A202-EVIDENCE-CHAIN-GAP",
                                           "sequence does not increase by one"))
            elif later_payload.get("previous_event_hash") != earlier.get("content_hash"):
                report.checks.append(Check(4, "event_chain", stream_key, "failed",
                                           "A202-EVIDENCE-CHAIN-GAP",
                                           "previous_event_hash does not match"))
            else:
                report.checks.append(Check(4, "event_chain", stream_key, "verified"))

    # Step 5: replay guarded transitions against the rules version in force
    # at the time the event appended, not the current one.
    for stream_key, events in streams.items():
        for event in events:
            payload = _payload(event)
            event_type = payload.get("event_type", "")
            triple = (payload.get("from_state"), event_type, payload.get("to_state"))
            rules = rules_resolver(payload.get("rules_ref")) if rules_resolver else None
            oid = event.get("id", "?")
            if rules is None:
                report.checks.append(Check(5, "transition_legality", oid, "not_checkable",
                                           detail="rules version in force did not resolve"))
                continue
            if triple in rules.get("transitions", set()):
                report.checks.append(Check(5, "transition_legality", oid, "verified"))
            else:
                report.checks.append(Check(5, "transition_legality", oid, "failed",
                                           "A202-EVIDENCE-TRANSITION-ILLEGAL",
                                           f"{triple[0]} to {triple[2]} on {event_type}"))

    # Step 6: every determination's outcome follows from its referenced
    # rules and inputs, and its effect does not exceed the grant.
    for obj in objects:
        if obj.get("object_type") != "determination":
            continue
        oid = obj.get("id", "?")
        payload = _payload(obj)
        question = payload.get("question", {})
        outcome = payload.get("outcome", {})
        rules = rules_resolver(question.get("rules_ref")) if rules_resolver else None
        if rules is None:
            report.checks.append(Check(6, "determination_rules", oid, "not_checkable",
                                       detail="rule set version did not resolve"))
            continue
        applied = outcome.get("rules_applied", [])
        if applied and all(rule in rules.get("rules", set()) for rule in applied):
            report.checks.append(Check(6, "rules_applied_resolve", oid, "verified"))
        else:
            report.checks.append(Check(6, "rules_applied_resolve", oid, "failed",
                                       "A202-DETERMINATION-NOT-FOLLOWING",
                                       "a named rule does not resolve in the rule set"))
        granted = rules.get("effect_grants", {}).get(question.get("subject_type"))
        claimed = payload.get("effect", "advisory")
        granted_rank = EFFECT_ORDER.get(granted, 0)
        if EFFECT_ORDER.get(claimed, 0) > granted_rank:
            report.checks.append(Check(6, "effect_within_grant", oid, "failed",
                                       "A202-DETERMINATION-EFFECT-OVERCLAIM",
                                       f"claimed {claimed}, granted {granted or 'none'}"))
        else:
            report.checks.append(Check(6, "effect_within_grant", oid, "verified"))

    # Step 7: report what could not be checked. None of this is a failure
    # and none of it is support for anything.
    referenced_evidence_ids = set()
    for obj in objects:
        for ref in _collect_evidence_refs(_payload(obj)):
            if isinstance(ref, str):
                evidence_id = ref
                evidence_type = None
            elif isinstance(ref, dict):
                evidence_id = ref.get("evidence_id", "?")
                evidence_type = ref.get("evidence_type")
            else:
                continue
            referenced_evidence_ids.add(evidence_id)
            if evidence_type is not None and evidence_type not in REGISTERED_EVIDENCE_TYPES:
                report.checks.append(Check(7, "evidence_type_registered", evidence_id,
                                           "failed", "A202-EVIDENCE-TYPE-UNKNOWN"))
            if evidence_id not in by_id:
                report.unresolved_references.append(evidence_id)
                report.checks.append(Check(7, "evidence_resolves", evidence_id,
                                           "not_checkable", detail="not in bundle"))
    report.unreferenced_evidence = sorted(
        obj["id"] for obj in objects
        if obj.get("object_type") == "evidence" and obj.get("id") not in referenced_evidence_ids
    )
    # A stream disclosed from mid-stream names a predecessor the verifier does
    # not hold. That is a stated boundary on a disclosed stream, reported at
    # step 4; the streams the bundle references but does not contain are the
    # session identifiers named by objects whose stream was never disclosed.
    for obj in objects:
        session_id = _payload(obj).get("session_id")
        if isinstance(session_id, str) and f"session:{session_id}" not in streams:
            if session_id not in report.undisclosed_streams:
                report.undisclosed_streams.append(session_id)
    report.undisclosed_streams.sort()

    report.unresolved_references = sorted(set(report.unresolved_references))
    return report
