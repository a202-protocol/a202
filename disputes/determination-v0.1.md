# Determination and dispute v0.1

**Status:** Experimental, adopted through proposal [A202-0003](../proposals/A202-0003-determination.md). Mixed. Sections 2, 3, 4, 5, 6, 7, and 9 are **normative**. Sections 1 and 8 are **informative** and state no requirement on an implementation.

**Date:** 27 July 2026

**Scope:** Synthetic pilot transactions only

**Depends on:** [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md), [commercial mandate v0.1](../authority/commercial-mandate-v0.1.md), [pilot transaction state machine v0.1](../negotiation/pilot-transaction-state-machine-v0.1.md), [obligation v0.1](../agreement/obligation-v0.1.md), [evidence verification v0.1](../evidence/evidence-verification-v0.1.md), [conformance grades v0.1](../conformance/conformance-grades-v0.1.md)

## 1. Purpose

Two parties transacting through agents will eventually disagree about whether an act was permitted, whether an obligation was performed, or whether a refusal was correct. A specification that defines authority, state, and evidence, and then says nothing about how a disagreement is raised or what a ruling on it looks like, leaves the most consequential object in the system undefined.

This document defines that object and the family around it: how a dispute is raised, what a determination is, how a later determination replaces an earlier one, what effect a determination has, and how it is appealed.

It specifies shapes and interfaces. It does not specify how any operator staffs, schedules, prices, or processes a dispute, how a determiner reaches a conclusion, or what a determiner should conclude on any question. Those are outside this specification and are not published here. The right to raise a dispute and the right to appeal are part of the protocol. What happens inside the room where the question is answered is not.

Two properties follow from the rest of the specification set rather than from anything new here. A determination is replayable, because everything it relies on is hash addressed and signed. A determination never claims more effect than the parties agreed in advance, because the effect is read from the rules in force and not from the determiner.

## 2. Conformance language

`MUST`, `MUST NOT`, `REQUIRED`, `SHOULD`, `SHOULD NOT`, and `MAY` are normative within this experimental specification.

An implementation conforms when it:

1. validates `dispute` and `determination` objects against `../schemas/v0.1/commercial-kernel.schema.json`;
2. enforces the raising rules in section 3;
3. enforces the supersession rules in section 5, including the absence of any deletion operation;
4. enforces the effect rules in section 6;
5. enforces the appeal rules in section 7;
6. returns the refusal codes in section 9 for the failures they name;
7. passes the dispute and determination fixtures in `../conformance/manifest-v0.1.json`.

## 3. Part 1: raising

### 3.1 Who may raise

Any party to the transaction may raise a dispute. This includes raising one against the party operating the venue in which the transaction is conducted.

An implementation MUST NOT restrict the right to raise by reference to a party's role, its assurance level, its conformance grade, or whether it prevailed on any earlier question. A right to contest that is available only to some participants is not a right to contest.

The raising party MUST hold a mandate whose `actions` include `dispute.raise` and whose `scope` covers the transaction. A dispute is a commercial act and is authorised on the ordinary path, through a signed `ActionEnvelope` evaluated against the mandate. There is no separate disputing credential.

### 3.2 What may be raised against

A dispute MUST reference exactly one subject, by content hash, from this closed list.

| `subject_type` | What it references |
|---|---|
| `act` | A signed act, referenced by the `content_hash` of the object that carried it |
| `determination` | An earlier determination, referenced by its `content_hash`. This is the appeal path in section 7 |
| `obligation_state` | An obligation together with the state it stood in, referenced by the `content_hash` of the object that placed it there |
| `refusal` | A refusal, referenced by the `content_hash` of the `PolicyDecision` that carried it |

The reference is REQUIRED and is a content hash, never a bare identifier. A dispute that names no resolvable subject, or that names one by identifier alone, is refused with `A202-DISPUTE-SUBJECT-UNREFERENCED`. A dispute about "the delivery" is not a dispute anyone can determine; a dispute about the exact bytes of a named act is.

### 3.3 Within what window

The window is set by the rules in force on the transaction at the time the subject act occurred. This document references that window and does not restate it, because a window restated in two places is a window with two values.

