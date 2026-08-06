"""Sweep every evidence-bundle fixture through the reference verifier.

Informative tooling, not a normative check. The conformance runner is the
normative layer and the manifest is the source for what the suite contains;
this test asks a different question, which is whether the reference reading of
the seven-step procedure agrees with the manifest on the fixtures the procedure
covers. It routes each bundle through `a202_reference.verifier` directly rather
than through the runner subprocess, so a disagreement between the two readings
shows up here rather than in a passing suite.

Two things are deliberately not asserted. A bundle whose offence lies outside
the procedure is skipped with a stated reason and counted, because a test that
silently ignored two thirds of the set would report agreement it had not
established. And a positive bundle is asserted to produce no failed check
rather than to produce a verified one for everything: signatures in the fixture
set carry the synthetic placeholder value and keys are not distributed with the
fixtures, so those checks are correctly not_checkable, which is the third value
existing for exactly this case.
"""

import json
import unittest

from a202_reference.verifier import verify_bundle

from .support import FIXTURES, REPO_ROOT, runner

# The refusals the seven-step procedure implements, mapped to the check codes
# the reference verifier reports for them. Most are one to one. The obligation
# response binding is the exception: the procedure checks it at step 1 as a
# declared hash that does not equal the recomputed one, and reports it under the
# generic evidence-hash code, while the runner reports the obligation-specific
# code the manifest declares. Both refuse the same bytes for the same reason.
IMPLEMENTED_CODES = {
    "A202-EVIDENCE-HASH-MISMATCH": {"A202-EVIDENCE-HASH-MISMATCH"},
    "A202-AGREEMENT-HASH-MISMATCH": {"A202-AGREEMENT-HASH-MISMATCH"},
    "A202-OBLIGATION-RESPONSE-HASH-MISMATCH": {"A202-EVIDENCE-HASH-MISMATCH"},
    "A202-EVIDENCE-CHAIN-GAP": {"A202-EVIDENCE-CHAIN-GAP"},
    "A202-EVIDENCE-TRANSITION-ILLEGAL": {"A202-EVIDENCE-TRANSITION-ILLEGAL"},
    "A202-DETERMINATION-NOT-FOLLOWING": {"A202-DETERMINATION-NOT-FOLLOWING"},
    "A202-DETERMINATION-EFFECT-OVERCLAIM": {"A202-DETERMINATION-EFFECT-OVERCLAIM"},
    "A202-DISPUTE-SUBJECT-UNREFERENCED": {"A202-DISPUTE-SUBJECT-UNREFERENCED"},
    "A202-EVIDENCE-TYPE-UNKNOWN": {"A202-EVIDENCE-TYPE-UNKNOWN"},
    "A202-EVIDENCE-SIGNATURE-INVALID": {"A202-EVIDENCE-SIGNATURE-INVALID"},
    # A supersession fork is a fork in a chain, and the verifier reports it at
    # step 3 alongside the version-chain forks it is the same defect as: two
    # records claiming to be current on one thing.
    "A202-DETERMINATION-SUPERSESSION-FORKED": {"A202-EVIDENCE-CHAIN-GAP"},
}

# Why a bundle is outside the procedure's remit. Each entry names the offence
# rather than the fixture, so that a fixture added to one of these classes is
# skipped for a reason someone wrote down rather than for an absence of code.
OUTSIDE_REMIT = {
    "A202-OBLIGATION-RESPONSE-UNAUTHORIZED": "obligation lifecycle authority, outside steps 1 to 7",
    "A202-OBLIGATION-REMAINDER-MISSING": "obligation lifecycle remainder, outside steps 1 to 7",
    "A202-OBLIGATION-SUBJECT-UNREFERENCED": "obligation subject binding, outside steps 1 to 7",
    "A202-OBLIGATION-CONDITION-CYCLIC": "due condition graph, outside steps 1 to 7",
    "A202-DISPUTE-OUT-OF-WINDOW": "dispute window resolution, outside steps 1 to 7",
    "A202-EVIDENCE-REPORT-INVALID": "the report's own shape, which is the bundle context rather than an object in it",
    "A202-EVIDENCE-DISCLOSURE-INCOMPLETE": "stated-gap accounting, which the verifier reports as scope rather than as failure",
    "A202-AGREEMENT-AMENDMENT-UNACCEPTED": "amendment freshness, outside steps 1 to 7",
    "A202-SETTLEMENT-TRIGGER-ABSENT": "settlement trigger resolution, outside steps 1 to 7",
}

