# A2A carrier binding v0.1

**Status:** Experimental, adopted through proposal [A202-0001](../proposals/A202-0001-carrier-bindings.md); section 7.4 adopted through [A202-0017](../proposals/A202-0017-submission-success-status.md). Mixed. Sections 2, 3, 4, 5, 6, 7, and 8 are **normative**. Sections 1 and 9 are **informative** and state no requirement on an implementation.

**Date:** 27 July 2026

**Scope:** Synthetic pilot transport only

**Relates to:** [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md), [pilot transaction state machine v0.1](../negotiation/pilot-transaction-state-machine-v0.1.md), [commercial mandate v0.1](../authority/commercial-mandate-v0.1.md), [release policy](../RELEASES.md)

## 1. Purpose

A202 objects are carrier-independent. An offer means the same thing whether it arrives over an agent protocol, over a plain HTTPS request, or on a memory stick. The canonical model defines that meaning and defines the bytes that carry it. Nothing in the meaning depends on how the bytes moved.

This document states how those objects travel over the A2A protocol, and how they travel over plain HTTPS for a party that does not run A2A. It is a binding, not a second specification of commercial semantics. Where this document and the canonical model appear to say different things about an object, the canonical model is the object's definition and this document is wrong.

Session mechanics belong to the carrier. Turn order, request timeouts, cancellation, streaming, retries, push notification, and connection lifetime are carrier concerns, and A202 states no requirement on any of them. This is deliberate rather than an omission. A commercial specification that also specified conversational discipline would have to be reimplemented for every carrier it was ported to, and the two sets of rules would drift. The transaction and session state machines constrain which transitions are legal; they do not constrain the conversation that proposes them.

Two consequences follow, and both are load-bearing later in this document. A carrier event is not a commercial event: a cancelled request, a dropped stream, and a timed-out task change nothing about what has been agreed. And a carrier session is not a commercial correlation: what binds an act to a transaction is the transaction identifier inside the signed object, not the connection it arrived on.

**Checked 27 July 2026** against the A2A specification and its interface definition at version 1.0. Where a detail of A2A could not be verified from those sources, this binding states the requirement at the level of the declaration and leaves the carrier detail to the carrier.

## 2. Extension declaration

The A202 commercial extension is declared using A2A's own extension mechanism. A202 defines no parallel discovery surface for it.

### 2.1 Where the declaration sits

A party that carries A202 commercial objects over A2A MUST declare the A202 commercial extension in its A2A AgentCard, as one entry in the extension array carried by the card's capabilities object.

The entry MUST populate A2A's declared extension fields as follows:

| A2A extension field | Required value |
|---|---|
| `uri` | Exactly the extension URI in section 2.2 |
| `description` | A human-readable statement that the agent exchanges A202 commercial objects |
| `required` | `true` when the party requires the extension under section 3, `false` otherwise |
| `params` | The version declaration object in section 4.1 |

A party MUST NOT declare the extension in any other field of the card, and MUST NOT treat a skill name, a description string, or an output mode as a declaration of A202 support. A capability that is inferred is a capability that was guessed.

### 2.2 Extension URI

The v0.1 extension URI is:

```text
https://schemas.a202.org/a2a-ext/commercial/0.1
```

The URI is issued under `schemas.a202.org`, a host the project controls, and is the long-lived commitment for v0.1. It replaces an earlier placeholder on the reserved `.invalid` top-level domain, which was used while no host had been settled so that the placeholder could not resolve to a host anyone controls. An implementation that hard-coded the placeholder hard-coded a value that has now changed.

The URI carries the specification minor version because A2A requires a new extension URI when an extension makes a breaking change to its logic, data structures, or required parameters. A breaking change to this binding therefore produces a new URI rather than a new value inside the existing one, and an agent that supports only the new version simply does not declare the old URI. Version negotiation inside a single URI is additionally available through section 4 for changes that are not breaking.

### 2.3 Activation

A client that intends to exchange A202 commercial objects in a request MUST activate the extension by naming the URI in section 2.2 in A2A's extension activation service parameter, which A2A carries as a comma-separated list of extension URIs under the field name `A2A-Extensions`.

A server that accepts the activation echoes it under A2A's own rules. A client MUST treat an absent echo as non-activation and MUST apply section 3 to it. Silence is not acceptance.

## 3. Mandatory to understand

### 3.1 A party may require the extension

A party MAY require the A202 commercial extension, by declaring `required` as `true` in its own card entry. A party that requires the extension is stating that it will not conduct a commercial exchange with a counterparty that cannot parse, validate, and refuse A202 objects correctly.

