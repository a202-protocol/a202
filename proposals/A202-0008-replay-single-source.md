# A202-0008: One normative home for replay

**Status:** Experimental. Stage 2 of the five stages in [README.md](README.md) section 3. The change is concrete and is explicitly not stable. It is raised and not yet executed: no edit has been made to any document under it.

**Date:** 27 July 2026

**Status of this document:** Informative in full. It states no requirement on an implementation. The text this proposal would land is carried by [negotiation/pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md), which marks its own normative sections.

## 1. Problem

Replay is normatively described in two documents.

[pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) section 9 lists seven activities: verify event-chain hashes within each stream, verify each actor signature, resolve the mandate and policy decision referenced by each event, apply session events then aggregate events in sequence order, recompute object and agreement hashes, produce final aggregate and session states, and produce a root per stream plus a combined root. Section 9 is a normative section of that document.

[evidence-verification-v0.1.md](../evidence/evidence-verification-v0.1.md) section 4 states the same activities as steps 1 to 5 of an executable procedure: canonicalise and check content hashes, verify every signature against its declared key and purpose, check version chains, check per-stream sequence continuity, and replay guarded transitions with the actor authority and policy decision checks inside step 5. Section 4 is a normative section of that document.

They agree today. That is the whole difficulty. Two normative statements of one rule, currently consistent, drift on the first edit to either, and the drift is invisible: both copies stay validly published and each reads as authoritative to whoever found it first. The repository's own boundary rule is that a normative rule which exists in two places has no single source of truth.

The commercial situation where the drift bites: a party exports its records after a dispute and hands them to the counterparty's verifier. The two implementations replayed the same bytes against two documents that had by then diverged on what replay checks, and they disagree about whether the record holds. The disagreement is about the specification rather than about the record, and neither party can resolve it from the record, which is the one thing they both hold.

The duplication was recorded, not discovered here. [A202-0004](A202-0004-evidence-verification.md) section 4.6 states it, says that collapsing the state machine's section 9 into a reference is a change to that document and belongs in its own proposal with its own review, and records it so it is not lost. This is that proposal.

## 2. Proposal

Replace section 9 of [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) with a short reference to the verification procedure, retaining the sentences in it that have no counterpart there.

### 2.1 The replacement text

The section becomes, in the words that would land:

> ## 9. Replay
>
> Replay is the verification procedure in [evidence-verification-v0.1.md](../evidence/evidence-verification-v0.1.md) section 4, executed against the records of one transaction. Steps 1 to 5 of that procedure are the whole of it: content hashes are recomputed under the canonicalisation rules, every signature is verified against its declared key and purpose, version chains and per-stream sequence continuity are checked, and each guarded transition is replayed against the rules version in force when the event appended, producing the final aggregate and session states. That procedure is the single statement of what replay does. It is executable by a party holding the records, the schemas, the referenced rule set versions, and the declared keys, with no operator access, and this document states nothing about replay that it does not state.
>
> Replay also produces one Merkle root or ordered-event root per stream, plus a combined root for the audit bundle.

Two sentences of the current section 9 are retained verbatim and are therefore not restated above: the sentence listing the conditions on which replay fails, and the sentence stating that cross-stream ordering from `kernel_annotations.received_at` is for presentation only and never authorises a transition. Both keep their existing wording, their position at the end of the section, and their normative force. Restating them in this proposal would reproduce the duplication the proposal exists to remove.

### 2.2 What is retained and why

| Current section 9 item | Where it lives after the edit |
|---|---|
| Event-chain hashes within each stream | Steps 1 and 4 of the procedure |
| Each actor signature | Step 2 |
| Mandate and policy decision resolution per event | Step 5, items 3 and 4 |
| Session events then aggregate events, in sequence order | Step 5, which states the same ordering |
| Object and agreement hashes recomputed | Step 1, which additionally enumerates the other hashes a bundle asserts |
| Final aggregate and session states | Step 5, item 5 |
| One root per stream, plus a combined root | Retained in the state machine. It has no counterpart in the verification procedure, because that procedure runs against whatever set of objects a verifier holds rather than over a sealed bundle |
| The failure conditions sentence | Retained verbatim in the state machine |
| Cross-stream ordering is presentation only | Retained verbatim in the state machine |

The root sentence is the one item that makes this edit a collapse rather than a deletion. Removing it would drop a rule, and the audit bundle it names has no defined payload today, which [A202-0007](A202-0007-exception-prefix-and-deferred-payloads.md) records as deferred. It stays where it is until the object it produces a root for is defined.

### 2.3 Why this is editorial

No rule changes. The set of things replay checks is identical before and after: every item in the current list has a named home in the procedure or is retained in place. No check is added, none is removed, none is loosened, none is tightened, and no refusal code changes the conditions under which it is returned. An implementation that replays correctly today replays correctly afterwards, and one that does not, does not.

What changes is that the rule has one home. A reader arriving at section 9 is sent to the procedure; a reader arriving at the procedure finds the whole of it there.

### 2.4 Why it is raised as a proposal anyway

[README.md](README.md) section 1 lists the changes that require a proposal, and lists separately the changes that do not: a typographical fix, a clarification whose meaning is unchanged, a broken internal link, an improved example. This edit rewrites a normative section of a normative document, which is not on the second list even though its effect on an implementation is nil.

