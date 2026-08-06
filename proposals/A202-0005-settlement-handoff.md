# A202-0005: Rail-neutral settlement handoff

**Status:** Fixtures and compatibility. Stage 3 of the five stages in [README.md](README.md) section 3. The static fixtures in section 5 are implemented in the conformance suite; the three runtime cases remain recorded for implementation-level verification.

**Date:** 27 July 2026

**Marking:** This proposal is informative in full. It states no requirement on an implementation. The normative text it proposes lands in [fulfillment/settlement-handoff-v0.1.md](../fulfillment/settlement-handoff-v0.1.md), which marks its own normative sections.

## 1. Problem

The specification already names the boundary and then stops at it. [CHARTER.md](../CHARTER.md) section 3 records settlement orchestration as a non-goal and states that a settlement instruction is an authorized object and an adapter receipt is evidence of an external system's response. [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md) section 5.5 lists `SettlementInstruction` and `AdapterReceipt` as objects. [pilot transaction state machine v0.1](../negotiation/pilot-transaction-state-machine-v0.1.md) has a `settlement_pending` state and a `settlement.instructed` event whose guard reads "payment mandate and conditions valid".

None of that says what a settlement instruction contains, what may cause one to be issued, or what an implementation does with a receipt. Four things go wrong as a result, and each of them goes wrong with money.

**Nothing states what triggers settlement.** An implementer wiring an obligation to a payment rail has to decide for itself whether the trigger is the acceptance event, the arrival of a delivery notification, a scheduler firing on a due date, or a callback from the rail. Each of these is a defensible reading of "conditions valid", and they disagree. Two of them let a carrier event or a local timer move money, which means a party can be debited on the strength of a fact its counterparty cannot re-evaluate from the record.

**A rail identifier has nowhere neutral to live.** With no stated field, rail selection ends up either as a typed field in the kernel, which breaks the market-neutrality property that section 8 of the canonical model makes testable, or as free text, which fails open on a value nobody checked. The value in question selects who receives the money.

**Retry is undefined at the boundary where retry is most dangerous.** The kernel has duplicate-event rules, but nothing extends them across the handoff. An adapter call that times out ambiguously is the ordinary case in payments, and an implementation that retries without a stated idempotency rule pays twice.

**Connectivity reads as permission.** An integration that can reach a payment rail can move money, and there is currently no statement anywhere that this capability confers no commercial authority. The absence is the dangerous kind: the wrong behaviour is the intuitive one. An adapter that holds working rail credentials and returns a successful receipt looks, to a system with no rule to the contrary, exactly like proof that the payment was authorized and the obligation discharged. It is proof of neither.

## 2. Proposal

Add one document, [fulfillment/settlement-handoff-v0.1.md](../fulfillment/settlement-handoff-v0.1.md), specifying the handoff interface, and add five refusal codes.

The substance is:

1. **Settlement instruction.** A closed payload on the common envelope, carrying `obligation_id`, `agreement_id`, `amount` in the A202 money type, `payer_organization_id`, `payee_organization_id`, a `trigger` object, an opaque `rail` identifier, and an `idempotency_key`. Every commercial reference is an identifier; the instruction names the obligation and the agreement rather than restating their terms.

2. **Rail registry fails closed.** `rail` is opaque to the commercial layer, no rule varies on its value, and an unregistered value is refused with `A202-SETTLEMENT-RAIL-UNKNOWN` rather than passed to a default adapter or ignored.

3. **Trigger condition.** Settlement is triggered by an explicit commercial transition, normally obligation acceptance, and the trigger carries the `content_hash` of the accepting act so that changing one byte of that act invalidates the binding. A carrier event never triggers settlement. Time alone never triggers settlement unless the agreement's own terms stated a deterministically parseable time condition.

4. **Adapter receipt.** A receipt references the instruction identifier and the idempotency key it answers, and an unmatched receipt is refused. A receipt is an evidence reference and never authority, stated as an explicit rule that an implementation must not infer authorization, performance, or discharge from a receipt, and must not infer any commercial authority from connectivity to a rail, possession of rail credentials, or the ability to obtain a receipt.

5. **Idempotency.** The same instruction identifier and idempotency key pair must not produce a second settlement; a retry returns the original result, and the same pair presented with different content is a refused conflict rather than an overwrite.

6. **Non-custodial posture.** The commercial layer never holds funds, and an instruction naming the operator as payee for onward transmission is refused. Custody is a rail property.

7. **Three informative annexes**, one per rail, describing how an accepted obligation and a settlement instruction line up with AP2, x402, and ACP at the level verified against each specification on 27 July 2026. Each annex is marked descriptive, creates no requirement on the external protocol, and states the same division: the rail owns authentication to itself, A202 owns the commercial state.

## 3. Alternatives considered

**Do nothing.** Leave the boundary named but unspecified, as it is today. Every implementation then defines its own trigger, its own retry rule, and its own reading of what a receipt proves, and the four failures in section 1 recur independently in each. It also leaves the non-custodial rule and the no-authority-from-connectivity rule with nowhere to be stated, which means neither can be tested. Rejected.

**Specify settlement execution.** Rejected on two independent grounds. It is a charter non-goal, and it would require the specification to describe holding funds, which section 6 of the proposed document forbids for reasons that are load-bearing for the disclosure and authority rules above it.

**Make `rail` a typed enumeration in the kernel.** Rejected. It puts a value in the kernel that is meaningful to one rail and meaningless to another, which is precisely what the market-neutrality rule forbids, and it makes every new rail a kernel change and therefore a specification release.

**Allow an open extension object on the instruction for rail-specific fields.** Rejected. An open payload on a shared object is the channel through which rail detail arrives first and private commercial strategy arrives later, and the specification has already made this argument once, in favour of allowlisted session event shapes. The closed payload plus an opaque rail identifier keeps neutrality testable rather than asserted.