The dispute object carries `rules_ref`, which names the rule set and version the window is read from. A dispute raised outside the window resolved through `rules_ref` is refused with `A202-DISPUTE-OUT-OF-WINDOW`. A `rules_ref` that does not resolve is refused with the same code, because a window that cannot be resolved cannot be shown to have been met, and unavailability is not permission.

### 3.4 What a dispute carries

| Field | Type | Rule |
|---|---|---|
| `raising_party` | `partyRef` | REQUIRED |
| `respondent_party` | `partyRef` | REQUIRED. The party the dispute is against, which MAY be the venue operator |
| `subject_type` | enum | REQUIRED. From the list in section 3.2 |
| `subject_hash` | `sha256Hex` | REQUIRED. The content hash of the referenced subject |
| `subject_id` | identifier | REQUIRED. The identifier of the referenced object, present for resolution and never load bearing on its own |
| `grounds` | array of enum, at least one | REQUIRED. From the list in section 3.5 |
| `description` | string, bounded, marked untrusted | OPTIONAL free text. See section 3.6 |
| `evidence_refs` | array of evidence references | REQUIRED, at least one. In the shape defined in [evidence-verification-v0.1.md](../evidence/evidence-verification-v0.1.md) section 3 |
| `rules_ref` | `rulesRef` | REQUIRED. The rule set and version in force, from which the window and the available effects are read |

### 3.5 Grounds

The list is closed in v0.1. An unregistered ground is refused with `A202-DISPUTE-GROUNDS-UNKNOWN`.

| Ground | Meaning |
|---|---|
| `authority_absent` | The act was taken without a mandate covering it |
| `authority_exceeded` | The act was outside the constraints of a mandate that otherwise covered it |
| `state_transition_invalid` | The transition was not legal from the state that stood at the time |
| `obligation_not_performed` | An obligation reached its due condition and was not performed |
| `obligation_wrongly_rejected` | An assertion of performance was rejected on grounds the record does not support |
| `evidence_unverified` | Evidence relied on does not verify |
| `disclosure_breach` | An act disclosed what the rules in force did not permit it to disclose |
| `refusal_incorrect` | A refusal was returned where the rules in force required the act to be permitted |
| `rule_misapplied` | The rules in force were applied incorrectly to the subject |

### 3.6 Free text is data

`description` is untrusted free text directed at a counterparty's agent. It is bounded in length, it is rendered as data, and it MUST NOT be interpreted as an instruction by any component that reads the dispute. Nothing in the protocol reads a meaning out of it: every element a determination relies on appears in `grounds`, `subject_hash`, `evidence_refs`, and `rules_ref`.

This is the same treatment the `purpose_note` field receives on an invitation, and for the same reason. A free-text field that is allowed to carry commercial meaning is a field through which anything can travel.

### 3.7 Raising suspends nothing

Raising a dispute does not by itself suspend, reverse, or pause the referenced act. The act stands until a determination with an effect sufficient to move it says otherwise.

If raising suspended the subject, raising would become a tactic: any party could halt a counterparty's act at no cost by contesting it. The remedy for an act that should not stand is a determination, not the act of complaining about one.

An implementation MAY record that a dispute is open against a subject, and that record is visible to the parties to the dispute. Recording it MUST NOT alter the subject's state.

## 4. Part 2: the determination object

A determination is a signed shared kernel object carrying the common envelope, the `det_` identifier prefix, and a non-null `transaction_id`.

| Field | Type | Rule |
|---|---|---|
| `dispute_id` | `dsp_` identifier | REQUIRED. The dispute determined |
| `question` | `questionRef` | REQUIRED. What was determined. See section 4.1 |
| `outcome` | `outcome` | REQUIRED. A reasoned finding. See section 4.2 |
| `determiner` | `partyRef` | REQUIRED. Who determined it |
| `authority_basis_ref` | reference | REQUIRED. The basis on which the determiner had authority to determine this question, resolvable to the rules in force |
| `effect` | enum | REQUIRED. `advisory`, `presumptive`, or `binding`. See section 6 |
| `supersedes` | `supersession` or null | REQUIRED and non-null where this determination replaces an earlier one. See section 5 |
| `appeal_route_ref` | reference | REQUIRED. The appeal route available against this determination, resolved from the rules in force |
| `determined_at` | RFC 3339 timestamp | REQUIRED. UTC |
| `effective_from` | RFC 3339 timestamp | REQUIRED. UTC. At or after `determined_at` |

