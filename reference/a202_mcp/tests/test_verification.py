"""verify_evidence and get_transaction_record over a party-held record."""

from __future__ import annotations

import copy
import tempfile
import unittest

from a202_mcp.state import LocalState
from a202_mcp.tools import (
    handle_get_transaction_record,
    handle_record_obligation,
    handle_verify_evidence,
)

from .support import (
    CONSIDERATION,
    DUE_CONDITION,
    EVIDENCE,
    TRANSACTION,
    committed_transaction,
    decision_for,
    obligation_decision,
)

from a202_mcp.transaction import assertion_act, response_act


def _performed(state, agreement_id, buyer, supplier):
    """The obligation exchange, each act carrying its own party's decision."""
    issued = handle_record_obligation(
        state,
        act="issue",
        agreement_id=agreement_id,
        obligor=supplier,
        obligee=buyer,
        term_path="$.terms.core.quantity",
        quantity="20",
        unit_code="H87",
        due_condition=DUE_CONDITION,
        consideration=CONSIDERATION,
        decision=obligation_decision(state, buyer, supplier, agreement_id),
    )
    asserted = handle_record_obligation(
        state,
        act="assert",
        obligation_id=issued["obligation"],
        obligor=supplier,
        obligee=buyer,
        asserted_quantity="20",
        evidence=EVIDENCE,
        decision=decision_for(
            state,
            supplier,
            assertion_act(issued["obligation"], TRANSACTION, buyer, "20", "H87",
                          CONSIDERATION),
        ),
    )
    handle_record_obligation(
        state,
        act="respond",
        assertion_id=asserted["assertion"],
        responder=buyer,
        counterparty=supplier,
        response_type="accept",
        decision=decision_for(
            state,
            buyer,
            response_act(asserted["assertion"], TRANSACTION, supplier, "accept",
                         "20", "H87", CONSIDERATION),
        ),
    )
    return issued, asserted


class VerifyEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.state, self.formed, buyer, supplier = committed_transaction()
        _performed(self.state, self.formed["agreement"]["id"], buyer, supplier)

    def test_a_complete_record_verifies_and_the_report_has_no_boolean(self):
        report = handle_verify_evidence(
            self.state, transaction_id=TRANSACTION, rules_version="1.3"
        )
        self.assertEqual(report["results"]["failed"], 0)
        self.assertGreater(report["results"]["verified"], 0)
        self.assertNotIn("passed", report)
        self.assertNotIn("ok", report)
        transitions = [
            check for check in report["checks"] if check["name"] == "transition_legality"
        ]
        self.assertEqual(len(transitions), 5)
        self.assertTrue(all(check["result"] == "verified" for check in transitions))

    def test_a_tampered_object_fails_at_step_one(self):
        objects = copy.deepcopy(self.state.objects_for(TRANSACTION))
        for obj in objects:
            if obj["object_type"] == "agreement":
                obj["payload"]["terms"]["core"]["total"]["amount"] = "1.00"
        report = handle_verify_evidence(
            self.state, objects=objects, rules_version="1.3"
        )
        codes = {
            check["code"] for check in report["checks"] if check["result"] == "failed"
        }
        self.assertIn("A202-EVIDENCE-HASH-MISMATCH", codes)

    def test_replay_against_a_version_that_never_registered_the_transition(self):
        report = handle_verify_evidence(
            self.state, transaction_id=TRANSACTION, rules_version="1.2"
        )
        illegal = [
            check
            for check in report["checks"]
            if check["code"] == "A202-EVIDENCE-TRANSITION-ILLEGAL"
        ]
        self.assertTrue(illegal)
        self.assertIn("draft to agreement_pending", illegal[0]["detail"])

    def test_without_a_stated_rules_version_transitions_are_not_checkable(self):
        report = handle_verify_evidence(self.state, transaction_id=TRANSACTION)
        transitions = [
            check for check in report["checks"] if check["name"] == "transition_legality"
        ]
        self.assertTrue(transitions)
        self.assertTrue(all(check["result"] == "not_checkable" for check in transitions))
        self.assertEqual(report["results"]["failed"], 0)

    def test_a_signature_whose_key_is_not_held_is_not_checkable(self):
        objects = copy.deepcopy(self.state.objects_for(TRANSACTION))
        stranger = LocalState()
        report = handle_verify_evidence(stranger, objects=objects, rules_version="1.3")
        self.assertEqual(report["results"]["failed"], 0)
        self.assertGreater(report["results"]["not_checkable"], 0)

    def test_nothing_disclosed_is_refused_rather_than_reported_as_verified(self):
        report = handle_verify_evidence(LocalState())
        self.assertEqual(report["outcome"], "refused")


class TransactionRecordTest(unittest.TestCase):
    def test_the_record_is_one_chain_and_states_where_it_stands(self):
        state, formed, buyer, supplier = committed_transaction()
        _performed(state, formed["agreement"]["id"], buyer, supplier)
        record = handle_get_transaction_record(state, TRANSACTION)
        self.assertEqual(record["chain"], "linked")
        self.assertEqual(record["chain_refusal"], None)
        self.assertEqual(record["state"], "settlement_pending")
        self.assertIsNone(record["events"][0]["previous_event_hash"])
        for earlier, later in zip(record["events"], record["events"][1:]):
            self.assertEqual(later["previous_event_hash"], earlier["content_hash"])
            self.assertEqual(later["sequence"], earlier["sequence"] + 1)

    def test_a_broken_link_is_reported_as_a_chain_gap(self):
        state, formed, buyer, supplier = committed_transaction()
        record = handle_get_transaction_record(state, TRANSACTION)
        second = state.get_object(record["events"][1]["event_id"])
        second["payload"]["previous_event_hash"] = "0" * 64
        state.put_object(second)
        broken = handle_get_transaction_record(state, TRANSACTION)
        self.assertEqual(broken["chain"], "broken")
        self.assertEqual(broken["chain_refusal"], "A202-EVIDENCE-CHAIN-GAP")

    def test_a_record_survives_a_restart_and_stays_verifiable(self):
        with tempfile.TemporaryDirectory() as directory:
            state, formed, buyer, supplier = committed_transaction(LocalState(directory))
            reopened = LocalState(directory)
            record = handle_get_transaction_record(reopened, TRANSACTION)
            self.assertEqual(record["state"], "committed")
            report = handle_verify_evidence(
                reopened, transaction_id=TRANSACTION, rules_version="1.3"
            )
            self.assertEqual(report["results"]["failed"], 0)


if __name__ == "__main__":
    unittest.main()
