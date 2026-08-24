# A202-0023: The runner and the reference implementation canonicalize differently

**Status:** Draft, submitted to enter at stage 1, problem statement, of [README.md](README.md) section 3, with the change of section 2 already drafted as a pull request by its finder. Nothing lands until that pull request is reviewed and merged under this proposal.

**Date:** 20 August 2026

**Status of this document:** Informative in full. It states no requirement on an implementation. The normative material this proposal corrects is carried by [conformance/run-conformance.py](../conformance/run-conformance.py), the normative runner, against the rule stated in [canonical-commercial-model-v0.1.md](../schemas/canonical-commercial-model-v0.1.md) section 4.

## 1. Problem

Canonical model section 4 rule 1 requires JSON objects to be serialized under the JSON Canonicalization Scheme, RFC 8785, which orders object member names by their UTF-16 code units. The repository holds two implementations of that rule, and they disagree.

The reference implementation, `reference/a202_reference/canonical.py`, sorts member names by `k.encode("utf-16-be")`, which is the RFC's order. The runner, `conformance/run-conformance.py`, carried its own serializer using Python's `json.dumps(sort_keys=True)`, which sorts by Unicode code point. The two orders agree on every string of basic-plane characters and diverge where a supplementary-plane character meets a basic-plane character above the surrogate range: U+1F6A2 encodes as the surrogate pair D83D DEA2, and D83D sorts before E000 in UTF-16 where the code point 1F6A2 sorts after E000. Over an object with member names `id`, U+E000, and U+1F6A2, the runner produced the order `id`, U+E000, U+1F6A2 and the reference implementation the order `id`, U+1F6A2, U+E000. Different bytes, therefore a different SHA-256, therefore a signature one layer accepts and the other refuses, on the layer whose stated property is that replay of the same valid inputs produces the same result.

The suite did not reach the divergence because every member name in the fixture set is ASCII, where the two orders agree, and the runner's own docstring recorded that assumption. Nothing bounds the exposure to fixtures: transaction profiles define their own member names, and no character-set constraint restricts them to ASCII.

The defect is the shape [A202-0015](A202-0015-fixture-minimality-orphan-codes-and-grade-scope.md) named for reason codes, applied to code: two statements of one rule, each fine alone, drifting where nothing forces them together. The runner is normative; a normative layer that disagrees with the reference implementation about which bytes are canonical is a defect in whichever side is wrong, and here the runner was wrong.

## 2. Change

1. **The runner loads the reference canonicalizer and carries no serializer of its own.** `conformance/run-conformance.py` obtains `canonical_bytes` from `reference/a202_reference/canonical.py`, loaded by file path so that the runner remains runnable from a checkout with no package installed, and its private `json.dumps` path is deleted. One canonicalizer, one source of truth, and the drift cannot recur because there is no second implementation to drift.

2. **The divergent pair becomes a fixture.** A canonicalization vector carries member names U+E000 and U+1F6A2 beside `content_hash`, `signatures`, and `kernel_annotations` members, and states the expected canonical bytes: supplementary-plane name before U+E000, per UTF-16 order, and the three excluded members absent, per section 4 rule 2. A test asserts that the reference canonicalizer and the runner both produce exactly those bytes, so the fixture proves the ordering and proves that the exclusion rule survived the substitution, which was the one behaviour the substitution could plausibly have broken.

## 3. Alternatives considered

**Fix the runner's serializer in place.** Correcting the sort key inside the runner's own function leaves two implementations of one rule in the tree, which is the condition that produced the defect. The correction would be exact today and unguarded tomorrow.

**Restrict member names to ASCII.** A character-set constraint on profile vocabulary would make the two orders agree everywhere by construction. Rejected: it narrows every future profile to protect an implementation shortcut, states a rule RFC 8785 does not state, and would be a normative change to the profile model rather than a correction to the runner.

**Have the reference implementation import from the runner.** Backwards. The reference package is the importable artifact; the runner is a script. Dependency should point from script to package, and the reference canonicalizer is the correct implementation of the two.

**Do nothing.** The suite passes today because the fixtures are ASCII. The first profile that uses a non-ASCII member name ships objects whose hashes the runner computes wrongly, and the failure surfaces as a signature dispute between counterparties rather than as a red suite here.

## 4. Compatibility

The specification is unchanged: RFC 8785 was the rule before and after, and the reference implementation already followed it. ASCII-only canonical output is byte-identical, so every fixture, digest, and recorded hash in the repository stands; no fixture changes classification. An implementation that reproduced the runner's previous code-point ordering for non-ASCII member names computed hashes the specification never permitted, and migrates by adopting UTF-16 code-unit ordering as the reference canonicalizer implements it. Under [RELEASES.md](../RELEASES.md) section 2 this is a correction of the runner to the released rule rather than a change to what a conformant implementation has to do.

## 5. Fixtures

Carried by the correcting pull request, as section 2 item 2 describes: the vector `conformance/fixtures/canonicalization/rfc8785-utf16-member-order.json` and a test binding both canonicalization call sites to its stated bytes. The allow and refuse directions collapse into one assertion here: the stated bytes are the only pass, and either implementation producing anything else is the failure.

## 6. Origin

Found by Erik Newton while reading the runner and the reference implementation side by side during review of the A202 extension proposal on the A2A repository, reported there with the diverging pair worked out (a2aproject/A2A#2143), and fixed by him in the pull request this proposal exists to receive. The exposure analysis in section 1, that profile member names are unconstrained, is his. This is context for reviewers rather than an argument.