### 4.1 The question

| Field | Rule |
|---|---|
| `subject_type`, `subject_hash`, `subject_id` | REQUIRED. Copied from the dispute, and MUST equal the dispute's values |
| `rules_ref` | REQUIRED. The rule set and version in force **at the time of the subject act**, not at the time of the determination |

A determination that names a different subject hash from its dispute is not a determination on that dispute and is refused with `A202-DISPUTE-SUBJECT-UNREFERENCED`.

`rules_ref` resolving to the version in force at the time of the subject act is what makes a determination stable. If a later rule version governed, then changing the rules would change the answer to a question that was already asked, and no record would be reliable for longer than the rules it was decided under.

### 4.2 The outcome is a reasoned finding

`outcome` is not an enumerated verdict. There is no three-value result, and an implementation MUST NOT reduce a determination to one.

| Field | Type | Rule |
|---|---|---|
| `finding` | string, bounded | REQUIRED. The finding on the question, stated in terms of the referenced rules |
| `rules_applied` | array, at least one | REQUIRED. Each entry names a rule inside `rules_ref` by its stable rule identifier |
| `evidence_relied_on` | array of evidence references, at least one | REQUIRED. Each entry is an evidence reference carried by the dispute, by the referenced act, or by the record the determiner replayed |
| `inputs_hash` | `sha256Hex` | REQUIRED. The canonical hash over the ordered set of inputs the determination was taken against |
| `state_result` | closed object or null | The determined subject's identifier and one registered state token, where the effect permits a state change. Null otherwise. A subject other than the determined one, an unregistered state, or a `state_result` under a non-binding effect is refused |

An enumerated verdict says which way a question went and nothing about why, which makes it unappealable in any meaningful sense: there is nothing to point at and say it was applied wrongly. A finding that names the rules applied and the evidence relied on can be checked, and a determination that cannot be checked is an assertion wearing a determination's shape.

`state_result` is the only field through which a determination touches state, and it is inert unless section 6 permits it.

### 4.3 A determination is replayable

A third party holding `rules_ref`, the inputs covered by `inputs_hash`, and the evidence named in `evidence_relied_on` MUST be able to check that the stated `finding` follows from them.

This is a property of the object, not a request for good faith. It requires all four of the following, and an implementation MUST satisfy each.

1. `rules_ref` resolves to an exact, hash-addressed rule set version.
2. `inputs_hash` covers a canonically ordered input set, serialised under JCS as required by [canonical-commercial-model-v0.1.md](../schemas/canonical-commercial-model-v0.1.md) section 4.
3. Every entry in `rules_applied` resolves inside the referenced rule set version.
4. Every entry in `evidence_relied_on` resolves and verifies under [evidence-verification-v0.1.md](../evidence/evidence-verification-v0.1.md) section 4.

A determination whose stated outcome does not follow from its referenced rules and inputs is reported by a verifier as `A202-DETERMINATION-NOT-FOLLOWING`. The check is the one at step 6 of the verification procedure, and it is the check that distinguishes a determination from an announcement.

No model output may serve as the deterministic authority for a finding. Where an implementation uses one, its output is an input recorded under `inputs_hash` like any other, and the finding still has to follow from the rules and the evidence.

## 5. Part 3: supersession

A determination is never edited and never removed. A later determination on the same question replaces an earlier one by reference, and both remain in evidence permanently.

`supersedes` carries:

| Field | Rule |
|---|---|
| `determination_id` | REQUIRED. The `det_` identifier of the determination replaced |
| `determination_hash` | REQUIRED. The `content_hash` of the determination replaced |
| `reason` | REQUIRED. One of `appeal_outcome`, `corrected_input`, `rule_misapplication` |

Rules:

