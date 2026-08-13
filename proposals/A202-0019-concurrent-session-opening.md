# A202-0019: The aggregate table cannot open a second negotiation session

**Status:** Draft, not yet submitted; held for founder review. Written to enter at stage 1, problem statement, of [README.md](README.md) section 3. Section 2 drafts the change stage 2 would adopt. Nothing is implemented: no specification document, rules version, fixture, or runner rule has been edited.

**Date:** 9 August 2026

**Status of this document:** Informative in full. It states no requirement on an implementation. The normative text this proposal amends is carried by [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md), which marks its own normative sections.

## 1. Problem

The aggregate transition table in section 5 of [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) registers one `negotiation.opened`, from `qualifying` to `negotiating`, with the side effect "Create isolated session and session stream". Session creation is an aggregate event, and each event creates one session. A transaction negotiating with two suppliers therefore needs two `negotiation.opened` events on its transaction stream, and the second has no registered transition: when it appends, the aggregate is already in `negotiating`, and no row accepts `negotiation.opened` from there.

The specification requires the case it cannot express. Section 2 separates the two state machines for confidentiality, because concurrent bilateral sessions are the situation the split exists for. Section 3 defines `negotiating` as "At least one private negotiation session is active", a meaning written in anticipation of more than one. Section 8's consequences are stated for "concurrent negotiation with three suppliers", and required test 15 runs three concurrent sessions on one transaction. Three sessions is three `negotiation.opened` events, of which the table permits the first. An implementation that refuses the second — which is what section 10's registry stance and the replay rule in section 9, "Replay MUST fail on … unauthorized transition", both instruct it to do — is conformant to the letter of the table and cannot pass test 15. The specification's own required tests do not all pass against its own table.

The gap is not hypothetical. The first surface to express the calibration scenario end to end outside the conformance suite opened a private session with each of two qualified suppliers, and had to record the second opening as an unregistered `negotiating` to `negotiating` self-loop, by analogy with the invitation self-loops of section 5.1, because no registered transition existed. A record carrying that event today fails replay under every rules version in force.

## 2. Change

1. **Section 5's aggregate transition table gains one row:**

   | Current | Event | Guard | Next | Required side effect |
   |---|---|---|---|---|
   | `negotiating` | `negotiation.opened` | Candidate passed required evidence checks | `negotiating` | Create isolated session and session stream |

   The guard and the side effect are the first row's, verbatim. Opening the second session is the same act as opening the first, performed while the first is running, and nothing about the act changes with its ordinal.

2. **Rules version 1.4 registers the transition.** Versions 1.0 through 1.3 are immutable, so a record made under any of them replays against the set in force when it appended, and a second `negotiation.opened` is illegal there. This is the treatment `termination.agreed` received when 1.2 registered it and `agreement.direct` when 1.3 did, and for the same reason section 5.3 states: editing a rules version in place would change the answer to a question that was already asked.

3. **Section 11 gains the transition's tests**, in the words that would land:

   28. Multi-session opening: a second and a third `negotiation.opened` append from `negotiating` under rules version 1.4, each creating an isolated session and session stream; test 15 then holds over the three.
   29. Multi-session opening refused: a second `negotiation.opened` replayed against a rules version that never permitted it is illegal at replay; and `negotiation.opened` from `agreement_pending` is refused, because the selection freeze admits no new room.

Isolation is preserved without further rules. The event appends to the transaction stream, which no counterparty reads before commitment — the kernel's `transactionEventData` states that the winning counterparty reads the stream after commitment, and section 5.1 states that an invited party never reads it at all — so no supplier can count the openings, and section 8 already guarantees that no session's sequence series reflects a rival's existence. The row adds a fact to a stream whose confidentiality rules were built for exactly this fact.

## 3. Alternatives considered

**Read the existing row permissively, as "one or more openings", and change nothing.** Section 10's registry stance is that what is not registered is refused, and section 9 makes replay fail on an unauthorized transition. A permissive reading would repair this table by weakening the property that makes every other row enforceable, and two implementations would disagree about a record's validity on a question the specification is supposed to answer.

**One `negotiation.opened` carrying several sessions.** A batch event would open every session at one instant, which cannot express suppliers qualified at different times, and would change the event's data shape for no gain: the aggregate needs to know that sessions exist, not that they were simultaneous. It would also make the second supplier's session creation contingent on the first's, which is a coupling section 8 exists to forbid.

**Create sessions off the aggregate entirely, on the session stream's own first event.** Then the aggregate would not record that a session exists, `qualifying` to `negotiating` would have no trigger, and the single-award contention of section 8 consequence 5 would lose the stream on which selection contends. That is a rewrite of the machine, not a repair of its table.

**Close the candidate pool at the first opening, with a stricter guard.** A guard such as "candidate qualified before the first session opened" was considered, because a late entrant joins a market that is already moving — the fairness question section 5.1 raises and defers when it denies invitation from `negotiating` onward. It is not taken, because it would decide that deferred question as a side effect of a concurrency repair. The row keeps the first row's guard, and whether a candidate can still qualify once negotiation has begun is decided by the qualification rules, exactly as it is for the first opening. The invitation path stays denied from `negotiating` under section 5.1, unchanged.

## 4. Compatibility

Under [RELEASES.md](../RELEASES.md) section 2 the set is pre-release, and no release has been made. The change is MINOR-shaped by the rule: it adds a permission and invalidates nothing. A record made under versions 1.0 through 1.3 replays exactly as before, because those versions are immutable and the transition is illegal there. An implementation that hardcoded `negotiation.opened` as reachable only from `qualifying` adds one row to operate under 1.4, which is added capability, not a broken assumption — no previously conformant behaviour becomes non-conformant. The one honest caveat: test 15 was always required, so an implementation claiming to pass it before this change was relying on an unregistered transition, and this proposal is what makes its record replayable.

## 5. Fixture plan

Planned, not implemented; stage 3 is where these land.

**Allow direction.** An evidence bundle whose transaction stream carries two `negotiation.opened` events under rules version 1.4 replays cleanly to `negotiating`, with two isolated session streams whose sequence series are each indistinguishable from solo participation.

**Refuse direction.** The same record declared under rules version 1.3 fails replay with `A202-EVIDENCE-TRANSITION-ILLEGAL`, on the section 5.3 precedent that a rules version never permitting a transition makes it illegal at replay. And a live `negotiation.opened` proposed from `agreement_pending` is refused with `A202-STATE-TRANSITION-DENIED`, because the selection freeze is in force and no new room opens against a frozen selection.

No new reason code is registered; both refusals use codes section 10 already carries.

## 6. Origin

Found while building the Plural Worlds console's mock dataset, the first surface to express the pilot calibration scenario end to end outside the conformance suite, and recorded there as a documented deviation: the dataset recorded the second supplier's opening as a `negotiating` to `negotiating` self-loop it acknowledged was unregistered, on the analogy of section 5.1's invitation self-loops, rather than invent a state. This is context for reviewers rather than an argument.
