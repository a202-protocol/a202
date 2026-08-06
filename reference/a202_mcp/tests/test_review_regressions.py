"""The attacks an adversarial review of this package found, each refused.

One class per finding. Every test runs the reproduction as the review stated
it and asserts the refusal, with the registered code, and that nothing was
recorded where nothing should have been.
"""

from __future__ import annotations

import copy
import unittest

from a202_mcp import gate
from a202_mcp.state import LocalState
from a202_mcp.tools import (
    handle_create_agreement,
    handle_get_transaction_record,
    handle_issue_approval,
    handle_issue_mandate,
    handle_record_obligation,
    handle_verify_evidence,
    handle_verify_mandate,
)
from a202_mcp.authority import action_hash_of
from a202_mcp.transaction import formation_acts, obligation_act

from .support import (
    BUYER,
    BUYER_PRINCIPAL,
    SUPPLIER,
    TERMS,
    TRANSACTION,
    decision_for,
    formation_decisions,
    fresh_status,
    mandate_arguments,
    parties,
    proposed_action,
    stamp,
)

APPROVAL_RULE = {
    "id": "a_large_commitment",
    "when": {
        "path": "$.proposed_terms.core.total.amount",
        "operator": "minimum",
        "value": "3000.00",
    },
    "approver": {"organization_id": "org_northstar", "role": "procurement_director"},
    "expires_after_seconds": 3600,
}


def _expensive_terms(amount: str = "999999.00") -> dict:
    terms = copy.deepcopy(TERMS)
    terms["core"]["total"]["amount"] = amount
    return terms


