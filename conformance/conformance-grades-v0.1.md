# Conformance grades v0.1

**Status:** Experimental working specification. Mixed. Sections 2, 3, 4, 5, and 6 are **normative**. Sections 1 and 7 are **informative** and state no requirement on an implementation.

**Date:** 26 July 2026

**Revised:** 30 July 2026, under [A202-0015](../proposals/A202-0015-fixture-minimality-orphan-codes-and-grade-scope.md): section 4 states the structure of `scope`, of `dimensions`, and of `held_out_coverage` explicitly, so that the grade object can be fixtured and the role scope rules can be checked rather than asserted. The `scope` example that named "bidder" and "event operator", neither of which resolves in the role scope registry, is replaced by the registered identifiers. No dimension, band, constraint, or appeal rule changes.

**Depends on:** [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md), [commercial mandate v0.1](../authority/commercial-mandate-v0.1.md), [pilot transaction state machine v0.1](../negotiation/pilot-transaction-state-machine-v0.1.md), [auction event semantics v0.1](../negotiation/auction-event-semantics-v0.1.md), and the fixture set, manifest, and runner in this directory

**No external body recognises anything defined here.** A grade defined by this document is a statement by whichever party issued it, about one implementation, scoped to one specification version. It is not certification by a standards body, a regulator, an auditor, or an insurer, and no material may describe it as one.

## 1. What a grade measures

A grade measures whether an implementation **refuses correctly**, not whether it works.

An implementation that passes every positive fixture has demonstrated that it can transact on a good day. Loss in agent-mediated commerce comes from the other direction: authority that outlived its revocation, a disclosure that let one counterparty infer another, a commitment that was accepted when it should have been refused, an unparseable input that was guessed at rather than rejected.

The published suite in this directory is therefore weighted toward negative fixtures, and the manifest is the single source for how many there are: a count restated here went stale once already, and this sentence now defers to `manifest-v0.1.json` instead of repeating one. The negative-to-positive ratio has stayed near five to one as the set has grown, and the ratio is deliberate. The grade defined below is weighted the same way, toward behaviour under hostile and malformed input.

## 2. Dimensions

A grade is a vector, never a single letter. A scalar hides exactly the information a relying party needs in order to decide whether this implementation may hold commitment authority in its transactions.

| # | Dimension | What it covers | Principal loss it predicts |
|---|---|---|---|
| **A** | **Authority handling** | Mandate parse, delegation chain narrowing, per-hop expiry, revocation signalling, fail-closed behaviour when a status endpoint is unreachable | A commitment made without valid authority behind it |
| **B** | **Disclosure and isolation** | Rival non-inference, denied-action visibility, close-reason discipline, refusal codes that carry aggregate state, timing and error-code side channels | One counterparty inferring another's existence, activity, or terms |
| **C** | **Commitment integrity** | Acceptance versus commitment separation, dual signature, guarded state transitions, award subordination, replay of transitions | A record read as a binding agreement when it is not, or a commitment that cannot be reconstructed |
| **D** | **Evidence** | Portable export, hash scope and canonicalisation, deterministic replay by a third party | An event that cannot be proved after the fact |
| **E** | **Adversarial failure behaviour** | Response to malformed, hostile, unregistered, and unanticipated input. Whether the implementation refuses or guesses | Silent wrong results, which are the failure mode that tests written by the same party never catch |

A grade MUST report all five dimensions. A dimension that was not assessed is reported explicitly as unassessed, never omitted.

## 3. Bands

Each dimension is scored on a four-point band.

| Band | Meaning |
|---|---|
| **0** | Fails at least one published negative fixture in the dimension |
| **1** | Passes the published set for the dimension |
| **2** | Passes the published set, and also passes an assessor's held-out case set exercising the same invariants as the published set |
| **3** | Passes both, and refuses cleanly on inputs no fixture anticipated, with a correct reason code rather than a generic error |

Band 2 requires that the subject was measured on rules it was told about, using inputs it was not given. The invariants exercised are the invariants of this specification set. A band 2 result therefore says that the implementation enforces the rule rather than that it recognises the fixture.

Band 3 is not reachable by automated fixture execution alone. It requires an assessor to construct inputs outside any published or held-out set and to judge the quality of the refusal. It is the band that separates an implementation that was tested from one that was designed to fail closed.

## 4. The grade object

A grade is emitted as a signed, machine-readable object, versioned alongside the kernel schemas.

| Field | Purpose |
|---|---|
| `subject` | The assessed implementation and the organisation responsible for it |
| `spec_version` | The specification version assessed. A grade is meaningless without it |
| `level` | The assessment level at which the grade was established. A grade is held at the level it was assessed at and is never inferred at a higher one |
| `dimensions` | Band per dimension A to E, and for each band the fixture families it was established from. Always all five, with any unassessed dimension explicitly null rather than absent |
| `scope` | Transaction profile coverage, transport coverage, and exactly one role scope identifier. A grade earned against `a202-scope/bilateral/0.1` says nothing about behaviour against `a202-scope/operated/0.1` |
| `held_out_coverage` | Which dimensions a held-out case set exercised, the case count, and the fixture families the cases were drawn against. Coverage and count only, never case content |
| `issued_at`, `expires_at` | Expiry is 12 months or the next specification minor version, whichever is first |
| `status` | `active`, `expired`, `suspended`, `withdrawn`, `under_appeal` |
| `determination_ref` | Reference to the determination record, so that a grade is contestable in the same way a protocol determination is |
| `signature` | Issuance signature |