### 3.2 Failure is closed and it happens first

When a party requires the extension, interaction with a counterparty that does not declare support MUST fail closed **before any A202 commercial object is exchanged**, and the refusal code is `A202-EXTENSION-UNSUPPORTED`.

Each of the following is a failure to declare support, and all four produce the same refusal:

1. the counterparty's card carries no entry with the URI in section 2.2;
2. the entry is present and its version declaration does not parse under section 4.1;
3. the version declaration parses and section 4.2 finds no compatible version;
4. the counterparty's card cannot be retrieved at all.

Condition 4 is included for the same reason that an unresolvable mandate status endpoint denies rather than allows: unavailability is not permission. A party that cannot be checked has not passed the check.

### 3.3 The check runs at capability negotiation, not at first commercial act

The fail-closed check applies to capability negotiation itself, not only to the exchange of mandates or of objects that carry money. The order is: resolve the counterparty declaration, evaluate section 4.2, then and only then transmit.

This ordering matters because the first A202 object a party sends is frequently not an offer. It is a counterparty invitation, a qualification request, or a mandate presented for verification, and each of those discloses something: that a transaction exists, that this party is participating in it, which categories it is buying in, or which principal issued its authority. A capability check that ran at first offer would have leaked all of that to a counterparty that was never able to participate.

A party MUST NOT downgrade to a bare carrier exchange when the check fails. There is no defined behaviour for a A202 object exchanged outside the extension, so a fallback path would be a path along which commercial objects move under no stated rules at all.

### 3.4 A declaration is not authority

Declaring the extension states what a counterparty can parse. It states nothing about what that counterparty may commit to, on whose behalf, or within what limits. Authority is established only by the mandate chain in [commercial mandate v0.1](../authority/commercial-mandate-v0.1.md), and an implementation MUST NOT treat extension support, extension activation, or a successful capability negotiation as an input to any authority decision.

## 4. Version declaration and mismatch

### 4.1 What travels in the declaration

The extension declaration's parameter object MUST carry exactly two fields:

| Field | Type | Meaning |
|---|---|---|
| `read_versions` | array of strings, at least one entry | The read version, as defined in [RELEASES.md](../RELEASES.md) section 4 |
| `write_version` | string | The write version, as defined in [RELEASES.md](../RELEASES.md) section 4 |

Each value is a specification set version of the form `MAJOR.MINOR`. The meaning of the two declarations, the rule that both are declared, and the rule that a party never writes a version it cannot read are stated in [RELEASES.md](../RELEASES.md) section 4 and are not restated here. This section states only how the two declarations travel over this carrier.

A declaration that omits either field, that carries `read_versions` as an empty array, or that carries a value that is not of the form `MAJOR.MINOR` does not parse, and section 3.2 condition 2 applies.

### 4.2 Mismatch fails closed

Before any A202 commercial object is exchanged, each party MUST evaluate the counterparty's declaration against its own:

1. the counterparty's `write_version` MUST appear in this party's `read_versions`;
2. this party's `write_version` MUST appear in the counterparty's `read_versions`.

If either check fails, the interaction fails closed with `A202-EXTENSION-UNSUPPORTED`. An implementation MUST NOT proceed on a partial match, MUST NOT select a nearest version, and MUST NOT fall back to an older version of the extension URI. A version an implementation did not declare is a version it did not commit to reading.

### 4.3 One code for four conditions

All four conditions in section 3.2 return `A202-EXTENSION-UNSUPPORTED`. They are not distinguished.

The reason is not disclosure; an AgentCard is published and a caller can read the declaration for itself. The reason is that the four conditions have exactly one correct outcome, and a caller handed four codes that must all be handled identically will eventually handle one of them differently. A single code keeps the fail-closed path single, so that widening one branch of it cannot quietly open another.

An implementation MAY log the distinguishing detail locally. It MUST NOT vary the code on the wire.

## 5. Object transport

### 5.1 Objects travel as message parts

A A202 shared object travels as a part of an A2A message. One part carries exactly one object. A message MAY carry several parts and therefore several objects.

### 5.2 Canonical bytes are the object

The bytes carried in the part MUST be byte-identical to the object's canonical form under [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md) section 4, which is JSON Canonicalization Scheme serialization under RFC 8785.

The object MUST therefore be carried in a part whose content is opaque bytes, with the media type `application/a202-commercial+json`. A part that carries the object as structured data is re-serialized by the carrier and by every intermediate library that touches it, and a re-serialized object is a different sequence of bytes even when it is the same JSON document. Such a part MAY accompany the object as a parsed convenience view for a reader, and an implementation MUST NOT treat it as the object, MUST NOT hash it, and MUST NOT verify a signature against it.

