# A202-0003: Determination and dispute family

**Status:** Fixtures and compatibility. Stage 3 of the five stages in [README.md](README.md) section 3. The static fixtures in section 5 are implemented in the conformance suite; the eight runtime cases in section 5.3 remain recorded for implementation-level verification.

**Date:** 27 July 2026

**Status of this document:** Informative in full. The normative text this proposal adopts is carried by [disputes/determination-v0.1.md](../disputes/determination-v0.1.md), which marks its own normative sections.

**Adopts:** [determination and dispute v0.1](../disputes/determination-v0.1.md)

## 1. Problem

The specification set defines authority, typed state, disclosure rules, and replay. It defines no way to contest any of them.

Three concrete gaps:

- **The aggregate has an `exception_open` state and no object that opens it on a contested question.** The transition table requires "exception type, scope, and evidence supplied" and defines no shape for any of the three. Two implementations can both satisfy that guard and mean different things by it.
- **The conformance grade object carries a `determination_ref` field that references nothing.** [conformance-grades-v0.1.md](../conformance/conformance-grades-v0.1.md) section 4 requires the field so that a grade is contestable, and section 6 defines an appeal with grounds, a status effect, and a superseding determination. The object being referenced is not defined anywhere in the set. A grade is therefore contestable in prose and not in the record.
- **There is no shape for a ruling.** A party told that its act was outside its mandate has nothing to point at, nothing to check, and nothing to appeal against. It has a refusal code and the word of whoever returned it.

The commercial situation where this bites: a supplier's bid is refused with `A202-POLICY-DENIED` two minutes before an event closes. The supplier believes the constraint was evaluated against the wrong rule version. Today it can raise this only outside the system, and whatever answer it receives leaves no verifiable record. Whatever the answer is, no third party can afterwards check that it followed from the rules that were in force.

A fourth gap is structural rather than missing. Nothing in the set says what a ruling is worth. Without a stated effect, a determination either means nothing or means whatever the party that issued it says it means, and neither is a position a counterparty can evaluate before agreeing to anything.

## 2. Proposal summary

Adopt [determination and dispute v0.1](../disputes/determination-v0.1.md), five normative parts plus refusal codes.

1. **Raising.** Any party to the transaction may raise, including against the party operating the venue, under a mandate carrying `dispute.raise`. The subject is one of `act`, `determination`, `obligation_state`, or `refusal`, referenced by `content_hash` and never by identifier alone. The window is set by the rules in force at the time of the subject act and is referenced through `rules_ref`, not restated. Grounds come from a closed list; `description` is bounded untrusted free text that nothing in the protocol reads meaning out of. Raising suspends nothing.
2. **The determination object.** `det_` prefix, common envelope. Carries the question with the rule set version in force at the time of the subject act, an `outcome` that is a reasoned finding naming `rules_applied` and `evidence_relied_on` with an `inputs_hash`, the determiner and its authority basis reference, timestamps, and an appeal route reference. **There is no enumerated verdict.** The object is replayable: a third party holding the referenced rules, inputs, and evidence can check that the stated outcome follows.
3. **Supersession.** A later determination replaces an earlier one by reference, stating one of `appeal_outcome`, `corrected_input`, or `rule_misapplication`. Both remain in evidence permanently. The chain is linear, with no forks. Deletion is not a defined operation and an implementation must not provide one.
4. **Binding effect.** `advisory`, `presumptive`, or `binding`, read from the rules the parties agreed in advance and checked independently of the carried claim. Absence resolves downward to `advisory`. An informative note states plainly that nothing in the specification makes any effect enforceable at law.
5. **Appeal route.** Four closed grounds, with disagreement with the rule itself excluded and routed to the proposal process. Preconditions including the appeal window and the no-forks rule. While an appeal is open the prior determination stands, neither raised nor suspended. The appeal produces a new determination that supersedes the appealed one.

Plus an informative certification note tying grade determinations into the same family, and eight refusal codes.

## 3. Alternatives considered

**Do nothing.** Rejected: `determination_ref` stays dangling, `exception_open` stays undefined, and the appeal described in the conformance grades document has no object to produce. A right to contest that produces no record is not usable by the party that most needs it.

