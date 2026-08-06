# Obligation v0.1

**Status:** Experimental, adopted through proposal [A202-0002](../proposals/A202-0002-obligation.md). Mixed. Sections 2, 3, 4, 5, 6, and 7 are **normative**. Sections 1 and 8 are **informative** and state no requirement on an implementation.

**Date:** 27 July 2026

**Revised:** 28 July 2026, under [A202-0010](../proposals/A202-0010-model-completion.md): the `released` terminal state and the `obligation.released` transition, so that a terminated transaction cannot strand an open obligation. Also under [A202-0011](../proposals/A202-0011-registry-and-waiver-corrections.md): the waiver reaches `asserted` and `rejected`, which section 5.4 already described as available.

**Scope:** Synthetic pilot transactions only

**Depends on:** [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md), [commercial mandate v0.1](../authority/commercial-mandate-v0.1.md), [pilot transaction state machine v0.1](../negotiation/pilot-transaction-state-machine-v0.1.md), [evidence verification v0.1](../evidence/evidence-verification-v0.1.md), [determination and dispute v0.1](../disputes/determination-v0.1.md)

## 1. Purpose

A commitment produces obligations. A counterparty cannot discharge an obligation it cannot parse, and two organisations that agree on price and then disagree on what was owed have not agreed on anything durable.

This document defines four things and nothing else: what is owed, by whom, when it is due, and what counts as done.

Everything that happens around those four is outside this specification. Tracking an obligation, monitoring its due condition, reminding a party, escalating, and enforcing a failure are operator concerns. They are not published here and an implementation is not conformant or non-conformant by reference to them. What is published is the shape a counterparty parses, the transitions the shape may take, and the refusals that hold when the shape or the transition is wrong.

The relationship to the transaction aggregate is already fixed. `obligation.activated` moves the aggregate from `committed` to `in_performance`, and a dispute over an obligation is an exception that moves the aggregate to `exception_open`. This document specifies the object underneath those transitions rather than adding new aggregate states.

## 2. Conformance language

`MUST`, `MUST NOT`, `REQUIRED`, `SHOULD`, `SHOULD NOT`, and `MAY` are normative within this experimental specification.

An implementation conforms to this specification when it:

1. validates `obligation`, `performance_event`, and `obligation_response` objects against `../schemas/v0.1/commercial-kernel.schema.json`;
2. enforces the due-condition typing rules in section 4;
3. enforces the discharge and acceptance rules in section 5;
4. enforces the guarded transitions in section 6;
5. returns the refusal codes in section 7 for the failures they name;
6. passes the obligation fixtures in `../conformance/manifest-v0.1.json`.

Schema validity is necessary and not sufficient. The rules in sections 4, 5, and 6 are cross-object and cannot be expressed in JSON Schema alone.

## 3. The obligation object

An obligation is a shared kernel object. It carries the common envelope defined in [canonical-commercial-model-v0.1.md](../schemas/canonical-commercial-model-v0.1.md) section 3, uses the `obl_` identifier prefix, and is canonicalised, hashed, and signed under section 4 of that document. `transaction_id` is REQUIRED and non-null.

| Field | Type | Rule |
|---|---|---|
| `agreement_id` | `agr_` identifier | The agreement the obligation derives from. REQUIRED |
| `commitment_id` | `cmt_` identifier | The commitment this obligation decomposes. REQUIRED |
| `obligor` | `partyRef` | The party that owes. REQUIRED |
| `obligee` | `partyRef` | The party owed to. REQUIRED |
| `subject` | `subjectRef` | What is owed, by reference. See section 3.1. REQUIRED |
| `due_condition` | `dueCondition` | When it is due. See section 4. REQUIRED |
| `quantity` | `quantityString` | How much is owed, in the same representation the kernel uses for terms. REQUIRED |
| `unit_code` | UN/ECE Recommendation 20 common code | REQUIRED. `unit_name` MAY accompany it and MUST NOT be used for matching or validation |
| `consideration` | `money` or null | The consideration attached to this obligation, where the agreement attaches one. Null where it does not |
| `state` | enum | One of the states in section 6. REQUIRED |

