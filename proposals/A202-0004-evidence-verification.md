# A202-0004: Evidence reference shape and public verification procedure

**Status:** Fixtures and compatibility. Stage 3 of the five stages in [README.md](README.md) section 3. The static fixtures in section 5 are implemented in the conformance suite; the seven runtime cases in section 5.3 remain recorded for implementation-level verification.

**Date:** 27 July 2026

**Status of this document:** Informative in full. The normative text this proposal adopts is carried by [evidence/evidence-verification-v0.1.md](../evidence/evidence-verification-v0.1.md), which marks its own normative sections.

**Adopts:** [evidence verification v0.1](../evidence/evidence-verification-v0.1.md)

## 1. Problem

The specification set claims that authorised parties can independently verify signed records, that replay of the same valid inputs produces the same result, and that no party depends on any operator's continued existence to prove what happened. It states those claims in four places and defines the procedure in none.

What a relying party cannot currently do:

- **Execute a verification.** Replay is described at a level that assumes the reader already knows what to do: [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) section 9 lists seven activities in one paragraph, and the isolation verification in [auction-event-semantics-v0.1.md](../negotiation/auction-event-semantics-v0.1.md) section 6 restates part of it in different words. Neither is a procedure a third party can execute step by step against a bundle it was handed.
- **Resolve an evidence reference.** Every object that references evidence does so with a bare `evd_` identifier. An identifier carries no content hash, so an evidence object can be replaced with a different one under the same identifier and every reference to it stays valid. The whole set is otherwise content addressed, and this is the one place it is not.
- **Distinguish a gap from a failure.** Selective disclosure is the normal case, and there is nothing that says what a verifier reports about the streams it was not given. An implementation that reports an undisclosed stream as failed makes ordinary partial disclosure look like misconduct. One that reports it as verified makes an absence look like proof. Both readings are currently available.

The situation where this bites: a losing bidder holds an export of its own session stream and the transaction-stream events it is party to, two years after the event, and the operator is gone. It has to establish, from bytes alone, that the transitions were legal, that the signatures were valid, and that the determination against it followed from the rules that were in force. Today it has to invent the algorithm, and whatever it invents is not the algorithm anyone else runs.

There is also a claim in the set that nothing supports. Conformance grade dimension D is "Evidence: portable export, hash scope and canonicalisation, deterministic replay by a third party". A grade cannot be issued against that dimension while the replay a third party is supposed to perform is unspecified.

## 2. Proposal summary

Adopt [evidence verification v0.1](../evidence/evidence-verification-v0.1.md).

1. **The evidence reference shape.** `evidence_id`, `content_hash` as lowercase hexadecimal SHA-256, `evidence_type` from a closed registered list that fails closed on an unknown value, an optional `locator_hint` that is never load bearing, and `signed_by` as a `partyRef`. Used by every object family so a verifier resolves one shape, not several.
2. **The verification procedure**, as seven numbered steps executable with no operator access: canonicalise and check hashes; verify every signature against declared keys and purposes; check version chains through `previous_version_id` with no gaps and no forks; check per-stream sequence continuity for the streams disclosed; replay guarded transitions and check each was legal under the rules version in force; check each determination's outcome follows from its referenced rules and inputs; report what could not be checked.
3. **Three-valued output.** `verified`, `failed`, and `not_checkable`, never collapsed, never reduced to a boolean, and never aggregated so that a gap reads as a pass.
4. **Selective disclosure.** A subset verifies on its own, the report states its scope, a disclosed boundary is not a gap, and the withheld remainder is not inferable beyond the existence of a named reference.
5. **An informative human oversight annex.** Which existing objects evidence oversight, plus a four-row mapping table to the oversight concerns of EU AI Act Article 14, each row pointing at the object that evidences it, with the plain statement that the mapping is informative and is not a legal compliance assessment.
6. **Eight refusal codes**, including the five the procedure's failing steps produce.

Bundle construction is explicitly outside the adopted document. How records are gathered, ordered, packaged, held, and exported is not specified and not published.

## 3. Alternatives considered

**Do nothing.** Rejected: the portability claim is unsupported without it, conformance dimension D cannot be assessed, and every implementation writes a different verifier. Two verifiers that disagree about whether a bundle checks out are worse than no verifier, because both produce confident output.

