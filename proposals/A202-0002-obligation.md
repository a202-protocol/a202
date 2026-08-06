# A202-0002: Obligation shape, due condition, and acceptance rule

**Status:** Fixtures and compatibility. Stage 3 of the five stages in [README.md](README.md) section 3. The static fixtures in section 5 are implemented in the conformance suite; the seven runtime cases in section 5.3 remain recorded for implementation-level verification.

**Date:** 27 July 2026

**Status of this document:** Informative in full. The normative text this proposal adopts is carried by [agreement/obligation-v0.1.md](../agreement/obligation-v0.1.md), which marks its own normative sections.

**Adopts:** [obligation v0.1](../agreement/obligation-v0.1.md)

## 1. Problem

The canonical model names `Obligation` in its object inventory, describes it as a "measurable duty, due condition, and acceptance rule", and defines none of the three. The state machine has an `obligation.activated` event that moves the aggregate from `committed` to `in_performance`, and a `performance.declared` and `acceptance.granted` pair that move it onward, with no object underneath any of them. The kernel schema has `obligation` in its `object_type` enum and `obl_` in its prefix table, and no payload definition.

What a counterparty cannot currently do:

- **Parse what it owes.** A supplier's agent receives a committed agreement and cannot compute, from the record, which discrete duties fall on it, in what quantity, or by when. The agreement carries terms; nothing decomposes them into duties with obligors.
- **Know when a duty is due.** There is no typed due condition, so an implementation either invents one or carries the due date as prose inside a term. Prose is not something a counterparty's agent can evaluate, and two implementations that parse it differently will disagree about whether a party is late.
- **Know what counts as done.** `acceptance.granted` moves the aggregate, and nothing states who may grant it, what it must bind to, or what happens when only part of what was owed is accepted.

The concrete situation where this goes wrong: a buyer commits to a supplier for ten calibration units against a `terms_hash`. The supplier delivers eight. Today the record can express `performance.declared` and `acceptance.granted`, and after that sequence the aggregate reads as if performance was accepted. Nothing in the record says two units are still owed. The party that most needs to prove they were owed has no object to point at.

A second failure is quieter. Because nothing binds an acceptance to the exact assertion it accepts, an acceptance and the performance it purports to accept can drift apart while both remain validly signed. The specification set already refuses that drift for offers, for agreements, and for approvals, and does not refuse it here.

## 2. Proposal summary

Adopt [obligation v0.1](../agreement/obligation-v0.1.md), which defines:

1. **The obligation object.** Common envelope, `obl_` prefix, non-null `transaction_id`. Payload carries `agreement_id`, `commitment_id`, `obligor` and `obligee` as `partyRef`, `subject`, `due_condition`, `quantity` as `quantityString`, `unit_code`, `consideration` as `money` or null, and `state`.
2. **Subject by reference.** `subject` names the owed term through the agreement's `terms_hash`, `profile`, and a `term_path` addressed the same way a mandate constraint `path` is. The obligation never restates a term, so a drifted copy becomes a hash mismatch rather than a second valid signature.
3. **Typed due conditions.** `due_at_time`, `due_on_event`, `due_on_discharge`, and `all_of`. AND composition only, one nesting level, closed registry, cycles refused. An unknown type fails closed with `A202-OBLIGATION-CONDITION-UNKNOWN`.
4. **Assertion and response as two acts.** The obligor asserts with a `performance_event` carrying at least one evidence reference. The obligee responds with an `obligation_response` bound to the assertion's `content_hash`, with `response_type` of `accept`, `reject`, or `waive`. Partial acceptance names a remainder obligation and never mutates the original. A rejection carries a reason code from a closed list and opens the dispute path without changing the obligation's terms.
5. **Nine states and a guarded transition table** in the style of the existing state machine, reusing `A202-STATE-TRANSITION-DENIED` rather than adding a parallel code.
6. **Nine refusal codes**, listed in section 7 of the adopted document.