`obligor` and `obligee` MUST both appear in the referenced agreement as `buyer` or `supplier`. An obligation naming a party that is not a party to the agreement is refused with `A202-OBLIGATION-SUBJECT-UNREFERENCED`.

Money uses the `money` type. Percentages, where a profile term expresses one, use `percentString`. An obligation MUST NOT introduce a parallel representation for either.

### 3.1 Subject is a reference, never a restatement

`subject` names what is owed by pointing at the agreement's terms. It does not copy them.

| Field | Type | Rule |
|---|---|---|
| `agreement_id` | `agr_` identifier | MUST equal the obligation's `agreement_id` |
| `terms_hash` | `sha256Hex` | MUST equal the referenced agreement's `terms_hash` |
| `profile` | registered profile identifier | MUST equal the agreement's `terms.profile` |
| `term_path` | path expression | Addresses the term under `$.terms.core` or `$.terms.profile_terms` |

`term_path` uses the same path addressing as a mandate constraint `path`, so a term that a mandate constrains and a term that an obligation owes are named the same way. A path that addresses a term outside the referenced profile, or that does not resolve against the referenced terms, is refused with `A202-OBLIGATION-SUBJECT-UNREFERENCED`.

Restating a term inside the obligation would create a second copy that can drift from the agreement, and the drift would be invisible because both copies would be validly signed. Reference plus terms hash makes drift a hash mismatch instead.

An obligation MUST NOT carry any of the private data classes listed in [canonical-commercial-model-v0.1.md](../schemas/canonical-commercial-model-v0.1.md) section 13.

## 4. Due condition

`due_condition` is typed. It is never free text, because a due date a counterparty has to read in order to compute is a due date the counterparty's agent cannot act on.

Three condition types are registered in v0.1, plus one composition.

| `type` | Fields | Meaning |
|---|---|---|
| `due_at_time` | `at`, RFC 3339 timestamp in UTC, or a date with a named business calendar reference | Due at a stated time |
| `due_on_event` | `act_ref`, or `evidence_type`, exactly one of the two | Due when the referenced act appends, or when evidence of the referenced registered type is presented and verifies |
| `due_on_discharge` | `obligation_id` | Due when the named obligation reaches `discharged`. This is how ordering between obligations is expressed |
| `all_of` | `conditions`, at least two entries | Due when every listed condition is met |

Rules:

1. Conditions compose with AND only. There is no OR and no NOT in v0.1. A disjunction is expressible as two obligations, and stating that explicitly is what makes the record replayable.
2. `all_of` MUST NOT nest more than one level deep. A nested conjunction is a flat conjunction written twice.
3. `due_on_event` MUST reference an act by content hash, or an evidence type from the registered evidence type list defined in [evidence-verification-v0.1.md](../evidence/evidence-verification-v0.1.md) section 3. An unregistered evidence type fails closed.
4. `due_on_discharge` MUST reference an obligation on the same `transaction_id`. A cycle among `due_on_discharge` references is refused: no obligation in the cycle can ever become due, so accepting the cycle would create an obligation set that is permanently unsatisfiable and silently so.
5. A `due_at_time` value expressed in business days MUST name a calendar, as required by [canonical-commercial-model-v0.1.md](../schemas/canonical-commercial-model-v0.1.md) section 7. A duration in business days with no named calendar is not a term.

An unknown `type`, or a registered `type` with fields belonging to a different one, fails closed with `A202-OBLIGATION-CONDITION-UNKNOWN`. The registry is closed in v0.1 and is enforced at validation and independently at evaluation, so that adding a member to the schema enum without an evaluator implementation cannot cause an obligation to become due.

## 5. Discharge and acceptance

Performance and acceptance are two acts by two parties. Collapsing them lets the obligor declare its own obligation discharged.

### 5.1 Assertion

The obligor asserts performance by appending a `performance_event` object that:

1. names the obligation in `obligation_id`;
2. carries at least one evidence reference in `evidence_refs`, in the shape defined in [evidence-verification-v0.1.md](../evidence/evidence-verification-v0.1.md) section 3;
3. states `asserted_quantity` and `unit_code`, where `unit_code` equals the obligation's;
4. is signed by the obligor.

