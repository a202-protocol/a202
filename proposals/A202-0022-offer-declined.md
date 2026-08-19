# A202-0022: The offeree has no event that declines an offer

**Status:** Draft, not yet submitted; held for founder review. Written to enter at stage 1, problem statement, of [README.md](README.md) section 3. Section 2 drafts the change stage 2 would adopt. Nothing is implemented: no schema, specification document, fixture, or runner rule has been edited.

**Date:** 16 August 2026

**Status of this document:** Informative in full. It states no requirement on an implementation. The normative material this proposal amends is carried by [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md), which marks its own normative sections, and by the session transition registry in [conformance/run-conformance.py](../conformance/run-conformance.py).

## 1. Problem

Section 6.1 of [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) registers every way a negotiation session leaves `active`. The offeree may accept (`offer.accepted`), either party may counter (`offer.submitted`), the offeror may withdraw (`offer.withdrawn`), the deadline may elapse (`deadline.elapsed`), and the session may be closed from above when the aggregate leaves `negotiating` or `agreement_pending` (`session.closed`). There is no event by which the offeree declines. A party that has received an offer and decided not to proceed has three options: counter with terms it does not want, accept, or say nothing and let the offer run to its `valid_until`.

Silence is the option every implementation takes today, and it is the wrong one on three counts.

First, it leaves the offeror bound. Under section 7 an offer stands until it expires or is withdrawn, and the offeror cannot withdraw what it does not know is unwanted. The capacity, price, and authority committed to the offer stay committed until the clock runs out, which in a sourcing event may be days.

Second, it makes silence meaningful. The offeror cannot distinguish an offeree that is still deliberating from one that has moved on, and the only way to learn which is to wait for expiry. The charter's second principle is that commercial meaning is carried by typed objects and named states, never by the absence of an object. Here the absence of an object is the decision.

Third, the model already half-expects the event. The kernel's `sessionCloseData.close_reason` enum carries `declined_by_offeree`, and section 6 registers the session state `rejected`, "Closed without acceptance". Neither is reachable: no transition in section 6.1 targets `rejected`, and no event produces a close whose reason is `declined_by_offeree`. The state and the reason exist; the event that would connect them does not. This is the shape [A202-0015](A202-0015-fixture-minimality-orphan-codes-and-grade-scope.md) called an orphan, and it was found the same way: by asking what record an implementation would write for an ordinary act and discovering that no honest one exists.

The commercial situation is the ordinary one. A supplier's agent, under its mandate, submits an offer into a bilateral session with a buyer. The buyer's agent runs the offer through its own policy and the answer is no: wrong delivery window, or the buyer's requirement changed, or the buyer simply prefers not to proceed. In procurement practice the buyer sends a regret notice and the supplier releases the capacity. Under the state machine as it stands the buyer's agent has no signed act that says so, the supplier's offer stays live, and the supplier's agent learns it lost only when nothing happens for long enough.

What the decline must not do is as important as what it must. The reason a buyer declines is its negotiating position, and the charter's fourth principle is that a refusal must not itself become a disclosure. The event needed here is the bare fact of the decline, signed, and nothing else. Anything reasoned, a debrief, scoring feedback, a standstill period, is jurisdiction- and sector-specific and is transaction-profile material, or sits above this specification entirely.

## 2. Change

1. **Section 6.1 gains one row**, in the words that would land:

   | Current | Event | Guard | Next |
   |---|---|---|---|
   | `active` | `offer.declined` | Declining party is the offeree of the session's current offer and is authorized for `offer.decline`; the offer is unaccepted, unwithdrawn, and unexpired | `rejected` |

   The event is the offeree's act. It is signed by the offeree's agent under a mandate whose `actions` include `offer.decline`, which joins `offer.submit` and `offer.accept` as a registered action name, and it is evaluated by the offeree's own policy like every other act of the offeree, per section 9.1 of [canonical-commercial-model-v0.1.md](../schemas/canonical-commercial-model-v0.1.md). It is not a decision about the offeror's act; it is a decision about the offeree's own next move, and the counterparty learns that the move was made and nothing about why.