**Keep bare `evd_` identifiers and add no content hash.** Rejected: it leaves one substitution attack open in an otherwise content-addressed set. Swap the object behind the identifier and every reference to it still validates, which is precisely the property hashing exists to remove.

**Specify bundle construction as well.** Rejected as out of scope rather than as wrong. Verification has to be public or the record is not portable. Construction does not, and specifying it would put operator implementation detail into a document whose whole purpose is to be executable by someone who has none.

**Report a gap as a failure.** Rejected: partial disclosure is the normal case, and a verifier that fails a bundle for the streams it was correctly not given produces an alarming report about a correct situation. The relying party then learns to ignore failures, which destroys the value of a real one.

**Report a gap as a pass.** Rejected harder. It is the same mistake the set already refuses everywhere else: absence of an assessment reads as unassessed, never as satisfactory, and absence of a check has to read the same way.

**Put the Article 14 mapping in a separate companion document.** Rejected: the mapping points at objects this set defines, and separating it invites a second document that drifts from the objects it describes. Keeping it as an informative annex to the verification procedure puts it next to the procedure by which the mapped objects are actually checked.

**Make the verification report a signed kernel object.** Rejected for v0.1: it would need a registered object type and prefix, and it would invite a report being treated as a determination. A report is a statement by whoever produced it and can be referenced as ordinary evidence, which is enough.

## 4. Compatibility

### 4.1 What breaks

One thing changes for existing objects, and it is the reason to look at this proposal carefully.

Objects that today carry `evidence_refs` as an array of bare `evd_` identifier strings gain a structured reference shape. Under [RELEASES.md](../RELEASES.md) section 2 a change that narrows what a previously conformant implementation may write is **MAJOR**, and a change that adds capability without invalidating anything is **MINOR**. This proposal takes the MINOR path deliberately, in the following form.

1. The identifier-only form remains valid in v0.1. It is the short form.
2. A verifier that cannot resolve an identifier-only reference to an object carrying a content hash reports it as `not_checkable`, never as verified and never as failed. The gap is visible rather than silent.
3. The structured shape is what new object families adopt. Disputes, determinations, obligations, and performance assertions require it from the start, because they are being defined now and nothing has been written against an earlier form.
4. Requiring the structured shape everywhere is a MAJOR change and is left for a later proposal, with migration notes, rather than taken here under a MINOR increment.

Reviewers should test that reasoning specifically. The alternative reading is that an unhashed reference is a defect that should be closed at once, and the counterargument is that closing it now would invalidate every currently valid object carrying `evidence_refs`. Both readings are defensible and the choice is recorded here rather than made silently.

Nothing else breaks. No existing field changes meaning, no state is added or removed, no transition changes, and no fixture is reclassified.

### 4.2 Kernel schema changes required

| Change | Detail |
|---|---|
| Add `evidenceRef` `$def` | The five fields in section 2 item 1. Closed with `additionalProperties: false` |
| Add `evidenceTypeId` `$def` | A pattern plus the closed registered list, so an unregistered type fails at schema as well as at verification |
| Permit both reference forms on `evidence_refs` | Existing arrays accept the identifier string form or the `evidenceRef` object form. New payloads accept the object form only |
| No new object type | The verification report is not a kernel object in v0.1 |

`partyRef`, `sha256Hex`, and the canonicalisation and signature rules of [canonical-commercial-model-v0.1.md](../schemas/canonical-commercial-model-v0.1.md) section 4 are reused unchanged. The procedure defines no new hash algorithm, no new signature suite, and no new canonicalisation.

### 4.3 Existing objects and documents

| Object or document | Effect |
|---|---|
| `Offer`, `CommercialMandate`, `InvitationAcceptance`, `CommercialRequest` | `evidence_refs` and `assurance_evidence_refs` accept both forms. Nothing currently valid becomes invalid |
| `Evidence` | Unchanged in shape. It is now referenced by content hash rather than only by identifier |
| `EvidenceManifest`, `AuditBundle` | Named in the object inventory with no defined payload. This proposal does not define either, and does not need to: the procedure is executed against whatever set of objects the verifier holds. The undefined payloads are recorded as an open item |
| Replay in [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) section 9 | Unchanged and now has a step-by-step counterpart. The seven activities listed there map onto steps 1 to 5 of the procedure. A later editorial proposal should replace the paragraph with a reference so that the rule has one home. See section 4.6 |
| Isolation verification in [auction-event-semantics-v0.1.md](../negotiation/auction-event-semantics-v0.1.md) section 6 | Unchanged. The procedure a losing bidder follows there is this procedure, with the additional isolation checks that document states |
| Conformance grade dimension D | Now assessable. The dimension covers "deterministic replay by a third party", and this is that replay |

