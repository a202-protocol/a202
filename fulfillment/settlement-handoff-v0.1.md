# Settlement handoff v0.1

**Status:** Experimental, adopted through proposal [A202-0005](../proposals/A202-0005-settlement-handoff.md). Mixed. Sections 2, 3, 4, 5, 6, and 7 are **normative**. Sections 1, 8, 9, and 10 are **informative** and state no requirement on an implementation. Sections 8, 9, and 10 are annexes describing external payment rails; they are descriptive and impose no requirement on any external protocol.

**Date:** 27 July 2026

**Revised:** 30 July 2026, under [A202-0016](../proposals/A202-0016-casing-short-form-and-amendment-corrections.md): section 2.1 names the registered enum value `settlement_instruction` where it previously named the object kind, which no object could carry and pass schema validation.

**Scope:** Synthetic pilot settlement handoff only

**Relates to:** [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md), [pilot transaction state machine v0.1](../negotiation/pilot-transaction-state-machine-v0.1.md), [commercial mandate v0.1](../authority/commercial-mandate-v0.1.md), [CHARTER.md](../CHARTER.md)

## 1. Purpose

A202 does not execute payments. It states what has been agreed, what is owed, to whom, and when settlement is triggered. Everything after the trigger belongs to a settlement rail.

The line is drawn there because the two sides answer different questions and fail in different ways. A rail answers whether value moved: whether an account was debited, whether a transfer cleared, whether a card authorization held. A202 answers whether value was owed: whether a mandate permitted the commitment, whether the obligation was accepted by a party with authority to accept it, and whether the acceptance can be reconstructed a year later by someone who was not there. A rail cannot answer the second question, because it never saw the negotiation. A202 must not attempt the first, because it holds no funds and settles nothing.

This document specifies the handoff between them: one object that states what a rail is being asked to do, one rule for what may trigger it, one rule for what comes back, and one rule that stops a retry becoming a second payment. The interface is rail-neutral by construction. A rail appears in it only as an opaque registered identifier, and no field in the object is meaningful to one rail and meaningless to another.

The charter records settlement orchestration as a non-goal. This document is not a retreat from that. Moving money, routing payments, choosing a rail, and reconciling ledgers remain outside the specification. What is specified here is the boundary object, which has to exist precisely because the orchestration does not.

## 2. Settlement instruction

`SettlementInstruction` is listed in [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md) section 5.5 as an authorized object whose status derives from receipts. This section states its shape.

### 2.1 Envelope

A `SettlementInstruction` is a shared object and MUST carry the common envelope defined in [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md) section 3, with `object_type` set to `settlement_instruction`. Its identifier prefix is `stl_`, allocated by [A202-0005](../proposals/A202-0005-settlement-handoff.md), which carries the corresponding row into the kernel prefix table.

Two spellings of one thing appear in this document and they are not interchangeable. `SettlementInstruction` names the object kind, which is how the object inventory and the annexes below refer to it. `settlement_instruction` is the registered member of the kernel schema's `object_type` enum, which is the value an instance carries in its envelope. Where a rule states what an object carries, the enum value is what it states.

The envelope's `id` is the instruction identifier referred to throughout this document. The envelope's `transaction_id` is the transaction the instruction belongs to and MUST NOT be null.

### 2.2 Payload

The payload MUST carry every field below and MUST NOT carry any field not listed. The shape is closed for the same reason the session event shapes are closed: an open payload is a channel through which rail-specific detail, and eventually private commercial strategy, arrives inside a shared object.

| Field | Type | Rule |
|---|---|---|
| `obligation_id` | string | The obligation being settled. MUST resolve within this transaction |
| `agreement_id` | string | The agreement the obligation derives from. MUST resolve within this transaction |
| `amount` | money | The A202 money type defined in [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md) section 7: an ISO 4217 alphabetic `currency` and a non-negative base-10 string `amount` |
| `payer_organization_id` | string | The organization that owes |
| `payee_organization_id` | string | The organization that is owed. MUST differ from `payer_organization_id` |
| `trigger` | object | The trigger reference defined in section 3.2 |
| `rail` | string | An opaque registered rail identifier, governed by section 2.3 |
| `idempotency_key` | string | Governed by section 5 |

Every reference is an identifier. The instruction names the obligation and the agreement; it does not restate their terms. A rail adapter that needs the terms resolves the named objects and verifies them, which is a different act from being told them by the instruction and a materially safer one.