2. **The event carries the close shape the kernel already defines.** The schema's conditional on session events whose `to_state` is `rejected` requires `data` to be `sessionCloseData`, whose only permitted member is `close_reason`. For `offer.declined` that member is `declined_by_offeree`, the enum value that has been waiting for this event. No schema change is needed: the shape exists, the value exists, and `additionalProperties: false` on `sessionCloseData` is what makes it structurally impossible for the event to carry a rationale, a score, a rival's terms, or free text. The event says the offeree declined, in kernel terms, and can say nothing further. Required test 16 therefore covers it without edit.

3. **Section 7 gains two offer rules**, in the words that would land, placed after "Withdrawal is valid only before acceptance":

   - Decline is valid only before acceptance, and only by the offeree.
   - A declined offer is released: the offeror is no longer bound by it and it cannot afterwards be accepted. A counteroffer after a decline is a new session, not a continuation of the declined one.

   The second rule is what gives the event its commercial effect. It mirrors withdrawal from the other side of the table: withdrawal is the offeror releasing itself, decline is the offeree releasing the offeror.

4. **`rejected` is terminal for negotiation and closes as it closes today.** The existing row "any non-terminal, `session.closed`, aggregate left `negotiating` or `agreement_pending`, `closed`" already carries a `rejected` session to `closed` when the transaction moves on, and the close reason on that later event remains whatever is true of the closing party's perspective. Nothing in section 6.2 on operated selection changes: losing sessions still close with a neutral reason after an award, and `offer.declined` is not that mechanism. It is the offeree's own act in its own session, available bilaterally and under an operator alike.

5. **Rules version 1.4 registers the transition.** Versions 1.0 through 1.3 are immutable, so a record made under any of them replays against the set in force when it appended and `offer.declined` is illegal there. This is the treatment `termination.agreed` and `agreement.direct` received, for the reason section 5.3 gives: editing a rules version in place would change the answer to a question that was already asked. In the runner this is one entry in a new `PILOT_TRANSITIONS_1_4` set.

6. **Section 11 gains two required tests**, numbered 28 and 29 in the words that would land:

   > 28. Decline: `offer.declined` by the offeree of an unaccepted current offer carries the session from `active` to `rejected` under rules version 1.4 with `close_reason` `declined_by_offeree` and nothing else in `data`; the declined offer is released and cannot afterwards be accepted; the offeror's record and the offeree's record agree on the event.
   > 29. Decline refused: `offer.declined` after `offer.accepted` in the same session; `offer.declined` signed by the offeror; `offer.declined` replayed against a rules version that never permitted it; and `offer.declined` whose `data` carries any member other than `close_reason`, or a `close_reason` other than `declined_by_offeree`.

No new reason code is registered. Refusals use codes section 10 already carries: `A202-STATE-TRANSITION-DENIED` live and `A202-EVIDENCE-TRANSITION-ILLEGAL` at replay for a decline from a state with no such row or under a rules version without it, `A202-STREAM-MISMATCH` for a decline signed by a party that is not the offeree of the current offer, and schema refusal, or `A202-DISCLOSURE-POLICY-VIOLATION` where the added content names rival state, for an event that carries more than the bare reason.

## 3. Alternatives considered

**Do nothing; expiry is the decline.** This is the current state and the reason for the proposal. It binds the offeror for the full validity window, makes silence the carrier of a decision, and leaves `rejected` and `declined_by_offeree` as registered names nothing can reach.

**Reuse `session.closed` with `declined_by_offeree`.** The reason value would be true, but `session.closed` is the aggregate reaching down into a session when the transaction leaves negotiation; its guard is an aggregate fact. A decline is a party's act inside the session, with the party's authority and the party's signature, and routing it through an event whose guard names the aggregate would either falsify the guard or require a special case in it. The state the session should land in also differs: `rejected`, closed without acceptance, is exactly what a decline produces, and it is the state that has been unreachable.

**Let the offeree withdraw the offer.** Withdrawal is the offeror's act over its own commitment. Letting the counterparty perform it would put one party's signature on another party's release, which is the kind of attenuation of a counterparty's act that section 9.1 forbids and that the A2A discussion this arose from was specifically asking about.