# Fixtures whose particular offence is outside the remit although their code
# generally is not. Each of these is a condition the runner reads from the
# bundle's stated context or from the record around an object, where the
# procedure reads the object. They are named one by one rather than by code,
# because the code's other fixtures are swept and a skip by code would drop
# those with them.
OUTSIDE_REMIT_FIXTURES = {
    "negative/dispute-subject-hash-unresolvable.json": (
        "an unresolvable subject hash is step 7 scope, never a failed check"
    ),
    "negative/determination-rules-ref-not-in-force.json": (
        "the version in force at the time of the subject act is stated by the "
        "record rather than by the determination, and step 6 checks the "
        "determination against the version it names"
    ),
    "negative/stream-cross-continuity-asserted.json": (
        "the verifier keys a stream by its own identifier, so the two streams "
        "are two streams and each is internally continuous; the claim of one "
        "sequence across both is made by the bundle rather than by an object"
    ),
    "negative/evidence-bundle-transition-current-rules.json": (
        "the bundle names a different rules version in force for different "
        "events, and reading one of them as governing all of them is the "
        "mistake step 5 exists to prevent"
    ),
    "negative/direct-formation-over-open-session.json": (
        "the direct-formation guard is a condition over the record around the "
        "event rather than the legality of the transition itself"
    ),
    "negative/evidence-bundle-signature-wrong-purpose.json": (
        "the fixture carries the synthetic placeholder signature value, which "
        "is correctly not_checkable before the purpose is reached"
    ),
}


def _rules_resolver_for(context):
    """Resolve a rules reference the way the bundle states it.

    The verifier reads a rules reference from the event payload. The fixture
    set states the version in force in the bundle's context instead, because
    the version that governs is the one in force when the event appended and
    that is a fact about the record rather than a field on the event. Where a
    bundle names one version for the whole record, this resolver supplies it, so
    that replay is executed rather than reported not checkable. Where a bundle
    names different versions for different events, it does not: reading one of
    them as governing all of them would replay a record against rules that were
    not in force for part of it, which is the mistake step 5 exists to prevent.
    """
    if context.get("event_rules_in_force"):
        return runner.resolve_rules
    version = context.get("rules_version_in_force")
    entry = runner.RULE_SETS.get(("a202-rules/pilot", version)) if version else None

    def resolve(ref):
        if ref is None:
            return entry
        return runner.resolve_rules(ref)

    return resolve


class FixtureSweepTest(unittest.TestCase):
    def test_verifier_agrees_with_the_manifest_on_every_bundle(self):
        with open(REPO_ROOT / "conformance" / "manifest-v0.1.json") as handle:
            manifest = json.load(handle)

        swept = 0
        skipped: list[tuple[str, str]] = []

        for expected_valid, entries in (
            (True, manifest["positive"]),
            (False, manifest["negative"]),
        ):
            for entry in entries:
                if entry["kind"] != "bundle":
                    continue
                with open(FIXTURES / entry["fixture"]) as handle:
                    fixture = json.load(handle)
                objects = [o for o in fixture.get("objects", []) if isinstance(o, dict)]
                context = fixture.get("context", {})
                report = verify_bundle(
                    objects, keys={}, rules_resolver=_rules_resolver_for(context)
                )
                failed = {
                    check.code
                    for check in report.checks
                    if check.result == "failed"
                }

                if expected_valid:
                    swept += 1
                    self.assertEqual(
                        failed,
                        set(),
                        f"{entry['fixture']} is positive in the manifest and the "
                        f"verifier failed it: {sorted(failed)}",
                    )
                    continue

                declared = entry["reason_code"]
                if entry["fixture"] in OUTSIDE_REMIT_FIXTURES:
                    skipped.append(
                        (entry["fixture"], OUTSIDE_REMIT_FIXTURES[entry["fixture"]])
                    )
                    continue
                if declared not in IMPLEMENTED_CODES:
                    skipped.append((entry["fixture"], OUTSIDE_REMIT.get(declared, declared)))
                    continue
                swept += 1
                self.assertTrue(
                    IMPLEMENTED_CODES[declared] & failed,
                    f"{entry['fixture']} declares {declared} and the verifier "
                    f"reported {sorted(failed) or 'no failure'}",
                )

        total = swept + len(skipped)
        self.assertGreater(total, 0)
        print(
            f"\nfixture sweep: {swept} of {total} evidence bundles swept through "
            f"the reference verifier, {len(skipped)} skipped as outside the "
            f"seven-step procedure"
        )
        for fixture, reason in skipped:
            print(f"  skipped {fixture}: {reason}")
        # Every skip is a stated reason rather than an omission, and the swept
        # majority is what makes the agreement a result rather than an anecdote.
        for fixture, reason in skipped:
            self.assertTrue(reason, fixture)
        self.assertGreater(
            swept,
            len(skipped),
            f"swept {swept} of {total} bundles, skipped {len(skipped)}: {skipped}",
        )


if __name__ == "__main__":
    unittest.main()