### 4.4 Existing states: `in_performance` and `exception_open` are the integration points

This proposal adds no state and changes no transition. It touches the state machine at step 5, where transitions are replayed rather than performed.

| Where it integrates | What the procedure does |
|---|---|
| `in_performance` and `acceptance_pending` | Step 5 replays `obligation.activated`, `performance.declared`, `acceptance.granted`, and `acceptance.rejected` against both the aggregate table and the obligation table adopted by [A202-0002](A202-0002-obligation.md), checking each guard against the rules version in force at append time |
| `exception_open` | Step 6 checks the determinations that a dispute produced, including whether the claimed effect was granted. A bundle whose exception was opened and resolved is checkable end to end only if both steps run |
| Every session state | Step 4 checks per-stream continuity and explicitly refuses to expect continuity across streams. This is the verification-side counterpart of the per-stream sequencing rule, and a verifier that expected a global sequence would report false gaps for a correct record |

One point of care: step 5 checks transitions against **the rules version in force at the time the event appended**, not the current one. A verifier that replays a two-year-old record against today's rules will report failures on a record that was correct when it was made. This is stated in the adopted document and is called out here because it is the mistake a straightforward implementation makes first.

### 4.5 Ordering against A202-0002 and A202-0003

Both depend on the evidence reference shape adopted here. A202-0004 depends on neither of them for its own steps 1 to 5, and its step 6 is inert until determinations exist.

A202-0004 lands first, or all three land together. It cannot land after either of the others.

### 4.6 A duplication to resolve later

Replay is now described in two places: [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) section 9, and the adopted document's steps 1 to 5. Both say the same thing today, and both drifting is a matter of time. A normative rule stated in two places has no single source of truth.

Resolving it is editorial and is deliberately not bundled here, because collapsing the state machine's section 9 into a reference is a change to that document and belongs in its own proposal with its own review. It is recorded so it is not lost.

### 4.7 Migration

Nothing to migrate for existing objects. An implementation that wants the structured reference form on an object it already emits adds it as a new object version through the ordinary `previous_version_id` chain; the earlier version stays valid and stays verifiable.

## 5. Fixture plan

Weighted the way the published suite is weighted: 3 positive and 15 negative static fixtures, plus 7 cases requiring runtime state.

### 5.1 Positive

| Fixture | What it exercises |
|---|---|
| `valid-evidence-reference.json` | The structured shape in the allow direction: content hash, registered type, a hint, and a signing party |
| `valid-evidence-reference-identifier-form.json` | The identifier-only short form, valid in v0.1, which a verifier resolves or reports as not checkable |
| `valid-verification-report-partial-disclosure.json` | A report over a disclosed subset: stated scope, a named undisclosed stream, and per-check results across all three outcomes |

### 5.2 Negative

