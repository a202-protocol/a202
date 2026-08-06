"""The tool surface, as pure functions over one party's local state.

Seven tools, all inside the bilateral role scope `a202-scope/bilateral/0.1`:
nothing here creates a room, orders a stream, awards among rivals, or issues a
determination as a venue, and no object any tool emits is authored, ordered,
or annotated by an operator.

Each tool carries its own name, title, agent-facing description, JSON input
schema, behaviour annotations, and handler in one place, so the transport in
server.py declares the surface rather than restating it. The handlers import
nothing from the MCP SDK and are callable directly.

A refused act returns `{"outcome": "refused", "reason_codes": [...]}` rather
than raising, because a caller told only that something failed will retry it.
Verification returns per-check results and no overall boolean: a report
reduced to a boolean discards the not-checkable set, which is a refusal in its
own right.

Nothing in a return value carries private key material.
"""

from __future__ import annotations

from a202_reference.verifier import verify_bundle

from . import gate
from .authority import Refused, issue_approval, issue_mandate, verify_mandate
from .state import KeyUnavailable
from .transaction import (
    assert_performance,
    create_agreement,
    issue_obligation,
    respond_to_assertion,
    transaction_record,
)

ROLE_SCOPE = "a202-scope/bilateral/0.1"

SERVER_INSTRUCTIONS = """\
This server exposes the commercial capabilities that two organisations
exercise directly between themselves, with no marketplace, venue, or operator
in the middle. It signs objects, records them in a local hash-chained
transaction record, and verifies records a counterparty produced.

Nothing is recorded that was not first authorized. Every recording tool takes
the decision a prior verify_mandate call produced for that exact act, and
records it as the policy decision the event cites. There is no way to record
an act by asserting that a mandate permitted it: the decision itself is
presented, and the server refuses anything else.

The usual order is:

1. issue_mandate, once per acting agent. Every later call names the mandate an
   agent acts under.
2. verify_mandate for the act you intend to take. It answers allow, deny, or
   require_approval, and reports the hash of the exact act.
3. issue_approval only when step 2 answered require_approval. It binds the
   action hash step 2 reported. Call verify_mandate again with the approval
   and it answers allow.
4. create_agreement, once per transaction, passing the allow decision each
   party obtained for its own act: the offeror verified offer.submit and the
   offeree verified offer.accept.
5. record_obligation with act=issue, then act=assert, then act=respond, each
   passing the acting party's own allow decision for that act.
6. get_transaction_record at any point to see where the transaction stands.
7. verify_evidence to check a record, yours or a counterparty's, against the
   published verification procedure.

Where a decision does not match the act, the refusal states the exact
proposed_action to verify, so the next call is always available from the
refusal itself.

A refusal is a result, not a crash: it carries registered A202 reason codes and
means nothing was recorded. Money, percentages, and quantities are always
base-10 strings, never numbers.
"""

_PARTY_SCHEMA = {
    "type": "object",
    "description": "One acting party: its organisation, its agent, the mandate that agent acts under, and the key it signs with.",
    "required": ["organization_id", "agent_id", "mandate_id", "key_id"],
    "properties": {
        "organization_id": {"type": "string", "description": "Organisation identifier, prefixed org_."},
        "agent_id": {"type": "string", "description": "Agent identifier, prefixed agt_."},
        "mandate_id": {"type": "string", "description": "The mandate this agent acts under, prefixed mnd_, as returned by issue_mandate."},
        "key_id": {"type": "string", "description": "Signing key identifier, prefixed key_. Created on first use and held in memory only."},
    },
}

_TERMS_SCHEMA = {
    "type": "object",
    "description": "The commercial terms. core is identical for every transaction profile; profile_terms is validated against the schema the profile names.",
    "required": ["profile", "core", "profile_terms"],
    "properties": {
        "profile": {
            "type": "string",
            "description": "Registered transaction profile identifier, of the form a202-profile/<name>/<version>. An unregistered profile is refused with A202-PROFILE-UNKNOWN.",
        },
        "core": {
            "type": "object",
            "description": "Market-neutral terms, identical in shape for every profile.",
            "required": ["description", "quantity", "unit_code", "total"],
            "properties": {
                "description": {"type": "string", "description": "What is being bought, in plain words."},
                "quantity": {"type": "string", "description": "Base-10 string, never a number."},
                "unit_code": {"type": "string", "description": "UN/ECE Recommendation 20 common code, for example H87 for piece."},
                "unit_name": {"type": "string", "description": "Optional label. Carries no commercial meaning and is never used for matching."},
                "total": {
                    "type": "object",
                    "description": "The total consideration.",
                    "required": ["currency", "amount"],
                    "properties": {
                        "currency": {"type": "string", "description": "ISO 4217 three-letter code."},
                        "amount": {"type": "string", "description": "Base-10 string, never a number."},
                    },
                },
            },
        },
        "profile_terms": {
            "type": "object",
            "description": "Terms specific to the named profile. Validated against that profile's schema; anything it does not allow is refused with A202-PROFILE-TERMS-INVALID.",
        },
    },
}