class UnauthorizedRecordingTest(unittest.TestCase):
    """F1. A recorded act carries the decision that allowed it, or is refused."""

    def setUp(self):
        self.state = LocalState()
        self.buyer, self.supplier = parties(self.state)

    def _arguments(self, terms, **overrides):
        arguments = {
            "transaction_id": TRANSACTION,
            "buyer": self.buyer,
            "supplier": self.supplier,
            "terms": terms,
            "offer_valid_until": stamp(12),
        }
        arguments.update(overrides)
        return arguments

    def _nothing_was_recorded(self):
        record = handle_get_transaction_record(self.state, TRANSACTION)
        self.assertEqual(record["events"], [])
        self.assertEqual(record["state"], "draft")

    def test_a_mandate_that_was_never_issued_records_nothing(self):
        # The review's reproduction: a mandate capped at EUR 4000, an
        # agreement for EUR 999,999, and a mandate identifier nobody issued.
        terms = _expensive_terms()
        invented = dict(self.buyer, mandate_id="mnd_never_issued_01")
        fabricated = {
            "decision": "allow",
            "reason_codes": [],
            "mandate_id": "mnd_never_issued_01",
            "action_hash": "0" * 64,
            "checked_at": stamp(),
        }
        result = handle_create_agreement(
            self.state,
            **self._arguments(
                terms,
                buyer=invented,
                buyer_decision=fabricated,
                supplier_decision=fabricated,
            ),
        )
        self.assertEqual(result["outcome"], "refused")
        self.assertIn("A202-APPROVAL-HASH-MISMATCH", result["reason_codes"])
        self._nothing_was_recorded()

    def test_an_over_limit_act_is_denied_and_then_cannot_be_recorded(self):
        terms = _expensive_terms()
        acts = formation_acts(TRANSACTION, self.buyer, self.supplier, terms)
        buyer_decision = decision_for(self.state, self.buyer, acts["offeree_act"])
        supplier_decision = decision_for(self.state, self.supplier, acts["offeror_act"])
        self.assertEqual(buyer_decision["decision"], "deny")
        self.assertIn("A202-POLICY-DENIED", buyer_decision["reason_codes"])

        result = handle_create_agreement(
            self.state,
            **self._arguments(
                terms,
                buyer_decision=buyer_decision,
                supplier_decision=supplier_decision,
            ),
        )
        self.assertEqual(result["outcome"], "refused")
        self.assertIn("A202-POLICY-DENIED", result["reason_codes"])
        self._nothing_was_recorded()

    def test_a_decision_over_a_cheaper_act_does_not_cover_a_dearer_one(self):
        cheap = formation_decisions(self.state, self.buyer, self.supplier, TERMS)
        result = handle_create_agreement(
            self.state, **self._arguments(_expensive_terms("3900.00"), **cheap)
        )
        self.assertEqual(result["outcome"], "refused")
        self.assertIn("A202-APPROVAL-HASH-MISMATCH", result["reason_codes"])
        self.assertIn("proposed_action", result["detail"])
        self._nothing_was_recorded()

    def test_a_decision_made_for_the_other_party_is_not_this_party_s(self):
        acts = formation_acts(TRANSACTION, self.buyer, self.supplier, TERMS)
        buyer_decision = decision_for(self.state, self.buyer, acts["offeree_act"])
        result = handle_create_agreement(
            self.state,
            **self._arguments(
                TERMS,
                buyer_decision=buyer_decision,
                supplier_decision=buyer_decision,
            ),
        )
        self.assertEqual(result["outcome"], "refused")
        self._nothing_was_recorded()

    def test_a_decision_older_than_the_status_bound_is_refused(self):
        decisions = formation_decisions(self.state, self.buyer, self.supplier)
        decisions["buyer_decision"] = dict(
            decisions["buyer_decision"], checked_at=stamp(-2)
        )
        result = handle_create_agreement(
            self.state, **self._arguments(TERMS, **decisions)
        )
        self.assertEqual(result["outcome"], "refused")
        self.assertIn("A202-MANDATE-STATUS-UNRESOLVED", result["reason_codes"])
        self._nothing_was_recorded()

    def test_a_held_act_is_not_a_recordable_act(self):
        decisions = formation_decisions(self.state, self.buyer, self.supplier)
        decisions["buyer_decision"] = dict(
            decisions["buyer_decision"], decision="require_approval"
        )
        result = handle_create_agreement(
            self.state, **self._arguments(TERMS, **decisions)
        )
        self.assertIn("A202-APPROVAL-REQUIRED", result["reason_codes"])
        self._nothing_was_recorded()

    def test_no_decision_at_all_states_the_act_to_verify(self):
        decisions = formation_decisions(self.state, self.buyer, self.supplier)
        decisions["supplier_decision"] = None
        result = handle_create_agreement(
            self.state, **self._arguments(TERMS, **decisions)
        )
        self.assertIn("A202-POLICY-DENIED", result["reason_codes"])
        self.assertIn("offer.submit", result["detail"])
        self._nothing_was_recorded()

    def test_an_obligation_act_nobody_verified_is_refused(self):
        formed = handle_create_agreement(
            self.state,
            **self._arguments(
                TERMS, **formation_decisions(self.state, self.buyer, self.supplier)
            ),
        )
        before = handle_get_transaction_record(self.state, TRANSACTION)
        result = handle_record_obligation(
            self.state,
            act="issue",
            agreement_id=formed["agreement_id"],
            obligor=self.supplier,
            obligee=self.buyer,
            term_path="$.terms.core.quantity",
            quantity="20",
            unit_code="H87",
            due_condition={"type": "due_at_time", "at": stamp(48)},
            consideration={"currency": "EUR", "amount": "3200.00"},
            decision={"decision": "allow", "action_hash": "0" * 64,
                      "mandate_id": self.buyer["mandate_id"], "reason_codes": [],
                      "checked_at": stamp()},
        )
        self.assertEqual(result["outcome"], "refused")
        self.assertIn("A202-APPROVAL-HASH-MISMATCH", result["reason_codes"])
        after = handle_get_transaction_record(self.state, TRANSACTION)
        self.assertEqual(len(after["events"]), len(before["events"]))