## 3. Alternatives considered

**Do nothing.** Leave `Obligation` named and undefined. Rejected: every implementation then defines the object itself, and two implementations that both pass the current conformance suite can disagree about what a committed agreement obliges. That disagreement surfaces only after performance, which is the worst possible time to discover it.

**Carry the due date as a profile term and define no due condition.** Rejected: it moves the problem into every profile, so the same commercial concept gets a different shape per domain, and the kernel loses the ability to say anything about whether an obligation is due. It also violates the market-neutrality rule in the other direction, by putting a market-neutral concept behind a profile boundary.

**Make acceptance a version bump on the obligation.** Rejected: it makes the accepted state the only state visible in the current version, and reconstructing what was originally owed then depends on holding the whole version chain. It also makes partial acceptance a mutation, which erases the shortfall from the record.

**Allow OR and NOT in due conditions.** Rejected for v0.1: a disjunction is expressible as two obligations, and writing it out is what keeps the record replayable. Boolean combinators can be added later under a MINOR increment without invalidating anything written under AND only.

**Reuse the existing `acceptance` object type for performance acceptance.** Rejected: its payload is closed and bound to `offer_id` and `offer_hash`. Overloading it would make one type mean two different things at two different points in the lifecycle, and the disambiguation would have to be inferred from context.

## 4. Compatibility

### 4.1 What breaks

Nothing that is currently valid becomes invalid. No existing field changes meaning, no existing state is removed, no existing transition is narrowed, and no existing fixture is reclassified. Under [RELEASES.md](../RELEASES.md) section 2 this is a **MINOR** change: new object types, new payload definitions, new error codes for cases previously undefined.

### 4.2 Kernel schema changes required

| Change | Detail |
|---|---|
| Add `obligationPayload` `$def` and its conditional | Keyed on `object_type: obligation`, `id` pattern `^obl_`, `signatures` `minItems` 1 |
| Add `performanceEventPayload` `$def` and its conditional | `object_type: performance_event` is already in the enum. The payload is undefined today |
| Add `obligation_response` to the `object_type` enum | New type. Prefix `obr_` |
| Register two identifier prefixes | `obr_` for obligation response, and `prf_` for `performance_event`, which is in the `object_type` enum today with no entry in the prefix table of [canonical-commercial-model-v0.1.md](../schemas/canonical-commercial-model-v0.1.md) section 3. See section 4.5 |
| Add `subjectRef` and `dueCondition` `$defs` | Both reuse `sha256Hex`, `quantityString`, and the registered profile identifier pattern |

No new value type is introduced. `money`, `percentString`, `quantityString`, `partyRef`, and `sha256Hex` are reused unchanged, and the obligation object is refused if it introduces a parallel representation of any of them.

### 4.3 Existing objects

| Object | Effect |
|---|---|
| `Agreement` | Unchanged. An obligation references `agr_` and `terms_hash`, and the agreement does not reference obligations back |
| `Commitment` | Unchanged in shape. The relationship model already states that a commitment decomposes into obligations; the obligation now names the commitment it decomposes |
| `Offer`, `Acceptance` | Untouched. Nothing in the negotiation path changes |
| `CommercialMandate` | Unchanged in shape. Three action names are used by this proposal, `obligation.waive`, `performance.declare`, and `acceptance.grant`, and the `actions` array is already an open list of action names |
| `Evidence` | Referenced through the evidence reference shape adopted by [A202-0004](A202-0004-evidence-verification.md). See section 4.6 |

### 4.4 Existing states: `in_performance` and `exception_open` are the integration points

The aggregate state machine is unchanged. This proposal supplies the object beneath transitions that already exist.