A receiver MUST verify against the bytes it received. An implementation that parses, re-serializes, and then hashes has verified its own serializer rather than the sender's object.

### 5.3 Signatures cover the object, never the framing

Signatures cover the canonical bytes defined in section 5.2 and nothing else. No signature in this binding covers a message identifier, a task identifier, a context identifier, a part metadata field, a transport header, or any other carrier framing.

This follows from the canonical model rather than adding to it: `content_hash` is computed over the object's canonical content with `content_hash`, `signatures`, and `kernel_annotations` omitted, and carrier framing is not part of that content at all.

### 5.4 Carrier metadata stays outside the signed bytes

Carrier metadata MUST NOT appear inside the signed bytes. A sender MUST NOT copy a task identifier, a context identifier, a message identifier, a header value, or any other carrier-assigned value into the object before hashing it.

A receiver that finds carrier framing inside the signed bytes MUST refuse the object. No new refusal code is defined for this case, because none is needed: the kernel envelope and the payload shapes are closed, an unknown field fails schema validation, and the canonical model already requires that unknown fields fail validation. The refusal is a kernel validation refusal and is reported as such.

The rule exists because a signature over carrier framing would make the object mean something different depending on how it travelled. An agreement that verifies only when replayed alongside the task that carried it is an agreement that depends on the carrier's records surviving, which is the dependency the audit design exists to remove.

## 6. Task to transaction correlation

### 6.1 The relationship is many to one, and it is not a mapping

Many A2A tasks may serve one A202 transaction. A task may serve none. A single task may carry objects belonging to more than one transaction, though an implementation is not obliged to allow that.

The A202 transaction aggregate defined in [pilot transaction state machine v0.1](../negotiation/pilot-transaction-state-machine-v0.1.md) is the commercial source of truth. There is no correspondence between the carrier's task lifecycle and the aggregate's states, and an implementation MUST NOT construct one.

### 6.2 Task state does not determine transaction state

Task state MUST NOT determine transaction state.

A task that reaches a failed, cancelled, or rejected state is a carrier event. It reports that a unit of carrier work did not complete. It does not cancel a transaction, does not withdraw an offer, does not release a selection freeze, and does not terminate an agreement. Any commercial consequence requires an explicit A202 transition: a signed, authorized event that satisfies the guard for that transition, exactly as required by [pilot transaction state machine v0.1](../negotiation/pilot-transaction-state-machine-v0.1.md) section 1.

The concrete case this rule exists for is ordinary. A supplier's agent submits a signed offer; the offer is appended to the session stream; the carrier request that delivered it then times out and its task is recorded as failed. The offer stands. The supplier is bound by it until it expires or is withdrawn by an authorized withdrawal event. An implementation that swept the offer away with the failed task would have let a network condition retract a commercial commitment, and neither party signed anything to that effect.

The same holds in the other direction. A task that reaches a completed state completes nothing commercially. Acceptance is not selection, selection is not agreement, and a completed carrier task is further from agreement than any of them.

### 6.3 Correlation is carried by the transaction identifier

Correlation between a carrier exchange and a transaction is carried by `transaction_id` in the extension payload. No carrier identifier correlates a commercial act to a transaction.

A message that carries a transaction-bound A202 object MUST carry, in the extension payload, the same `transaction_id` as the object's envelope. Where the two disagree, the envelope is authoritative and the object MUST NOT be processed; the refusal is `A202-STREAM-MISMATCH`, defined in [pilot transaction state machine v0.1](../negotiation/pilot-transaction-state-machine-v0.1.md) section 10, because the carrier exchange has directed an act at a stream the object does not belong to.

An implementation MAY align the carrier's own grouping of related tasks with a transaction as an operational convenience. Such alignment MUST NOT be relied on for correlation, MUST NOT be relied on for authorization, and MUST NOT be used to decide which stream an event targets.

## 7. Plain HTTPS binding

This section binds A202 objects to plain HTTPS for a party that does not run A2A. It is deliberately minimal. It defines a capability check, a request, and a refusal, and nothing else.

### 7.1 Endpoint and request

