"""Shared fixtures for the tool tests.

The parties, terms, and mandate below are the synthetic ones the published
fixture set uses, so that what these tools emit is judged against the same
shapes the conformance suite judges.

Every party here holds a mandate this state actually issued, and every
recording act carries the decision that mandate produced for it. A helper that
short-circuited either would be exercising a server nobody can run.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REFERENCE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REFERENCE_DIR))

from a202_mcp.authority import verify_mandate  # noqa: E402
from a202_mcp.state import LocalState  # noqa: E402
from a202_mcp.tools import handle_issue_mandate  # noqa: E402
from a202_mcp.transaction import (  # noqa: E402
    create_agreement,
    formation_acts,
    obligation_act,
)

TRANSACTION = "txn_bilateral_mcp_01"

BUYER = {
    "organization_id": "org_northstar",
    "agent_id": "agt_northstar_buyer_01",
    "mandate_id": "mnd_northstar_buyer_01",
    "key_id": "key_northstar_agent_01",
}
SUPPLIER = {
    "organization_id": "org_delta",
    "agent_id": "agt_delta_supplier_01",
    "mandate_id": "mnd_delta_supplier_01",
    "key_id": "key_delta_agent_01",
}

BUYER_PRINCIPAL = {
    "organization_id": "org_northstar",
    "principal_id": "prn_northstar_procurement_director",
    "key_id": "key_northstar_principal_01",
}
SUPPLIER_PRINCIPAL = {
    "organization_id": "org_delta",
    "principal_id": "prn_delta_managing_director",
    "key_id": "key_delta_principal_01",
}

ACTIONS = [
    "offer.submit",
    "offer.accept",
    "agreement.sign",
    "obligation.activated",
    "performance.declared",
    "acceptance.granted",
    "acceptance.rejected",
]

TERMS = {
    "profile": "a202-profile/calibration-service/0.1",
    "core": {
        "description": "Calibration and digital certificates for 20 pressure transmitters",
        "quantity": "20",
        "unit_code": "H87",
        "unit_name": "piece",
        "total": {"currency": "EUR", "amount": "3200.00"},
    },
    "profile_terms": {
        "completion": {"business_days_after_collection": 15, "business_calendar": "NL"},
        "payment": {"prepayment_percent": "20", "balance_trigger": "buyer_acceptance"},
        "acceptance": {
            "certificate_required": True,
            "machine_readable_result_required": True,
            "qualification_standard": "ISO/IEC 17025:2017",
        },
        "rework": {"included_attempts": 1},
    },
}

CONSIDERATION = {"currency": "EUR", "amount": "3200.00"}


def stamp(offset_hours: int = 0) -> str:
    moment = datetime.now(timezone.utc) + timedelta(hours=offset_hours)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def fresh_status(status: str = "active") -> dict:
    return {"status": status, "retrieved_at": stamp()}


def mandate_arguments(**overrides) -> dict:
    arguments = {
        "issuer": dict(BUYER_PRINCIPAL),
        "subject": {"agent_id": BUYER["agent_id"], "key_id": BUYER["key_id"]},
        "represented_organization_id": BUYER["organization_id"],
        "valid_from": stamp(-1),
        "valid_until": stamp(24),
        "status_endpoint": "https://status.a202.invalid/v1/mandates/one/status",
        "actions": list(ACTIONS),
        "scope": {
            "transaction_ids": [TRANSACTION],
            "categories": ["services.calibration"],
            "counterparty_organization_ids": ["org_delta"],
            "geographies": ["NL"],
        },
        "spending_limit": {"currency": "EUR", "amount": "4000.00"},
    }
    arguments.update(overrides)
    return arguments


def proposed_action(amount: str = "3200.00", **overrides) -> dict:
    action = {
        "action_type": "offer.accept",
        "transaction_id": TRANSACTION,
        "category": "services.calibration",
        "counterparty_organization_id": "org_delta",
        "geography": "NL",
        "proposed_terms": {
            "core": {"total": {"currency": "EUR", "amount": amount}},
        },
    }
    action.update(overrides)
    return action


def issue_for(state, party: dict, principal: dict, counterparty: dict, **overrides) -> dict:
    """Issue one party's mandate and return the party naming it."""
    arguments = mandate_arguments(
        issuer=dict(principal),
        subject={"agent_id": party["agent_id"], "key_id": party["key_id"]},
        represented_organization_id=party["organization_id"],
        scope={
            "transaction_ids": [TRANSACTION],
            "counterparty_organization_ids": [counterparty["organization_id"]],
        },
    )
    arguments.update(overrides)
    issued = handle_issue_mandate(state, **arguments)
    assert issued["outcome"] == "issued", issued
    return dict(party, mandate_id=issued["mandate_id"])


def decision_for(state, party: dict, document: dict) -> dict:
    """The decision a party's own mandate produces for one act."""
    return verify_mandate(
        state,
        state.get_mandate(party["mandate_id"]),
        status=fresh_status(),
        proposed_action=document,
    )


def parties(state) -> tuple:
    """Both parties, each holding a mandate this state issued."""
    buyer = issue_for(state, BUYER, BUYER_PRINCIPAL, SUPPLIER)
    supplier = issue_for(state, SUPPLIER, SUPPLIER_PRINCIPAL, BUYER)
    return buyer, supplier


def formation_decisions(state, buyer: dict, supplier: dict, terms: dict | None = None) -> dict:
    """The two decisions a direct formation needs, one per acting party."""
    acts = formation_acts(TRANSACTION, buyer, supplier, terms or TERMS)
    return {
        "supplier_decision": decision_for(state, supplier, acts["offeror_act"]),
        "buyer_decision": decision_for(state, buyer, acts["offeree_act"]),
    }


def committed_transaction(state: LocalState | None = None) -> tuple:
    """A state holding one directly formed, committed transaction."""
    state = state or LocalState()
    buyer, supplier = parties(state)
    formed = create_agreement(
        state,
        transaction_id=TRANSACTION,
        buyer=buyer,
        supplier=supplier,
        terms=TERMS,
        offer_valid_until=stamp(12),
        **formation_decisions(state, buyer, supplier),
    )
    return state, formed, buyer, supplier


def obligation_decision(state, buyer: dict, supplier: dict, agreement_id: str,
                        quantity: str = "20") -> dict:
    """The obligee's decision for activating one obligation."""
    return decision_for(
        state,
        buyer,
        obligation_act(agreement_id, TRANSACTION, supplier, buyer, quantity,
                       "H87", CONSIDERATION),
    )


DUE_CONDITION = {"type": "due_at_time", "at": stamp(48)}

EVIDENCE = [
    {
        "evidence_type": "third_party_certificate",
        "claim": "Calibration certificates issued for 20 transmitters",
        "artifact_hash": "a" * 64,
        "issuer": {"organization_id": "org_delta"},
        "verification": {
            "status": "verified",
            "verified_at": stamp(),
            "verifier_organization_id": "org_northstar",
        },
    }
]