class ForgedVerdictTest(unittest.TestCase):
    """N1. A presented verdict is recomputed, never believed."""

    def setUp(self):
        self.state = LocalState()
        self.buyer, self.supplier = parties(self.state)

    def _forgery(self, party, document):
        """The review's forgery: right act, real mandate, fresh, and a lie."""
        return {
            "decision": "allow",
            "reason_codes": [],
            "mandate_id": party["mandate_id"],
            "action_hash": action_hash_of(document),
            "checked_at": stamp(),
            "status": "verified",
        }

    def test_a_forged_allow_over_an_honest_deny_records_nothing(self):
        terms = _expensive_terms()
        acts = formation_acts(TRANSACTION, self.buyer, self.supplier, terms)

        # Both mandates honestly deny the act.
        self.assertEqual(
            decision_for(self.state, self.buyer, acts["offeree_act"])["decision"],
            "deny",
        )
        self.assertEqual(
            decision_for(self.state, self.supplier, acts["offeror_act"])["decision"],
            "deny",
        )

        result = handle_create_agreement(
            self.state,
            transaction_id=TRANSACTION,
            buyer=self.buyer,
            supplier=self.supplier,
            terms=terms,
            offer_valid_until=stamp(12),
            buyer_decision=self._forgery(self.buyer, acts["offeree_act"]),
            supplier_decision=self._forgery(self.supplier, acts["offeror_act"]),
        )
        self.assertEqual(result["outcome"], "refused")
        self.assertIn("A202-POLICY-DENIED", result["reason_codes"])
        for code in result["reason_codes"]:
            self.assertRegex(code, r"^A202-[A-Z0-9-]+$")

        record = handle_get_transaction_record(self.state, TRANSACTION)
        self.assertEqual(record["events"], [])
        self.assertEqual(record["state"], "draft")
        self.assertEqual(
            [obj for obj in self.state.objects_for(TRANSACTION)
             if obj["object_type"] == "policy_decision"],
            [],
        )

    def test_a_forged_allow_on_an_obligation_act_records_nothing(self):
        formed = handle_create_agreement(
            self.state,
            transaction_id=TRANSACTION,
            buyer=self.buyer,
            supplier=self.supplier,
            terms=TERMS,
            offer_valid_until=stamp(12),
            **formation_decisions(self.state, self.buyer, self.supplier),
        )
        before = handle_get_transaction_record(self.state, TRANSACTION)
        dear = {"currency": "EUR", "amount": "999999.00"}
        document = obligation_act(
            formed["agreement_id"], TRANSACTION, self.supplier, self.buyer,
            "20", "H87", dear,
        )
        self.assertEqual(
            decision_for(self.state, self.buyer, document)["decision"], "deny"
        )
        result = handle_record_obligation(
            self.state,
            act="issue",
            agreement_id=formed["agreement_id"],
            obligor=self.supplier,
            obligee=self.buyer,
            term_path="$.terms.core.quantity",
            quantity="20",
            unit_code="H87",
            due_condition={"type": "due_at_time", "at": stamp(48)},
            consideration=dear,
            decision=self._forgery(self.buyer, document),
        )
        self.assertEqual(result["outcome"], "refused")
        self.assertIn("A202-POLICY-DENIED", result["reason_codes"])
        after = handle_get_transaction_record(self.state, TRANSACTION)
        self.assertEqual(len(after["events"]), len(before["events"]))

    def test_a_forged_allow_over_a_held_act_records_nothing(self):
        # The mandate holds the act for approval and no approval exists. An
        # allow claiming no reason codes is refused, and the hold stands.
        issued = handle_issue_mandate(
            self.state,
            **mandate_arguments(
                approval_rules=[APPROVAL_RULE],
                scope={
                    "transaction_ids": [TRANSACTION],
                    "counterparty_organization_ids": ["org_delta"],
                },
            ),
        )
        acting = dict(BUYER, mandate_id=issued["mandate_id"])
        acts = formation_acts(TRANSACTION, acting, self.supplier, TERMS)
        honest = decision_for(self.state, acting, acts["offeree_act"])
        self.assertEqual(honest["decision"], "require_approval")

        result = handle_create_agreement(
            self.state,
            transaction_id=TRANSACTION,
            buyer=acting,
            supplier=self.supplier,
            terms=TERMS,
            offer_valid_until=stamp(12),
            buyer_decision=self._forgery(acting, acts["offeree_act"]),
            supplier_decision=decision_for(
                self.state, self.supplier, acts["offeror_act"]
            ),
        )
        self.assertEqual(result["outcome"], "refused")
        self.assertIn("A202-APPROVAL-REQUIRED", result["reason_codes"])
        self.assertEqual(
            handle_get_transaction_record(self.state, TRANSACTION)["events"], []
        )

    def test_an_allow_that_invents_reason_codes_is_refused(self):
        acts = formation_acts(TRANSACTION, self.buyer, self.supplier, TERMS)
        honest = decision_for(self.state, self.buyer, acts["offeree_act"])
        self.assertEqual(honest["decision"], "allow")
        result = handle_create_agreement(
            self.state,
            transaction_id=TRANSACTION,
            buyer=self.buyer,
            supplier=self.supplier,
            terms=TERMS,
            offer_valid_until=stamp(12),
            buyer_decision=dict(honest, reason_codes=["A202-APPROVAL-REQUIRED"]),
            supplier_decision=decision_for(
                self.state, self.supplier, acts["offeror_act"]
            ),
        )
        self.assertEqual(result["outcome"], "refused")
        self.assertIn("A202-POLICY-DENIED", result["reason_codes"])

    def test_an_honest_allow_still_records(self):
        result = handle_create_agreement(
            self.state,
            transaction_id=TRANSACTION,
            buyer=self.buyer,
            supplier=self.supplier,
            terms=TERMS,
            offer_valid_until=stamp(12),
            **formation_decisions(self.state, self.buyer, self.supplier),
        )
        self.assertEqual(result["state"], "committed")


