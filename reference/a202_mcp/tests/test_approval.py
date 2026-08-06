"""issue_approval, and the approval binding verify_mandate enforces."""

from __future__ import annotations

import unittest

from a202_mcp.state import LocalState
from a202_mcp.tools import (
    handle_issue_approval,
    handle_issue_mandate,
    handle_verify_mandate,
)

from .support import BUYER, TRANSACTION, mandate_arguments, proposed_action, stamp

APPROVAL_RULE = {
    "id": "a_large_commitment",
    "when": {
        "path": "$.proposed_terms.core.total.amount",
        "operator": "minimum",
        "value": "3000.00",
    },
    "approver": {
        "organization_id": "org_northstar",
        "role": "procurement_director",
    },
    "expires_after_seconds": 3600,
}

APPROVER = {
    "principal_id": "prn_northstar_procurement_director",
    "role": "procurement_director",
    "key_id": "key_northstar_principal_01",
}


def _fresh_status() -> dict:
    return {"status": "active", "retrieved_at": stamp()}


class ApprovalTest(unittest.TestCase):
    def setUp(self):
        self.state = LocalState()
        issued = handle_issue_mandate(
            self.state, **mandate_arguments(approval_rules=[APPROVAL_RULE])
        )
        self.mandate = issued["mandate"]
        self.requested_by = dict(BUYER, mandate_id=issued["mandate_id"])

    def _verify(self, action=None, **overrides):
        return handle_verify_mandate(
            self.state,
            mandate=self.mandate,
            status=_fresh_status(),
            proposed_action=action or proposed_action(),
            **overrides,
        )

    def _approve(self, action_hash, **overrides):
        arguments = {
            "transaction_id": TRANSACTION,
            "action_hash": action_hash,
            "requested_by": self.requested_by,
            "approver": APPROVER,
        }
        arguments.update(overrides)
        return handle_issue_approval(self.state, **arguments)

    def test_a_held_act_reports_the_hash_an_approval_must_bind(self):
        held = self._verify()
        self.assertEqual(held["decision"], "require_approval")
        self.assertIn("A202-APPROVAL-REQUIRED", held["reason_codes"])
        self.assertEqual(held["approval_rules_matched"], ["a_large_commitment"])
        self.assertEqual(len(held["action_hash"]), 64)
        self.assertEqual(held["approval"], "not_presented")

    def test_an_approval_over_the_exact_act_releases_the_hold(self):
        held = self._verify()
        approval = self._approve(held["action_hash"])
        self.assertEqual(approval["outcome"], "recorded")
        self.assertEqual(approval["action_hash"], held["action_hash"])

        allowed = self._verify(approval_id=approval["approval_id"])
        self.assertEqual(allowed["decision"], "allow")
        self.assertEqual(allowed["approval"], "verified")
        self.assertEqual(allowed["reason_codes"], [])

    def test_an_approval_over_a_different_act_does_not_release_it(self):
        # One byte of the act changes the hash, and the approval no longer
        # binds the act being taken.
        other = self._verify(action=proposed_action(amount="3100.00"))
        approval = self._approve(other["action_hash"])
        held = self._verify(approval_id=approval["approval_id"])
        self.assertEqual(held["decision"], "require_approval")
        self.assertEqual(held["approval"], "failed")
        self.assertIn("A202-APPROVAL-HASH-MISMATCH", held["reason_codes"])

    def test_an_expired_approval_authorizes_nothing(self):
        held = self._verify()
        approval = self._approve(held["action_hash"], expires_after_seconds=1)
        later = handle_verify_mandate(
            self.state,
            mandate=self.mandate,
            at=stamp(1),
            status={"status": "active", "retrieved_at": stamp(1)},
            proposed_action=proposed_action(),
            approval_id=approval["approval_id"],
        )
        self.assertEqual(later["decision"], "require_approval")
        self.assertIn("A202-APPROVAL-REQUIRED", later["reason_codes"])

    def test_an_approval_from_an_unnamed_role_does_not_release_it(self):
        held = self._verify()
        approval = self._approve(
            held["action_hash"],
            approver=dict(APPROVER, role="office_manager"),
        )
        still_held = self._verify(approval_id=approval["approval_id"])
        self.assertEqual(still_held["decision"], "require_approval")
        self.assertEqual(still_held["approval"], "failed")

    def test_a_rejected_approval_releases_nothing(self):
        held = self._verify()
        approval = self._approve(held["action_hash"], decision="rejected")
        still_held = self._verify(approval_id=approval["approval_id"])
        self.assertEqual(still_held["decision"], "require_approval")

    def test_an_approval_never_releases_a_deny(self):
        # The act is over the mandate's spending limit, which is a limit
        # rather than a question, so no approval reaches it.
        over = self._verify(action=proposed_action(amount="9000.00"))
        self.assertEqual(over["decision"], "deny")
        approval = self._approve(over["action_hash"])
        still_denied = self._verify(
            action=proposed_action(amount="9000.00"),
            approval_id=approval["approval_id"],
        )
        self.assertEqual(still_denied["decision"], "deny")
        self.assertIn("A202-POLICY-DENIED", still_denied["reason_codes"])

    def test_an_approval_identifier_that_resolves_to_nothing_is_refused(self):
        result = self._verify(approval_id="apr_not_held_01")
        self.assertEqual(result["outcome"], "refused")
        self.assertIn("A202-APPROVAL-REQUIRED", result["reason_codes"])

    def test_an_approval_is_a_signed_object_the_gate_accepts(self):
        held = self._verify()
        approval_id = self._approve(held["action_hash"])["approval_id"]
        approval = self.state.get_object(approval_id)
        self.assertEqual(approval["object_type"], "approval")
        self.assertEqual(
            [entry["key_id"] for entry in approval["signatures"]],
            [APPROVER["key_id"]],
        )
        self.assertNotEqual(approval["signatures"][0]["key_id"], BUYER["key_id"])

    def test_a_malformed_action_hash_is_refused_rather_than_recorded(self):
        result = self._approve("not-a-hash")
        self.assertEqual(result["outcome"], "refused")
        self.assertTrue(result["reason_codes"])


if __name__ == "__main__":
    unittest.main()