An assertion with no evidence reference is refused with `A202-OBLIGATION-ASSERTION-UNEVIDENCED`. An assertion carries a claim about the world, and a claim with nothing behind it cannot be checked by the obligee now or by a third party later.

The assertion's `content_hash` is the assertion hash. It is the value the obligee's response binds to.

### 5.2 Response

The obligee responds by appending an `obligation_response` object, signed by the obligee, with `response_type` one of `accept`, `reject`, or `waive`.

| Field | Rule |
|---|---|
| `obligation_id` | REQUIRED. The obligation responded to |
| `response_type` | REQUIRED. `accept`, `reject`, or `waive` |
| `assertion_id` | REQUIRED for `accept` and `reject`. Absent for `waive` |
| `assertion_hash` | REQUIRED for `accept` and `reject`. MUST equal the referenced assertion's `content_hash` |
| `accepted_quantity` | REQUIRED for `accept`. A `quantityString` at or below the asserted quantity |
| `remainder_obligation_id` | REQUIRED for `accept` where `accepted_quantity` is below the obligation's `quantity`. Absent otherwise |
| `reason_code` | REQUIRED for `reject`. From the closed list in section 5.5 |

Four rules hold and an implementation MUST enforce each independently.

1. **Acceptance is a distinct signed act by the obligee.** A response signed by any party other than the obligee named on the obligation is refused with `A202-OBLIGATION-RESPONSE-UNAUTHORIZED`. This holds for `waive` as well as for `accept`.
2. **Acceptance binds an exact assertion.** `assertion_hash` MUST equal the `content_hash` of the assertion named in `assertion_id`. A mismatch is refused with `A202-OBLIGATION-RESPONSE-HASH-MISMATCH`. Changing one byte of the assertion invalidates the response, exactly as changing one byte of an action invalidates an approval under [commercial-mandate-v0.1.md](../authority/commercial-mandate-v0.1.md) section 8.
3. **Partial acceptance creates a new obligation.** Where `accepted_quantity` is below the obligation's `quantity`, the response MUST name a `remainder_obligation_id`, and that obligation MUST reference the same `agreement_id`, the same `subject`, and a `quantity` equal to the difference. A partial acceptance with no remainder named is refused with `A202-OBLIGATION-REMAINDER-MISSING`.
4. **No response mutates the obligation.** An obligation's `subject`, `due_condition`, `quantity`, `unit_code`, and `consideration` are fixed at issue. A response that would alter any of them is refused with `A202-OBLIGATION-TERMS-MUTATED`. Changed terms are a new obligation under an amended agreement, never a new version of this one.

### 5.3 Why partial acceptance is never a mutation

If accepting eight of ten units rewrote the obligation to say eight, the record would afterwards show an obligation that was fully performed. The two units that were not delivered would have left no trace, and the party that most needs to prove they were owed would be the party whose evidence had been edited away. Splitting into an accepted obligation and a remainder obligation keeps both facts, and both remain independently verifiable.

### 5.4 Rejection

A rejection carries a `reason_code` and leaves the obligation's terms untouched. It moves the obligation to `rejected` and opens the dispute path defined in [determination-v0.1.md](../disputes/determination-v0.1.md). It does not renegotiate the obligation, and it does not by itself determine anything: a rejection is one party's position, and a determination is what resolves a contested one.

The obligor MAY assert again against the same obligation. Each assertion is a new object with its own hash, and each response binds exactly one of them.

### 5.5 Rejection reason codes

The list is closed in v0.1. An unregistered value is refused with `A202-OBLIGATION-REJECTION-REASON-UNKNOWN`.

| `reason_code` | Meaning |
|---|---|
| `evidence_insufficient` | The evidence presented does not support the assertion |
| `evidence_unverified` | Required evidence is absent or failed verification |
| `quantity_short` | The asserted quantity is below what the obligation owes and no remainder was accepted |
| `subject_not_as_agreed` | What was performed does not match the referenced term |
| `due_condition_not_met` | The obligation was not due when the assertion was made |
| `assertion_unauthorized` | The assertion was not signed under a mandate covering the obligor's act |