class SelfApprovalTest(unittest.TestCase):
    """F2. An approval is signed by a principal, never by the acting agent."""

    def setUp(self):
        self.state = LocalState()
        self.buyer, self.supplier = parties(self.state)

    def test_an_approval_signed_with_the_agent_s_own_key_is_refused(self):
        result = handle_issue_approval(
            self.state,
            transaction_id=TRANSACTION,
            action_hash="a" * 64,
            requested_by=self.buyer,
            approver={
                "principal_id": "prn_northstar_procurement_director",
                "role": "procurement_director",
                "key_id": BUYER["key_id"],
            },
        )
        self.assertEqual(result["outcome"], "refused")
        self.assertIn("A202-APPROVAL-REQUIRED", result["reason_codes"])

    def test_a_key_bound_to_one_principal_cannot_become_another_s(self):
        first = handle_issue_approval(
            self.state,
            transaction_id=TRANSACTION,
            action_hash="a" * 64,
            requested_by=self.buyer,
            approver={
                "principal_id": "prn_northstar_procurement_director",
                "role": "procurement_director",
                "key_id": BUYER_PRINCIPAL["key_id"],
            },
        )
        self.assertEqual(first["outcome"], "recorded")
        second = handle_issue_approval(
            self.state,
            transaction_id=TRANSACTION,
            action_hash="b" * 64,
            requested_by=self.buyer,
            approver={
                "principal_id": "prn_northstar_intern",
                "role": "procurement_director",
                "key_id": BUYER_PRINCIPAL["key_id"],
            },
        )
        self.assertEqual(second["outcome"], "refused")

    def test_an_approval_signed_under_an_unbound_key_does_not_verify(self):
        # The approval names a principal, and the signature is under a key
        # that principal does not own. The signature verifies as bytes and
        # still releases nothing.
        state = LocalState()
        buyer, _supplier = parties(state)
        mandate = state.get_mandate(buyer["mandate_id"])
        approval = handle_issue_approval(
            state,
            transaction_id=TRANSACTION,
            action_hash="a" * 64,
            requested_by=buyer,
            approver={
                "principal_id": "prn_northstar_procurement_director",
                "role": "procurement_director",
                "key_id": BUYER_PRINCIPAL["key_id"],
            },
        )
        held = state.get_object(approval["approval_id"])
        forged = copy.deepcopy(held)
        forged["payload"]["approver"]["principal_id"] = "prn_northstar_intern"
        report = handle_verify_mandate(
            state,
            mandate=mandate,
            status=fresh_status(),
            proposed_action=proposed_action(),
            approval=forged,
        )
        self.assertNotEqual(report["approval"], "verified")


