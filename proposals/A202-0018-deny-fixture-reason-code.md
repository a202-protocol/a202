# A202-0018: A conformance fixture carries a reason code the registry does not

**Status:** Draft, not yet submitted; held for founder review. Written to enter at stage 1, problem statement, of [README.md](README.md) section 3. Section 2 drafts the change stage 2 would adopt. Nothing is implemented: no fixture, schema, runner rule, or specification document has been edited.

**Date:** 9 August 2026

**Status of this document:** Informative in full. It states no requirement on an implementation. The normative material this proposal amends is carried by the fixture set and the documents it names.

## 1. Problem

Section 10 of [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) declares its table, together with the additions in [auction-event-semantics-v0.1.md](../negotiation/auction-event-semantics-v0.1.md) section 8.1 and [conformance-role-scopes-v0.1.md](../conformance/conformance-role-scopes-v0.1.md) section 8, the complete refusal-code registry, and states that a code resolving in none of the three tables is an unregistered code an implementation MUST NOT invent.

One shipped fixture carries such a code. `conformance/fixtures/v0.1/negative/policy-deny-visible-to-counterparty.json` is a policy decision whose `payload.reason_codes` is `["A202-MANDATE-PREPAYMENT-LIMIT"]`. That code resolves in none of the three tables. The fixture's declared offence is elsewhere and is real: a `deny` recorded with `visibility` `transaction_parties` on the shared transaction stream, refused by the kernel schema's conditional on `policyDecisionPayload` and declared in the manifest with `A202-DISCLOSURE-DENIED`. The unregistered code sits in the payload content around that offence, and no layer reads it: the schema constrains `reason_codes` members to the pattern `^A202-[A-Z0-9-]+$` and nothing else, and the runner asserts declared codes from the manifest, not codes inside fixture payloads. The registry-completion pass of [A202-0010](A202-0010-model-completion.md) swept the codes that documents and the manifest were already using; a code inside a fixture's payload content is exactly what that sweep did not read.

The cost is not that any check fails. It is that the fixture set is the material implementers copy, and the one shipped example of a mandate-constraint deny models a party inventing a code section 10 forbids. It also breaks the fixture-minimality rule in the form that rule is stated: repairing the documented offence — `visibility` to `private_to_actor`, the stream to `private` — leaves a document the schema accepts but a conformant implementation could not have produced, because its one reason code is unregistered.

The condition arose in practice. The first surface built against the calibration scenario outside the conformance suite could not carry the fixture's code without violating section 10, and had to substitute registered codes while the fixture continued to ship the unregistered one.

## 2. Change

`negative/policy-deny-visible-to-counterparty.json` replaces `payload.reason_codes` `["A202-MANDATE-PREPAYMENT-LIMIT"]` with `["A202-POLICY-DENIED"]`, and its `content_hash` is recomputed over the corrected canonical bytes. Nothing else about the fixture changes: its name, its kind, its manifest entry, its declared code `A202-DISCLOSURE-DENIED`, its offence, and its row in the fixture partition all stand.

`A202-POLICY-DENIED` is registered in section 10 as "Deterministic constraint failed", which is the condition the fixture depicts: a proposed action exceeded a prepayment ceiling stated as a mandate constraint, and the evaluation is deterministic. The correction makes the fixture a document a conformant party could actually have produced, offence aside.

## 3. Alternatives considered

**Register `A202-MANDATE-PREPAYMENT-LIMIT` instead.** The mock-dataset finding stated both repairs, and this is the other one. It is not taken, for three reasons. First, the set already has the code that says what happened: a prepayment ceiling is one deterministic constraint among many, and `A202-POLICY-DENIED` covers a failed deterministic constraint by its registered meaning. Registering a second code for one instance of the same condition creates two codes a caller must handle identically, which is the failure [A202-0015](A202-0015-fixture-minimality-orphan-codes-and-grade-scope.md) section 5 named: a caller handed several codes that must be handled the same way will eventually handle one of them differently. Second, it opens an unbounded family. Every registered constraint type — total value, per-transaction value, category, counterparty, calendar — would have equal claim to its own deny code, and the registry would grow one code per constraint per negotiable term. Third, it would be an orphan on arrival, the defect class A202-0015 closed: no evaluator in the repository distinguishes a prepayment deny from any other constraint deny, and none should, because a deny is `private_to_actor` — the kernel schema states that a denied action never becomes visible to a counterparty — so the specific code has no reader who does not already hold the mandate and the proposed action, and the constraint that matched is the acting party's own private detail.

**Tighten the schema so `reason_codes` accepts only registered codes.** The registry lives in three prose tables and grows by proposal; encoding it into the kernel schema would turn every code registration into a schema change and would break the declared mechanism by which the auction and role-scope documents extend the table. The schema keeps the prefix pattern, and registration remains a documentary fact, which is how section 10 states it.

**Do nothing.** The fixture passes today and no runner assertion is false. But the registry rule is only as credible as the repository's own conformance to it, and the one place an implementer sees a constraint-deny modelled end to end currently models the violation. The correction costs one line and a hash.

## 4. Compatibility

Under [RELEASES.md](../RELEASES.md) section 2 the set is pre-release, and section 5 records that no release has been made. This change alters no normative statement: the declared code, the offence, the manifest, the schema, and the registry are all unchanged, which makes it PATCH-shaped. It is raised as a proposal rather than landed as an ordinary pull request because fixture content is conformance material and [README.md](README.md) section 1 resolves doubt toward a proposal. The migration surface is one item: an implementation pinned to the fixture's exact bytes rereads one file, whose name, subject, and declared code did not change.

## 5. Fixture plan

The change is itself a fixture repair, checked in the form the minimality rule states. The corrected fixture is still refused for exactly its declared reason: a `deny` visible to the counterparty on a shared stream, `A202-DISCLOSURE-DENIED` per the manifest. A copy with the documented offence repaired — `visibility` `private_to_actor` and the stream `private`, per the kernel schema's conditional — validates cleanly and carries only codes that resolve in the registry, which the pre-correction fixture could not satisfy. No fixture is added or removed, and the partition's total-and-disjoint property is untouched.

## 6. Origin

Found while building the Plural Worlds console's mock dataset, the first surface to express the pilot calibration scenario end to end outside the conformance suite, and recorded there as a documented deviation: the dataset refused to carry the unregistered code and used `A202-DISCLOSURE-DENIED` and `A202-POLICY-DENIED` for the two refusal conditions the scenario requires. The code itself descends from an earlier draft of the calibration scenario written before the registry existed; the fixture carried its renamed form forward, and the completion pass of A202-0010 did not reach inside fixture payloads. This is context for reviewers rather than an argument.