_DECISION_SCHEMA = {
    "type": "object",
    "description": (
        "The result verify_mandate returned for this exact act, passed through "
        "unchanged. It must be an allow, made under this party's own mandate, "
        "over the act document this tool builds, and made within the last 60 "
        "seconds. Where it does not match, the refusal detail states the exact "
        "proposed_action to verify."
    ),
}

_PROPOSED_ACTION_SCHEMA = {
    "type": "object",
    "description": "The act to evaluate against the mandate. Constraint paths address this document from $, so a spending limit reads $.proposed_terms.core.total.amount.",
    "required": ["action_type"],
    "properties": {
        "action_type": {
            "type": "string",
            "description": "The act, for example offer.accept or agreement.sign. An act the mandate does not name is denied: actions are deny by default.",
        },
        "transaction_id": {"type": "string", "description": "The transaction the act belongs to, prefixed txn_."},
        "category": {"type": "string", "description": "The capability category, for example services.calibration."},
        "counterparty_organization_id": {"type": "string", "description": "The organisation on the other side of the act."},
        "geography": {"type": "string", "description": "Two-letter country code where the act performs."},
        "proposed_terms": {
            "type": "object",
            "description": "The terms being proposed, in the same shape as an agreement's terms. This is what commercial constraints read.",
        },
        "message": {
            "type": "object",
            "description": "Anything the act would disclose to the counterparty. Disclosure constraints read this.",
        },
    },
}


def _refused(codes: list[str], detail: str | None = None) -> dict:
    result = {"outcome": "refused", "reason_codes": codes}
    if detail:
        result["detail"] = detail
    return result


def _recorded_ids(result: dict) -> dict:
    recorded = {
        key: value["id"]
        for key, value in result.items()
        if isinstance(value, dict) and "id" in value
    }
    if "evidence" in result:
        recorded["evidence_ids"] = [obj["id"] for obj in result["evidence"]]
    return recorded


def handle_issue_mandate(state, **arguments) -> dict:
    """Issue a signed commercial mandate for an agent."""
    try:
        mandate = issue_mandate(state, **arguments)
    except Refused as refusal:
        return _refused(refusal.codes, refusal.detail)
    except KeyUnavailable as unavailable:
        return _refused(["A202-EVIDENCE-SIGNATURE-INVALID"], str(unavailable))
    except (TypeError, KeyError) as wrong:
        return _refused(["A202-POLICY-DENIED"], f"argument error: {wrong}")
    return {
        "outcome": "issued",
        "mandate_id": mandate["id"],
        "mandate": mandate,
        "role_scope": ROLE_SCOPE,
    }


def handle_verify_mandate(
    state, mandate=None, mandate_id=None, approval=None, approval_id=None, **arguments
) -> dict:
    """Check a presented mandate, and an act proposed under it."""
    document = mandate or state.get_mandate(mandate_id)
    if document is None:
        return _refused(
            ["A202-POLICY-DENIED"],
            "no mandate was presented and none is held under that identifier",
        )
    held = approval or (state.get_object(approval_id) if approval_id else None)
    if approval_id and held is None:
        return _refused(
            ["A202-APPROVAL-REQUIRED"], f"no approval is held under {approval_id}"
        )
    try:
        return verify_mandate(state, document, approval=held, **arguments)
    except (TypeError, KeyError) as wrong:
        return _refused(["A202-POLICY-DENIED"], f"argument error: {wrong}")


def handle_issue_approval(state, **arguments) -> dict:
    """Record a human approval bound to one exact action hash."""
    try:
        approval = issue_approval(state, **arguments)
    except Refused as refusal:
        return _refused(refusal.codes, refusal.detail)
    except KeyUnavailable as unavailable:
        return _refused(["A202-EVIDENCE-SIGNATURE-INVALID"], str(unavailable))
    except (TypeError, KeyError) as wrong:
        return _refused(["A202-APPROVAL-REQUIRED"], f"argument error: {wrong}")
    return {
        "outcome": "recorded",
        "approval_id": approval["id"],
        "action_hash": approval["payload"]["action_hash"],
        "expires_at": approval["payload"]["expires_at"],
        "decision": approval["payload"]["decision"],
    }