1. A superseding determination MUST name the same `question.subject_hash` as the determination it supersedes. A determination on a different question is a separate determination, not a replacement.
2. A superseding determination MUST state `reason`. A replacement with no stated reason is refused with `A202-DETERMINATION-SUPERSESSION-UNREASONED`. A record that changes for reasons it does not give is a record whose changes cannot be audited.
3. A determination MUST NOT supersede one that has already been superseded. The chain is linear, and a fork means two determinations claim to be current on one question. This is refused with `A202-DETERMINATION-SUPERSESSION-FORKED`, and it is the same no-forks rule the version chain check enforces at step 3 of the verification procedure.
4. Both determinations remain in the evidence record, retrievable, and verifiable. The superseded one is marked as superseded by the existence of the later one's reference, not by a mutation of its own bytes.
5. **Deletion is not a defined operation.** There is no protocol operation that removes a determination, and an implementation MUST NOT provide one. A record that can be removed when it is unfavourable is a record nobody has a reason to read.

Section 5 rule 5 and the retention practices of any particular operator are different questions. This specification defines no deletion operation. It states nothing about how long any operator retains anything.

## 6. Part 4: binding effect

A determination's effect is exactly what the parties' rules in force agreed in advance. It is never more.

| `effect` | What it means |
|---|---|
| `advisory` | The determination is a finding. It moves no state and binds no party. Each party's own process decides what to do with it |
| `presumptive` | The determination is presumptive evidence of the finding on the question. It moves no state by itself. A party asserting a different account of the same facts carries the burden of displacing it |
| `binding` | The determination is binding on the parties on the stated question. Where `state_result` is present, the subject moves to the stated state |

Three rules hold.

1. **The effect is read from the rules, not from the determiner.** The determination carries an `effect` claim, and that claim MUST NOT exceed what the rule set resolved through `question.rules_ref` granted for this question class and these parties. A determination claiming `binding` where the rules granted `presumptive`, or claiming any effect where the rules granted none, is refused with `A202-DETERMINATION-EFFECT-OVERCLAIM`.
2. **The check is independent of the claim.** A relying party MUST evaluate the effect against the referenced rules rather than accept the carried value. Both layers fail closed on their own: an implementation that widened the carried enum without the rules granting it, and one that read the rules without checking the carried claim, must each refuse.
3. **Absence is not permission.** Where `question.rules_ref` does not resolve, or resolves to a rule set that states no effect for this question class, the effect is `advisory`. It is never inferred upward.

Where the effect is `binding` and `state_result` is present, the state change is subject to the guards of the state machine it targets. A determination cannot produce a transition that would be illegal for any other event. This is why the obligation transition table admits `determination.recorded` under a guard rather than as an unconditional move.

**Informative note on legal effect.** Nothing in this specification makes any determination enforceable at law. `binding` is a statement about what the parties' rules in force said, recorded in a form that can be verified afterwards. Whether an agreement to be bound is enforceable, in which jurisdiction, between which parties, and on which questions, is a matter of the law applicable to those parties and their contract. This specification defines an object and a check. It does not create an obligation to comply with one, and no material may describe it as doing so.

## 7. Part 5: appeal route

An appeal is a dispute whose `subject_type` is `determination`. It runs on the same path, with the additional rules in this section.

### 7.1 Grounds

An appeal MUST state at least one of the following. The list is closed.

| Ground | Meaning |
|---|---|
| `rule_misapplied` | The rules in force were applied incorrectly to the subject |
| `input_did_not_exercise_invariant` | An input the determination relied on does not exercise the invariant the finding attributes to it |
| `wrong_scope` | The determination reached beyond the question that was raised |
| `wrong_rule_version` | The determination applied a rule set version other than the one in force at the time of the subject act |

**Disagreement with the rule itself is not a ground of appeal.** A party that thinks the rule is wrong is asking for the rule to change, and that is a change proposal against this specification set under [proposals/README.md](../proposals/README.md), handled through the proposal process. An appeal on that basis is refused with `A202-APPEAL-GROUNDS-UNKNOWN`.

The distinction is load bearing. An appeal route that accepts "the rule produced an outcome I dislike" is a route through which every determination is relitigated, and a rule that can be set aside case by case is not a rule.

### 7.2 Preconditions

