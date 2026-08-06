"""Direct formation, obligation acts, and the party-held transaction record.

Everything here runs between two organisations. No object is authored,
ordered, or annotated by an operator, no session stream is created, and the
record is the hash-chained event sequence of section 8.1 of
pilot-transaction-state-machine-v0.1.md: each event names the content hash of
the event it follows, and the party that appended it signs it.

Nothing here records an act that was not authorized. Every recording function
requires the decision a prior verify_mandate call produced, checks that the
decision covers this exact act under a mandate this party holds, and writes
that decision into the record as the policy decision the event cites. The
decision recorded is the one that was made: its value, its reason codes, and
the mandate it evaluated. A decision this package manufactured would be an
attestation that a check happened when none did, which is worse than no
decision at all, because a verifier reading the record cannot tell the two
apart.

Every object is additionally checked against the published schema and the
published cross-object rules before it enters the record, so a refused act
leaves no trace of having been recorded.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from a202_reference.canonical import content_hash
from a202_reference.emission import make_object, new_id
from a202_reference.signing import sign_object

from . import gate
from .authority import Refused, act_document, action_hash_of, rederive_decision

DRAFT = "draft"

DECISION_FRESHNESS_SECONDS = 60
"""How old a presented decision may be when it is acted on.

The bound is the mandate document's own cache bound on revocation status, for
the same reason: a decision made against a status that may since have changed
is a decision about a mandate that may since have been revoked, and section
6.1 of commercial-mandate-v0.1.md requires the mandate to be active at append
time and not only at proposal time.
"""


class ActRefused(Refused):
    """An act was refused, and nothing about it entered the record."""


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value) -> datetime:
    if not isinstance(value, str):
        raise ValueError("not an RFC 3339 instant")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def new_session_id() -> str:
    """A session identifier minted by the offeror on its own offer.

    The identifier prefix table registers object types, and a session is not
    a shared object, so this is minted in the form the kernel schema's session
    identifier states rather than through the object emitter. Bilaterally
    there is no session stream: the counterparty adopts this identifier as it
    adopts the offer's other bytes, and nothing orders it.
    """
    return "ses_" + secrets.token_hex(12)


def _actor(party: dict, mandate_id: str) -> dict:
    return {
        "organization_id": party["organization_id"],
        "agent_id": party["agent_id"],
        "mandate_id": mandate_id,
    }


def _party(party: dict) -> dict:
    return {
        "organization_id": party["organization_id"],
        "agent_id": party["agent_id"],
    }


def _admit(state, obj: dict, extra: list | None = None) -> dict:
    """Check one object against both layers and record it, or refuse it."""
    context = gate.object_context(
        list(state.objects_for(obj["transaction_id"])) + list(extra or [])
    )
    codes, errors = gate.kernel_refusals(obj, context)
    if codes:
        raise ActRefused(codes, errors)
    state.put_object(obj)
    return obj


def _sign_in(state, obj: dict, key_id: str, purpose: str) -> None:
    obj["signatures"].append(
        sign_object(obj, state.signing_key(key_id), key_id, purpose)
    )
    actor = obj.get("created_by", {})
    if actor.get("agent_id") and obj.get("object_type") != "approval":
        # The key signed as an agent on this transaction, which is what stops
        # it being presented later as an approving principal's key.
        state.record_agent_key(obj.get("transaction_id"), key_id)


def current_state(state, transaction_id: str) -> str:
    """The aggregate state the record reaches, or `draft` for an empty one."""
    last = state.last_event(transaction_id)
    return last["payload"]["to_state"] if last else DRAFT


# --- authorization ------------------------------------------------------------

def check_decision(state, decision, party: dict, document: dict) -> dict:
    """Refuse unless this act is authorized, and unless the presented decision
    is the decision the mandate produces for it.

    The decision is the result of a prior verify_mandate call. Five things
    place it, and each refuses with the code that names it: the decision
    exists and claims an allow, it was made over these exact act bytes, it
    evaluated a mandate this party holds, that mandate's subject is the acting
    agent, and it is recent enough that the mandate status it rested on still
    stands.

    None of those five establishes that the verdict is true. The presented
    decision is an unsigned document written by the party the mandate
    constrains, so the verdict is recomputed here from the mandate and the act
    and the two are compared. What the presented decision is still needed for
    is what it alone carries: which approval released a hold, and the reasons
    the acting party recorded.
    """
    expected = action_hash_of(document)
    if not isinstance(decision, dict):
        raise ActRefused(
            ["A202-POLICY-DENIED"],
            "no verify_mandate decision was presented for this act; call "
            f"verify_mandate with proposed_action {document}",
        )

    value = decision.get("decision")
    if value != "allow":
        code = (
            "A202-APPROVAL-REQUIRED"
            if value == "require_approval"
            else "A202-POLICY-DENIED"
        )
        raise ActRefused(
            [code],
            f"the presented decision is {value!r}, and only an allow is recorded",
        )

    if decision.get("action_hash") != expected:
        raise ActRefused(
            ["A202-APPROVAL-HASH-MISMATCH"],
            "the presented decision was made over a different act; call "
            f"verify_mandate with proposed_action {document}",
        )

    mandate_id = decision.get("mandate_id")
    if mandate_id != party.get("mandate_id"):
        raise ActRefused(
            ["A202-POLICY-DENIED"],
            f"the presented decision evaluated {mandate_id!r} and the acting "
            f"party cites {party.get('mandate_id')!r}",
        )

    mandate = state.get_mandate(mandate_id)
    if mandate is None:
        raise ActRefused(
            ["A202-POLICY-DENIED"],
            f"no mandate is held under {mandate_id!r}, so nothing was evaluated",
        )
    subject = mandate.get("subject", {})
    if (
        subject.get("agent_id") != party.get("agent_id")
        or mandate.get("represented_organization_id") != party.get("organization_id")
    ):
        raise ActRefused(
            ["A202-POLICY-DENIED"],
            "the mandate the decision evaluated does not name the acting agent",
        )

    try:
        made_at = _parse(decision.get("checked_at"))
    except ValueError:
        raise ActRefused(["A202-MANDATE-STATUS-UNRESOLVED"],
                         "the presented decision states no time it was made")
    if abs(_now() - made_at) > timedelta(seconds=DECISION_FRESHNESS_SECONDS):
        raise ActRefused(
            ["A202-MANDATE-STATUS-UNRESOLVED"],
            "the presented decision is older than the status cache bound; the "
            "mandate may have been revoked since it was made",
        )

    # Everything above establishes which act and which mandate the decision
    # claims to be about. None of it establishes that the verdict is the one
    # that mandate produces, and the party presenting it is the party the
    # mandate constrains. So the verdict is derived again here, and a
    # presented decision that disagrees with it is refused rather than
    # recorded.
    rederived = rederive_decision(state, mandate, document, decision)
    if rederived["decision"] != "allow":
        raise ActRefused(
            rederived["reason_codes"] or ["A202-POLICY-DENIED"],
            f"this mandate answers {rederived['decision']} for this act, and the "
            "decision presented claims an allow",
        )
    if set(rederived["reason_codes"]) != set(decision.get("reason_codes") or []):
        raise ActRefused(
            ["A202-POLICY-DENIED"],
            "the presented decision states reasons this evaluation does not: "
            f"{sorted(set(decision.get('reason_codes') or []))} against "
            f"{sorted(set(rederived['reason_codes']))}",
        )
    if rederived["mandate_id"] != decision.get("mandate_id"):
        raise ActRefused(
            ["A202-POLICY-DENIED"],
            "the decision names a mandate other than the one that was evaluated",
        )
    return decision


def _record_decision(state, decision: dict, actor: dict, transaction_id: str,
                     key_id: str, sequence: int) -> dict:
    """Write the decision that was made, as the object the event will cite.

    Every member comes from the decision presented. Nothing here decides
    anything, and nothing here improves what was decided.

    One decision is written once. A party that verified an act and then
    appended two events under it cites the same decision from both, rather
    than leaving two objects a reader would have to notice are one decision
    recorded twice.
    """
    for held in state.objects_for(transaction_id):
        if held.get("object_type") != "policy_decision":
            continue
        payload = held["payload"]
        if (
            payload.get("action_hash") == decision["action_hash"]
            and payload.get("mandate_ids") == [decision["mandate_id"]]
            and payload.get("evaluated_at") == decision["checked_at"]
        ):
            return held

    obj = make_object(
        "policy_decision",
        {
            "action_hash": decision["action_hash"],
            "decision": decision["decision"],
            "reason_codes": list(decision.get("reason_codes") or []),
            "evaluated_at": decision["checked_at"],
            "mandate_ids": [decision["mandate_id"]],
            "stream": {"kind": "transaction", "id": transaction_id},
            "stream_sequence": sequence,
            "visibility": "transaction_parties",
        },
        actor,
        transaction_id,
    )
    _sign_in(state, obj, key_id, "policy_decision")
    return _admit(state, obj)


def _append_event(
    state,
    transaction_id: str,
    event_type: str,
    to_state: str,
    data: dict,
    decision: dict,
    actor: dict,
    actor_key_id: str,
    counter_key_id: str,
    rules_version: str,
) -> dict:
    """Append one event to the party-held transaction record.

    The transition is checked against the rule set version in force before the
    event is written, using the same registry a verifier replays against, so a
    transition this package appends is a transition a replay accepts. The
    event cites the decision object written from the decision the caller
    presented, and carries that decision's action hash.

    Both parties' keys sign the event, which is the shape of the
    countersignature section 8.1 describes. One process holds both keys, so
    what this demonstrates is the shape and not the property: it does not
    establish that two organisations independently held the keys or
    independently kept the record.
    """
    from_state = current_state(state, transaction_id)
    rules = gate.resolve_rules(gate.rules_ref(rules_version))
    if (from_state, event_type, to_state) not in rules["transitions"]:
        raise ActRefused(["A202-STATE-TRANSITION-DENIED"],
                         f"{from_state} to {to_state} on {event_type}")

    previous = state.last_event(transaction_id)
    sequence = previous["payload"]["sequence"] + 1 if previous else 1
    recorded = _record_decision(
        state, decision, actor, transaction_id, actor_key_id, sequence
    )

    event = make_object(
        "transaction_event",
        {
            "stream": {"kind": "transaction", "id": transaction_id},
            "sequence": sequence,
            "event_type": event_type,
            "occurred_at": _stamp(),
            "previous_event_hash": previous["content_hash"] if previous else None,
            "action_hash": decision["action_hash"],
            "policy_decision_id": recorded["id"],
            "from_state": from_state,
            "to_state": to_state,
            "data": data,
        },
        actor,
        transaction_id,
    )
    _sign_in(state, event, actor_key_id, "event_append")
    _sign_in(state, event, counter_key_id, "event_append")
    return _admit(state, event)


# --- the acts -----------------------------------------------------------------

def formation_acts(
    transaction_id: str,
    buyer: dict,
    supplier: dict,
    terms: dict,
    offeror_role: str = "supplier",
) -> dict:
    """The two act documents a direct formation is evaluated as.

    The offeror submits and the offeree accepts. Each party's own act names
    the other as counterparty, so neither decision covers the other's act.
    """
    parties = {"buyer": buyer, "supplier": supplier}
    offeror = parties[offeror_role]
    offeree = parties["buyer" if offeror_role == "supplier" else "supplier"]
    return {
        "offeror": offeror,
        "offeree": offeree,
        "offeror_act": act_document(
            "offer.submit", transaction_id, offeree["organization_id"], terms
        ),
        "offeree_act": act_document(
            "offer.accept", transaction_id, offeror["organization_id"], terms
        ),
    }


def create_agreement(
    state,
    transaction_id: str,
    buyer: dict,
    supplier: dict,
    terms: dict,
    offer_valid_until: str,
    buyer_decision: dict,
    supplier_decision: dict,
    offeror_role: str = "supplier",
    session_id: str | None = None,
    offer_evidence_refs: list | None = None,
    rules_version: str = gate.DIRECT_FORMATION_RULES_VERSION,
) -> dict:
    """Form an agreement between two parties with no venue.

    Both parties present the decision their own mandate produced for their own
    act: the offeror for `offer.submit`, the offeree for `offer.accept`. An
    act neither mandate allowed is refused here rather than recorded and
    attested to.

    The offeror mints the session identifier on its own offer, the offeree
    accepts over the exact offer hash, `agreement.direct` carries the
    transaction from `draft` to `agreement_pending`, and `agreement.committed`
    carries it to `committed` once both parties have signed the same agreement
    bytes. The two events are separate because acceptance of an offer does not
    establish the approval, the authority, or the dual signature that
    commitment requires.
    """
    if current_state(state, transaction_id) != DRAFT:
        raise ActRefused(["A202-STATE-TRANSITION-DENIED"],
                         "this transaction has already left draft")
    if offeror_role not in ("buyer", "supplier"):
        raise ActRefused(["A202-POLICY-DENIED"], "offeror_role is buyer or supplier")
    if terms.get("profile") not in gate.registered_profiles():
        raise ActRefused(["A202-PROFILE-UNKNOWN"],
                         f"registered profiles are {gate.registered_profiles()}")

    acts = formation_acts(transaction_id, buyer, supplier, terms, offeror_role)
    offeror, offeree = acts["offeror"], acts["offeree"]
    decisions = {
        "buyer": buyer_decision,
        "supplier": supplier_decision,
    }
    offeror_decision = decisions[offeror_role]
    offeree_decision = decisions["buyer" if offeror_role == "supplier" else "supplier"]
    check_decision(state, offeror_decision, offeror, acts["offeror_act"])
    check_decision(state, offeree_decision, offeree, acts["offeree_act"])
    buyer_act_decision = decisions["buyer"]

    session = session_id or new_session_id()

    offer = make_object(
        "offer",
        {
            "offeror": _party(offeror),
            "offeree": _party(offeree),
            "session_id": session,
            "supersedes_offer_id": None,
            "valid_until": offer_valid_until,
            "terms": terms,
            "evidence_refs": list(offer_evidence_refs or []),
        },
        _actor(offeror, offeror["mandate_id"]),
        transaction_id,
    )
    _sign_in(state, offer, offeror["key_id"], "offer_submission")
    _admit(state, offer)
    # The offeror's own decision is written into the record too. It authorizes
    # the offer, which is an act with no event of its own, and a record that
    # held the offer but not the decision behind it would leave a verifier
    # unable to resolve who allowed it.
    _record_decision(
        state,
        offeror_decision,
        _actor(offeror, offeror["mandate_id"]),
        transaction_id,
        offeror["key_id"],
        0,
    )

    acceptance = make_object(
        "acceptance",
        {
            "offer_id": offer["id"],
            "offer_hash": offer["content_hash"],
            "session_id": session,
            "accepting_party": _party(offeree),
        },
        _actor(offeree, offeree["mandate_id"]),
        transaction_id,
    )
    _sign_in(state, acceptance, offeree["key_id"], "offer_acceptance")
    _admit(state, acceptance)

    _append_event(
        state,
        transaction_id,
        "agreement.direct",
        "agreement_pending",
        {
            "offer_id": offer["id"],
            "acceptance_id": acceptance["id"],
            "session_id": session,
        },
        offeree_decision,
        _actor(offeree, offeree["mandate_id"]),
        offeree["key_id"],
        offeror["key_id"],
        rules_version,
    )

    commitment_id = new_id("commitment")
    agreement = make_object(
        "agreement",
        {
            "accepted_offer_id": offer["id"],
            "accepted_offer_hash": offer["content_hash"],
            "acceptance_id": acceptance["id"],
            "buyer": _party(buyer),
            "supplier": _party(supplier),
            "terms": terms,
            "terms_hash": content_hash(terms),
            "effective_at": _stamp(),
            "commitment_ids": [commitment_id],
        },
        _actor(buyer, buyer["mandate_id"]),
        transaction_id,
    )
    # An agreement exists only when both parties have signed the same
    # canonical bytes. Neither signature covers the signatures array, so the
    # second never invalidates the first.
    _sign_in(state, agreement, buyer["key_id"], "agreement_commitment")
    _sign_in(state, agreement, supplier["key_id"], "agreement_commitment")
    _admit(state, agreement)

    commitment = make_object(
        "commitment",
        {
            "agreement_id": agreement["id"],
            "committed_party": _party(supplier),
            "subject": {
                "agreement_id": agreement["id"],
                "terms_hash": agreement["payload"]["terms_hash"],
                "profile": terms["profile"],
                "term_path": "$.terms.core.quantity",
            },
        },
        _actor(supplier, supplier["mandate_id"]),
        transaction_id,
    )
    _sign_in(state, commitment, supplier["key_id"], "object_issuance")
    _admit(state, commitment)

    _append_event(
        state,
        transaction_id,
        "agreement.committed",
        "committed",
        {"agreement_id": agreement["id"], "commitment_id": commitment["id"]},
        buyer_act_decision,
        _actor(buyer, buyer["mandate_id"]),
        buyer["key_id"],
        supplier["key_id"],
        rules_version,
    )

    return {
        "transaction_id": transaction_id,
        "session_id": session,
        "offer": offer,
        "acceptance": acceptance,
        "agreement": agreement,
        "commitment": commitment,
        "state": current_state(state, transaction_id),
        "rules_version": rules_version,
    }


def obligation_act(
    agreement_id: str,
    transaction_id: str,
    obligor: dict,
    obligee: dict,
    quantity: str,
    unit_code: str,
    consideration: dict | None,
) -> dict:
    """The act document an obligation issue is evaluated as."""
    return act_document(
        "obligation.activated",
        transaction_id,
        obligor["organization_id"],
        _core_terms(quantity, unit_code, consideration),
        {"agreement_id": agreement_id},
    )


def issue_obligation(
    state,
    agreement_id: str,
    obligor: dict,
    obligee: dict,
    term_path: str,
    quantity: str,
    unit_code: str,
    due_condition: dict,
    decision: dict,
    consideration: dict | None = None,
    commitment_id: str | None = None,
    rules_version: str = gate.DIRECT_FORMATION_RULES_VERSION,
) -> dict:
    """Derive one obligation from a committed agreement and activate it.

    The obligee acts, and presents the decision its own mandate produced for
    this act. The subject names the owed term by pointing at the agreement's
    terms and carrying their hash; it never restates them, because a restated
    term can drift from the agreement while both copies stay validly signed.
    """
    agreement = state.get_object(agreement_id)
    if agreement is None or agreement.get("object_type") != "agreement":
        raise ActRefused(["A202-OBLIGATION-SUBJECT-UNREFERENCED"],
                         f"no agreement is held under {agreement_id!r}")
    transaction_id = agreement["transaction_id"]
    payload = agreement["payload"]

    check_decision(
        state,
        decision,
        obligee,
        obligation_act(agreement_id, transaction_id, obligor, obligee,
                       quantity, unit_code, consideration),
    )

    obligation = make_object(
        "obligation",
        {
            "agreement_id": agreement_id,
            "commitment_id": commitment_id or payload["commitment_ids"][0],
            "obligor": _party(obligor),
            "obligee": _party(obligee),
            "subject": {
                "agreement_id": agreement_id,
                "terms_hash": payload["terms_hash"],
                "profile": payload["terms"]["profile"],
                "term_path": term_path,
            },
            "due_condition": due_condition,
            "quantity": quantity,
            "unit_code": unit_code,
            "consideration": consideration,
            "state": "pending",
        },
        _actor(obligee, obligee["mandate_id"]),
        transaction_id,
    )
    _sign_in(state, obligation, obligee["key_id"], "object_issuance")
    _admit(state, obligation)

    _append_event(
        state,
        transaction_id,
        "obligation.activated",
        "in_performance",
        {"obligation_id": obligation["id"]},
        decision,
        _actor(obligee, obligee["mandate_id"]),
        obligee["key_id"],
        obligor["key_id"],
        rules_version,
    )
    return {"obligation": obligation, "state": current_state(state, transaction_id)}


def _core_terms(quantity: str, unit_code: str, consideration: dict | None) -> dict:
    """The proposed terms an obligation act carries.

    The money at stake travels with every act, so a mandate's amount ceiling
    binds asserting and accepting as well as issuing. An act that carried no
    amount would slip past a ceiling that is expressed over one.
    """
    core = {"quantity": quantity, "unit_code": unit_code}
    if consideration is not None:
        core["total"] = consideration
    return {"core": core}


def assertion_act(
    obligation_id: str,
    transaction_id: str,
    obligee: dict,
    asserted_quantity: str,
    unit_code: str,
    consideration: dict | None = None,
) -> dict:
    """The act document a performance assertion is evaluated as."""
    return act_document(
        "performance.declared",
        transaction_id,
        obligee["organization_id"],
        _core_terms(asserted_quantity, unit_code, consideration),
        {"obligation_id": obligation_id},
    )


def assert_performance(
    state,
    obligation_id: str,
    obligor: dict,
    obligee: dict,
    asserted_quantity: str,
    evidence: list,
    decision: dict,
    rules_version: str = gate.DIRECT_FORMATION_RULES_VERSION,
) -> dict:
    """The obligor asserts performance, with evidence.

    An assertion carries a claim about the world, and a claim with nothing
    behind it cannot be checked by the obligee now or by anyone later, so an
    assertion with no evidence is refused before any object is written.
    """
    obligation = state.get_object(obligation_id)
    if obligation is None or obligation.get("object_type") != "obligation":
        raise ActRefused(["A202-OBLIGATION-SUBJECT-UNREFERENCED"],
                         f"no obligation is held under {obligation_id!r}")
    if not evidence:
        raise ActRefused(["A202-OBLIGATION-ASSERTION-UNEVIDENCED"],
                         "an assertion carries at least one evidence reference")
    transaction_id = obligation["transaction_id"]
    unit_code = obligation["payload"]["unit_code"]

    check_decision(
        state,
        decision,
        obligor,
        assertion_act(obligation_id, transaction_id, obligee, asserted_quantity,
                      unit_code, obligation["payload"].get("consideration")),
    )

    refs = []
    written = []
    for item in evidence:
        obj = make_object("evidence", dict(item), _actor(obligor, obligor["mandate_id"]),
                          transaction_id)
        _sign_in(state, obj, obligor["key_id"], "object_issuance")
        _admit(state, obj)
        written.append(obj)
        refs.append(
            {
                "evidence_id": obj["id"],
                "content_hash": obj["content_hash"],
                "evidence_type": obj["payload"]["evidence_type"],
                "signed_by": _party(obligor),
            }
        )

    assertion = make_object(
        "performance_event",
        {
            "obligation_id": obligation_id,
            "asserted_quantity": asserted_quantity,
            "unit_code": unit_code,
            "evidence_refs": refs,
        },
        _actor(obligor, obligor["mandate_id"]),
        transaction_id,
    )
    _sign_in(state, assertion, obligor["key_id"], "object_issuance")
    _admit(state, assertion)

    _append_event(
        state,
        transaction_id,
        "performance.declared",
        "acceptance_pending",
        {"obligation_id": obligation_id, "performance_event_id": assertion["id"]},
        decision,
        _actor(obligor, obligor["mandate_id"]),
        obligor["key_id"],
        obligee["key_id"],
        rules_version,
    )
    return {
        "assertion": assertion,
        "evidence": written,
        "state": current_state(state, transaction_id),
    }


def response_act(
    assertion_id: str,
    transaction_id: str,
    counterparty: dict,
    response_type: str,
    accepted_quantity: str,
    unit_code: str,
    consideration: dict | None = None,
) -> dict:
    """The act document a response to an assertion is evaluated as.

    The quantity is the one being accepted, which defaults to the quantity
    asserted. Accepting performance is agreeing that what is owed was owed, so
    the money travels with it and the mandate's ceiling reaches it.
    """
    return act_document(
        "acceptance.granted" if response_type == "accept" else "acceptance.rejected",
        transaction_id,
        counterparty["organization_id"],
        _core_terms(accepted_quantity, unit_code, consideration),
        {"assertion_id": assertion_id},
    )


def respond_to_assertion(
    state,
    assertion_id: str,
    responder: dict,
    counterparty: dict,
    response_type: str,
    decision: dict,
    accepted_quantity: str | None = None,
    reason_code: str | None = None,
    remainder_obligation_id: str | None = None,
    rules_version: str = gate.DIRECT_FORMATION_RULES_VERSION,
) -> dict:
    """The obligee responds to one assertion, binding its exact bytes.

    Acceptance is a distinct signed act by the obligee. A response signed by
    any other party is refused, and the response binds the assertion hash, so
    changing one byte of the assertion invalidates the response.
    """
    assertion = state.get_object(assertion_id)
    if assertion is None or assertion.get("object_type") != "performance_event":
        raise ActRefused(["A202-OBLIGATION-RESPONSE-HASH-MISMATCH"],
                         f"no assertion is held under {assertion_id!r}")
    if response_type not in ("accept", "reject"):
        raise ActRefused(["A202-STATE-TRANSITION-DENIED"],
                         "response_type is accept or reject")
    transaction_id = assertion["transaction_id"]
    obligation_id = assertion["payload"]["obligation_id"]
    obligation = state.get_object(obligation_id) or {"payload": {}}
    effective_quantity = accepted_quantity or assertion["payload"]["asserted_quantity"]

    check_decision(
        state,
        decision,
        responder,
        response_act(
            assertion_id,
            transaction_id,
            counterparty,
            response_type,
            effective_quantity,
            assertion["payload"]["unit_code"],
            obligation["payload"].get("consideration"),
        ),
    )

    payload = {
        "obligation_id": obligation_id,
        "response_type": response_type,
    }
    payload["assertion_id"] = assertion_id
    payload["assertion_hash"] = assertion["content_hash"]
    if response_type == "accept":
        payload["accepted_quantity"] = effective_quantity
        if remainder_obligation_id:
            payload["remainder_obligation_id"] = remainder_obligation_id
    if response_type == "reject":
        payload["reason_code"] = reason_code

    response = make_object(
        "obligation_response",
        payload,
        _actor(responder, responder["mandate_id"]),
        transaction_id,
    )
    _sign_in(state, response, responder["key_id"], "object_issuance")
    _admit(state, response)

    event_type, to_state = (
        ("acceptance.granted", "settlement_pending")
        if response_type == "accept"
        else ("acceptance.rejected", "in_performance")
    )
    _append_event(
        state,
        transaction_id,
        event_type,
        to_state,
        {"obligation_id": obligation_id, "obligation_response_id": response["id"]},
        decision,
        _actor(responder, responder["mandate_id"]),
        responder["key_id"],
        counterparty["key_id"],
        rules_version,
    )
    return {"response": response, "state": current_state(state, transaction_id)}


def transaction_record(state, transaction_id: str) -> dict:
    """The party-held record: the event chain, its links, and where it stands.

    The chain is checked here rather than asserted. A record whose links do
    not form one chain from the first event is reported with the code a
    verifier would raise on the same record, because a break in the chain is a
    fact about the record and not a presentation detail.
    """
    events = state.events_for(transaction_id)
    entries = []
    breaks = []
    expected_previous = None
    for event in events:
        payload = event["payload"]
        linked = payload.get("previous_event_hash") == expected_previous
        if not linked:
            breaks.append(event["id"])
        entries.append(
            {
                "event_id": event["id"],
                "sequence": payload["sequence"],
                "event_type": payload["event_type"],
                "from_state": payload["from_state"],
                "to_state": payload["to_state"],
                "occurred_at": payload["occurred_at"],
                "previous_event_hash": payload.get("previous_event_hash"),
                "content_hash": event["content_hash"],
                "signed_by": [entry["key_id"] for entry in event["signatures"]],
                "policy_decision_id": payload["policy_decision_id"],
                "action_hash": payload["action_hash"],
                "data": payload["data"],
            }
        )
        expected_previous = event["content_hash"]

    return {
        "transaction_id": transaction_id,
        "state": current_state(state, transaction_id),
        "events": entries,
        "chain": "linked" if not breaks else "broken",
        "chain_refusal": None if not breaks else "A202-EVIDENCE-CHAIN-GAP",
        "unlinked_events": breaks,
        "objects": sorted(
            obj["id"] for obj in state.objects_for(transaction_id)
        ),
    }