class ApprovalReplayTest(unittest.TestCase):
    """F3. An approval cannot be reused across transactions."""

    def setUp(self):
        self.state = LocalState()
        self.buyer, _supplier = parties(
            self.state
        )
        issued = handle_issue_mandate(
            self.state,
            **mandate_arguments(
                approval_rules=[APPROVAL_RULE],
                scope={"transaction_ids": [TRANSACTION, "txn_other_deal_01"]},
            ),
        )
        self.mandate = issued["mandate"]
        self.acting = dict(BUYER, mandate_id=issued["mandate_id"])

    def test_an_approval_from_another_transaction_releases_nothing(self):
        other = proposed_action(transaction_id="txn_other_deal_01")
        held_elsewhere = handle_verify_mandate(
            self.state, mandate=self.mandate, status=fresh_status(),
            proposed_action=other,
        )
        self.assertEqual(held_elsewhere["decision"], "require_approval")
        approval = handle_issue_approval(
            self.state,
            transaction_id="txn_other_deal_01",
            action_hash=held_elsewhere["action_hash"],
            requested_by=self.acting,
            approver={
                "principal_id": "prn_northstar_procurement_director",
                "role": "procurement_director",
                "key_id": BUYER_PRINCIPAL["key_id"],
            },
        )
        self.assertEqual(approval["outcome"], "recorded")

        # The same approval, presented against the act it was not issued for.
        replayed = copy.deepcopy(self.state.get_object(approval["approval_id"]))
        replayed["payload"]["action_hash"] = handle_verify_mandate(
            self.state, mandate=self.mandate, status=fresh_status(),
            proposed_action=proposed_action(),
        )["action_hash"]
        report = handle_verify_mandate(
            self.state,
            mandate=self.mandate,
            status=fresh_status(),
            proposed_action=proposed_action(),
            approval=replayed,
        )
        self.assertEqual(report["decision"], "require_approval")
        self.assertIn("A202-STREAM-MISMATCH", report["reason_codes"])


class ConstraintHoldApproverTest(unittest.TestCase):
    """F4. A hold no approval rule raised still needs the right approver."""

    def setUp(self):
        self.state = LocalState()
        issued = handle_issue_mandate(
            self.state,
            **mandate_arguments(
                spending_limit=None,
                constraints=[
                    {
                        "id": "c_review_above_3000",
                        "type": "commercial.decimal",
                        "path": "$.proposed_terms.core.total.amount",
                        "operator": "maximum",
                        "value": "3000.00",
                        "on_failure": "require_approval",
                    }
                ],
            ),
        )
        self.mandate = issued["mandate"]
        self.acting = dict(BUYER, mandate_id=issued["mandate_id"])

    def test_a_constraint_hold_is_not_released_by_an_outside_approver(self):
        held = handle_verify_mandate(
            self.state, mandate=self.mandate, status=fresh_status(),
            proposed_action=proposed_action(),
        )
        self.assertEqual(held["decision"], "require_approval")
        self.assertEqual(held["approval_rules_matched"], [])

        approval = handle_issue_approval(
            self.state,
            transaction_id=TRANSACTION,
            action_hash=held["action_hash"],
            requested_by=self.acting,
            approver={
                "principal_id": "prn_someone_elses_intern",
                "role": "intern",
                "key_id": "key_someone_else_01",
            },
        )
        self.assertEqual(approval["outcome"], "recorded")
        forged = copy.deepcopy(self.state.get_object(approval["approval_id"]))
        forged["payload"]["approver"]["organization_id"] = "org_meridian"
        report = handle_verify_mandate(
            self.state,
            mandate=self.mandate,
            status=fresh_status(),
            proposed_action=proposed_action(),
            approval=forged,
        )
        self.assertEqual(report["decision"], "require_approval")
        self.assertIn("A202-APPROVAL-REQUIRED", report["reason_codes"])

    def test_the_acting_organisation_s_own_principal_releases_it(self):
        held = handle_verify_mandate(
            self.state, mandate=self.mandate, status=fresh_status(),
            proposed_action=proposed_action(),
        )
        approval = handle_issue_approval(
            self.state,
            transaction_id=TRANSACTION,
            action_hash=held["action_hash"],
            requested_by=self.acting,
            approver={
                "principal_id": "prn_northstar_procurement_director",
                "role": "procurement_director",
                "key_id": BUYER_PRINCIPAL["key_id"],
            },
        )
        report = handle_verify_mandate(
            self.state,
            mandate=self.mandate,
            status=fresh_status(),
            proposed_action=proposed_action(),
            approval_id=approval["approval_id"],
        )
        self.assertEqual(report["decision"], "allow")