**A three-value verdict enum.** Rejected, and this is the substantive choice in the proposal. An enumerated verdict is cheap to implement and cannot be checked: it says which way a question went and nothing about why, so there is nothing to point at and say a rule was applied wrongly. It also makes the appeal grounds in [conformance-grades-v0.1.md](../conformance/conformance-grades-v0.1.md) section 6 unusable, because "the rule was misapplied" cannot be assessed against an outcome that never names a rule. A reasoned finding costs more to produce and is the only form that supports replay.

**Let raising suspend the subject act.** Rejected: raising would become free leverage. Any party could halt a counterparty's act by contesting it, and the cost of a meritless dispute would fall entirely on the other side.

**Let a determination be edited or withdrawn.** Rejected: a record that can be removed when it is unfavourable is a record nobody has a reason to read. Supersession with both records retained gives the same corrective power and leaves the correction itself auditable.

**Define the effect on the determination alone.** Rejected: it lets the issuing party decide how much weight its own ruling carries. Reading the effect from the rules the parties agreed in advance, and checking the carried claim against them, is what keeps a determination from expanding its own authority.

**Fold appeals into ordinary disputes with no separate grounds.** Rejected: the ordinary grounds include substantive ones such as `obligation_not_performed`, which on appeal would relitigate the original question rather than test how it was decided. The narrower appeal grounds are what stop every determination from being reopened on the merits.

## 4. Compatibility

### 4.1 What breaks

Nothing currently valid becomes invalid. No existing field changes meaning and no fixture is reclassified. Under [RELEASES.md](../RELEASES.md) section 2 this is a **MINOR** change: two new object types, new error codes for cases previously undefined, and a previously dangling reference given a target.

One existing document gains a resolvable reference rather than a changed rule. `determination_ref` in [conformance-grades-v0.1.md](../conformance/conformance-grades-v0.1.md) section 4 is already a required field; it now resolves to a defined object. An implementation that populated it with something of its own design has to move to the defined shape, which is adoption rather than migration.

### 4.2 Kernel schema changes required

| Change | Detail |
|---|---|
| Add `dispute` to the `object_type` enum | Prefix `dsp_`, `signatures` `minItems` 1, non-null `transaction_id` |
| Add `determination` to the `object_type` enum | Prefix `det_`, `signatures` `minItems` 1, non-null `transaction_id` |
| Add `disputePayload` and `determinationPayload` `$defs` and their conditionals | Both closed with `additionalProperties: false` |
| Add `rulesRef` `$def` | Rule set identifier, version, and `sha256Hex` hash. Referenced by both payloads and by the appeal route |
| Add `questionRef` and `outcome` `$defs` | `outcome` has no verdict member, and its closure is what a fixture checks |
| Register two identifier prefixes | `dsp_` and `det_`, in the prefix table of [canonical-commercial-model-v0.1.md](../schemas/canonical-commercial-model-v0.1.md) section 3 |

`partyRef`, `sha256Hex`, and the evidence reference shape adopted by [A202-0004](A202-0004-evidence-verification.md) are reused unchanged. No new value type is introduced.

### 4.3 Existing objects

| Object | Effect |
|---|---|
| Conformance grade object | `determination_ref` resolves to a `determination`. `status: under_appeal` is unchanged and is the status effect this proposal's section 7.3 requires |
| `PolicyDecision` | Unchanged in shape, and becomes a disputable subject through `subject_type: refusal`, referenced by its `content_hash` |
| `CommercialMandate` | Unchanged in shape. Uses the action name `dispute.raise` in `actions`, which is an open list |
| `Obligation` | Adopted by [A202-0002](A202-0002-obligation.md). Becomes a disputable subject through `subject_type: obligation_state`, and its transition table admits `determination.recorded` under a guard |
| `Evidence` | Referenced through the shape adopted by [A202-0004](A202-0004-evidence-verification.md) |
| `Exception` | Named in the object inventory with no defined payload. This proposal does not define it, and does not need to: a dispute is the object that carries a contested question. The undefined `Exception` payload is recorded as an open item rather than resolved here |

