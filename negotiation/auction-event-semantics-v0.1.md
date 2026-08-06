# Auction event semantics v0.1

**Status:** Experimental working specification. Mixed. Sections 2, 3, 4, 5, 6, 7, and 8 are **normative**. Sections 1 and 9 are **informative** and state no requirement on an implementation.

**Date:** 26 July 2026

**Scope:** Synthetic and non-binding validation only

**Relates to:** [pilot transaction state machine v0.1](pilot-transaction-state-machine-v0.1.md), [transaction profile extension model v0.1](../schemas/transaction-profile-extension-model-v0.1.md), [commercial mandate v0.1](../authority/commercial-mandate-v0.1.md), [counterparty invitation v0.1](../discovery/counterparty-invitation-v0.1.md)

## 1. Purpose

A competitive bidding event is a transaction with several counterparties bidding against one demand, exactly one of which is awarded. The state machine already carries the states and streams such an event needs. This document states the semantics that are specific to it: what a bidder may be told, under what authority a bid may be appended, when an award is distinct from an acceptance, what may not change once the event has opened, and what a losing bidder can verify afterwards.

It specifies event semantics. It does not specify how an implementation ranks or scores bids, how it advances or extends an event in time, how it executes the event internally, or how it eliminates the side channels that would otherwise carry rival information. Those are implementation concerns. This document states the properties an implementation has to exhibit and the procedures by which a participant checks them.

Auction mechanism design is a mature field. Nothing here attempts novel mechanism design and nothing here should be read as doing so.

## 2. Bid authority

Every bid is an ordinary offer under an ordinary mandate. There is no separate bidding credential.

1. A bid MUST be carried in a signed `ActionEnvelope` under a `CommercialMandate` whose `actions` include `offer.submit`, and whose `scope` covers the transaction being bid into.
2. A bid whose mandate does not resolve, has expired, is suspended, is revoked, or does not cover the transaction MUST NOT append to any stream.
3. Bid limits are mandate constraints in the ordinary vocabulary. A maximum or minimum price, a permitted currency, and a prohibited disclosure path are expressed as `commercial.decimal`, `commercial.string`, and `disclosure.path` constraints, and are evaluated by the same path as any other action.

The consequence is that a bid which no principal authorised cannot exist. An operator or an event owner cannot inject a bid that is not backed by a mandate, because a bid with no valid mandate cannot append. This is the structural control against a bid that is placed only to move the outcome.

## 3. Award is a transition distinct from acceptance

Three things happen in sequence and MUST NOT be collapsed:

- **Acceptance is not selection.** An `Acceptance` signed over a current offer hash moves one bilateral session to `accepted`. It does not commit the transaction and it does not end the event.
- **Selection is not agreement.** `offer.selected` on the transaction stream is the award. It moves the aggregate to `agreement_pending`. It is not itself the agreement.
- **Agreement is agreement.** `agreement.committed` requires both parties to have signed the same agreement hash.

Where an implementation ranks bids, ranking MUST NOT award. Ranking produces an order; `offer.selected` produces a winner. The party holding selection authority retains it subject to its own mandate, and an award that does not follow the ranking MUST record a reason.

Exactly one award appends per award unit. Two `offer.selected` events contend on the transaction stream, and the losing attempt is refused. This is the one place where contention is intended, and it is what makes single-award integrity an invariant rather than an expectation.

## 4. Disclosure policy

Isolation is the default value of a declared disclosure policy, not the only behaviour an event may have. An event that reveals nothing across bidders and an event that reveals a bidder's own rank are both legitimate. What is not legitimate is disclosure that is undeclared, asymmetric, unrecorded, or inferred from a refusal.

| Policy | What a bidder observes |
|---|---|
| `sealed` | Nothing about rivals. The default |
| `participant_count` | The number of qualified bidders only |
| `rank_only` | Its own position, and neither prices nor identities |
| `best_value_anonymous` | The current best price, with no identity attached |
| `full_public` | All bids and all identities |

Every policy other than `sealed` MUST satisfy all five of the following.