class HostileInputTest(unittest.TestCase):
    """F5. Hostile input fails closed, and never as a traceback."""

    def setUp(self):
        self.state = LocalState()
        issued = handle_issue_mandate(self.state, **mandate_arguments())
        self.mandate = issued["mandate"]

    def _decide(self, **overrides):
        return handle_verify_mandate(
            self.state, mandate=self.mandate, status=fresh_status(), **overrides
        )

    def test_a_not_a_number_amount_denies(self):
        report = self._decide(proposed_action=proposed_action(amount="NaN"))
        self.assertEqual(report["decision"], "deny")
        self.assertIn("A202-MANDATE-CONSTRAINT-UNKNOWN", report["reason_codes"])

    def test_an_infinite_amount_denies(self):
        report = self._decide(proposed_action=proposed_action(amount="Infinity"))
        self.assertEqual(report["decision"], "deny")

    def test_a_constraint_expression_that_does_not_compile_denies(self):
        issued = handle_issue_mandate(
            self.state,
            **mandate_arguments(
                spending_limit=None,
                constraints=[
                    {
                        "id": "c_broken_expression",
                        "type": "commercial.string",
                        "path": "$.proposed_terms.core.total.currency",
                        "operator": "matches",
                        "value": "[",
                        "on_failure": "deny",
                    }
                ],
            ),
        )
        report = handle_verify_mandate(
            self.state,
            mandate=issued["mandate"],
            status=fresh_status(),
            proposed_action=proposed_action(),
        )
        self.assertEqual(report["decision"], "deny")
        self.assertIn("A202-MANDATE-CONSTRAINT-UNKNOWN", report["reason_codes"])

    def test_a_presented_mandate_whose_interval_is_a_number_denies(self):
        hostile = copy.deepcopy(self.mandate)
        hostile["valid_from"] = 12345
        report = handle_verify_mandate(
            self.state, mandate=hostile, status=fresh_status()
        )
        self.assertEqual(report["decision"], "deny")
        self.assertIn("A202-MANDATE-INACTIVE", report["reason_codes"])

    def test_an_identifier_of_the_wrong_type_resolves_to_nothing(self):
        report = handle_verify_mandate(self.state, mandate_id={"a": 1})
        self.assertEqual(report["outcome"], "refused")
        self.assertIn("A202-POLICY-DENIED", report["reason_codes"])

    def test_an_unexpected_argument_is_refused_rather_than_raised(self):
        for result in (
            handle_verify_evidence(self.state, transaction_id=TRANSACTION, extra=1),
            handle_get_transaction_record(
                self.state, transaction_id=TRANSACTION, extra=1
            ),
        ):
            self.assertEqual(result["outcome"], "refused")
            self.assertIn("A202-POLICY-DENIED", result["reason_codes"])

    def test_a_bundle_entry_that_is_not_an_object_is_refused(self):
        result = handle_verify_evidence(self.state, objects=["not an object"])
        self.assertEqual(result["outcome"], "refused")
        self.assertIn("A202-POLICY-DENIED", result["reason_codes"])

    def test_an_unregistered_rules_version_is_refused(self):
        result = handle_verify_evidence(
            self.state, transaction_id=TRANSACTION, rules_version="9.9"
        )
        self.assertEqual(result["outcome"], "refused")


class ReasonCodeHygieneTest(unittest.TestCase):
    """F6. Reason codes are registered codes. Prose lives in detail."""

    def test_a_schema_refusal_carries_codes_and_not_validator_messages(self):
        state = LocalState()
        result = handle_issue_mandate(
            state, **mandate_arguments(actions="offer.accept")
        )
        self.assertEqual(result["outcome"], "refused")
        self.assertTrue(result["reason_codes"])
        for code in result["reason_codes"]:
            self.assertRegex(code, r"^A202-[A-Z0-9-]+$")
        self.assertTrue(result["detail"])
        self.assertIn("actions", result["detail"])

    def test_the_gate_keeps_the_two_apart(self):
        codes, errors = gate.mandate_refusals({"id": "mnd_broken_01"})
        self.assertTrue(errors)
        for code in codes:
            self.assertRegex(code, r"^A202-[A-Z0-9-]+$")


class StatusFreshnessTest(unittest.TestCase):
    """F7. The freshness bound on a status result is two sided."""

    def test_a_status_retrieved_in_the_future_is_no_status(self):
        state = LocalState()
        mandate = handle_issue_mandate(state, **mandate_arguments())["mandate"]
        report = handle_verify_mandate(
            state,
            mandate=mandate,
            status={"status": "active", "retrieved_at": stamp(24)},
        )
        self.assertEqual(report["decision"], "deny")
        self.assertIn("A202-MANDATE-STATUS-UNRESOLVED", report["reason_codes"])


if __name__ == "__main__":
    unittest.main()
