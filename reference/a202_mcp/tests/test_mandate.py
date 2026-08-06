"""issue_mandate and verify_mandate, in the allow and the refuse direction."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest

from a202_mcp import gate
from a202_mcp.state import LocalState
from a202_mcp.tools import handle_issue_mandate, handle_verify_mandate

from .support import mandate_arguments, proposed_action, stamp


def _issued(state, **overrides):
    return handle_issue_mandate(state, **mandate_arguments(**overrides))


def _fresh_status(status: str = "active") -> dict:
    return {"status": status, "retrieved_at": stamp()}


class IssueMandateTest(unittest.TestCase):
    def test_issued_mandate_passes_the_published_gate(self):
        state = LocalState()
        result = _issued(state)
        self.assertEqual(result["outcome"], "issued")
        mandate = result["mandate"]
        self.assertEqual(mandate["spec_version"], gate.MANDATE_SPEC_VERSION)
        self.assertEqual(gate.mandate_refusals(mandate), ([], []))
        self.assertEqual(mandate["proof"]["purpose"], "mandate_issuance")

    def test_spending_limit_becomes_an_amount_and_a_currency_constraint(self):
        state = LocalState()
        constraints = _issued(state)["mandate"]["constraints"]
        operators = {(item["operator"], item["path"]) for item in constraints}
        self.assertIn(("maximum", "$.proposed_terms.core.total.amount"), operators)
        self.assertIn(("equals", "$.proposed_terms.core.total.currency"), operators)

    def test_scope_bounded_only_by_geography_is_refused(self):
        state = LocalState()
        result = _issued(state, scope={"geographies": ["NL"]})
        self.assertEqual(result["outcome"], "refused")
        self.assertIn("A202-MANDATE-SCOPE-TOO-BROAD", result["reason_codes"])

    def test_mandate_with_no_constraint_is_refused(self):
        state = LocalState()
        result = _issued(state, spending_limit=None, constraints=[])
        self.assertIn("A202-MANDATE-UNBOUNDED", result["reason_codes"])

    def test_status_endpoint_over_plain_http_is_refused(self):
        state = LocalState()
        result = _issued(state, status_endpoint="http://status.a202.invalid/one")
        self.assertIn("A202-MANDATE-STATUS-INSECURE", result["reason_codes"])

    def test_no_private_key_material_is_returned_or_written(self):
        with tempfile.TemporaryDirectory() as directory:
            state = LocalState(directory)
            rendered = json.dumps(_issued(state))
            self.assertNotIn("PRIVATE", rendered)
            written = "".join(
                path.read_text(errors="ignore")
                for path in state.state_dir.rglob("*")
                if path.is_file()
            )
            self.assertNotIn("PRIVATE KEY", written)


class VerifyMandateTest(unittest.TestCase):
    def setUp(self):
        self.state = LocalState()
        self.mandate = _issued(self.state)["mandate"]

    def test_presented_mandate_and_act_within_it_are_allowed(self):
        report = handle_verify_mandate(
            self.state,
            mandate=self.mandate,
            status=_fresh_status(),
            proposed_action=proposed_action(),
        )
        self.assertEqual(report["proof"], "verified")
        self.assertEqual(report["decision"], "allow")
        self.assertEqual(report["reason_codes"], [])

    def test_act_over_the_spending_limit_is_denied(self):
        report = handle_verify_mandate(
            self.state,
            mandate=self.mandate,
            status=_fresh_status(),
            proposed_action=proposed_action(amount="5000.00"),
        )
        self.assertEqual(report["decision"], "deny")
        self.assertIn("A202-POLICY-DENIED", report["reason_codes"])
        unsatisfied = [
            item for item in report["constraints"] if item["result"] == "unsatisfied"
        ]
        self.assertEqual([item["id"] for item in unsatisfied], ["c_total_amount"])

    def test_act_the_mandate_does_not_name_is_denied(self):
        report = handle_verify_mandate(
            self.state,
            mandate=self.mandate,
            status=_fresh_status(),
            proposed_action=proposed_action(action_type="settlement.instruct"),
        )
        self.assertEqual(report["decision"], "deny")
        self.assertIn("A202-POLICY-DENIED", report["reason_codes"])

    def test_counterparty_outside_scope_is_denied(self):
        report = handle_verify_mandate(
            self.state,
            mandate=self.mandate,
            status=_fresh_status(),
            proposed_action=proposed_action(counterparty_organization_id="org_meridian"),
        )
        self.assertEqual(report["decision"], "deny")

    def test_unresolved_status_is_not_permission(self):
        report = handle_verify_mandate(self.state, mandate=self.mandate)
        self.assertEqual(report["decision"], "deny")
        self.assertIn("A202-MANDATE-STATUS-UNRESOLVED", report["reason_codes"])

    def test_stale_status_result_is_no_status_result(self):
        report = handle_verify_mandate(
            self.state,
            mandate=self.mandate,
            status={"status": "active", "retrieved_at": stamp(-2)},
        )
        self.assertIn("A202-MANDATE-STATUS-UNRESOLVED", report["reason_codes"])

    def test_revoked_mandate_is_inactive(self):
        report = handle_verify_mandate(
            self.state, mandate=self.mandate, status=_fresh_status("revoked")
        )
        self.assertEqual(report["decision"], "deny")
        self.assertIn("A202-MANDATE-INACTIVE", report["reason_codes"])

    def test_expired_interval_is_inactive(self):
        report = handle_verify_mandate(
            self.state,
            mandate=self.mandate,
            at=stamp(48),
            status=_fresh_status(),
        )
        self.assertEqual(report["validity_interval"], "failed")
        self.assertIn("A202-MANDATE-INACTIVE", report["reason_codes"])

    def test_an_action_added_after_signing_breaks_the_proof(self):
        tampered = copy.deepcopy(self.mandate)
        tampered["actions"].append("settlement.instruct")
        report = handle_verify_mandate(
            self.state, mandate=tampered, status=_fresh_status()
        )
        self.assertEqual(report["proof"], "failed")
        self.assertIn("A202-EVIDENCE-SIGNATURE-INVALID", report["reason_codes"])

    def test_approval_rule_holds_the_act_rather_than_denying_it(self):
        state = LocalState()
        mandate = _issued(
            state,
            approval_rules=[
                {
                    "id": "a_new_counterparty",
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
            ],
        )["mandate"]
        report = handle_verify_mandate(
            state,
            mandate=mandate,
            status=_fresh_status(),
            proposed_action=proposed_action(),
        )
        self.assertEqual(report["decision"], "require_approval")
        self.assertIn("A202-APPROVAL-REQUIRED", report["reason_codes"])

    def test_unregistered_constraint_operator_denies_at_evaluation(self):
        # The schema refuses this too. Both layers must fail closed on their
        # own, so the evaluator is checked against a document the schema layer
        # never saw.
        mandate = copy.deepcopy(self.mandate)
        mandate["constraints"][0]["operator"] = "approximately"
        report = handle_verify_mandate(
            self.state,
            mandate=mandate,
            status=_fresh_status(),
            proposed_action=proposed_action(),
        )
        self.assertIn("A202-MANDATE-CONSTRAINT-UNKNOWN", report["reason_codes"])
        self.assertEqual(report["decision"], "deny")


if __name__ == "__main__":
    unittest.main()
