"""create_agreement: the direct bilateral formation path, and its refusals."""

from __future__ import annotations

import copy
import unittest

from a202_mcp.state import LocalState
from a202_mcp.tools import handle_create_agreement, handle_get_transaction_record

from .support import TERMS, TRANSACTION, formation_decisions, parties, stamp


class CreateAgreementTest(unittest.TestCase):
    def setUp(self):
        self.state = LocalState()
        self.buyer, self.supplier = parties(self.state)

    def arguments(self, terms=None, **overrides):
        terms = terms or TERMS
        arguments = {
            "transaction_id": TRANSACTION,
            "buyer": self.buyer,
            "supplier": self.supplier,
            "terms": terms,
            "offer_valid_until": stamp(12),
        }
        arguments.update(
            formation_decisions(self.state, self.buyer, self.supplier, terms)
        )
        arguments.update(overrides)
        return arguments

    def test_direct_formation_reaches_committed_with_no_operator(self):
        result = handle_create_agreement(self.state, **self.arguments())
        self.assertEqual(result["outcome"], "recorded")
        self.assertEqual(result["state"], "committed")
        self.assertEqual(result["rules_version"], "1.3")

        record = handle_get_transaction_record(self.state, TRANSACTION)
        self.assertEqual(
            [event["event_type"] for event in record["events"]],
            ["agreement.direct", "agreement.committed"],
        )
        self.assertEqual(record["events"][0]["from_state"], "draft")
        self.assertEqual(record["events"][0]["to_state"], "agreement_pending")
        self.assertEqual(record["chain"], "linked")

    def test_the_offeror_mints_the_session_identifier_and_the_offeree_adopts_it(self):
        result = handle_create_agreement(self.state, **self.arguments())
        offer = self.state.get_object(result["offer_id"])
        acceptance = self.state.get_object(result["acceptance_id"])
        self.assertTrue(result["session_id"].startswith("ses_"))
        self.assertEqual(offer["payload"]["session_id"], result["session_id"])
        self.assertEqual(acceptance["payload"]["session_id"], result["session_id"])
        self.assertEqual(acceptance["payload"]["offer_hash"], offer["content_hash"])

    def test_the_agreement_carries_both_signatures_over_the_same_bytes(self):
        result = handle_create_agreement(self.state, **self.arguments())
        agreement = self.state.get_object(result["agreement_id"])
        signers = {entry["key_id"] for entry in agreement["signatures"]}
        self.assertEqual(signers, {self.buyer["key_id"], self.supplier["key_id"]})
        purposes = {entry["purpose"] for entry in agreement["signatures"]}
        self.assertEqual(purposes, {"agreement_commitment"})

    def test_every_event_carries_both_parties_signatures(self):
        handle_create_agreement(self.state, **self.arguments())
        record = handle_get_transaction_record(self.state, TRANSACTION)
        for event in record["events"]:
            self.assertEqual(
                set(event["signed_by"]),
                {self.buyer["key_id"], self.supplier["key_id"]},
            )

    def test_every_event_cites_the_decision_that_was_actually_made(self):
        handle_create_agreement(self.state, **self.arguments())
        record = handle_get_transaction_record(self.state, TRANSACTION)
        for event in record["events"]:
            recorded = self.state.get_object(event["policy_decision_id"])
            self.assertEqual(recorded["object_type"], "policy_decision")
            self.assertEqual(recorded["payload"]["decision"], "allow")
            self.assertEqual(recorded["payload"]["action_hash"], event["action_hash"])
            self.assertIn(
                recorded["payload"]["mandate_ids"][0],
                {self.buyer["mandate_id"], self.supplier["mandate_id"]},
            )

    def test_the_offerors_own_decision_is_in_the_record(self):
        handle_create_agreement(self.state, **self.arguments())
        decisions = [
            obj for obj in self.state.objects_for(TRANSACTION)
            if obj["object_type"] == "policy_decision"
        ]
        mandates = {obj["payload"]["mandate_ids"][0] for obj in decisions}
        self.assertEqual(
            mandates, {self.buyer["mandate_id"], self.supplier["mandate_id"]}
        )

    def test_a_second_formation_on_one_transaction_is_refused(self):
        handle_create_agreement(self.state, **self.arguments())
        again = handle_create_agreement(self.state, **self.arguments())
        self.assertEqual(again["outcome"], "refused")
        self.assertIn("A202-STATE-TRANSITION-DENIED", again["reason_codes"])

    def test_direct_formation_under_an_earlier_rules_version_is_refused(self):
        # Rules versions 1.0 to 1.2 are immutable and never registered this
        # transition, so a record cannot be written under one of them.
        result = handle_create_agreement(
            self.state, **self.arguments(rules_version="1.2")
        )
        self.assertEqual(result["outcome"], "refused")
        self.assertIn("A202-STATE-TRANSITION-DENIED", result["reason_codes"])

    def test_unregistered_profile_fails_closed(self):
        terms = copy.deepcopy(TERMS)
        terms["profile"] = "a202-profile/unregistered/9.9"
        result = handle_create_agreement(self.state, **self.arguments(terms=terms))
        self.assertIn("A202-PROFILE-UNKNOWN", result["reason_codes"])

    def test_terms_outside_the_named_profile_are_refused(self):
        terms = copy.deepcopy(TERMS)
        terms["profile_terms"]["payment"]["prepayment_percent"] = "not a percentage"
        result = handle_create_agreement(self.state, **self.arguments(terms=terms))
        self.assertEqual(result["outcome"], "refused")
        self.assertIn("A202-PROFILE-TERMS-INVALID", result["reason_codes"])

    def test_an_offer_expiring_before_it_was_made_is_refused(self):
        result = handle_create_agreement(
            self.state, **self.arguments(offer_valid_until=stamp(-12))
        )
        self.assertIn("A202-OFFER-EXPIRED", result["reason_codes"])

    def test_a_refusal_carries_codes_and_keeps_validator_prose_out_of_them(self):
        terms = copy.deepcopy(TERMS)
        terms["core"]["quantity"] = "twenty"
        result = handle_create_agreement(self.state, **self.arguments(terms=terms))
        self.assertEqual(result["outcome"], "refused")
        for code in result["reason_codes"]:
            self.assertTrue(code.startswith("A202-"), code)
        self.assertTrue(result["detail"])


if __name__ == "__main__":
    unittest.main()