| Aggregate transition | What this proposal adds beneath it |
|---|---|
| `committed` to `in_performance`, on `obligation.activated` | The obligation object the event activates, and the guard that its `subject.terms_hash` equals the agreement's `terms_hash` |
| `in_performance` to `acceptance_pending`, on `performance.declared` | The assertion object, and the requirement that it carries at least one evidence reference. The existing guard reads "evidence manifest present" and now has an object that satisfies it |
| `acceptance_pending` to `settlement_pending`, on `acceptance.granted` | The `obligation_response` bound to the assertion hash, signed by the obligee |
| `acceptance_pending` to `in_performance`, on `acceptance.rejected` | The `obligation_response` carrying a registered reason code. The existing required side effect reads "activate rework obligation if agreed", which is now the named remainder or a new obligation rather than an unspecified one |
| any eligible committed state to `exception_open`, on `exception.opened` | An obligation reaching `disputed` is the object-level fact behind the exception. The dispute itself is adopted by [A202-0003](A202-0003-determination.md) |
| `exception_open` to `in_performance`, on `remediation.accepted` | Remediation lands as a new obligation, so the transition has an object to activate |

One asymmetry is recorded rather than smoothed over. The aggregate carries a single `exception_open` state while an obligation set may carry several `disputed` obligations at once. The aggregate leaves `exception_open` when the events for that transition append, and not automatically when one obligation's dispute resolves. This proposal does not change that, and does not add a per-obligation aggregate state, because doing so would multiply the aggregate state space by the obligation count.

### 4.5 A prefix table gap found while drafting

`performance_event` and `exception` are members of the `object_type` enum in the kernel schema and have no entries in the identifier prefix table of [canonical-commercial-model-v0.1.md](../schemas/canonical-commercial-model-v0.1.md) section 3. The generic identifier pattern `^[a-z]{3}_` admits any three-letter prefix, so two implementations can mint different prefixes for the same object type and both validate.

This proposal registers `prf_` for `performance_event`, because obligation discharge depends on that object. It does not register a prefix for `exception`, which is out of its scope and is recorded here so it is not lost.

### 4.6 Ordering against A202-0004

The assertion requires at least one evidence reference in the shape defined by [evidence-verification-v0.1.md](../evidence/evidence-verification-v0.1.md) section 3, which [A202-0004](A202-0004-evidence-verification.md) adopts. A202-0002 depends on A202-0004 for that shape and on nothing else in it. Either both land in one release or A202-0004 lands first. They cannot land in the reverse order, because the assertion rule would then reference an undefined shape.

### 4.7 Migration

There is nothing to migrate. No obligation object exists under any earlier version of the specification set, because none was defined. An implementation that has been minting an object of its own design under the `obl_` prefix is not migrating from a previous version of this specification; it is adopting the specification for the first time.

## 5. Fixture plan

The published suite holds 7 positive and 31 negative fixtures. The ratio is deliberate, and this proposal is weighted the same way: 2 positive and 13 negative static fixtures, plus 7 cases that require runtime state.

### 5.1 Positive

| Fixture | What it exercises |
|---|---|
| `valid-obligation.json` | A complete obligation: subject by reference against a `terms_hash`, a `due_at_time` condition, quantity and unit code, and `money` consideration |
| `valid-obligation-response-partial-acceptance.json` | Accept in the allow direction with `accepted_quantity` below `quantity` and a named `remainder_obligation_id` |

### 5.2 Negative