`amount` is expressed in the A202 money type and inherits its rules unchanged, including that it is a base-10 string rather than a binary floating-point number and that it is non-negative. A refund, a credit, or a downward adjustment is a directed adjustment object with its own type. A settlement instruction MUST NOT express one as a negative amount, because a sign error in a settlement instruction pays the wrong party.

### 2.3 The rail identifier is opaque and registered

`rail` is a hint to the adapter layer about which settlement rail is expected. It is opaque to the commercial layer: no rule in this specification varies on its value, no invariant depends on it, and no schema field exists for one rail and not another.

An implementation MUST reject an instruction whose `rail` value does not resolve in its registered rail set, with `A202-SETTLEMENT-RAIL-UNKNOWN`. An unregistered rail fails closed. It MUST NOT be passed through to a default adapter, MUST NOT be treated as a free-text routing hint, and MUST NOT be ignored so that the instruction proceeds without a rail.

The reason is the reason given for unregistered constraint types and unresolvable transaction profiles: an unrecognised value that is permitted to pass is a value whose meaning was never checked, and here the unchecked value selects who receives money.

## 3. Trigger condition

### 3.1 What may trigger settlement

Settlement is triggered by an explicit commercial transition. In the normal case that transition is acceptance of the obligation, which is the `acceptance.granted` event that moves the transaction aggregate to `settlement_pending` in [pilot transaction state machine v0.1](../negotiation/pilot-transaction-state-machine-v0.1.md) section 5.

A settlement MUST NOT be triggered by a carrier event. A delivered message, a completed request, a closed connection, a successful callback, and a task reaching a terminal state are all carrier facts and none of them is a commercial transition.

A settlement MUST NOT be triggered by time alone, unless the agreement's own terms stated a time-based condition in a form that parses deterministically. A term such as a named payment date under a named business calendar is such a condition. An implementation's scheduler firing is not, and neither is an operator's belief that enough time has passed.

The distinction is that a parseable condition in the agreement was agreed by both parties and can be re-evaluated identically by anyone replaying the record, whereas an elapsed timer exists only inside one party's infrastructure and cannot be re-evaluated by the other at all.

### 3.2 The trigger reference

The `trigger` object MUST carry both fields:

| Field | Type | Rule |
|---|---|---|
| `condition_ref` | string | The identifier of the accepted term or obligation condition that makes the amount due |
| `accepting_act_hash` | string | The `content_hash` of the act that satisfied the condition, in the lowercase hexadecimal SHA-256 form required by [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md) section 4 |

`accepting_act_hash` binds the instruction to exact bytes. Changing one byte of the accepting act invalidates the binding, in the same way and for the same reason that an approval is bound to an exact action hash.

An implementation MUST refuse an instruction whose `trigger` is absent, whose `accepting_act_hash` does not resolve to a recorded act in this transaction, or whose named act does not satisfy the named condition. The refusal is `A202-SETTLEMENT-TRIGGER-ABSENT`.

A settlement instruction that reaches an adapter without a resolvable trigger is a payment nobody can later show was owed. Refusing it is cheaper than reconstructing it.

## 4. Adapter receipt

### 4.1 What comes back

Whatever executes settlement returns an `AdapterReceipt`, as listed in [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md) section 5.5. The receipt MUST reference both the instruction identifier and the `idempotency_key` of the instruction it answers.

An implementation MUST refuse a receipt that references no instruction, or that references an instruction identifier and idempotency key pair that was never issued, with `A202-SETTLEMENT-RECEIPT-UNMATCHED`. An unmatched receipt is either a misrouted message or an attempt to record a settlement that was never instructed, and both are refused for the same reason: a receipt is an answer, and an answer to a question nobody asked is not evidence of anything.

A failed attempt produces a receipt recording the failure. It does not edit the instruction and does not delete the earlier receipt, because a settlement that failed twice and succeeded on the third attempt is a fact about the transaction that a reader is entitled to see.

### 4.2 A receipt is evidence, never authority

An `AdapterReceipt` is an evidence reference. It records what an external system said in response to a request.

An implementation MUST NOT infer authority from a receipt. Specifically:

1. it MUST NOT treat a successful receipt as evidence that the instruction was authorized;
2. it MUST NOT treat a successful receipt as evidence that an obligation was performed, or accepted, or discharged;
3. it MUST NOT treat connectivity to a rail, possession of rail credentials, or the ability to obtain a receipt from a rail as conferring any commercial authority whatsoever.