An appeal MUST satisfy all of the following, and each failure fails closed.

1. It references the determination by `content_hash`, not by identifier alone.
2. It is raised inside the appeal window resolved through the determination's `appeal_route_ref`. Outside it, `A202-DISPUTE-OUT-OF-WINDOW`.
3. It is raised by a party to the transaction, on the terms in section 3.1.
4. The referenced determination has not already been superseded. An appeal against a superseded determination is refused with `A202-DETERMINATION-SUPERSESSION-FORKED`, because determining it would fork the chain.
5. It states at least one ground from section 7.1.

### 7.3 Effect on status while an appeal is open

While an appeal is open, the prior determination stands. It is neither raised nor suspended by the act of appealing.

Both alternatives are worse. If appealing suspended the determination, appealing would be a way of setting aside any unfavourable outcome for the duration. If appealing raised its standing, appealing would be a way of strengthening what it contests. Either would make appealing a tactic rather than a remedy, which is exactly the failure the right to appeal exists to prevent.

Where the subject carries a status field, that status reflects that an appeal is open. A conformance grade's `status` becomes `under_appeal` under [conformance-grades-v0.1.md](../conformance/conformance-grades-v0.1.md) section 6, and the bands it carries are unchanged while it is there.

### 7.4 What an appeal produces

An appeal produces a new determination. That determination supersedes the appealed one under section 5, with `supersedes.reason` set to `appeal_outcome`, and both remain in the evidence record permanently.

An appeal that upholds the original still produces a determination. There is no null outcome, because "the appeal was heard and the original stands" is a finding that a third party has to be able to verify as much as any other.

### 7.5 What is not specified here

The right to raise an appeal is part of the protocol. How any operator staffs an appeal, what it charges for one, how it schedules or sequences one, who reviews it, and what internal procedure it follows are outside this specification and are not published here.

## 8. Certification note

A conformance grade determination is a determination in this family. The `determination_ref` field on the grade object defined in [conformance-grades-v0.1.md](../conformance/conformance-grades-v0.1.md) section 4 references a `determination` object of the shape in section 4 above, and the appeal in section 6 of that document is an appeal under section 7 above.

The consequence is that a grade is contestable in exactly the way any other determination is contestable, by the same parties, on the same grounds, through the same route, producing the same superseding record. Nothing about a grade makes it a different kind of statement.

The four grounds line up directly. Ground 4 of the grade appeal, "the specification version was wrong", is the `wrong_rule_version` ground in section 7.1, where the rule set in question is a version of this specification set. The other three carry the same names.

This section is informative. The normative rules are in sections 3 to 7 and in the conformance grades document, and neither restates the other.

## 9. Refusal codes

All fail closed. These extend the table in [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) section 10.

| Code | Meaning |
|---|---|
| `A202-DISPUTE-OUT-OF-WINDOW` | A dispute or appeal was raised outside the window resolved through the rules in force, or the window could not be resolved |
| `A202-DISPUTE-GROUNDS-UNKNOWN` | A dispute states a ground outside the closed list, or states none |
| `A202-DISPUTE-SUBJECT-UNREFERENCED` | A dispute or determination names no resolvable subject, names one by identifier alone, or names a subject hash that differs from the dispute it determines |
| `A202-DETERMINATION-EFFECT-OVERCLAIM` | A determination claims an effect greater than the referenced rules granted for this question class and these parties |
| `A202-DETERMINATION-SUPERSESSION-UNREASONED` | A superseding determination states no reason for superseding |
| `A202-DETERMINATION-SUPERSESSION-FORKED` | A determination supersedes one that has already been superseded, or an appeal targets a superseded determination |
| `A202-DETERMINATION-NOT-FOLLOWING` | A determination's stated outcome does not follow from its referenced rules and inputs |
| `A202-APPEAL-GROUNDS-UNKNOWN` | An appeal states a ground outside the closed list, including disagreement with the rule itself |

`A202-DETERMINATION-NOT-FOLLOWING` is returned by a verifier executing step 6 of [evidence-verification-v0.1.md](../evidence/evidence-verification-v0.1.md) section 4, and by an implementation that refuses to record a determination it cannot itself replay. Both layers are required.