Each value is stated from the obligee's own position. None of them discloses the identity, price, count, or timing of any other party's activity on the transaction, and an implementation MUST NOT extend the list with a value that would.

## 6. States and transitions

| State | Meaning |
|---|---|
| `pending` | The obligation exists and its due condition is not met |
| `due` | The due condition is met and no assertion is outstanding |
| `asserted` | The obligor asserted performance and the obligee has not responded |
| `accepted` | The obligee accepted an assertion |
| `rejected` | The obligee rejected an assertion |
| `disputed` | A dispute has been raised on the obligation |
| `discharged` | Nothing further is owed under this obligation |
| `waived` | The obligee released the obligor by signed act |
| `expired` | A deadline elapsed before the obligation was discharged or waived |
| `released` | The transaction ended through an authorized termination whose record named this obligation's disposition |

`discharged`, `waived`, `expired`, and `released` are terminal in v0.1.

`released` exists because a terminated transaction must not strand its obligations. It is distinct from `waived` because the release is carried by the termination record both parties signed, not by a unilateral obligee response, and distinct from `discharged` because nothing was performed. The record shows that the duty ended with the transaction, which is a different fact from the duty having been met.

### 6.1 Transition table

| Current | Event | Guard | Next |
|---|---|---|---|
| none | `obligation.activated` | Obligation derives from a committed agreement; `subject.terms_hash` equals the agreement's `terms_hash` | `pending` |
| `pending` | `obligation.due` | Every clause of `due_condition` evaluates true against a referenced act, evidence, discharge, or the authoritative clock | `due` |
| `pending`, `due`, `asserted`, or `rejected` | `obligation.waived` | Response signed by the obligee with `response_type` `waive` | `waived` |
| `pending` or `due` | `deadline.elapsed` | Authoritative clock passed the agreement or transaction deadline governing this obligation | `expired` |
| `due` | `performance.declared` | Assertion names this obligation, carries at least one evidence reference, and is signed by the obligor | `asserted` |
| `asserted` | `acceptance.granted` | Response signed by the obligee; `response_type` `accept`; `assertion_hash` matches; remainder named where the accepted quantity is short | `accepted` |
| `asserted` | `acceptance.rejected` | Response signed by the obligee; `response_type` `reject`; `assertion_hash` matches; `reason_code` registered | `rejected` |
| `asserted`, `accepted`, or `rejected` | `dispute.raised` | Dispute references this obligation's state by content hash and is raised inside the window in force | `disputed` |
| `rejected` | `performance.declared` | A new assertion, with its own hash, naming the same obligation | `asserted` |
| `accepted` | `obligation.discharged` | `accepted_quantity` equals `quantity`, or a remainder obligation exists and is named | `discharged` |
| `disputed` | `determination.recorded` | The determination's stated effect is `binding` on this question under the rules in force at the time | the state the determination states |
| `disputed` | `determination.recorded` | The determination's stated effect is `advisory` or `presumptive` | `disputed` |
| `pending`, `due`, `asserted`, `rejected`, or `disputed` | `obligation.released` | The transaction appended `termination.agreed` or `transaction.terminated`, and the termination record names this obligation's disposition | `released` |

Two guards carry most of the weight and are stated separately because they are easy to lose.

**A determination moves state only where the rules granted it that effect.** An advisory or presumptive determination is evidence and is recorded as evidence. It does not move the obligation, and an implementation that lets it move the obligation has given a determination an effect the parties did not agree to. This fails closed: where the effect is unstated or does not resolve, the obligation does not move.

**A rejection does not end the obligation.** `rejected` is not terminal. The obligation is still owed, and the path forward is a further assertion, a waiver, a determination, or expiry.

**A waiver is available wherever the obligation is still owed.** The obligee may release the obligor from `pending`, `due`, `asserted`, and `rejected`. Restricting the waiver to the states before an assertion would mean that an obligee who wished to release its counterparty after seeing a partial or unsatisfactory assertion had no way to say so: it would have to accept performance it did not receive, or reject and wait for a deadline it did not want to enforce. Both would put a false record on the transaction, and the second leaves the obligation owed until it expires, which is a worse outcome for the obligor the waiver was meant to benefit.