1. The endpoint MUST use HTTPS. Plain HTTP is refused, for the reason given for mandate status endpoints in [commercial mandate v0.1](../authority/commercial-mandate-v0.1.md) section 3.3.
2. An object is submitted by `POST`.
3. The request body MUST be the object's canonical bytes exactly as defined in section 5.2, with the media type `application/a202-commercial+json`. Every rule in section 5 applies unchanged, including the rule that carrier framing stays outside the signed bytes; under this binding, carrier framing means the request line, the headers, and any envelope a proxy adds.

### 7.2 Capability check

The capability check MUST complete, and MUST pass, before any A202 commercial object is transmitted. An implementation MUST support at least one of the two following forms and MAY support both.

**Preflight.** A `GET` on a declared capability path returns a document carrying the same three values as the A2A declaration: the extension URI from section 2.2, and the `read_versions` and `write_version` fields defined in section 4.1.

**Declared header.** The caller names the extension URI from section 2.2 in a request header field `A202-Extensions`, carried as a comma-separated list of extension URIs in the same form A2A uses for activation. A responder that accepts the activation echoes the header field with the URIs it activated. An absent echo is non-activation, and section 3 applies to it.

### 7.3 Refusal

Every condition in section 3.2 and every mismatch under section 4.2 fails closed here identically, with `A202-EXTENSION-UNSUPPORTED`. The refusal is carried with HTTP status `412`, because a stated precondition on the exchange was not met.

A responder MUST NOT accept a commercial object on a request that failed the capability check, and MUST NOT queue it for later evaluation.

### 7.4 The response to an accepted submission

Adopted through [A202-0017](../proposals/A202-0017-submission-success-status.md).

1. A submission under section 7.1 that the responder does not refuse in the response MUST be answered with HTTP status `202`.
2. A responder MUST NOT answer a submission with `200` or `201`. Either status asserts an outcome, completion in one case and creation in the other, and the outcome of a commercial act is never in the carrier response. An adapter acknowledgment is not agreement, as [pilot transaction state machine v0.1](../negotiation/pilot-transaction-state-machine-v0.1.md) section 7 states; a determination arrives, if it arrives, as a signed object.
3. `202` states receipt for evaluation and nothing else. It does not state that the object validated, appended, or will be acted on. The refusal statuses stand unchanged: `412` under section 7.3, and `409` for a sequence mismatch under the state machine's section 8. A responder that answers `202` and evaluates afterwards conveys any later refusal the way every commercial outcome is conveyed, as a signed object; the status carries no promise that a refusal cannot follow.

No response body is defined for the `202`. Anything a responder puts there is carrier framing under section 5.2, is covered by no signature, and section 9 applies to it.

## 8. Refusal codes

This binding adds one code. It belongs to the same registry as the codes in [pilot transaction state machine v0.1](../negotiation/pilot-transaction-state-machine-v0.1.md) section 10.

| Code | Meaning |
|---|---|
| `A202-EXTENSION-UNSUPPORTED` | Returned uniformly for an absent extension declaration, an unparseable version declaration, an incompatible version, and an unretrievable capability surface |

Codes this binding reuses without redefining are `A202-STREAM-MISMATCH`, used in section 6.3, and the kernel validation refusals used in section 5.4. Their definitions are in the documents that own them.

## 9. Security considerations

Replay resistance in A202 comes from the object envelope, not from the carrier. Three properties do the work, and all three are defined in the canonical model and the state machine rather than here: `content_hash` fixes the object's bytes, `previous_version_id` fixes an object's place in its own version chain, and the per-stream sequence fixes an event's place in its stream. A carrier that redelivers a message therefore redelivers bytes whose sequence has already been consumed, and the duplicate is recognised without reference to the connection it arrived on. This is why the binding needs no session token, no nonce, and no carrier-level replay window.

The binding adds no new signed material. Nothing in the extension declaration, the version declaration, the activation parameter, the correlation payload, or the HTTPS headers is covered by any A202 signature, and no security property in this specification depends on any of them being authentic. That is the intended shape: a hostile carrier that reorders, drops, duplicates, or rewrites framing can degrade availability, and it cannot manufacture a commercial act, because every act is a signed object evaluated against a mandate chain.

Two smaller observations follow from the same design. A capability declaration is a public statement about parsing, so treating it as evidence of anything else, including good standing, willingness to transact, or authority, imports a trust decision the declaration was never able to support. And the capability check is a check on the counterparty, not a mutual secret, so a party that fails it learns only that the exchange will not proceed, which is what it needed to know.

Retrieving a counterparty's capability surface is itself a disclosure: it tells the counterparty, or anyone observing, that this party is looking. Where that matters, the discovery and invitation rules in the specification govern who may be approached at all, and this binding neither widens nor narrows them.
