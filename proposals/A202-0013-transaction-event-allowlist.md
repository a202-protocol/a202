# A202-0013: Type the transaction stream, closing the last open event payload

**Status:** Fixtures and compatibility. Stage 3 of the five stages in [README.md](README.md) section 3. The schema change and fixtures are implemented, and the suite passes with them in place.

**Date:** 28 July 2026

**Status of this document:** Informative in full. It states no requirement on an implementation. The normative text this proposal adopts lands in [schemas/v0.1/commercial-kernel.schema.json](../schemas/v0.1/commercial-kernel.schema.json) and is described by [schemas/canonical-commercial-model-v0.1.md](../schemas/canonical-commercial-model-v0.1.md) section 12.1.

## 1. Problem

Session-stream event `data` has been a closed allowlist since the disclosure work that produced section 12.1 of the canonical model. Transaction-stream `data` stayed an open object, and section 12.1 recorded the reason: suppliers act on session streams and never read the transaction stream, so its audience is the buyer, the operator, and scoped auditors, and typing the whole aggregate lifecycle was deferred.

That reasoning was incomplete in one case, and the case is not an edge. After `agreement.committed` the winning counterparty is a party to the transaction and reads its stream. Every event that named the award therefore reached a supplier, and an `offer.selected` event carrying a losing rival's price, identity, or count in an open `data` object disclosed across counterparties on exactly the boundary the per-session design exists to protect. The review that produced [A202-0009](A202-0009-enforcement-fidelity.md) demonstrated it with an event carrying `winning_price`, `rival_count`, and `losing_bidders` that validated cleanly.

A202-0009 extended the evaluator denylist to every stream kind, which closed the demonstrated leak. It did not close the class. A denylist refuses only the members somebody anticipated, and section 12.1's own argument for preferring allowlists says so: a field named `note` carrying "selected over two cheaper bids" defeats any keyword filter. The allowlist was the real protection on session streams and the transaction stream did not have one.

## 2. Change

A `transactionEventData` definition, closed with `additionalProperties: false`, applied by a third conditional on `eventPayload` gated on `stream.kind` equal to `transaction`. It carries pattern-checked object references and bound hashes only, on the same rule as the session shapes: an event names the signed object it concerns and never restates that object's terms.

The members are the references and hashes the aggregate lifecycle actually uses, drawn from the transition tables rather than invented: `request_id`, `session_id`, `invitation_id`, `invitation_acceptance_id`, `offer_id`, `acceptance_id`, `agreement_id`, `commitment_id`, `obligation_id`, `performance_event_id`, `obligation_response_id`, `exception_id`, `dispute_id`, `determination_id`, `approval_id`, `settlement_instruction_id`, `adapter_receipt_id`, `termination_record_hash`, `remediation_hash`, and `audit_bundle_hash`.

The list was checked back against the transition tables event by event, which is how `acceptance_id` came to be in it: `acceptance.withdrawn` moves the aggregate out of `agreement_pending`, and without that member the record could show that an acceptance had been withdrawn but not which one. An allowlist that cannot express a legal transition's own subject is an allowlist that will be widened in a hurry later, which is the way closed shapes come open.

**No member is required.** Most aggregate transitions are fully described by `from_state`, `event_type`, and `to_state`, and carry no reference at all; an empty `data` object stays valid, which is what every existing transaction-stream fixture carries.

The `req_` prefix is registered for `CommercialRequest` in the canonical model's prefix table, because `request.published` needs to name the request it published and an unregistered prefix would let two implementations mint different ones permanently, for the reason section 5.6 gives for `exc_`.

Section 12.1 is retitled and rewritten: three shapes, and the paragraph that deferred this work is replaced by the reason it was wrong.

## 3. Why this is not over-reach for a pilot

The aggregate transitions are few and reference-shaped, so the allowlist is short and its members were enumerated from the transition tables rather than guessed at. The cost is one definition and one conditional. Against that, the alternative is the position A202-0009 left the set in: an allowlist on one stream, a denylist on the other, and a documented argument for why denylists are insufficient sitting in the same section as the stream that relied on one.

The evaluator denylist remains as the independent second layer on both stream kinds. Both layers still fail closed on their own, which is the property section 12.1 requires and the reason neither replaces the other.

## 4. Compatibility

Under [RELEASES.md](../RELEASES.md) section 2 this is a **MAJOR-shaped tightening** applied pre-1.0. A transaction-stream event carrying any member outside the list is now refused where it previously validated. Every existing fixture passes unchanged, because each carries either an empty `data` object or a member on the list. An implementation that carried commercial content in aggregate event data was carrying content section 12.1 already described as a disclosure risk, and the migration is to move that content into the signed object the event should have named.

## 5. Fixture plan

Implemented: `valid-transaction-event-references` in the allow direction, an award event naming an offer and a session and nothing else. In the refuse direction, `transaction-event-data-free-text-note` carries the `note` field the denylist would never have anticipated, and `transaction-event-data-restates-terms` carries an agreed total on a commitment event; both are refused with `A202-DISCLOSURE-POLICY-VIOLATION`. The pre-existing `transaction-event-data-discloses-rivals` fixture, which the denylist already caught, is now refused by both layers independently.