### 4.1 The structure of `scope`, `dimensions`, and `held_out_coverage`

Three of the fields above carry structure rather than a scalar, and until 30 July 2026 this section described them in prose alone. The prose was not enough to write a grade against: it named "roles covered" with an example that resolved in no registry, and it said a band was established from a scope without saying where a band records what established it. The three shapes below close that, and [conformance-grade.schema.json](../schemas/v0.1/conformance-grade.schema.json) carries them.

**`scope`** is an object with three members.

| Member | Contents |
|---|---|
| `role_scopes` | An array of role scope identifiers from section 3.1 of [conformance-role-scopes-v0.1.md](conformance-role-scopes-v0.1.md). A grade MUST name exactly one. An identifier that does not resolve there is refused with `A202-GRADE-SCOPE-UNKNOWN`; naming none or naming more than one is refused with `A202-GRADE-SCOPE-INVALID` |
| `profiles` | The transaction profile identifiers the assessment covered |
| `transports` | The carrier extension URIs the assessment covered |

The member is an array although exactly one identifier is permitted. The cardinality rule is a refusal carrying a reason code, not a shape: a grade naming none is the unscoped form that existed before the registry, a grade naming two is the form that claims one assessment as two, and both have to be expressible in order to be refused with the code section 3.2 of the role scope document names. A shape that could not express them could not fixture them either.

**`dimensions`** is an object with the five members `A` to `E`. Each is either `null`, meaning the dimension was not assessed, or an object carrying `band`, an integer 0 to 3 from section 3, and `established_from`, the fixture families the band was established from. A band that does not record what established it cannot be checked against the scope it is reported under, and section 6.3 of the role scope document requires exactly that check.

**`held_out_coverage`** is `null` where no held-out set was used, or an object carrying `dimensions`, the dimension letters the held-out cases exercised, `case_count`, and `families`, the fixture families the cases were drawn against. It reports coverage and count and never case content.

A **fixture family identifier** is a family's name in the Family column of sections 4.3 and 5.3 of [conformance-role-scopes-v0.1.md](conformance-role-scopes-v0.1.md), lowercased with spaces replaced by hyphens: `mandate`, `delegation-chain`, `evidence-and-verification`, `session-event`, and so on. A family outside the scope the grade names is the overclaim refused with `A202-GRADE-SCOPE-OVERCLAIM`.

Nothing else about the field set changes. Profile and transport coverage are carried as they were carried before, verbatim, and this section states no registry for either.

### 4.2 Design constraints

Four design constraints hold, and an implementation of this object MUST satisfy all four.

1. **No overall score.** The object carries no composite figure and no weighting. A consumer combines the vector under its own policy. A published weighting is immediately optimised against, which converts the grade from a measurement into a target.
2. **Absence is not a pass.** A null dimension reads as unassessed everywhere it is consumed. A relying party that treats null as satisfactory has misconfigured its own bar, and the object MUST NOT make that reading easy by omitting the field.
3. **Expiry is enforced, not advisory.** An expired grade fails a check exactly as a band 0 does. A consumer MUST evaluate `expires_at` before relying on `dimensions`.
4. **A grade is never raised by re-running.** A failed assessment is recorded. Re-assessment is available after a stated remediation interval, and the record shows the sequence rather than the best result. This is what stops grade shopping.

## 5. Published fixture policy

The published fixture set is the set a subject is measured against for band 1, and it is the set an implementer may use freely to test against before any assessment takes place.

1. The published set, the manifest, and the runner are open. Anyone may execute them, and a self-run result is a legitimate statement by the party that ran it. It is not a grade, because a published fixture can be hard-coded and a self-run result carries no independent evidence that it was not.
2. Publication is one way. A fixture that enters the published set stays published. It does not return to any held-out set afterwards, so a contributed fixture is a permanent addition to what every implementer can see.
3. Band 1 is defined entirely by the published set. An implementation that passes it has demonstrated exactly that, and the grade says so and no more.
4. Above band 1, a subject is measured using inputs it was not given. `held_out_coverage` reports which dimensions were exercised and how many cases were used. It MUST NOT disclose the cases themselves, because a disclosed case is a case the next subject can hard-code.

## 6. Appeal

A grade is a determination and is appealable on the same terms as any other determination under this specification set.

**Grounds.** An appeal MUST state at least one of:

1. the rule was misapplied;
2. the input did not exercise the stated invariant;
3. the scope was wrong;
4. the specification version was wrong.

Disagreement with the rule itself is not a ground of appeal. That is a change proposal against this specification, and it goes through the proposal process rather than through an appeal.

**Effect on status.** While an appeal is open, `status` becomes `under_appeal` and the prior grade stands. It is neither raised nor suspended. Both would let the act of appealing move the outcome, which would make appealing a tactic rather than a remedy.

**Determination.** An appeal determination is written, recorded alongside the original, and supersedes it. It never deletes it. A record that can be deleted when it is unfavourable is a record nobody has a reason to read.

## 7. Open questions

- Whether a subject may hold different grades for different scopes at the same time, and how a relying party evaluates a mixed holding.
- Whether an implementation assessed while running under a hosting provider inherits or shares that provider's grade, and how the boundary is stated when the provider custodies keys.
