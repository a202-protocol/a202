"""Objects emitted by this package are judged by the published gate.

Each test takes a payload from a published positive fixture, re-emits it on
a fresh envelope through this package, signs it, and then applies the same
kernel schema and the same normative checks the conformance runner applies.
Passing here means the emission path produces objects the public gate
accepts, not merely objects this package likes.
"""

from __future__ import annotations

import json
import unittest

from a202_reference.emission import PREFIXES, make_object, new_id
from a202_reference.schemas import SchemaSet
from a202_reference.signing import generate_key, sign_object

from .support import FIXTURES, runner

SCHEMAS = SchemaSet()
PROFILES = runner.profile_registry()
REGISTRY = runner.build_registry()


def _reemit(fixture_name: str, purpose: str, object_type: str | None = None) -> dict:
    source = json.loads((FIXTURES / fixture_name).read_text())
    if "objects" in source:
        # A bundle fixture: take the named object out of it.
        source = next(
            item for item in source["objects"] if item["object_type"] == object_type
        )
    obj = make_object(
        source["object_type"],
        source["payload"],
        source["created_by"],
        source["transaction_id"],
    )
    key = generate_key()
    obj["signatures"].append(sign_object(obj, key, "key_reference_test_01", purpose))
    return obj


class EmissionTest(unittest.TestCase):
    def test_new_id_uses_registered_prefixes(self):
        for object_type, prefix in PREFIXES.items():
            self.assertTrue(new_id(object_type).startswith(prefix))

    def test_unregistered_type_refused(self):
        with self.assertRaises(ValueError):
            new_id("audit_bundle")

    def test_emitted_obligation_passes_the_public_gate(self):
        obj = _reemit("valid-obligation.json", "object_issuance")
        self.assertEqual(SCHEMAS.kernel_errors(obj), [])
        self.assertEqual(
            runner.normative_checks(obj, "kernel", PROFILES, REGISTRY), []
        )

    def test_emitted_settlement_instruction_passes_the_public_gate(self):
        obj = _reemit(
            "valid-settlement-instruction.json",
            "object_issuance",
            object_type="settlement_instruction",
        )
        self.assertEqual(SCHEMAS.kernel_errors(obj), [])
        self.assertEqual(
            runner.normative_checks(obj, "kernel", PROFILES, REGISTRY), []
        )

    def test_profile_resolution_fails_closed(self):
        self.assertIsNone(SCHEMAS.resolve_profile("a202-profile/unregistered/9.9"))
        self.assertIsNone(
            SCHEMAS.profile_terms_errors("a202-profile/unregistered/9.9", {})
        )


if __name__ == "__main__":
    unittest.main()
