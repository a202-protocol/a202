# A202-0020: The awarded session has no close reason it can state truthfully

**Status:** Draft, not yet submitted; held for founder review. Written to enter at stage 1, problem statement, of [README.md](README.md) section 3. Section 2 drafts the change stage 2 would adopt. Nothing is implemented: no schema, specification document, fixture, or runner rule has been edited.

**Date:** 9 August 2026

**Status of this document:** Informative in full. It states no requirement on an implementation. The normative material this proposal amends is carried by [schemas/v0.1/commercial-kernel.schema.json](../schemas/v0.1/commercial-kernel.schema.json) and [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md), which marks its own normative sections.

## 1. Problem

Section 6 of [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) defines the session state `closed` as "Terminal, after aggregate commitment or cancellation", and section 6.1 registers the transition that reaches it from success: `accepted`, on `session.closed`, under the guard "Aggregate reached `committed` or `cancelled`". The winning session is meant to close when its transaction commits; the state's own meaning names commitment first.

The kernel cannot express that closure. A session-stream event whose `to_state` is `closed` must carry `sessionCloseData`, whose required `close_reason` is a closed enum of eight members: `not_selected`, `withdrawn_by_offeror`, `declined_by_offeree`, `session_expired`, `transaction_cancelled`, `transaction_expired`, `mandate_inactive`, `qualification_failed`. Every member states a reason the session did not proceed. For the awarded session — in `accepted`, on a transaction that reached `committed` — every member is false. `not_selected` is the opposite of what happened; `transaction_cancelled` and `transaction_expired` name aggregate facts that did not occur; the rest describe failures the session did not have. The registered transition exists, and the only event that could record it must either lie or fail validation.

So the success path ends in a contradiction between two normative layers: the state machine says the awarded session closes on commitment, and the schema refuses every truthful record of it. The first surface to express the calibration scenario end to end outside the conformance suite hit exactly this: it closed the losing session with `not_selected`, as the fixture set does, and left the winning session resting at `accepted` forever, because no honest close event could be written. A session that can never reach its terminal state on the one path the pilot exists to demonstrate is a completeness hole in every audit over sessions, permanently special-cased for the winner.

## 2. Change

1. **`sessionCloseData.close_reason` gains one member, `transaction_committed`**, meaning: this session's accepted offer became the committed agreement, and the session's work is done. The definition's existing discipline holds without edit: the reason is stated from the closing party's own perspective and reveals nothing about any other session on the transaction. The winning counterparty learns nothing from this value it does not already hold — it countersigned the agreement — and no rival session ever reads it, because a close event is readable only inside the session it closes. Losing sessions continue to close as `rejected` with a neutral reason under section 6.2, and test 16 is untouched.

2. **Section 6.2 states the pairing**, in the words that would land, appended to the paragraph on competing-session closure: "The winning session closes from `accepted` with `transaction_committed`, the one close reason that reports success. It appears only in the winner's own session stream, and its absence from a losing session's close is not information: every losing session closes with a neutral reason whether or not an award occurred."

No transition changes. Section 6.1's rows already carry the closure; this proposal gives the event they describe a value it can carry truthfully.

## 3. Alternatives considered

**State normatively that the awarded session does not close.** This was the mock dataset's de facto behaviour and the other repair the finding named. It is not taken because it contradicts the model twice over: the `closed` state's own meaning says "after aggregate commitment", and section 6.1 registers `accepted` to `closed` under the commitment guard. Adopting it would mean editing both to say the opposite of what they say, in order to preserve an enum's omission. It also leaves a non-terminal session on every completed transaction forever, so every liveness check, every session sweep, and every archival rule must carry a permanent exception for exactly the sessions that succeeded.

**Reuse an existing member.** None is true of the awarded session, and a close reason that is false on its face poisons the audit record at the layer whose whole purpose is that it can be replayed and believed. The enum's discipline is that the reason is stated from the closing party's own perspective; a discipline about perspective presupposes the statement is true from it.

**Make `close_reason` optional when closing from `accepted`.** This weakens the allowlist for no gain: the record would then say a session ended and refuse to say why, on the one path where the reason is the least sensitive fact in the transaction. The allowlist-over-denylist reasoning in the kernel's own comment — a denylist only refuses the leaks someone anticipated — argues for keeping the member required and giving it a truthful value.

**Name it `awarded`.** Considered, and `transaction_committed` chosen for the registry's internal grammar: the members that report an aggregate fact — `transaction_cancelled`, `transaction_expired` — share the `transaction_` prefix, so a reader knows the reason's subject from its form. `awarded` also states the selection rather than the commitment, and selection is not agreement, by section 7 of the state machine; the session closes on the commitment, which is the fact the guard checks.

**Do nothing.** The contradiction stands, and every implementation resolves it privately: some leave the winner open, some invent a value, some reuse a false one. Three implementations, three record shapes for the same success, on the layer where records are supposed to be checkable against one procedure.

## 4. Compatibility

Under [RELEASES.md](../RELEASES.md) section 2 the set is pre-release, and no release has been made. The change is MINOR-shaped by the closest rule in the table: it adds a value for a case previously unexpressible, as an added error code covers a case previously undefined, and no previously conformant implementation emitted the new member, because no schema accepted it. The honest caveat is cross-version validation: a verifier pinned to the old schema refuses a counterparty's `transaction_committed` close event. If reviewers read that as genuine ambiguity, section 2 resolves ambiguity to MAJOR, and pre-release the classification costs nothing either way. The migration surface is one item: an implementation that left awarded sessions resting at `accepted` appends the close event its records were always meant to carry.

## 5. Fixture plan

Planned, not implemented; stage 3 is where these land.

**Allow direction.** A session-stream `session.closed` event from `accepted` carrying `close_reason` `transaction_committed`, on a transaction whose aggregate reached `committed`, validates and replays cleanly to a record in which every session on the committed transaction is terminal.

**Refuse direction.** A session closing with `transaction_committed` on a transaction whose aggregate never reached `committed` fails replay with `A202-EVIDENCE-TRANSITION-ILLEGAL`, because section 6.1's guard did not hold. And a losing session — one not in `accepted` — closing with `transaction_committed` fails the same way, which is what keeps the success reason from ever appearing in a stream whose reader lost, and keeps test 16's property checkable in both directions.

No new reason code is registered; `transaction_committed` is a `close_reason` enum member, not a refusal code, and both refusals use codes section 10 already carries.

## 6. Origin

Found while building the Plural Worlds console's mock dataset, the first surface to express the pilot calibration scenario end to end outside the conformance suite, and recorded there as a documented deviation: the dataset closed the losing session with `not_selected`, as the fixture set does, and left the winning session at `accepted` rather than invent a reason the registry does not carry. This is context for reviewers rather than an argument.