**Carry a reason code from a new closed list.** Considered, and not taken, because the kernel already has the mechanism and the discipline: `sessionCloseData` is an allowlist with one member, its values are stated from the closing party's perspective, and `declined_by_offeree` is already in it. A second list would duplicate the first, and any member beyond the bare fact of the decline is a step toward the rationale this proposal deliberately keeps out of the kernel. A domain that requires a reasoned decline, public procurement being the obvious one, states that requirement in its transaction profile under the profile's own disclosure rules.

**Allow a decline from `paused_for_approval`.** Not taken in this proposal. An offeree whose own act is held for approval declines by having the approval rejected and then declining from `active`, which is two events but leaves each with one meaning. Widening the row can be a later proposal if implementation experience wants it.

**Permit the session to continue after a decline.** Not taken. A party that declines and wants to keep talking counters instead; that is what `offer.submitted` with `supersedes_offer_id` is for. A decline that leaves the session open would make `rejected` a non-terminal state and reopen the question of what the offeror is bound by.

## 4. Compatibility

Under [RELEASES.md](../RELEASES.md) section 2 the change is MINOR-shaped by the closest rule in the table: it adds a transition and a registered action name for a case previously unexpressible, and no previously conformant implementation emitted the event, because no rules version registered it. The honest caveat is cross-version replay: a verifier pinned to rules version 1.3 or earlier refuses a record carrying `offer.declined`, which is the immutability rule working as designed and not a failure. No schema changes. No existing fixture changes classification. The migration surface is one item for an implementation that let offers expire in place of declining: it may now append the event its records were always meant to carry, and it adds `offer.decline` to the mandates of agents that are permitted to do so, which is a narrowing-safe addition to a mandate's `actions`.

## 5. Fixture plan

Planned, not implemented; stage 3 is where these land.

**Allow direction.** A session-stream event `offer.declined`, from `active` to `rejected`, `created_by` the offeree organisation and agent under a mandate whose `actions` include `offer.decline`, with `data` of exactly `{"close_reason": "declined_by_offeree"}`, validates against the kernel schema and replays under rules version 1.4 to a session in `rejected`. A companion bilateral bundle carries the same event signed by the offeree and countersigned by the offeror, per section 8.1, and replays clean.

**Refuse direction.** Four fixtures, each minimal under the rule in [README.md](../README.md) that removing the single offending element leaves a document that validates:

1. `offer.declined` appended after `offer.accepted` in the same session fails replay with `A202-EVIDENCE-TRANSITION-ILLEGAL`, because no row leaves `accepted` on that event.
2. `offer.declined` whose `created_by` is the offeror of the current offer is refused with `A202-STREAM-MISMATCH`: the act is directed at a release the signing party does not hold.
3. `offer.declined` replayed against a bundle whose rules version is 1.3 fails with `A202-EVIDENCE-TRANSITION-ILLEGAL`, which is test 29's immutability leg and the same shape as test 25 and test 27.
4. `offer.declined` whose `data` carries `close_reason` `declined_by_offeree` and a second member naming a rival's price is refused at the schema by `additionalProperties: false`, and, where the runner applies the disclosure rule to the payload, with `A202-DISCLOSURE-POLICY-VIOLATION`. This is the leak fixture the existing `auction-close-reason-leaks-rival-data` provides for operated closes, re-expressed for the bilateral decline.

A fifth fixture, mechanical: a mandate whose `actions` include `offer.decline` validates, and a mandate chain in which a child adds `offer.decline` absent from its parent is refused with `A202-MANDATE-DELEGATION-WIDENING`, so the new action name is covered by the widening rule from the day it is registered.

## 6. Origin

Raised on 16 August 2026 from a question put to the A202 extension proposal on the A2A repository (a2aproject/A2A#2143) by Poke-nushi, who asked whether a receiving party's refusal of an incoming offer sits inside or outside A202. Answering it established that the receiver's admission decision is its own act under section 9.1 and is in scope, and that a narrowed acceptance is a counteroffer; rereading section 6.1 to write that answer exposed that the bare decline, the one act the receiver most often takes, has no event. This is context for reviewers rather than an argument.