| Fixture | Expected code | What it refuses |
|---|---|---|
| `negative/obligation-condition-type-unknown.json` | `A202-OBLIGATION-CONDITION-UNKNOWN` | An unregistered due condition type. Fails closed at schema and independently at evaluation |
| `negative/obligation-condition-fields-of-another-type.json` | `A202-OBLIGATION-CONDITION-UNKNOWN` | `type: due_at_time` carrying `obligation_id`. A registered type wearing another type's fields |
| `negative/obligation-condition-cycle.json` | `A202-OBLIGATION-CONDITION-CYCLIC` | Two obligations each due on the other's discharge. Neither can ever become due, and today nothing says so |
| `negative/obligation-condition-nested-all-of.json` | `A202-OBLIGATION-CONDITION-UNKNOWN` | `all_of` nested more than one level |
| `negative/obligation-subject-restates-terms.json` | `A202-OBLIGATION-SUBJECT-UNREFERENCED` | `subject` carrying a copy of the term instead of a `term_path` and `terms_hash` |
| `negative/obligation-subject-terms-hash-mismatch.json` | `A202-OBLIGATION-SUBJECT-UNREFERENCED` | `subject.terms_hash` differing from the referenced agreement's. This is the drift case, caught as a hash mismatch |
| `negative/obligation-obligee-not-party-to-agreement.json` | `A202-OBLIGATION-SUBJECT-UNREFERENCED` | An obligee that is neither the buyer nor the supplier on the agreement |
| `negative/obligation-assertion-no-evidence.json` | `A202-OBLIGATION-ASSERTION-UNEVIDENCED` | An assertion with an empty `evidence_refs` |
| `negative/obligation-response-hash-mismatch.json` | `A202-OBLIGATION-RESPONSE-HASH-MISMATCH` | A response whose `assertion_hash` does not match the named assertion. The direct analogue of `A202-APPROVAL-HASH-MISMATCH` |
| `negative/obligation-response-signed-by-obligor.json` | `A202-OBLIGATION-RESPONSE-UNAUTHORIZED` | The obligor accepting its own performance |
| `negative/obligation-waiver-signed-by-obligor.json` | `A202-OBLIGATION-RESPONSE-UNAUTHORIZED` | The obligor waiving its own obligation. Held separately from the case above because a waiver names no assertion, so a check written only against `assertion_id` would miss it |
| `negative/obligation-partial-acceptance-no-remainder.json` | `A202-OBLIGATION-REMAINDER-MISSING` | Eight of ten accepted with no remainder obligation. The shortfall would otherwise disappear from the record |
| `negative/obligation-partial-acceptance-mutates-quantity.json` | `A202-OBLIGATION-TERMS-MUTATED` | A response that rewrites the obligation's `quantity` to the accepted amount |
| `negative/obligation-rejection-reason-unregistered.json` | `A202-OBLIGATION-REJECTION-REASON-UNKNOWN` | A rejection carrying a reason code outside the closed list |
| `negative/obligation-consideration-negative-money.json` | `A202-TERMS-INVALID` | A negative `consideration`. Confirms the obligation reuses `money` rather than a parallel type, which is the failure this fixture exists to catch |
| `negative/obligation-due-business-days-no-calendar.json` | `A202-TERMS-INVALID` | A `due_at_time` expressed in business days with no named calendar |

### 5.3 Cases requiring runtime state

These cannot be expressed as static documents and are verified against a running implementation, in the manner of the existing runtime lists.

1. An obligation whose due condition is met moves `pending` to `due`, and one whose condition is not met does not.
2. A rejected obligation accepts a second assertion, and each response binds exactly one assertion hash.
3. An advisory determination on a disputed obligation leaves the obligation in `disputed`. This is the fail-closed case: an implementation that lets any determination move state passes every static fixture and fails here.
4. A presumptive determination likewise leaves the obligation in `disputed`.
5. A binding determination moves the obligation only where the target transition would be legal for any other event.
6. `obligation.activated` against an agreement whose `terms_hash` differs is refused, and the aggregate stays in `committed`.
7. A waiver from `pending` and a waiver from `due` both reach `waived`, and a waiver from `discharged` is refused with `A202-STATE-TRANSITION-DENIED`.

## 6. Origin

Drafted against the object inventory and the state machine of the v0.1 specification set, which name `Obligation`, `obligation.activated`, `performance.declared`, and `acceptance.granted` without defining the object any of them acts on. The partial-acceptance case in section 1 is the situation that forced the split between an accepted obligation and a remainder obligation rather than a mutation. This is context for reviewers rather than an argument.
