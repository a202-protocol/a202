"""Canonicalization agrees with the specification and with the runner."""

import json
import unittest

from a202_reference.canonical import canonical_bytes, canonicalize, content_hash

from .support import FIXTURES, runner


class CanonicalizationTest(unittest.TestCase):
    def test_member_ordering_and_compact_form(self):
        value = {"b": 1, "a": {"y": None, "x": [True, False]}}
        self.assertEqual(canonicalize(value), '{"a":{"x":[true,false],"y":null},"b":1}')

    def test_string_escaping(self):
        self.assertEqual(canonicalize({"k": 'a"b\\c\n'}), '{"k":"a\\"b\\\\c\\n"}')
        self.assertEqual(canonicalize({"k": "\x01"}), '{"k":"\\u0001"}')

    def test_utf16_code_unit_ordering(self):
        # A supplementary-plane character sorts by its surrogate pair under
        # RFC 8785, which places it before U+FF01 despite the higher code
        # point. Python's native string order would sort these the other way.
        value = {"！": 1, "\U0001d306": 2}
        self.assertEqual(canonicalize(value), '{"\U0001d306":2,"！":1}')

    def test_floats_refused(self):
        with self.assertRaises(ValueError):
            canonicalize({"amount": 10.5})

    def test_integers_pass(self):
        self.assertEqual(canonicalize({"version": 3}), '{"version":3}')

    def test_agreement_with_runner_on_fixtures(self):
        for name in (
            "valid-offer.json",
            "valid-obligation.json",
            "valid-settlement-instruction.json",
        ):
            with self.subTest(fixture=name):
                doc = json.loads((FIXTURES / name).read_text())
                self.assertEqual(canonical_bytes(doc), runner.canonical_bytes(doc))
                self.assertEqual(content_hash(doc), runner.content_hash_of(doc))

    def test_bundle_fixture_hashes_recompute(self):
        # Bundle fixtures carry real content hashes, so recomputation must
        # reproduce the declared value for objects the fixture marks valid.
        doc = json.loads(
            (FIXTURES / "negative" / "obligation-subject-terms-hash-mismatch.json").read_text()
        )
        first = doc["objects"][0]
        self.assertEqual(content_hash(first), first["content_hash"])


if __name__ == "__main__":
    unittest.main()