The third is the one that matters most in practice. An integration that can reach a payment rail is an integration that can move money, and it is tempting to read that capability as permission. It is not. Authority in A202 comes from the mandate chain and from nowhere else, and an adapter with excellent connectivity and no mandate may do nothing. Payment is not agreement, and an adapter acknowledgment is not agreement; both statements are already in the state machine's offer rules and this section adds no exception to them.

The corollary runs the other way too. A rail that refuses or reverses a payment has not cancelled an obligation. The obligation stands, and the shortfall is a performance or settlement exception, resolved through the exception path in the state machine by parties with authority to resolve it.

## 5. Idempotency

The same instruction identifier and `idempotency_key` pair MUST NOT produce a second settlement.

An implementation MUST record the pair on first submission and MUST, on any subsequent submission of the same pair, return the original result rather than performing the settlement again. A retry references the original; it does not create a new instruction.

A submission that presents an already-recorded pair with different instruction content MUST be refused with `A202-SETTLEMENT-IDEMPOTENCY-CONFLICT`. It MUST NOT be treated as a retry, and it MUST NOT overwrite the recorded instruction. Two different instructions carrying one key is an error in the sender, and resolving it by preferring either version silently would pay one of the two amounts with no record of the disagreement.

This mirrors the kernel's existing duplicate-event rules, where a duplicate with an identical idempotency key returns the original result and a duplicate with different content returns a conflict. The rules are the same here because the failure is the same: a retry after an ambiguous timeout is the ordinary case, and it is the case in which a system most easily pays twice.

## 6. Non-custodial posture

The commercial layer never holds funds.

1. An implementation of this specification MUST NOT receive, hold, pool, or disburse funds belonging to a transacting party as part of its commercial-layer function.
2. A `SettlementInstruction` MUST NOT name the operator, or any commercial-layer component, as `payee_organization_id` for the purpose of onward transmission to the true payee. The payee is the party that is owed.
3. An implementation MUST refuse an instruction that violates either rule, with `A202-SETTLEMENT-CUSTODY-REFUSED`.

Custody is a rail property. Where funds are held between the payer and the payee, they are held by the rail or by a party the rail defines, under that rail's own rules, and the commercial layer records only that an instruction was issued and what came back.

The posture is stated normatively rather than left as an implementation choice because it is load-bearing for everything above it. A layer that holds funds acquires an interest in the outcome of the disputes it also adjudicates, and every disclosure and authority rule in this specification is written on the assumption that no such interest exists.

## 7. Refusal codes

These codes belong to the same registry as the codes in [pilot transaction state machine v0.1](../negotiation/pilot-transaction-state-machine-v0.1.md) section 10.

| Code | Meaning |
|---|---|
| `A202-SETTLEMENT-RAIL-UNKNOWN` | The `rail` identifier does not resolve in the registered rail set |
| `A202-SETTLEMENT-TRIGGER-ABSENT` | The trigger is absent, does not resolve, or does not satisfy the named condition |
| `A202-SETTLEMENT-IDEMPOTENCY-CONFLICT` | A recorded instruction identifier and idempotency key pair was presented with different content |
| `A202-SETTLEMENT-RECEIPT-UNMATCHED` | A receipt references no issued instruction identifier and idempotency key pair |
| `A202-SETTLEMENT-CUSTODY-REFUSED` | An instruction would place funds in the custody of the commercial layer |

## 8. Annex A: AP2

**Informative.** This annex is descriptive. It records how the objects in this document line up with a purchase-authorization protocol so that an implementer holding both can see where a mapping is available and where it is lossy. It creates no requirement on AP2 and asserts no equivalence.

**Checked 27 July 2026** against the AP2 v0.2 specification documents.

AP2 defines two mandate types. A Checkout Mandate is described as providing the merchant with cryptographic proof that the shopping agent is authorized to purchase. A Payment Mandate is described as providing the credential provider, the payment network, and the merchant's payment processor with cryptographic proof. AP2 describes two modes, one in which the user is present and approves directly, and one in which the user is not present and approves a constrained mandate in advance that the agent later closes with its own key. AP2 states that it operates as a security feature within a commerce protocol, and that catalog interfaces, checkout update interfaces, and the specific interfaces between roles are outside its scope.

At the level verified, the correspondence is:

| A202 | Nearest AP2 construct |
|---|---|
| Accepted obligation, bound by `accepting_act_hash` | Input to the purchase content over which a Checkout Mandate is taken |
| `SettlementInstruction` | Input to the payment authorization a Payment Mandate covers |
| `AdapterReceipt` | Reference to the result reported by the payment side |