A waiver is deliberately not available from `disputed`. A dispute is a contested question already before a determiner, and a unilateral release while it is open would moot a determination the other party is entitled to receive. The obligee that wishes to release a disputed obligation withdraws its position through the dispute path, and the determination records what happened.

### 6.2 Relationship to the aggregate

The aggregate transitions are unchanged by this document.

| Obligation event | Aggregate effect under [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) |
|---|---|
| `obligation.activated` | `committed` to `in_performance` |
| `performance.declared` | `in_performance` to `acceptance_pending` |
| `acceptance.granted` | `acceptance_pending` to `settlement_pending` |
| `acceptance.rejected` | `acceptance_pending` to `in_performance` |
| `dispute.raised` on an obligation | `exception.opened`, reaching `exception_open` |
| `obligation.released` | None. The aggregate already moved to `terminated`; the release is the obligation-level consequence, not a further aggregate event |

An obligation reaching `disputed` is the object-level fact behind `exception.opened`. The aggregate carries one exception state; an obligation set may carry several disputed obligations at once, and the aggregate leaves `exception_open` only when the events for that transition append.

An illegal transition returns `A202-STATE-TRANSITION-DENIED`, the existing code, rather than a new one. There is one state machine vocabulary and this document joins it.

## 7. Refusal codes

All fail closed. These extend the table in [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) section 10.

| Code | Meaning |
|---|---|
| `A202-OBLIGATION-CONDITION-UNKNOWN` | A due condition names an unregistered type, or a registered type with fields belonging to a different one |
| `A202-OBLIGATION-CONDITION-CYCLIC` | A set of `due_on_discharge` conditions forms a cycle, so no obligation in it can become due |
| `A202-OBLIGATION-SUBJECT-UNREFERENCED` | `subject` does not resolve against the referenced agreement, its terms hash differs, or a named party is not a party to the agreement |
| `A202-OBLIGATION-ASSERTION-UNEVIDENCED` | An assertion carries no evidence reference |
| `A202-OBLIGATION-RESPONSE-UNAUTHORIZED` | A response was signed by a party other than the obligee |
| `A202-OBLIGATION-RESPONSE-HASH-MISMATCH` | A response references different assertion bytes |
| `A202-OBLIGATION-REMAINDER-MISSING` | A partial acceptance names no remainder obligation |
| `A202-OBLIGATION-TERMS-MUTATED` | An act would alter an obligation's subject, due condition, quantity, unit code, or consideration |
| `A202-OBLIGATION-REJECTION-REASON-UNKNOWN` | A rejection carries a reason code outside the closed list |

Codes reused unchanged from existing specifications, rather than duplicated here: `A202-STATE-TRANSITION-DENIED` for an illegal transition, `A202-SEQUENCE-CONFLICT` for a stream conflict, `A202-EVIDENCE-UNVERIFIED` for absent or failed evidence, `A202-MANDATE-INACTIVE` for an act under an inactive mandate, and `A202-AGREEMENT-HASH-MISMATCH` for an agreement hash that does not match.

## 8. Explicit non-goals

None of the following is specified here, and an implementation is neither conformant nor non-conformant by reference to any of them.

1. **Delivery logistics.** Routing, carriage, handover, custody, and the operational sequence by which performance actually happens.
2. **Quality standards.** What counts as acceptable quality for a given subject. That belongs to the transaction profile, to a referenced external standard, or to the agreement's own terms, and this document only carries the reference.
3. **Tracking.** Holding obligation state, watching due conditions, and computing what is outstanding across a portfolio.
4. **Reminders and notification.** Who is told what, when, and through which channel.
5. **Enforcement.** What happens when an obligation is not performed. This document defines the states a failure produces and the record it leaves. It does not define a remedy, and nothing here makes any obligation enforceable at law.

Each is named because a reader would otherwise reasonably expect to find it in a document about obligations. A non-goal is a statement about this specification's scope, not a claim that the excluded capability is unimportant.
