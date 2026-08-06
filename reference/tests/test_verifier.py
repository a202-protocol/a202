"""The seven-step verifier: verified, failed, and not checkable, each where
the procedure says it belongs."""

import copy
import unittest

from a202_reference.emission import make_object
from a202_reference.signing import generate_key, public_key_of, sign_object
from a202_reference.verifier import verify_bundle

from .support import runner

CREATED_BY = {
    "organization_id": "org_delta",
    "agent_id": "agt_delta_supplier_01",
    "mandate_id": "mnd_delta_supplier_01",
}
TXN = "txn_reference_test_01"


def _mini_bundle():
    """An obligation, an evidence object, an assertion referencing it, and a
    response binding the assertion hash. All signed with one test key."""
    key = generate_key()
    keys = {}

    def sign(obj, purpose):
        entry = sign_object(obj, key, "key_reference_test_01", purpose)
        obj["signatures"].append(entry)
        keys["key_reference_test_01"] = public_key_of(key)

    evidence = make_object(
        "evidence",
        {"evidence_type": "attestation", "statement": "delivery attested"},
        CREATED_BY,
        TXN,
    )
    sign(evidence, "object_issuance")

    obligation = make_object(
        "obligation", {"state": "due", "note": "synthetic"}, CREATED_BY, TXN
    )
    sign(obligation, "object_issuance")

    assertion = make_object(
        "performance_event",
        {
            "obligation_id": obligation["id"],
            "asserted_quantity": "10",
            "unit_code": "EA",
            "evidence_refs": [
                {
                    "evidence_id": evidence["id"],
                    "content_hash": evidence["content_hash"],
                    "evidence_type": "attestation",
                    "signed_by": {"organization_id": "org_delta"},
                }
            ],
        },
        CREATED_BY,
        TXN,
    )
    sign(assertion, "object_issuance")

    response = make_object(
        "obligation_response",
        {
            "obligation_id": obligation["id"],
            "response_type": "accept",
            "assertion_id": assertion["id"],
            "assertion_hash": assertion["content_hash"],
            "accepted_quantity": "10",
        },
        CREATED_BY,
        TXN,
    )
    sign(response, "object_issuance")

    return [evidence, obligation, assertion, response], keys


class VerifierTest(unittest.TestCase):
    def test_valid_bundle_verifies_and_report_has_no_boolean(self):
        objects, keys = _mini_bundle()
        report = verify_bundle(objects, keys)
        results = report.results()
        self.assertEqual(results["failed"], 0)
        self.assertGreater(results["verified"], 0)
        self.assertFalse(hasattr(report, "passed"))
        self.assertFalse(hasattr(report, "ok"))

    def test_tampered_object_fails_step_one(self):
        objects, keys = _mini_bundle()
        objects = copy.deepcopy(objects)
        objects[1]["payload"]["note"] = "tampered after signing"
        report = verify_bundle(objects, keys)
        codes = {check.code for check in report.checks if check.result == "failed"}
        self.assertIn("A202-EVIDENCE-HASH-MISMATCH", codes)

    def test_response_binding_detects_swapped_assertion(self):
        objects, keys = _mini_bundle()
        objects = copy.deepcopy(objects)
        objects[3]["payload"]["assertion_hash"] = "0" * 64
        objects[3]["content_hash"] = runner.content_hash_of(objects[3])
        report = verify_bundle(objects, keys)
        failed = [c for c in report.checks if c.name == "assertion_hash_binding"]
        self.assertEqual(failed[0].result, "failed")

    def test_version_fork_is_a_chain_gap(self):
        objects, keys = _mini_bundle()
        base = objects[1]
        fork_a = make_object(
            "obligation", dict(base["payload"]), CREATED_BY, TXN,
            previous_version_id=base["id"], version=2,
        )
        fork_b = make_object(
            "obligation", dict(base["payload"], note="rival successor"), CREATED_BY, TXN,
            previous_version_id=base["id"], version=2,
        )
        report = verify_bundle(objects + [fork_a, fork_b], keys)
        codes = {check.code for check in report.checks if check.result == "failed"}
        self.assertIn("A202-EVIDENCE-CHAIN-GAP", codes)

    def test_unresolvable_rules_version_is_not_checkable_never_verified(self):
        determination = make_object(
            "determination",
            {
                "dispute_id": "dsp_not_in_bundle_01",
                "question": {
                    "subject_type": "act",
                    "subject_hash": "1" * 64,
                    "subject_id": "act_synthetic_01",
                    "rules_ref": {"rule_set_id": "a202-rules/none", "version": "9.9"},
                },
                "outcome": {
                    "finding": "synthetic",
                    "rules_applied": ["a202-rules/pilot#state.transition-legality"],
                    "evidence_relied_on": [],
                    "inputs_hash": "2" * 64,
                    "state_result": None,
                },
                "determiner": {"organization_id": "org_meridian"},
                "effect": "binding",
            },
            CREATED_BY,
            TXN,
        )
        report = verify_bundle([determination], rules_resolver=runner.resolve_rules)
        step6 = [c for c in report.checks if c.step == 6]
        self.assertTrue(step6)
        self.assertTrue(all(c.result == "not_checkable" for c in step6))

    def test_effect_overclaim_fails_against_resolved_rules(self):
        # The pilot rule set grants presumptive on obligation_state, so a
        # binding claim on that class must fail with the overclaim code.
        rules_ref = {
            "rule_set_id": "a202-rules/pilot",
            "version": "1.0",
            "rules_hash": runner.RULE_SETS[("a202-rules/pilot", "1.0")]["rules_hash"],
        }
        determination = make_object(
            "determination",
            {
                "dispute_id": "dsp_not_in_bundle_01",
                "question": {
                    "subject_type": "obligation_state",
                    "subject_hash": "1" * 64,
                    "subject_id": "obl_synthetic_01",
                    "rules_ref": rules_ref,
                },
                "outcome": {
                    "finding": "synthetic",
                    "rules_applied": ["a202-rules/pilot#state.transition-legality"],
                    "evidence_relied_on": [],
                    "inputs_hash": "2" * 64,
                    "state_result": None,
                },
                "determiner": {"organization_id": "org_meridian"},
                "effect": "binding",
            },
            CREATED_BY,
            TXN,
        )
        report = verify_bundle([determination], rules_resolver=runner.resolve_rules)
        codes = {check.code for check in report.checks if check.result == "failed"}
        self.assertIn("A202-DETERMINATION-EFFECT-OVERCLAIM", codes)

    def test_unresolved_evidence_reference_is_scope_not_failure(self):
        objects, keys = _mini_bundle()
        objects = copy.deepcopy(objects)
        objects[2]["payload"]["evidence_refs"].append(
            {
                "evidence_id": "evd_undisclosed_01",
                "content_hash": "3" * 64,
                "evidence_type": "attestation",
                "signed_by": {"organization_id": "org_delta"},
            }
        )
        objects[2]["content_hash"] = runner.content_hash_of(objects[2])
        report = verify_bundle(objects, keys)
        self.assertIn("evd_undisclosed_01", report.unresolved_references)
        resolves = [
            c for c in report.checks
            if c.name == "evidence_resolves" and c.subject == "evd_undisclosed_01"
        ]
        self.assertEqual(resolves[0].result, "not_checkable")


if __name__ == "__main__":
    unittest.main()