### 4.4 Existing states: `exception_open` and `in_performance` are the integration points

The aggregate state machine is unchanged. No state is added, removed, or renamed, and no transition is narrowed.

| Aggregate transition | What this proposal supplies |
|---|---|
| any eligible committed state to `exception_open`, on `exception.opened` | The dispute object. Its `grounds`, `subject_type`, and `evidence_refs` are the "type, scope, and evidence" the existing guard requires and does not define |
| `exception_open` to `in_performance`, on `remediation.accepted` | A determination may be the basis on which remediation is agreed. The transition still requires the parties to accept a remediation hash, and a determination alone does not produce it |
| `exception_open` to `settlement_pending`, on `exception.resolved` | A binding determination on the disputed question can be the resolution condition. An advisory or presumptive one cannot, which is the fail-closed case |
| `exception_open` to `terminated`, on `transaction.terminated` | Unchanged. A determination is evidence toward the termination authority check, never the termination itself |
| `in_performance` and `acceptance_pending` | Reached again from `exception_open` through the existing paths. A disputed obligation returning to `asserted` or `accepted` under a binding determination is subject to the obligation transition table, not to a new aggregate path |

Two constraints on the integration are worth stating.

**A determination does not append aggregate transitions on its own.** Recording a determination and moving the aggregate are separate events with separate guards. An implementation that couples them gives every determination the effect of a binding one.

**A dispute against the venue operator uses the same path.** Section 3.1 of the adopted document permits it, and no transition treats it differently. The operator is the respondent on an ordinary dispute object, and the record of it is verifiable by the same procedure as any other.

### 4.5 Ordering against A202-0002 and A202-0004

A202-0003 depends on the evidence reference shape adopted by [A202-0004](A202-0004-evidence-verification.md), which its `evidence_refs` and `evidence_relied_on` fields use. It does not depend on [A202-0002](A202-0002-obligation.md): `subject_type: obligation_state` is inert until obligations exist, and every other subject type works without them. A202-0002 depends on A202-0003 only for the dispute path a rejection opens, which is a reference rather than a requirement.

Either all three land in one release, or A202-0004 lands first and the other two follow in any order.

### 4.6 Migration

Nothing to migrate. No dispute or determination object exists under any earlier version of the set. The only implementation-side change is for a party that populated `determination_ref` with an object of its own design.

## 5. Fixture plan

Weighted the way the published suite is weighted: 3 positive and 14 negative static fixtures, plus 8 cases requiring runtime state.

### 5.1 Positive

| Fixture | What it exercises |
|---|---|
| `valid-dispute.json` | A dispute against an act, referenced by content hash, with a registered ground, a bounded description, an evidence reference, and a resolvable `rules_ref` |
| `valid-determination.json` | A determination with a reasoned finding, `rules_applied`, `evidence_relied_on`, an `inputs_hash`, and `effect: presumptive` matching what the referenced rules granted |
| `valid-appeal-determination-superseding.json` | An appeal outcome superseding a prior determination with `reason: appeal_outcome`, both records present |

### 5.2 Negative