The mapping is stated at the level of the objects and not at the level of fields. No AP2 field name is restated here, because a binding written against field names would become false the first time either specification revised one, and an implementer who needs those names should read AP2 rather than a summary of it.

What AP2 covers that A202 deliberately does not restate: the presentation and handling of payment credentials, the roles and obligations of the credential provider, the network, and the payment processor, the proof each of those parties requires, and the dispute procedures attached to a payment. A202 states none of these and defers to AP2 or to any other rail on all of them.

The division of ownership is that AP2 owns authentication to itself, including whatever proves to a merchant or a processor that a purchase was authorized on the payment side. A202 owns the commercial state: what was negotiated, under what authority, what was accepted, and what is therefore owed.

## 9. Annex B: x402

**Informative.** This annex is descriptive. It creates no requirement on x402 and asserts no equivalence.

**Checked 27 July 2026** against the x402 HTTP transport specification, version 2.

x402 defines a payment interaction over HTTP for machine-payable endpoints. A resource server that requires payment answers a request with HTTP status `402 Payment Required` and a challenge carried in a base64-encoded header field, `PAYMENT-REQUIRED`, whose object carries `x402Version`, `error`, `resource`, and an `accepts` array. Each entry in `accepts` carries `scheme`, `network`, `amount`, `asset`, `payTo`, `maxTimeoutSeconds`, and `extra`. The client resubmits with a payment payload in a `PAYMENT-SIGNATURE` header field, and the server returns settlement detail in a `PAYMENT-RESPONSE` header field. Header field names have differed between x402 transport versions, so an implementation binds to a specific transport version rather than to the names alone; this annex accordingly states the mapping at the level of the flow.

The mapping to this document is short, and the important part of it is a negative:

- receiving a `402` challenge is **not** a A202 trigger. It is a rail's demand for payment at the point of resource access. Under section 3, the trigger is a commercial transition, and a challenge issued by a counterparty's server is not one;
- where a A202 obligation exists, the trigger governs. The accepted obligation is what makes the amount due, and the `402` exchange is how the corresponding `SettlementInstruction` is discharged for that rail;
- the settlement detail returned in the response is an evidence reference for an `AdapterReceipt` under section 4, and inherits section 4.2 in full: it evidences that a transfer was reported, never that a commitment was authorized.

x402 is designed for interactions in which the commercial relationship is thin, often a single priced request with no negotiation and no prior agreement. A202 has nothing to add to that case, and an endpoint operating in it is not obliged to produce A202 objects at all. The mapping is for the case where a negotiated obligation exists and the parties choose this rail to discharge it.

The division of ownership is that x402 and its facilitators own authentication to the rail and the movement of value on it. A202 owns the commercial state that says the value was owed.

## 10. Annex C: ACP

**Informative.** This annex is descriptive. It creates no requirement on ACP and asserts no equivalence.

**Checked 27 July 2026** against the Agentic Commerce Protocol specification, maintained by OpenAI and Stripe, whose specification versions are dated; the surfaces below were read at version `2026-04-17`.

ACP defines a delegated checkout model in which a buyer's agent completes a purchase with a business without becoming the merchant of record. It defines an Agentic Checkout API organized around a checkout session, with operations to create, update, retrieve, complete, and cancel one, and a Delegate Payment API through which a payment credential is delegated for that purchase. It also defines a product feed, cart and order surfaces, capability negotiation, and an extension mechanism.

At the level verified, the correspondence is:

| A202 | Nearest ACP construct |
|---|---|
| Accepted obligation, bound by `accepting_act_hash` | Upstream of the checkout session; the commercial fact the session is opened to discharge |
| `SettlementInstruction` | Input to completing the checkout session for the named rail |
| `AdapterReceipt` | Reference to the order or completion result the merchant side returns |

The checkout session is the rail's own state for a purchase and A202 does not restate it. In particular, a A202 transaction does not track session lifecycle, and a cancelled checkout session does not cancel an obligation; that would be a carrier or rail event determining commercial state, which section 3.1 and the state machine both refuse.

A delegated payment credential is authority over a payment instrument. It is not commercial authority, and section 4.2 applies to it directly: holding a delegated credential does not permit an agent to commit its organization to anything, and the rule that forbids reading it that way is the one already stated in section 4.2. This annex only points at it.

The division of ownership is that ACP owns authentication to itself, including how an agent proves to a business that it may complete a checkout and how a payment credential is delegated. A202 owns the commercial state: what was negotiated, under what authority, what was accepted, and what is owed.
