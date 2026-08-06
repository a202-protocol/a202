# A202-0009: Enforcement fidelity: every claimed check is a real check

**Status:** Fixtures and compatibility. Stage 3 of the five stages in [README.md](README.md) section 3. Every change in this proposal is implemented in the runner, the schemas, the fixture set, and the manifest, and the suite passes with the changes in place.

**Date:** 28 July 2026

**Status of this document:** Informative in full. It states no requirement on an implementation. The normative text this proposal amends is carried by the documents it names, each of which marks its own normative sections.

## 1. Problem

An external deep-dive review of the specification set, conducted 28 July 2026, found a consistent failure class: the prose claims machine enforcement that the machine layer does not provide. The individual findings differ, but the shape is one shape: a sentence says "this is checked", and nothing checks it.

The instances this proposal closes:

1. **Delegation narrowing was neither checked nor fixtured.** The canonical model's section 12 said every listed invariant is checked by the runner with a negative fixture each; `A202-MANDATE-DELEGATION-WIDENING` had neither. A child mandate that outlived, out-scoped, out-acted, and out-spent its parent tenfold validated clean.
2. **Agreement hashes were never recomputed.** The verification procedure requires checking `terms_hash` and `accepted_offer_hash`; no layer did. A dual-signed agreement whose hashes were unrelated to its own terms passed the schema, the runner, and the reference verifier.
3. **Negative fixtures were not verified to fail for their declared reason.** The manifest declares a `reason_code` for every negative fixture and the runner ignored the field. One declared code was already wrong, which is what an unasserted declaration decays into.
4. **The rival-disclosure denylist did not reach the transaction stream**, although the runner's own comment said it did. Post-commit the winning counterparty reads that stream.
5. **The event-chain check was weaker than the procedure it implements.** `previous_event_hash` was checked to name some same-stream event, not the immediately preceding one. A chain that skipped an event replayed clean.
6. **Quantity comparison used binary floating point** in the runner, against the mandate specification's own decimal-arithmetic requirement, and failed open on unparseable input.
7. **The disclosure-bearing reason-code list had one member.** A deny carrying `A202-LOT-ALREADY-AWARDED`, which tells a bidder an award happened, validated.
8. **A determination's `state_result` was an unconstrained object**, described as "the only field through which a determination touches state". A binding determination could carry a bag of transitions across three state machines in one unvalidated blob.
9. **The mandate second layer did not exist.** All eight mandate negatives were schema-caught only, so the codes an implementation must return for them were never exercised, and several codes used by the manifest resolved in no registry.
10. **The identifier-smuggling claim overstated the pattern layer.** Canonical 12.1 said a value cannot be smuggled into an identifier field; a session event's `clarification_id` could carry a rival's price in its free characters under a generic prefix.
11. **Restated fixture counts had gone stale in three documents**, including the role-scope partition, which classified thirty-eight fixtures out of what had grown to one hundred and six, leaving the whole obligation, evidence, dispute, determination, and settlement families ungradeable in either scope.

## 2. Change

1. **Runner, mandate layer.** A `mandate_checks` evaluator enforces the interval, boundedness, scope, subject, constraint-registry, delegation-coherence, and status-transport rules independently of the schema, emitting the codes the manifest declares. A `delegation_checks` evaluator and a new `mandate_chain` fixture kind carry a parent and child pair and refuse widening on every axis of the mandate specification section 7, under decimal comparison. One valid chain fixture and one widening fixture per axis are added.
2. **Runner, hashes.** Agreement `terms_hash` is recomputed and `accepted_offer_hash` and acceptance `offer_hash` are checked against the referenced objects wherever they are disclosed, refusing with `A202-AGREEMENT-HASH-MISMATCH`. The reference verifier gains the same checks in step 1. Negative fixtures cover the standalone and bundle directions.
3. **Runner, reasons.** The runner asserts that a negative fixture's raised codes include its declared `reason_code` wherever the normative layer raises codes at all; a fixture the schema alone refuses remains legitimate. The one wrong declared code is corrected.
4. **Runner, disclosure.** The rival-key scan applies to every stream kind, recursively over nested members, with a negative fixture on the transaction stream. `A202-LOT-ALREADY-AWARDED` joins the disclosure-bearing set, with a fixture, and the auction document states the same policy rule for it as for `A202-BID-NO-IMPROVEMENT`.
5. **Runner, chains.** `previous_event_hash` must name the immediately preceding same-stream event. A regression fixture carries continuous sequences with a skipping hash chain, which the previous runner passed.
6. **Schema and evaluator, `state_result`.** The shape closes to one subject and one registered state token; the evaluator refuses a subject differing from the determined question, an unregistered state, and any `state_result` under a non-binding effect. Fixtures cover both refusals.
7. **Session reference prefixes.** `clarification_id` and `approval_id` bind to the registered `clr_` and `apr_` prefixes, the `clr_` prefix is registered in the canonical model's prefix table, and canonical 12.1 now states accurately that patterns constrain the claimed family while opacity is enforced at resolution. A fixture refuses a foreign-prefix reference.
8. **Registry completeness.** The state machine's section 10 table is declared the registry, jointly with the auction and role-scope tables, and absorbs every code the manifest, runner, and other documents were already using.
9. **Counts.** The three documents that restated fixture counts now defer to the manifest as the single source. The role-scope partition is restated by family pattern so that it covers the whole manifest and does not go stale as the set grows; the reference package's suite test derives its expected total from the manifest instead of a hardcoded number.

## 3. What this proposal does not change

No object changes shape except `state_result`, whose previous shape was an open object nothing could rely on. No state, transition, or guard changes. No new aggregate capability is introduced; that is [A202-0010](A202-0010-model-completion.md). The changes make the specification's existing claims true, which is why they land as one proposal.

## 4. Compatibility

Under [RELEASES.md](../RELEASES.md) section 2 the set is pre-release and pre-1.0. The change set is **MAJOR-shaped** where it tightens (`state_result` shape, session reference prefixes, the stricter chain check, hash recomputation): an implementation that relied on the untightened forms was relying on gaps the prose already denied it. It is MINOR-shaped where it adds (the `mandate_chain` kind, new fixtures, registry rows). Pre-1.0, the set may break on a MINOR increment with migration notes; this section is those notes, and the affected surfaces are exactly the four named in this paragraph.

## 5. Fixture plan

Implemented, not planned: `valid-mandate-delegation-chain`, four `mandate-chain-*` widening negatives, `agreement-terms-hash-mismatch`, `transaction-event-data-discloses-rivals`, `policy-deny-award-disclosing-reason`, `session-event-clarification-foreign-prefix`, `determination-state-result-unregistered-state`, `determination-state-result-without-binding-effect`, and `evidence-bundle-event-chain-skips-predecessor`. The suite passes at the new totals the manifest carries, with the reason assertion active.
