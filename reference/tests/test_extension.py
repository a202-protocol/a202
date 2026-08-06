"""Carrier extension declaration handling: one refusal, four ways in."""

import unittest

from a202_reference.extension import (
    A202_EXTENSION_UNSUPPORTED,
    COMMERCIAL_EXTENSION_URI,
    build_declaration,
    check_counterparty,
)


def _own():
    return build_declaration(read_versions=["0.1"], write_version="0.1")


class ExtensionDeclarationTest(unittest.TestCase):
    def test_compatible_declarations_proceed(self):
        self.assertIsNone(check_counterparty(_own(), [_own()]))

    def test_missing_entry_fails_closed(self):
        other = {"uri": "https://example.invalid/some-other-extension"}
        self.assertEqual(
            check_counterparty(_own(), [other]), A202_EXTENSION_UNSUPPORTED
        )

    def test_unparseable_version_declaration_fails_closed(self):
        entry = {
            "uri": COMMERCIAL_EXTENSION_URI,
            "params": {"read_versions": [], "write_version": "zero.one"},
        }
        self.assertEqual(
            check_counterparty(_own(), [entry]), A202_EXTENSION_UNSUPPORTED
        )

    def test_version_mismatch_fails_closed_with_no_nearest_match(self):
        entry = build_declaration(read_versions=["0.2"], write_version="0.2")
        self.assertEqual(
            check_counterparty(_own(), [entry]), A202_EXTENSION_UNSUPPORTED
        )

    def test_unretrievable_surface_fails_closed(self):
        # Unavailability is not permission: a party that cannot be checked
        # has not passed the check.
        self.assertEqual(check_counterparty(_own(), None), A202_EXTENSION_UNSUPPORTED)

    def test_a_party_never_writes_what_it_cannot_read(self):
        with self.assertRaises(ValueError):
            build_declaration(read_versions=["0.1"], write_version="0.2")


if __name__ == "__main__":
    unittest.main()