| Fixture | Expected code | What it refuses |
|---|---|---|
| `negative/evidence-ref-multibase-hash.json` | `A202-HASH-FORMAT-INVALID` | A multibase content hash. v0.1 accepts lowercase hexadecimal SHA-256 only, and the reference must not become the one place that does not |
| `negative/evidence-ref-uppercase-hash.json` | `A202-HASH-FORMAT-INVALID` | An uppercase hexadecimal hash, which would compare unequal to a correctly encoded one |
| `negative/evidence-ref-unregistered-type.json` | `A202-EVIDENCE-TYPE-UNKNOWN` | An unregistered `evidence_type`. Fails closed at schema and independently at verification |
| `negative/evidence-ref-locator-carries-secret.json` | `A202-DISCLOSURE-DENIED` | A `locator_hint` carrying a bearer token. The hint is an ordinary field of a shared object and the private-data rules apply to it |
| `negative/evidence-ref-locator-load-bearing.json` | `A202-EVIDENCE-HASH-MISMATCH` | A reference with a hint and no `content_hash`, so retrieval would be the only check |
| `negative/evidence-bundle-tampered-object.json` | `A202-EVIDENCE-HASH-MISMATCH` | One byte changed in a signed object, caught at step 1 |
| `negative/evidence-bundle-hash-covers-annotations.json` | `A202-EVIDENCE-HASH-MISMATCH` | A `content_hash` computed over bytes that include `kernel_annotations`, which would let a control-plane field become load bearing |
| `negative/evidence-bundle-signature-wrong-purpose.json` | `A202-EVIDENCE-SIGNATURE-INVALID` | A signature valid over the bytes and issued for a different `purpose`. The case a naive verifier passes |
| `negative/evidence-bundle-agreement-single-signature.json` | `A202-EVIDENCE-SIGNATURE-INVALID` | An agreement in a bundle carrying one signature, checked at step 2 rather than only at issue |
| `negative/evidence-bundle-version-chain-gap.json` | `A202-EVIDENCE-CHAIN-GAP` | Version 3 naming version 1 as its predecessor |
| `negative/evidence-bundle-version-chain-fork.json` | `A202-EVIDENCE-CHAIN-GAP` | Two objects naming the same `previous_version_id`. Two successors means two objects claim to be current |
| `negative/evidence-bundle-cross-stream-continuity-asserted.json` | `A202-EVIDENCE-CHAIN-GAP` | A bundle asserting a single sequence across a session and the transaction stream. A verifier that accepted it would be reading a covert channel as a correctness property |
| `negative/evidence-bundle-illegal-transition.json` | `A202-EVIDENCE-TRANSITION-ILLEGAL` | A replayed `published` to `committed` transition, the illegal direct transition the state machine already names |
| `negative/evidence-bundle-transition-current-rules.json` | `A202-EVIDENCE-TRANSITION-ILLEGAL` | A transition legal under the current rules version and not under the version in force when it appended |
| `negative/evidence-determination-not-following.json` | `A202-DETERMINATION-NOT-FOLLOWING` | A determination whose finding is not supported by the rules it names and the evidence it relies on |
| `negative/evidence-report-gap-reported-as-verified.json` | `A202-EVIDENCE-REPORT-INVALID` | A report marking an undisclosed stream as verified. The failure that makes an absence look like proof |
| `negative/evidence-report-boolean-only.json` | `A202-EVIDENCE-REPORT-INVALID` | A report reducing all checks to a single pass value, discarding the `not_checkable` set |
| `negative/evidence-report-scope-unstated.json` | `A202-EVIDENCE-REPORT-INVALID` | A report over a subset that states no scope, so its silence is indistinguishable from completeness |
| `negative/evidence-selective-disclosure-requires-undisclosed.json` | `A202-EVIDENCE-DISCLOSURE-INCOMPLETE` | A subset that cannot be verified without an object the verifier was not given |

### 5.3 Cases requiring runtime state

1. A disclosed subset verifies fully with no access to the remainder, and the report names the undisclosed streams.
2. A stream disclosed from mid stream produces a stated boundary at step 4, not `A202-EVIDENCE-CHAIN-GAP`.
3. An unresolvable `locator_hint` changes no result. Every check that passed with the hint resolving still passes with it stale.
4. A key expired at verification time and valid at `signed_at` produces a signature reported as valid when created, with current key status reported separately.
5. A key whose status cannot be resolved at either point produces `not_checkable` for that point and does not produce a verified signature.
6. An unresolvable rule set version at step 6 produces `not_checkable` for that determination, never `verified`.
7. Two independent verifiers running the procedure over the same bundle produce the same per-check results.

Case 7 is the case the whole document exists for. If two verifiers disagree, the procedure is underspecified, and the disagreement is the finding.

## 6. Origin

Drafted from four claims in the v0.1 set that no published procedure supports: independent verification by an authorised party with no privileged operator access, replay determinism, the statement that no party depends on an operator's continued existence to prove what happened, and conformance dimension D. The evidence reference gap in section 1 was found while drafting [A202-0002](A202-0002-obligation.md), where an assertion has to reference evidence and there was no shape that carried a content hash. This is context for reviewers rather than an argument.
