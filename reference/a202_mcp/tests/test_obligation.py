"""record_obligation: issue, assert, and respond, and what each refuses."""

from __future__ import annotations

import unittest

from a202_mcp.tools import handle_get_transaction_record, handle_record_obligation
from a202_mcp.transaction import assertion_act, response_act

from .support import (
    CONSIDERATION,
    DUE_CONDITION,
    EVIDENCE,
    TRANSACTION,
    committed_transaction,
    decision_for,
    obligation_decision,
)


class ObligationTest(unittest.TestCase):
    def setUp(self):
        self.state, self.formed, self.buyer, self.supplier = committed_transaction()
        self.agreement_id = self.formed["agreement"]["id"]

    # --- helpers ----------------------------------------------------------

    def issue(self, **overrides):
        quantity = overrides.pop("quantity", "20")
        arguments = {
            "act": "issue",
            "agreement_id": self.agreement_id,
            "obligor": self.supplier,
            "obligee": self.buyer,
            "term_path": "$.terms.core.quantity",
            "quantity": quantity,
            "unit_code": "H87",
            "due_condition": DUE_CONDITION,
            "consideration": CONSIDERATION,
            "decision": obligation_decision(
                self.state, self.buyer, self.supplier, self.agreement_id, quantity
            ),
        }
        arguments.update(overrides)
        return handle_record_obligation(self.state, **arguments)

    def assert_performance(self, obligation_id, quantity="20", evidence=None, **over):
        act = assertion_act(
            obligation_id, TRANSACTION, self.buyer, quantity, "H87", CONSIDERATION
        )
        arguments = {
            "act": "assert",
            "obligation_id": obligation_id,
            "obligor": self.supplier,
            "obligee": self.buyer,
            "asserted_quantity": quantity,
            "evidence": EVIDENCE if evidence is None else evidence,
            "decision": decision_for(self.state, self.supplier, act),
        }
        arguments.update(over)
        return handle_record_obligation(self.state, **arguments)

    def respond(self, assertion_id, response_type="accept", quantity="20",
                responder=None, counterparty=None, **over):
        responder = responder or self.buyer
        counterparty = counterparty or self.supplier
        act = response_act(
            assertion_id, TRANSACTION, counterparty, response_type, quantity,
            "H87", CONSIDERATION,
        )
        arguments = {
            "act": "respond",
            "assertion_id": assertion_id,
            "responder": responder,
            "counterparty": counterparty,
            "response_type": response_type,
            "decision": decision_for(self.state, responder, act),
        }
        arguments.update(over)
        return handle_record_obligation(self.state, **arguments)

    # --- the exchange -----------------------------------------------------

    def test_issued_obligation_activates_the_transaction(self):
        result = self.issue()
        self.assertEqual(result["outcome"], "recorded")
        self.assertEqual(result["state"], "in_performance")
        obligation = self.state.get_object(result["obligation"])
        self.assertEqual(
            obligation["payload"]["subject"]["terms_hash"],
            self.formed["agreement"]["payload"]["terms_hash"],
        )
        self.assertEqual(obligation["payload"]["state"], "pending")

    def test_subject_naming_a_term_outside_the_terms_is_refused(self):
        result = self.issue(term_path="$.invoice.total")
        self.assertEqual(result["outcome"], "refused")
        self.assertIn("A202-OBLIGATION-SUBJECT-UNREFERENCED", result["reason_codes"])

    def test_unregistered_due_condition_fails_closed(self):
        result = self.issue(
            due_condition={"type": "due_when_convenient", "at": "2026-09-01T00:00:00Z"}
        )
        self.assertIn("A202-OBLIGATION-CONDITION-UNKNOWN", result["reason_codes"])

    def test_assertion_and_response_complete_the_exchange(self):
        obligation_id = self.issue()["obligation"]
        asserted = self.assert_performance(obligation_id)
        self.assertEqual(asserted["state"], "acceptance_pending")
        self.assertEqual(len(asserted["evidence_ids"]), 1)

        answered = self.respond(asserted["assertion"])
        self.assertEqual(answered["state"], "settlement_pending")
        response = self.state.get_object(answered["response"])
        assertion = self.state.get_object(asserted["assertion"])
        self.assertEqual(
            response["payload"]["assertion_hash"], assertion["content_hash"]
        )

        record = handle_get_transaction_record(self.state, TRANSACTION)
        self.assertEqual(record["chain"], "linked")
        self.assertEqual(
            [event["event_type"] for event in record["events"]],
            [
                "agreement.direct",
                "agreement.committed",
                "obligation.activated",
                "performance.declared",
                "acceptance.granted",
            ],
        )

    def test_assertion_with_no_evidence_is_refused(self):
        obligation_id = self.issue()["obligation"]
        result = self.assert_performance(obligation_id, evidence=[])
        self.assertEqual(result["outcome"], "refused")
        self.assertIn("A202-OBLIGATION-ASSERTION-UNEVIDENCED", result["reason_codes"])

    def test_a_response_signed_by_the_obligor_is_unauthorized(self):
        obligation_id = self.issue()["obligation"]
        asserted = self.assert_performance(obligation_id)
        # The obligor answers its own performance, under its own mandate and
        # inside its own scope, so nothing before the gate refuses it.
        result = self.respond(
            asserted["assertion"], responder=self.supplier, counterparty=self.buyer
        )
        self.assertEqual(result["outcome"], "refused")
        self.assertIn("A202-OBLIGATION-RESPONSE-UNAUTHORIZED", result["reason_codes"])

    def test_partial_acceptance_with_no_remainder_is_refused(self):
        obligation_id = self.issue()["obligation"]
        asserted = self.assert_performance(obligation_id)
        result = self.respond(
            asserted["assertion"], quantity="8", accepted_quantity="8"
        )
        self.assertIn("A202-OBLIGATION-REMAINDER-MISSING", result["reason_codes"])

    def test_rejection_carries_a_registered_reason_code(self):
        obligation_id = self.issue()["obligation"]
        asserted = self.assert_performance(obligation_id)
        unknown = self.respond(
            asserted["assertion"],
            response_type="reject",
            reason_code="did_not_like_it",
        )
        self.assertIn(
            "A202-OBLIGATION-REJECTION-REASON-UNKNOWN", unknown["reason_codes"]
        )

        registered = self.respond(
            asserted["assertion"],
            response_type="reject",
            reason_code="evidence_insufficient",
        )
        self.assertEqual(registered["state"], "in_performance")

    def test_an_unknown_act_is_refused(self):
        result = handle_record_obligation(self.state, act="discharge", decision={})
        self.assertEqual(result["outcome"], "refused")


if __name__ == "__main__":
    unittest.main()