| Fixture | Expected code | What it refuses |
|---|---|---|
| `negative/dispute-subject-by-identifier-only.json` | `A202-DISPUTE-SUBJECT-UNREFERENCED` | A dispute naming its subject by `subject_id` with no `subject_hash`. A dispute about an object that can change is a dispute about nothing fixed |
| `negative/dispute-subject-hash-unresolvable.json` | `A202-DISPUTE-SUBJECT-UNREFERENCED` | A `subject_hash` that resolves to nothing in the record |
| `negative/dispute-grounds-unregistered.json` | `A202-DISPUTE-GROUNDS-UNKNOWN` | A ground outside the closed list |
| `negative/dispute-grounds-empty.json` | `A202-DISPUTE-GROUNDS-UNKNOWN` | An empty `grounds` array. Absence is not a wildcard |
| `negative/dispute-no-evidence-refs.json` | `A202-EVIDENCE-UNVERIFIED` | A dispute with no evidence reference at all |
| `negative/dispute-description-carries-rival-data.json` | `A202-DISCLOSURE-POLICY-VIOLATION` | A `description` naming a rival's price. Free text is the field through which anything travels, and the disclosure rules apply to it unchanged |
| `negative/dispute-out-of-window.json` | `A202-DISPUTE-OUT-OF-WINDOW` | Raised after the window resolved through `rules_ref` |
| `negative/dispute-rules-ref-unresolvable.json` | `A202-DISPUTE-OUT-OF-WINDOW` | A `rules_ref` that does not resolve. The window cannot be shown to have been met, and unavailability is not permission |
| `negative/determination-enumerated-verdict.json` | `A202-DETERMINATION-NOT-FOLLOWING` | A determination carrying `verdict: upheld` with no `rules_applied` and no `evidence_relied_on`. Schema-enforced by the closed `outcome` shape and independently by the evaluator |
| `negative/determination-subject-differs-from-dispute.json` | `A202-DISPUTE-SUBJECT-UNREFERENCED` | A determination whose `question.subject_hash` differs from its dispute's |
| `negative/determination-rules-ref-not-in-force.json` | `A202-DETERMINATION-NOT-FOLLOWING` | A determination applying the current rule version rather than the one in force at the time of the subject act |
| `negative/determination-effect-overclaim.json` | `A202-DETERMINATION-EFFECT-OVERCLAIM` | `effect: binding` where the referenced rules granted `presumptive` |
| `negative/determination-effect-unstated-rules.json` | `A202-DETERMINATION-EFFECT-OVERCLAIM` | An effect claimed where the referenced rules state none for the question class. The upward-inference case |
| `negative/determination-supersedes-without-reason.json` | `A202-DETERMINATION-SUPERSESSION-UNREASONED` | A superseding determination with no stated reason |
| `negative/determination-supersedes-superseded.json` | `A202-DETERMINATION-SUPERSESSION-FORKED` | A second determination superseding one already superseded. Two determinations would claim to be current |
| `negative/determination-deletion-event.json` | `A202-STATE-TRANSITION-DENIED` | A `determination.deleted` event. Deletion is not a defined operation and the refusal is what makes that testable rather than asserted |
| `negative/appeal-grounds-disagrees-with-rule.json` | `A202-APPEAL-GROUNDS-UNKNOWN` | An appeal whose stated ground is that the rule itself is wrong. Routed to the proposal process, not to an appeal |
| `negative/appeal-out-of-window.json` | `A202-DISPUTE-OUT-OF-WINDOW` | An appeal raised after the window resolved through `appeal_route_ref` |

### 5.3 Cases requiring runtime state

1. Raising a dispute against an act leaves that act's state unchanged, and leaves every shared stream sequence unchanged.
2. A dispute raised against the party operating the venue is accepted on the same terms as any other, with the same grounds, window, and route.
3. While an appeal is open, the prior determination's carried outcome is unchanged, and a grade's `status` reads `under_appeal` with its bands unchanged.
4. An appeal that upholds the original still produces a determination, and that determination supersedes with `reason: appeal_outcome`.
5. A superseded determination remains retrievable and verifiable after supersession.
6. A determination with `effect: advisory` moves no state anywhere in the set.
7. A binding determination whose `state_result` would produce an illegal transition is refused with `A202-STATE-TRANSITION-DENIED` rather than applied.
8. A party with no mandate carrying `dispute.raise` is refused, and the refusal consumes no shared stream sequence.

Case 6 is the one an implementation is most likely to fail while passing every static fixture, because the effect field validates on its own and the coupling between effect and state change is where the mistake lives.

## 6. Origin

Drafted from three unresolved references inside the v0.1 set: the `determination_ref` field on the conformance grade object, the appeal described in that document with no determination object to produce, and the `exception.opened` guard requiring a type, a scope, and evidence that nothing defines. The choice of a reasoned finding over an enumerated verdict follows from the appeal grounds already written in the conformance grades document, which cannot be assessed against a verdict that names no rule. This is context for reviewers rather than an argument.