def handle_create_agreement(state, **arguments) -> dict:
    """Form an agreement directly between two parties, with no venue."""
    try:
        formed = create_agreement(state, **arguments)
    except Refused as refusal:
        return _refused(refusal.codes, refusal.detail)
    except KeyUnavailable as unavailable:
        return _refused(["A202-EVIDENCE-SIGNATURE-INVALID"], str(unavailable))
    except (TypeError, KeyError) as wrong:
        return _refused(["A202-POLICY-DENIED"], f"argument error: {wrong}")
    return {
        "outcome": "recorded",
        "transaction_id": formed["transaction_id"],
        "session_id": formed["session_id"],
        "offer_id": formed["offer"]["id"],
        "acceptance_id": formed["acceptance"]["id"],
        "agreement_id": formed["agreement"]["id"],
        "commitment_id": formed["commitment"]["id"],
        "terms_hash": formed["agreement"]["payload"]["terms_hash"],
        "state": formed["state"],
        "rules_version": formed["rules_version"],
    }


def handle_record_obligation(state, act=None, **arguments) -> dict:
    """Issue an obligation, assert performance, or answer an assertion."""
    handlers = {
        "issue": issue_obligation,
        "assert": assert_performance,
        "respond": respond_to_assertion,
    }
    if act not in handlers:
        return _refused(
            ["A202-STATE-TRANSITION-DENIED"], f"act must be one of {sorted(handlers)}"
        )
    try:
        result = handlers[act](state, **arguments)
    except Refused as refusal:
        return _refused(refusal.codes, refusal.detail)
    except KeyUnavailable as unavailable:
        return _refused(["A202-EVIDENCE-SIGNATURE-INVALID"], str(unavailable))
    except (TypeError, KeyError) as wrong:
        return _refused(["A202-POLICY-DENIED"], f"argument error: {wrong}")
    return {
        "outcome": "recorded",
        "act": act,
        "state": result["state"],
        **_recorded_ids(result),
    }


def handle_verify_evidence(
    state,
    objects=None,
    object_ids=None,
    transaction_id=None,
    rules_version=None,
    **arguments,
) -> dict:
    """Execute the seven-step verification procedure over a set of objects."""
    if arguments:
        return _refused(
            ["A202-POLICY-DENIED"], f"unexpected arguments: {sorted(arguments)}"
        )
    bundle = [obj for obj in (objects or []) if isinstance(obj, dict)]
    if len(bundle) != len(objects or []):
        # An entry that is not an object is not an object with a failed
        # check. Verifying the rest and reporting silently on the whole would
        # state a scope the caller did not present.
        return _refused(
            ["A202-POLICY-DENIED"], "every entry of objects must be a JSON object"
        )
    for object_id in object_ids or []:
        held = state.get_object(object_id)
        if held is not None:
            bundle.append(held)
    if isinstance(transaction_id, str) and transaction_id:
        bundle.extend(state.objects_for(transaction_id))
    if not bundle:
        return _refused(
            ["A202-EVIDENCE-DISCLOSURE-INCOMPLETE"], "no object was disclosed to verify"
        )

    resolver = None
    if rules_version:
        try:
            stated = gate.rules_ref(rules_version)
        except ValueError as unknown:
            return _refused(["A202-STATE-TRANSITION-DENIED"], str(unknown))
        # A bilateral event carries no rules reference of its own, so the
        # version in force is stated by the party presenting the record and
        # every transition replays against that version and no other.
        resolver = lambda ref: gate.resolve_rules(ref or stated)  # noqa: E731

    report = verify_bundle(bundle, state.public_keys(), resolver)
    return {
        "role_scope": ROLE_SCOPE,
        "rules_version": rules_version,
        "objects_in_scope": report.objects_in_scope,
        "streams_disclosed": report.streams_disclosed,
        "undisclosed_streams": report.undisclosed_streams,
        "unresolved_references": report.unresolved_references,
        "unreferenced_evidence": report.unreferenced_evidence,
        "results": report.results(),
        "checks": [
            {
                "step": check.step,
                "name": check.name,
                "subject": check.subject,
                "result": check.result,
                "code": check.code,
                "detail": check.detail,
            }
            for check in report.checks
        ],
    }


def handle_get_transaction_record(state, transaction_id=None, **arguments) -> dict:
    """Return the party-held, hash-chained record for one transaction."""
    if arguments:
        return _refused(
            ["A202-POLICY-DENIED"], f"unexpected arguments: {sorted(arguments)}"
        )
    if not isinstance(transaction_id, str) or not transaction_id:
        return _refused(["A202-POLICY-DENIED"], "transaction_id is required")
    return transaction_record(state, transaction_id)