**Allow time-based triggers generally.** Rejected. A due date agreed in the terms and a scheduler firing in one party's infrastructure look identical from inside that party and are not the same fact. The first can be re-evaluated identically by anyone replaying the record; the second cannot be re-evaluated by the counterparty at all.

**Treat the adapter receipt as the settlement fact.** Rejected. It inverts the direction of authority: the obligation would be discharged because an external system said so, rather than the external system having been instructed because the obligation was accepted. It also leaves no coherent answer when a rail reverses a payment.

## 4. Compatibility

**A new object family reference, not a change to an existing one.** `SettlementInstruction` and `AdapterReceipt` are already listed in [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md) section 5.5. This proposal states the shape of the first and the binding rule for the second. No existing object gains, loses, or reinterprets a field. No state, transition, or guard changes; the existing `settlement.instructed` event and `settlement_pending` state are unchanged, and the proposal states what satisfies the guard rather than altering it.

**One identifier prefix is allocated:** `stl_`, carried into the kernel prefix table in [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md) section 3 under this proposal. No existing prefix changes.

**Five codes are added,** in the same registry as the codes in [pilot transaction state machine v0.1](../negotiation/pilot-transaction-state-machine-v0.1.md) section 10: `A202-SETTLEMENT-RAIL-UNKNOWN`, `A202-SETTLEMENT-TRIGGER-ABSENT`, `A202-SETTLEMENT-IDEMPOTENCY-CONFLICT`, `A202-SETTLEMENT-RECEIPT-UNMATCHED`, and `A202-SETTLEMENT-CUSTODY-REFUSED`. All five cover conditions that are currently undefined, so no case that previously produced a code produces a different one.

**The rail registry is fail-closed and initially empty.** An implementation registers the rails it operates. An unregistered value is refused, which means an implementation that adds a rail adds it deliberately rather than by transmitting a string. Adding a rail to a registry is not a specification change.

Under [RELEASES.md](../RELEASES.md) section 2 this is a **MINOR** change: it adds an object shape and error codes for previously unspecified behaviour and invalidates no conformant implementation. An implementation that issues no settlement instructions is unaffected.

**Migration.** None for an implementation that does not settle. An implementation that already emits an instruction-shaped object of its own devising migrates by adopting the closed payload, registering its rail identifiers, and binding its trigger to an accepting act hash. There is no compatibility mode in which an unregistered rail is accepted, because a fail-closed registry with an escape hatch is an open registry.

## 5. Fixtures

Fixtures are added to [conformance/manifest-v0.1.json](../conformance/manifest-v0.1.json) and run by [conformance/run-conformance.py](../conformance/run-conformance.py).

| Fixture | Direction | Expected | What it distinguishes |
|---|---|---|---|
| `valid-settlement-instruction.json` | allow | valid | A complete instruction: closed payload, money as a base-10 string, a trigger naming a condition and an accepting act hash, a registered rail, and an idempotency key |
| `negative/settlement-instruction-unknown-rail.json` | refuse | `A202-SETTLEMENT-RAIL-UNKNOWN` | A `rail` value absent from the registered set fails closed. An implementation that routes it to a default adapter, or that drops the field and proceeds, fails |
| `negative/settlement-instruction-no-trigger.json` | refuse | `A202-SETTLEMENT-TRIGGER-ABSENT` | An instruction with no trigger, and an instruction whose trigger names no resolvable accepting act, are both refused. Settlement without a stated commercial cause does not reach an adapter |

Three required behaviours need runtime state and cannot be expressed as static documents. They are verified against a running implementation, in the manner of the runtime items already listed in [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md) section 15:

1. **Duplicate idempotency key refused.** The same instruction identifier and idempotency key pair is submitted twice with identical content, then a third time with a different amount. The assertions are that the second submission returns the original result and causes no second settlement, and that the third is refused with `A202-SETTLEMENT-IDEMPOTENCY-CONFLICT` and does not overwrite the recorded instruction. An implementation that settles twice, or that silently prefers either amount, fails.

2. **Receipt without a matching instruction refused.** A receipt is presented naming an instruction identifier and idempotency key pair that was never issued. The assertion is refusal with `A202-SETTLEMENT-RECEIPT-UNMATCHED`, and that no obligation status changes as a result. The negative direction of the rule that a receipt is an answer, not an authority.

3. **Settlement without a trigger refused at runtime.** An instruction is submitted for an obligation that has not been accepted, with the transaction not in `settlement_pending`. The assertion is refusal, no adapter call, and no state change. This is required test 6 in [pilot transaction state machine v0.1](../negotiation/pilot-transaction-state-machine-v0.1.md) section 11, "settlement instruction before acceptance", now carrying a stated code.

Both directions are present for every rule this proposal introduces, which is the stage 3 requirement in [README.md](README.md) section 3. Stage 3 is not claimed here; the fixtures above are the plan against which it is attempted.

## 6. Origin

The proposal arose from specification review rather than from any implementation's experience, and no rail integration informs it. The four failures in section 1 are reasoned from the existing objects and guards rather than observed.

The external rails described in the annexes were read on 27 July 2026: AP2 at version 0.2, the x402 HTTP transport specification at version 2, and the Agentic Commerce Protocol at its dated specification version `2026-04-17`. The annexes state mappings at the level of objects and flows rather than at the level of fields, because a mapping written against another specification's field names becomes false the first time that specification revises one, and a reader who needs those names is better served by the source.

Reviewers should treat the annexes as the weakest part of the proposal. They are informative, they create no requirement in either direction, and any of the three external specifications may have moved since the date above.