1. **Declared before the event opens.** The policy is part of the signed event definition. It MUST NOT change while bidding is live.
2. **Symmetric.** Every bidder in a class receives the same disclosure on the same terms. Asymmetric visibility is the definition of an unfair event, and an implementation MUST NOT produce it.
3. **Bounded by the mandate.** A bidder's `disclosure.path` constraints continue to apply to its own outbound content. An event policy widens what a bidder is shown. It never widens what a bidder may send.
4. **Recorded.** Every disclosure is an event. What was revealed, to whom, at which sequence, and at what time MUST be replayable.
5. **Fail closed.** An unrecognised policy value MUST evaluate to `sealed`. This matches the closed-registry treatment of mandate constraint types and operators: an unknown value is a refusal, never a permission.

Property 4 is what makes a disclosure checkable rather than promised. A bidder that is told its rank can, after the event, replay the record and confirm that the rank it was shown is the rank the record carries.

## 5. Rule freezing

The event definition is signed and frozen when the event opens.

1. Disclosure policy, close time, and any published rule governing how bids are compared MUST be part of the signed event definition.
2. An attempt to modify any of them after the event has opened MUST be refused with `A202-SCORING-RULE-FROZEN` and MUST be recorded.
3. A change to a frozen rule requires a new event. It is not an amendment to a running one.

A rule that changes after bids are visible is the classic manipulation of a competitive event, and it is the one an outside party has the least chance of detecting after the fact. Freezing it at open and recording every refused attempt is what converts "the rules did not change" from an assurance into a check.

## 6. Isolation, stated as a property

**The property.** No participant in a sealed event can infer the existence, the activity, or the terms of another participant. This holds for the content a participant receives, for the sequence numbers it observes, for the reason codes it is returned, and for the timing of the responses it gets.

Three consequences follow, and an implementation MUST exhibit all three.

1. A bidder never observes a sequence number that was influenced by a rival's activity. Sequence numbers are per stream, and a bidder's session stream carries only its own activity. A shared counter across concurrent sessions would be a covert channel, because a bidder that watched it advance would learn that somebody else acted and when.
2. A bidder never receives a conflict, a refusal, or a delay that was caused by a rival's activity.
3. A refused act consumes no sequence number in any shared stream and is therefore invisible to every other participant.

**How a losing bidder verifies it.** The verification does not require access to the operator. A losing bidder holds a replayable export of its own session stream and of the transaction-stream events it is party to. It verifies the event-chain hashes within each stream, verifies each actor signature, resolves the mandate and policy decision referenced by each event, replays the events in sequence order, and recomputes the object and agreement hashes. It then checks that the sequence series it observed is the series it would have observed as the only participant, and that no close reason, refusal code, or event payload it received names a rival, a price, a count, or a time attributable to another party.

The property is verified by tests 1 to 5 in section 8. It is asserted here against the state machine's per-stream concurrency rules and the session event allowlist, and it is those tests that establish it for any particular implementation.

**What isolation does not cover.** Isolation is a property of the event record and the responses an implementation gives. It says nothing about what participants tell each other outside the system. See section 7.

## 7. Market integrity

An implementation can enforce mechanism integrity: sealed bids stay sealed, the declared rules do not change once the event has opened, every bid is authorised, and the whole event is replayable. Those are the properties this document specifies.

An implementation cannot detect collusion agreed outside the system. Two bidders who agree their prices by telephone produce a record that is indistinguishable from two bidders who did not. Any claim to detect that would be unsupportable, and this specification does not make it.

The controls that are enforceable are these:

| Threat | Control |
|---|---|
| A bid placed only to move the outcome, by a party with no intention or no authority to perform | Every bid carries a mandate. A bid with no valid mandate cannot append. Section 2 |
| A rule altered after bids are visible | The event definition is signed and frozen at open. Changes require a new event. Section 5 |
| A participant inferring another participant's existence, activity, or terms | Isolation, as a property with a verification procedure. Section 6 |
| A refusal that discloses what the refusal was protecting | Disclosure-bearing reason codes fail closed under a policy that does not permit them. Section 8 |
| A late entrant joining a market that has already moved | Invitation is refused once the aggregate reaches `negotiating`. See [counterparty-invitation-v0.1.md](../discovery/counterparty-invitation-v0.1.md) section 6.1 |

