# A202-0017: State the status an accepted submission returns, and state that no status is acceptance

**Status:** Adopted. The normative text this proposal adds is carried by [bindings/a2a-binding-v0.1.md](../bindings/a2a-binding-v0.1.md) section 7.4, which marks it.

**Date:** 3 August 2026

**Status of this document:** Informative in full. It states no requirement on an implementation.

## 1. Problem

Section 7 of the carrier binding states what a refusal returns and does not state what success returns. A capability failure is answered with `412`, by section 7.3. A sequence mismatch is answered with `409`, by [pilot transaction state machine v0.1](../negotiation/pilot-transaction-state-machine-v0.1.md) section 8. A submission that fails neither is answered with whatever status the implementer guessed, and every likely guess asserts something the carrier is not entitled to assert. `200` asserts that the request's effect is complete. `201` asserts that a resource was created. Each lets the carrier response appear to state a commercial outcome, and the binding's own doctrine is that it never does: a carrier event is not a commercial event, in section 1 of the binding, and an adapter acknowledgment is not agreement, in section 7 of the state machine.

The gap also manufactures meaningless divergence. Two responders that accept the same submission and answer with different statuses hand an integrator a difference that means nothing, and a difference that means nothing is the kind that gets meaning read into it.

There is one HTTP status whose registered meaning is receipt without outcome: `202`, accepted for processing, processing not completed, no commitment to the result. It is the only status section 7 could have meant, and it was not written.

## 2. Change

One subsection, [section 7.4 of the binding](../bindings/a2a-binding-v0.1.md), stating three rules:

1. A submission under section 7.1 that the responder does not refuse in the response is answered with HTTP status `202`.
2. A responder does not answer a submission with `200` or `201`. Either status asserts an outcome, completion in one case and creation in the other, and the outcome of a commercial act is never in the carrier response.
3. `202` states receipt for evaluation and nothing else. It does not state that the object validated, appended, or will be acted on. The refusal statuses stand unchanged: `412` under section 7.3, `409` under the state machine's section 8. A responder that answers `202` and evaluates afterwards conveys any later refusal the way every commercial outcome is conveyed, as a signed object; the status carries no promise that a refusal cannot follow.

No response body is defined for the `202`. Anything a responder puts there is carrier framing under section 5.2, is covered by no signature, and section 9 of the binding applies to it.

## 3. What this proposal does not change

No schema changes. No object changes shape, no enum gains or loses a member, no reason code is added, and no state or transition is touched. The refusal statuses in section 7.3 and the state machine's section 8 are unchanged. The A2A leg of the binding is unchanged: statuses belong to the plain HTTPS binding, and A2A's framing is A2A's own. The reference implementation is unchanged because nothing in the set implements the HTTPS binding today: `a202_mcp` speaks stdio and `a202_reference` is a library.

## 4. Alternatives considered

**`200 OK`.** Rejected. It is the natural default and it is wrong even where evaluation is synchronous: the append can be complete while the commercial determination is not in the response, because it is never in the response. A status that reads as "done" invites the integrator to treat the carrier as the outcome, which is the reading the binding exists to forbid.

**`201 Created` with a `Location`.** Rejected. It treats a commercial object as a carrier resource. An object's identifier is minted inside the signed object, not by the endpoint that received it, and a `Location` header would be unsigned carrier framing pointing at signed material.

**Return the new stream sequence in the response body.** Rejected. It is derivable, because an append succeeds only when `expected_sequence` equals the stream's current sequence, so the successor is one more, and putting it in the response would place load-bearing data in unsigned carrier framing, against section 9.

**Leave it unspecified.** Rejected; it is the defect. The section states two of the three responses an endpoint can give and lets the third diverge silently.

## 5. Compatibility

This is the MAJOR shape under [RELEASES.md](../RELEASES.md) section 2 by the letter: it adds a requirement, and a responder that answered `200` yesterday was conformant and today is not. The ambiguity rule is not needed to classify it. No release has been tagged, so there is no version number to increment against and no implementation population to migrate; the rule enters the set before the first tag, which is the last moment a MAJOR-shaped correction is free.

## 6. Fixture plan

None, and deliberately. The fixture surface is canonical bytes and classifications: the manifest and the runner open no connection and observe no status line. This is the boundary [A202-0001](A202-0001-carrier-bindings.md) drew for carrier behaviour that fixtures cannot reach: the runtime case is recorded for implementation-level verification. When an implementation of the HTTPS binding enters the set, its test asserting the `202` is implementation-level, not conformance-level.

## 7. Origin

The founder review of 3 August 2026, reading section 7's response semantics end to end: the section stated what a refusal returns and what a conflict returns, and did not state what success returns.
