"""Signature creation and verification round trips, and the failure modes."""

import unittest

from a202_reference.emission import make_object
from a202_reference.signing import (
    SYNTHETIC_SIGNATURE_VALUE,
    generate_key,
    public_key_of,
    sign_object,
    verify_signature,
)

CREATED_BY = {
    "organization_id": "org_northstar",
    "agent_id": "agt_northstar_buyer_01",
    "mandate_id": "mnd_northstar_buyer_01",
}


def _signed_obligation():
    obj = make_object(
        "obligation",
        {"note": "test payload; schema validity is exercised elsewhere"},
        CREATED_BY,
        "txn_reference_test_01",
    )
    key = generate_key()
    entry = sign_object(obj, key, "key_reference_test_01", "object_issuance")
    obj["signatures"].append(entry)
    return obj, entry, public_key_of(key)


class SignatureTest(unittest.TestCase):
    def test_round_trip_verifies(self):
        obj, entry, public = _signed_obligation()
        self.assertEqual(
            verify_signature(obj, entry, public, {"object_issuance"}), "verified"
        )

    def test_tampered_byte_fails(self):
        obj, entry, public = _signed_obligation()
        obj["payload"]["note"] = "tampered"
        self.assertEqual(
            verify_signature(obj, entry, public, {"object_issuance"}), "failed"
        )

    def test_wrong_purpose_fails_despite_valid_cryptography(self):
        obj, entry, public = _signed_obligation()
        self.assertEqual(
            verify_signature(obj, entry, public, {"offer_submission"}), "failed"
        )

    def test_relabeled_purpose_fails_at_the_cryptographic_layer(self):
        # The protected members are inside the signed bytes. A signature whose
        # purpose is rewritten after signing must fail even when no expected
        # purpose set is supplied, because otherwise a valid signature could be
        # presented as a signature for a different act.
        obj, entry, public = _signed_obligation()
        relabeled = dict(entry, purpose="agreement_commitment")
        self.assertEqual(verify_signature(obj, relabeled, public, None), "failed")

    def test_backdated_signed_at_fails_at_the_cryptographic_layer(self):
        # signed_at is a protected member for the same reason: key status is
        # resolved at the signed time, and an unprotected timestamp could be
        # backdated to before a revocation.
        obj, entry, public = _signed_obligation()
        backdated = dict(entry, signed_at="2020-01-01T00:00:00Z")
        self.assertEqual(verify_signature(obj, backdated, public, None), "failed")

    def test_synthetic_placeholder_is_not_checkable(self):
        obj, entry, public = _signed_obligation()
        entry = dict(entry, signature=SYNTHETIC_SIGNATURE_VALUE)
        self.assertEqual(
            verify_signature(obj, entry, public, {"object_issuance"}), "not_checkable"
        )

    def test_unresolvable_key_is_not_checkable_never_verified(self):
        obj, entry, _ = _signed_obligation()
        self.assertEqual(
            verify_signature(obj, entry, None, {"object_issuance"}), "not_checkable"
        )


if __name__ == "__main__":
    unittest.main()