## 8. Error codes and required tests

### 8.1 Error codes

Additions to [pilot-transaction-state-machine-v0.1.md](pilot-transaction-state-machine-v0.1.md) section 10. All fail closed.

| Code | Meaning |
|---|---|
| `A202-AUCTION-CLOSED` | A bid arrived after the authoritative close for its event |
| `A202-AUCTION-FORMAT-UNSUPPORTED` | The requested event format is not defined in this specification version |
| `A202-BID-NO-IMPROVEMENT` | The event requires an improving bid and this bid does not improve on the bidder's own standing bid |
| `A202-LOT-UNKNOWN` | A bid names an award unit that does not resolve on this event. v0.1 defines no award-unit object, so any bid naming one fails with this code |
| `A202-LOT-ALREADY-AWARDED` | An award has already appended for this award unit |
| `A202-DISCLOSURE-POLICY-VIOLATION` | A requested view exceeds the event's declared disclosure policy |
| `A202-SCORING-RULE-FROZEN` | An attempt to modify a frozen event rule after the event opened |
| `A202-ROUND-NOT-OPEN` | A bid arrived outside the window it was submitted against |

`A202-BID-NO-IMPROVEMENT` MUST NOT be returned under `sealed` or `participant_count`. Under those policies the refusal itself would tell the bidder that a better standing bid exists, which is precisely what those policies withhold. This is a disclosure rule expressed as an error-code rule, and it is the case that shows why a code cannot be chosen independently of the policy in force.

`A202-LOT-ALREADY-AWARDED` is bound by the same rule. Returned to a bidder under `sealed` or `participant_count` it discloses that an award happened before the neutral close reason delivers that fact symmetrically to every loser at once. Under those policies a late bid is refused with the ordinary state-transition refusal, and the award-specific code is reserved for policies that already disclose the event's progress. Both codes fail closed the same way: the v0.1 kernel has no disclosure policy object, so a policy decision carrying either code is refused with `A202-DISCLOSURE-POLICY-VIOLATION`.

### 8.2 Required tests

These extend the required transition tests in [pilot-transaction-state-machine-v0.1.md](pilot-transaction-state-machine-v0.1.md) section 11. Each is a normative requirement on an implementation and each is the procedure by which a participant, rather than the operator, establishes the corresponding property.

1. **Sealed-bid isolation under award.** Five concurrent bidders. After the award, each losing bidder's full replayable export permits no inference of rival count, identity, price, or timing.
2. **Hard close.** A bid arriving one second after the authoritative close is refused with `A202-AUCTION-CLOSED`, consumes no sequence in any shared stream, and is invisible to every other bidder.
3. **Single award under contention.** Two selections on one award unit. Exactly one appends and the other is refused with `A202-LOT-ALREADY-AWARDED`.
4. **A refusal leaks nothing.** A bid refused for mandate, policy, or award-unit reasons leaves every shared stream sequence unchanged.
5. **Award-unit independence.** Award, cancellation, and expiry on one award unit produce no observable event, sequence change, or timing signal for a bidder participating only on another.
6. **Disclosure policy conformance.** Under `rank_only`, no bidder's export contains a rival price or a rival identity. Under `best_value_anonymous`, no bidder's export contains a rival identity.
7. **Frozen rules.** Any attempt to alter the disclosure policy, the close time, or a published comparison rule after open is refused and recorded.

## 9. Limitations

- The sealed-bid semantics stated here are asserted against the transaction state machine and the session event allowlist. Tests 1 to 4 in section 8.2 are what verify them for a given implementation, and an implementation that has not run them has not established the property.
- This specification version defines a single award unit per event. The `A202-LOT-UNKNOWN` and `A202-LOT-ALREADY-AWARDED` codes exist so that a bid naming an award unit is refused rather than silently accepted against the wrong one.
- Formats that require an event to advance in time under an authoritative timeline, rather than to close at an absolute deadline, are not defined in this version. An implementation MUST refuse to open an event in a format this specification does not define, rather than approximate it. An approximated event is one whose fairness cannot be proven, which removes the reason to run it under this specification at all.
- Regulated public procurement has format, notice, and record obligations that are not analysed here.