TOOLS = [
    {
        "name": "issue_mandate",
        "title": "Issue a commercial mandate",
        "description": (
            "Issue and sign a commercial mandate: the document stating which "
            "organisation an agent represents, which acts it may take, under "
            "which limits, for which transaction or category, and for how "
            "long. Call this once per acting agent before anything else. Every "
            "other tool names the mandate an agent acts under.\n\n"
            "A spending_limit becomes two explicit constraints, an amount "
            "ceiling and a currency, both visible in the audit record.\n\n"
            "The mandate is checked before it is signed, so a refused one "
            "never receives a signature that would make it look issued. "
            "Refusals: no constraint at all (A202-MANDATE-UNBOUNDED), a scope "
            "naming neither a transaction nor a category "
            "(A202-MANDATE-SCOPE-TOO-BROAD), an inverted validity interval "
            "(A202-MANDATE-INTERVAL-INVALID), a status endpoint that is not "
            "HTTPS (A202-MANDATE-STATUS-INSECURE), a subject naming both an "
            "agent and a principal (A202-MANDATE-SUBJECT-AMBIGUOUS).\n\n"
            "Returns the mandate identifier and the signed document."
        ),
        "handler": handle_issue_mandate,
        "annotations": {
            "title": "Issue a commercial mandate",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "issuer",
                "subject",
                "represented_organization_id",
                "valid_from",
                "valid_until",
                "status_endpoint",
                "actions",
                "scope",
            ],
            "properties": {
                "issuer": {
                    "type": "object",
                    "description": "The principal issuing the authority, and the key it signs with.",
                    "required": ["organization_id", "principal_id", "key_id"],
                    "properties": {
                        "organization_id": {"type": "string", "description": "Issuing organisation, prefixed org_."},
                        "principal_id": {"type": "string", "description": "The authorised person or role, prefixed prn_. Carries no personal data."},
                        "key_id": {"type": "string", "description": "The issuer's signing key, prefixed key_."},
                    },
                },
                "subject": {
                    "type": "object",
                    "description": "Who acts under the mandate: exactly one of an agent or a delegated principal, never both.",
                    "required": ["key_id"],
                    "properties": {
                        "agent_id": {"type": "string", "description": "The agent, prefixed agt_. Use this or principal_id, not both."},
                        "principal_id": {"type": "string", "description": "A delegated principal, prefixed prn_. Use this or agent_id, not both."},
                        "key_id": {"type": "string", "description": "The subject's signing key, prefixed key_."},
                    },
                },
                "represented_organization_id": {
                    "type": "string",
                    "description": "The organisation the subject represents in its acts, prefixed org_.",
                },
                "valid_from": {"type": "string", "description": "RFC 3339 UTC instant. Must be strictly earlier than valid_until."},
                "valid_until": {"type": "string", "description": "RFC 3339 UTC instant. The mandate authorises nothing at or after it."},
                "status_endpoint": {
                    "type": "string",
                    "description": "HTTPS URL where this mandate's current status is published. HTTPS only: cached status is the only channel a revocation reaches a relying party through.",
                },
                "actions": {
                    "type": "array",
                    "description": "The acts the subject may take, for example offer.submit, offer.accept, agreement.sign. Deny by default: an omitted act is not allowed.",
                    "items": {"type": "string"},
                },
                "scope": {
                    "type": "object",
                    "description": "The boundary of the authority. Must carry transaction_ids, categories, or both. Counterparty and geography narrow an existing boundary and cannot establish one, so a scope naming only a country is refused.",
                    "properties": {
                        "transaction_ids": {"type": "array", "items": {"type": "string"}, "description": "Transactions the subject may act on, prefixed txn_."},
                        "categories": {"type": "array", "items": {"type": "string"}, "description": "Capability categories, for example services.calibration."},
                        "counterparty_organization_ids": {"type": "array", "items": {"type": "string"}, "description": "The only counterparties the subject may act with."},
                        "geographies": {"type": "array", "items": {"type": "string"}, "description": "Two-letter country codes."},
                    },
                },
                "spending_limit": {
                    "type": "object",
                    "description": "Optional. Becomes an amount ceiling and a currency constraint. A ceiling with no currency would be satisfied by that number of any currency, so both are written.",
                    "required": ["currency", "amount"],
                    "properties": {
                        "currency": {"type": "string", "description": "ISO 4217 three-letter code."},
                        "amount": {"type": "string", "description": "Base-10 string, for example 4000.00. Never a number."},
                    },
                },
                "constraints": {
                    "type": "array",
                    "description": "Optional further constraints, each with id, type, path, operator, value, and on_failure of deny or require_approval. At least one constraint must exist in total, counting those a spending limit generates.",
                    "items": {"type": "object"},
                },
                "approval_rules": {
                    "type": "array",
                    "description": "Optional. Each rule carries id, a when predicate of path, operator, and value, an approver of organization_id and role, and expires_after_seconds. A matching act is held until an approval from that approver binds it.",
                    "items": {"type": "object"},
                },
                "delegation": {
                    "type": "object",
                    "description": "Optional, defaults to no delegation. allowed false requires maximum_depth 0; allowed true requires at least 1. An incoherent pair is refused rather than interpreted.",
                },
                "evidence_refs": {"type": "array", "description": "Optional identity, role, or authorisation evidence supporting the issue."},
                "parent_mandate_id": {"type": ["string", "null"], "description": "The mandate this one is delegated from, or null for a root mandate."},
                "mandate_id": {"type": "string", "description": "Optional explicit identifier, prefixed mnd_. One is minted when absent."},
            },
        },
    },
    {
        "name": "verify_mandate",
        "title": "Verify a mandate and decide on an act",
        "description": (
            "Check a mandate and decide whether an act is permitted under it. "
            "Call this before every act, on your own mandate or on one a "
            "counterparty presented.\n\n"
            "It checks the document against the published schema and the rules "
            "the schema cannot express, verifies the issuer signature, checks "
            "the validity interval, and, when proposed_action is given, checks "
            "the act against the mandate's actions, its four scope axes, its "
            "constraints in stable order, and its approval rules.\n\n"
            "Returns one decision, allow, deny, or require_approval, with the "
            "registered reason codes behind it, the per-constraint outcomes, "
            "and action_hash, the hash of the exact act evaluated.\n\n"
            "On require_approval: pass that action_hash to issue_approval, "
            "then call this tool again with the returned approval_id and the "
            "identical proposed_action. The decision becomes allow. A deny is "
            "never approvable.\n\n"
            "This server makes no network call. Resolve the mandate's "
            "status_endpoint yourself and pass the result as status. An absent "
            "result, one older than 60 seconds, or any status other than "
            "active denies with A202-MANDATE-STATUS-UNRESOLVED or "
            "A202-MANDATE-INACTIVE: unavailability is not permission."
        ),
        "handler": handle_verify_mandate,
        "annotations": {
            "title": "Verify a mandate and decide on an act",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "description": "Supply either mandate or mandate_id.",
            "properties": {
                "mandate": {"type": "object", "description": "The mandate document, when it came from a counterparty."},
                "mandate_id": {"type": "string", "description": "A mandate this server holds, as returned by issue_mandate."},
                "at": {"type": "string", "description": "RFC 3339 instant to check against. Defaults to now."},
                "status": {
                    "type": "object",
                    "description": "What you retrieved from the mandate's status endpoint, and when. Omit it and the decision is deny.",
                    "required": ["status", "retrieved_at"],
                    "properties": {
                        "status": {"enum": ["active", "suspended", "revoked", "expired"], "description": "The status the endpoint reported."},
                        "retrieved_at": {"type": "string", "description": "RFC 3339 instant it was retrieved. Older than 60 seconds counts as no result."},
                    },
                },
                "proposed_action": _PROPOSED_ACTION_SCHEMA,
                "approval_id": {"type": "string", "description": "An approval this server holds, from issue_approval, that releases a require_approval hold."},
                "approval": {"type": "object", "description": "An approval object presented directly, instead of approval_id."},
            },
        },
    },
    {
        "name": "issue_approval",
        "title": "Approve one exact act",
        "description": (
            "Record a named principal's approval of one exact act, bound to "
            "the action_hash verify_mandate reported. Call this only after "
            "verify_mandate answered require_approval, then call verify_mandate "
            "again passing approval_id and the identical proposed_action.\n\n"
            "The approval is signed by the approving principal's own key, not "
            "by the agent's, because the control is that somebody other than "
            "the acting agent said yes. It binds one action hash and one "
            "transaction and is reusable across neither: change one byte of "
            "the act and the next verify_mandate returns "
            "A202-APPROVAL-HASH-MISMATCH. It also expires, after which it "
            "authorises nothing.\n\n"
            "An approval never releases a deny. A denied constraint is a "
            "limit, not a question.\n\n"
            "Returns the approval identifier, the action hash it binds, and "
            "when it expires."
        ),
        "handler": handle_issue_approval,
        "annotations": {
            "title": "Approve one exact act",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["transaction_id", "action_hash", "requested_by", "approver"],
            "properties": {
                "transaction_id": {"type": "string", "description": "The transaction the approved act belongs to, prefixed txn_."},
                "action_hash": {
                    "type": "string",
                    "description": "The action_hash verify_mandate returned for this act. 64 lowercase hexadecimal characters.",
                },
                "requested_by": dict(
                    _PARTY_SCHEMA,
                    description="The agent whose act is being approved. The approver is a principal of this same organisation.",
                ),
                "approver": {
                    "type": "object",
                    "description": "The principal giving the approval, and the key that principal signs with.",
                    "required": ["principal_id", "role", "key_id"],
                    "properties": {
                        "principal_id": {"type": "string", "description": "The approving principal, prefixed prn_."},
                        "role": {"type": "string", "description": "The role the approval is given in. It must match the role the mandate's approval rule names, for example procurement_director."},
                        "key_id": {"type": "string", "description": "The principal's signing key, prefixed key_. Not the agent's key."},
                    },
                },
                "decision": {
                    "enum": ["approved", "rejected"],
                    "description": "Defaults to approved. A rejected approval releases nothing and is recorded as the refusal it is.",
                },
                "expires_after_seconds": {
                    "type": "integer",
                    "description": "How long the approval is good for, from now. Defaults to 3600.",
                },
                "expires_at": {
                    "type": "string",
                    "description": "RFC 3339 instant the approval expires, when you would rather state it than count from now. Overrides expires_after_seconds.",
                },
                "conditions": {
                    "type": "array",
                    "description": "Optional conditions the approver attached. They are part of the signed approval and travel with it.",
                    "items": {"type": "string"},
                },
            },
        },
    },
    {
        "name": "create_agreement",
        "title": "Form an agreement with a known counterparty",
        "description": (
            "Form an agreement between two parties who already know each "
            "other, with no marketplace and no negotiation room. Call this "
            "once per transaction.\n\n"
            "Both parties present the allow decision their own mandate "
            "produced. The offeror verifies {\"action_type\": \"offer.submit\", "
            "\"transaction_id\": ..., \"counterparty_organization_id\": <the "
            "offeree's org>, \"proposed_terms\": <the same terms>} and the "
            "offeree verifies the same document with action_type "
            "offer.accept and the offeror's organisation. Pass each result as "
            "buyer_decision and supplier_decision. A decision over a different "
            "act, a different mandate, or an amount the mandate did not allow "
            "refuses the whole call and records nothing.\n\n"
            "It writes the whole formation in one call: the offeror's signed "
            "offer carrying a session identifier it mints, the offeree's "
            "acceptance over the exact offer hash, the agreement carrying both "
            "parties' signatures over the same bytes, the supplier's "
            "commitment, and two events, agreement.direct (draft to "
            "agreement_pending) and agreement.committed (agreement_pending to "
            "committed), each countersigned by the other party.\n\n"
            "The transaction ends this call in state committed. Follow with "
            "record_obligation act=issue.\n\n"
            "Refusals: a transaction that already left draft "
            "(A202-STATE-TRANSITION-DENIED), an unregistered profile "
            "(A202-PROFILE-UNKNOWN), terms the profile does not allow "
            "(A202-PROFILE-TERMS-INVALID), an offer expiring before it was made "
            "(A202-OFFER-EXPIRED)."
        ),
        "handler": handle_create_agreement,
        "annotations": {
            "title": "Form an agreement with a known counterparty",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "transaction_id",
                "buyer",
                "supplier",
                "terms",
                "offer_valid_until",
                "buyer_decision",
                "supplier_decision",
            ],
            "properties": {
                "transaction_id": {
                    "type": "string",
                    "description": "The transaction, prefixed txn_. Choose one per deal; it is the key everything else is recorded under.",
                },
                "buyer": dict(_PARTY_SCHEMA, description="The buying party: organisation, agent, mandate, and signing key."),
                "supplier": dict(_PARTY_SCHEMA, description="The supplying party: organisation, agent, mandate, and signing key."),
                "buyer_decision": dict(
                    _DECISION_SCHEMA,
                    description=_DECISION_SCHEMA["description"]
                    + " For the buyer this is the decision over its own act: offer.accept when the supplier is the offeror, offer.submit when the buyer is.",
                ),
                "supplier_decision": dict(
                    _DECISION_SCHEMA,
                    description=_DECISION_SCHEMA["description"]
                    + " For the supplier this is the decision over its own act: offer.submit when the supplier is the offeror, offer.accept when the buyer is.",
                ),
                "terms": _TERMS_SCHEMA,
                "offer_valid_until": {
                    "type": "string",
                    "description": "RFC 3339 instant the offer expires. Must be later than now.",
                },
                "offeror_role": {
                    "enum": ["buyer", "supplier"],
                    "description": "Which party makes the offer. Defaults to supplier.",
                },
                "session_id": {
                    "type": "string",
                    "description": "Optional session identifier, prefixed ses_. The offeror mints one when absent. Bilaterally this names the relationship; nothing orders it.",
                },
                "offer_evidence_refs": {
                    "type": "array",
                    "description": "Optional evidence the offer relies on, such as an accreditation.",
                },
                "rules_version": {
                    "type": "string",
                    "description": "The rule set version the record is written under. Defaults to 1.3, the version that registers direct formation. Earlier versions never registered it and refuse the path.",
                },
            },
        },
    },
    {
        "name": "record_obligation",
        "title": "Issue, assert, or answer an obligation",
        "description": (
            "Record one act in the obligation exchange. Three acts, in this "
            "order, each signed by a different party, and each carrying that "
            "party's own allow decision from verify_mandate.\n\n"
            "act=issue: the obligee derives an obligation from a committed "
            "agreement and activates it. Needs agreement_id, obligor, obligee, "
            "term_path, quantity, unit_code, due_condition, and a decision the "
            "obligee obtained for {\"action_type\": \"obligation.activated\", "
            "\"transaction_id\": ..., \"counterparty_organization_id\": <the "
            "obligor's org>, \"proposed_terms\": {\"core\": {\"quantity\": ..., "
            "\"unit_code\": ..., \"total\": <the consideration>}}, "
            "\"agreement_id\": ...}. The transaction moves to "
            "in_performance.\n\n"
            "act=assert: the obligor asserts it performed. Needs "
            "obligation_id, obligor, obligee, asserted_quantity, at least one "
            "evidence entry, and a decision the obligor obtained for "
            "action_type performance.declared naming the obligee as "
            "counterparty, the asserted quantity and unit as proposed_terms, "
            "and the obligation_id. An assertion with no evidence is refused "
            "with A202-OBLIGATION-ASSERTION-UNEVIDENCED. The transaction moves "
            "to acceptance_pending.\n\n"
            "act=respond: the obligee accepts or rejects, bound to the exact "
            "assertion hash. Needs assertion_id, responder, counterparty, "
            "response_type, and a decision the responder obtained for "
            "action_type acceptance.granted or acceptance.rejected naming the "
            "counterparty and the assertion_id. A response signed by anyone "
            "but the obligee is "
            "refused with A202-OBLIGATION-RESPONSE-UNAUTHORIZED; accepting less "
            "than is owed without naming a remainder obligation is refused "
            "with A202-OBLIGATION-REMAINDER-MISSING. Accept moves the "
            "transaction to settlement_pending, reject back to in_performance, "
            "where the obligor may assert again."
        ),
        "handler": handle_record_obligation,
        "annotations": {
            "title": "Issue, assert, or answer an obligation",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["act", "decision"],
            "properties": {
                "act": {
                    "enum": ["issue", "assert", "respond"],
                    "description": "Which act to record. Which other fields are required depends on it.",
                },
                "decision": dict(
                    _DECISION_SCHEMA,
                    description=_DECISION_SCHEMA["description"]
                    + " The acting party is the obligee for issue, the obligor for assert, and the responder for respond.",
                ),
                "agreement_id": {"type": "string", "description": "act=issue. The committed agreement the obligation derives from, prefixed agr_."},
                "obligor": dict(_PARTY_SCHEMA, description="act=issue and act=assert. The party that owes."),
                "obligee": dict(_PARTY_SCHEMA, description="act=issue and act=assert. The party owed to."),
                "term_path": {
                    "type": "string",
                    "description": "act=issue. The owed term, addressed under $.terms.core or $.terms.profile_terms. The obligation points at the agreement's terms and never restates them, so drift shows up as a hash mismatch.",
                },
                "quantity": {"type": "string", "description": "act=issue. Base-10 string of how much is owed."},
                "unit_code": {"type": "string", "description": "act=issue. UN/ECE Recommendation 20 common code, matching the terms."},
                "due_condition": {
                    "type": "object",
                    "description": "act=issue. One of due_at_time with at, due_on_event with act_ref or evidence_type, due_on_discharge with obligation_id, or all_of with at least two of those. Anything else is refused with A202-OBLIGATION-CONDITION-UNKNOWN.",
                },
                "consideration": {"type": ["object", "null"], "description": "act=issue. The money attached to this obligation as currency and amount, or null."},
                "commitment_id": {"type": "string", "description": "act=issue. Optional. Defaults to the agreement's first commitment."},
                "obligation_id": {"type": "string", "description": "act=assert. The obligation being performed, prefixed obl_."},
                "asserted_quantity": {"type": "string", "description": "act=assert. Base-10 string of how much was performed."},
                "evidence": {
                    "type": "array",
                    "description": "act=assert. At least one entry. Each becomes a signed evidence object the assertion references by hash.",
                    "items": {
                        "type": "object",
                        "required": ["evidence_type", "claim", "artifact_hash", "issuer", "verification"],
                        "properties": {
                            "evidence_type": {
                                "enum": [
                                    "attestation",
                                    "third_party_certificate",
                                    "inspection_result",
                                    "delivery_confirmation",
                                    "measurement_record",
                                    "adapter_receipt",
                                    "verification_report",
                                    "signed_document",
                                ],
                                "description": "The registered type. The list is closed and anything else fails closed.",
                            },
                            "claim": {"type": "string", "description": "What the evidence is presented to show."},
                            "artifact_hash": {"type": "string", "description": "SHA-256 of the artifact behind the claim, 64 lowercase hexadecimal characters. The artifact itself stays where its holder keeps it."},
                            "issuer": {
                                "type": "object",
                                "description": "The organisation that issued the evidence.",
                                "required": ["organization_id"],
                                "properties": {"organization_id": {"type": "string", "description": "Prefixed org_."}},
                            },
                            "verification": {
                                "type": "object",
                                "description": "The reported verification status. Status is reported, never inferred, and absence of verification reads as unverified.",
                                "required": ["status", "verified_at", "verifier_organization_id"],
                                "properties": {
                                    "status": {"enum": ["unverified", "verified", "failed"], "description": "What verification found."},
                                    "verified_at": {"type": ["string", "null"], "description": "RFC 3339 instant, or null when unverified."},
                                    "verifier_organization_id": {"type": ["string", "null"], "description": "Who verified it, or null."},
                                },
                            },
                        },
                    },
                },
                "assertion_id": {"type": "string", "description": "act=respond. The assertion being answered, prefixed prf_."},
                "responder": dict(_PARTY_SCHEMA, description="act=respond. Must be the obligee named on the obligation."),
                "counterparty": dict(_PARTY_SCHEMA, description="act=respond. The other party, which countersigns the event."),
                "response_type": {"enum": ["accept", "reject"], "description": "act=respond."},
                "accepted_quantity": {"type": "string", "description": "act=respond with accept. Defaults to the asserted quantity. Below what is owed, a remainder_obligation_id is required."},
                "remainder_obligation_id": {"type": "string", "description": "act=respond with a short acceptance. The obligation carrying the shortfall, so it stays in the record."},
                "reason_code": {
                    "enum": [
                        "evidence_insufficient",
                        "evidence_unverified",
                        "quantity_short",
                        "subject_not_as_agreed",
                        "due_condition_not_met",
                        "assertion_unauthorized",
                    ],
                    "description": "act=respond with reject. The list is closed and anything else is refused.",
                },
                "rules_version": {"type": "string", "description": "The rule set version the record is written under. Defaults to 1.3."},
            },
        },
    },
    {
        "name": "verify_evidence",
        "title": "Verify a record against the published procedure",
        "description": (
            "Run the seven-step verification procedure over a set of objects: "
            "content hashes, signatures and the purpose each was issued for, "
            "version chains, event-chain continuity, guarded transitions "
            "replayed against the rules version in force, whether each "
            "determination follows from its rules, and what could not be "
            "checked. Use it on your own record before relying on it, and on "
            "anything a counterparty sends you.\n\n"
            "Pass transaction_id to verify this server's record of one "
            "transaction, object_ids to verify part of it, or objects to "
            "verify a bundle somebody handed you.\n\n"
            "Every check returns verified, failed, or not_checkable, and the "
            "result carries no overall boolean, because a report reduced to "
            "one discards what could not be checked. A signature whose key you "
            "do not hold is not checkable and is never thereby verified. "
            "Without rules_version, guarded transitions are not checkable "
            "rather than verified: an unresolvable rule set is not permission "
            "in either direction."
        ),
        "handler": handle_verify_evidence,
        "annotations": {
            "title": "Verify a record against the published procedure",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "description": "Supply at least one of objects, object_ids, or transaction_id.",
            "properties": {
                "objects": {"type": "array", "items": {"type": "object"}, "description": "Objects presented by value, for example a bundle a counterparty sent."},
                "object_ids": {"type": "array", "items": {"type": "string"}, "description": "Identifiers of objects this server holds."},
                "transaction_id": {"type": "string", "description": "Verify every object this server holds for one transaction."},
                "rules_version": {
                    "type": "string",
                    "description": "The rule set version in force when the record appended, for example 1.3. A record replays against the version it was written under, never the current one.",
                },
            },
        },
    },
    {
        "name": "get_transaction_record",
        "title": "Read the transaction record",
        "description": (
            "Return this party's own copy of the hash-chained transaction "
            "record: every event in chain order with the state it moved the "
            "transaction to, which keys signed it, and the object it concerns, "
            "plus the state the record currently reaches and every object "
            "identifier held for the transaction.\n\n"
            "Call it at any point to see where a transaction stands before "
            "deciding what to do next. Ordering is by predecessor reference "
            "rather than by a counter, because bilaterally there is no "
            "ordering service, and a record whose links do not form one chain "
            "is reported as broken with A202-EVIDENCE-CHAIN-GAP."
        ),
        "handler": handle_get_transaction_record,
        "annotations": {
            "title": "Read the transaction record",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["transaction_id"],
            "properties": {
                "transaction_id": {"type": "string", "description": "The transaction to read, prefixed txn_."},
            },
        },
    },
]

BY_NAME = {tool["name"]: tool for tool in TOOLS}


def call(state, name: str, arguments: dict | None = None) -> dict:
    """Run one tool by name.

    An unknown name raises, because it is a protocol error rather than a
    commercial refusal. A refusal is a result and does not raise.
    """
    tool = BY_NAME.get(name)
    if tool is None:
        raise KeyError(name)
    return tool["handler"](state, **(arguments or {}))