The section also states the rule directly: if it is unclear which of the two a change is, it is a proposal, because the cost of an unnecessary proposal is an hour and the cost of a normative change that landed without one is that nobody can later say why the specification says what it says. Whether an edit is editorial or normative is judged by review, and the way to obtain that review is to raise it.

There is a second reason specific to this edit. The claim that nothing changes rests on the mapping table in section 2.2 being complete. If a reviewer finds an item in the current section 9 that has no home in the procedure and is not retained, the edit is not editorial and the finding is the whole value of raising it.

## 3. Alternatives considered

**Do nothing.** Leave both statements standing. Rejected: they agree today and there is no mechanism that keeps them agreeing, because nothing links them and an editor of either has no reason to open the other. The failure is silent and arrives at the worst moment, which is when two parties are already disagreeing about a record.

**Collapse in the other direction: make the state machine the home and the verification document the reference.** Rejected, and this is the alternative that decides the proposal.

The verification document is the better home for four reasons.

1. **It is the executable procedure.** It is written as numbered steps with a stated input set, a stated output shape with three values, and a stated rule that a failing step continues so the report names everything wrong rather than the first thing. The state machine's section 9 is a list of activities. A reference from a list to a procedure sends a reader forward; a reference from a procedure to a list sends them back to something less complete.
2. **The audience is the verifier, not the implementer of state.** Replay is executed by a party that holds records, often after the fact, often with no operator and possibly with no running system at all. That reader is already in the verification document, which exists for them. The state machine's reader is implementing transitions.
3. **The procedure covers more than the state machine's replay does.** Steps 6 and 7, determinations and the report of what could not be checked, have no counterpart in section 9. Making the state machine the home would mean either moving those steps into a document about transitions, where they do not belong, or leaving the procedure split across two documents, which is the current problem with extra steps.
4. **Selective disclosure is already specified next to the procedure.** A verifier replaying a partial bundle needs the boundary rules in section 6 of the verification document. Those rules are about disclosure, not about transitions, and moving replay towards them is moving it towards the rest of what its reader needs.

The argument for the other direction, which is not negligible: the state machine defines the transitions being replayed, so replay is arguably a property of the state machine. It is rejected because replay checks signatures, hashes, version chains, and stream continuity as well as transitions, and only one of those four is a state machine concern.

**Move replay to a third document of its own.** Rejected. It would produce a document whose entire content is a procedure that already exists in a document about evidence, and it would leave the state machine referencing a third place. Three homes is not an improvement on two.

**Leave section 9 and add a cross-reference to the procedure.** Rejected as the worst of both. The duplication would remain, now with an explicit invitation to compare two texts, and the first divergence would leave a cross-reference pointing at a document that says something else.

## 4. Compatibility

**No behaviour change.** No object shape, field, state, transition, guard, refusal code, or fixture classification changes. No implementation becomes conformant or non-conformant by this edit. A relying party's verification of an existing record produces the same per-check results before and after.

Under [RELEASES.md](../RELEASES.md) section 2 this is a **PATCH** change: a change that alters no normative statement, which that table covers as editorial corrections and clarifications whose meaning is unchanged. PATCH is the correct class exactly to the extent that section 2.2 of this proposal is complete, and that is the thing to review.

**Effect on conformance is nil.** The conformance suite exercises replay through the fixtures adopted by [A202-0004](A202-0004-evidence-verification.md), which reference the procedure. None of them references section 9 of the state machine, so none of them changes classification, and the manifest is untouched.

**Effect on citations.** Anything citing "section 9 of the state machine" for the content of replay continues to resolve: the section still exists, still has the same number, and now points at the procedure. Documents in this set that reference section 9 keep their references, and no link becomes broken.

**Migration.** None. There is nothing for an implementation to do.

## 5. Fixtures

**None are required, and this section exists to say why rather than to leave the absence unexplained.**

[README.md](README.md) section 4 lists fixtures among the contents of a proposal, and section 3 states that a proposal which cannot be expressed as a fixture is a proposal whose semantics are not yet decided. The semantics here are decided and unchanged: the rule replay states before this edit is the rule it states afterwards, and a fixture distinguishes a conformant implementation from a non-conformant one rather than distinguishing two spellings of the same requirement. There is no behaviour on either side of this edit that a fixture could separate.

What replaces a fixture plan is a check on the existing suite. The suite is run before and after the edit, and the required result is that every fixture keeps its classification and the manifest is unchanged. A fixture whose result moves would mean the edit changed a rule, which would mean the edit is not editorial and this proposal has the wrong compatibility class. That is a real check with a real failure mode, and it is the one this proposal should be held to.

## 6. Origin

Recorded in [A202-0004](A202-0004-evidence-verification.md) section 4.6, which identified the duplication while adopting the verification procedure, declined to bundle the resolution, and stated that collapsing the state machine's section 9 belongs in its own proposal with its own review. Nothing about the duplication was discovered after that record; this proposal supplies the direction of the collapse, the retained items, and the argument for which document is the home.

It arose from specification review rather than from any implementation's experience. No implementation has replayed a record against both texts and reported a disagreement, which is unsurprising, because the two texts agree today. This is context for reviewers rather than an argument.
