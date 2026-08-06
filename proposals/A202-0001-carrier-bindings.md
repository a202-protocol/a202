# A202-0001: A2A and plain HTTPS carrier bindings

**Status:** Fixtures and compatibility. Stage 3 of the five stages in [README.md](README.md) section 3. The static fixtures in section 5 are implemented in the conformance suite; the runtime case remains recorded for implementation-level verification.

**Date:** 27 July 2026

**Marking:** This proposal is informative in full. It states no requirement on an implementation. The normative text it proposes lands in [bindings/a2a-binding-v0.1.md](../bindings/a2a-binding-v0.1.md), which marks its own normative sections.

## 1. Problem

The specification defines commercial meaning and deliberately defines no transport. That is the carrier-neutrality principle in [CHARTER.md](../CHARTER.md) section 4, and it is correct. It leaves two things undone that a counterparty cannot supply for itself.

**Objects need a carrier, and there is no stated one.** Two implementations can each pass the whole conformance suite, produce byte-identical canonical objects, and still be unable to exchange a single offer, because nothing states which field of which carrier message the bytes go in, whether they survive re-serialization, or how a receiver knows the bytes it is verifying are the bytes that were signed. Every implementer resolves this privately, and the resolutions will not match. Carrier neutrality means the meaning does not depend on the transport; it does not mean that no transport is ever specified.

**Capability cannot fail closed, because there is nothing to check.** The specification's first design principle is that an unrecognised value produces a refusal and never a permissive default. There is at present no way for a party to discover, before it transmits, whether a counterparty can parse a A202 object at all. Consider the concrete case: a buyer's agent sends a counterparty invitation to a supplier's agent that has never heard of A202. The supplier's agent receives a message it cannot interpret. In the best case it errors, and the buyer has already disclosed that a transaction exists, that it is participating, and which category it is buying in, to a party that was never able to take part. In the worse case the supplier's agent passes the content to a language model, which produces a plausible reply that no mandate authorized and no signature covers. The exchange has failed open, and it failed open before the first commercial object could be validated by anything.

A third problem follows from the first two once a carrier is in use. Carriers have their own lifecycles: requests time out, streams drop, and units of work are cancelled or marked failed. Nothing currently states that those events are commercially inert. An implementer connecting the two layers for the first time will reasonably assume that a cancelled unit of carrier work cancels the commercial act it carried, and that assumption lets a network condition retract a signed commitment.

## 2. Proposal

Add one document, [bindings/a2a-binding-v0.1.md](../bindings/a2a-binding-v0.1.md), specifying two carrier bindings, and add one refusal code.

The substance is:

1. **Extension declaration.** The A202 commercial extension is declared using A2A's own extension mechanism, as one entry in the extension array carried by the AgentCard's capabilities object, populating A2A's `uri`, `description`, `required`, and `params` fields. The v0.1 extension URI is `https://schemas.a202.org/a2a-ext/commercial/0.1`. It was raised under this proposal as a placeholder on the reserved `.invalid` domain, to be reissued against a real host before publication; that reissue has since been made and the URI above is the issued form. Activation uses A2A's own activation service parameter.

2. **Mandatory to understand.** A party may require the extension. When it does, interaction with a counterparty that does not declare support fails closed before any commercial object is exchanged, with `A202-EXTENSION-UNSUPPORTED`. The check runs at capability negotiation, not at the first act that carries money, so that the disclosures listed in section 1 never leave the party. An unretrievable capability surface is a failure, on the existing rule that unavailability is not permission. There is no downgrade path to a bare carrier exchange.

3. **Version declaration and mismatch.** The extension parameters carry `read_versions` and `write_version`, whose meaning is the read and write version already defined in [RELEASES.md](../RELEASES.md) section 4 and is not restated. Each party checks that the counterparty's write version is one it reads and that its own write version is one the counterparty reads. Failure is closed, with no nearest-version selection and no fallback to an earlier extension URI.

4. **Object transport.** Objects travel as message parts, one object per part, carried as opaque bytes with the media type `application/a202-commercial+json` and byte-identical to the canonical RFC 8785 form. A structured-data representation may accompany the object as a reader's convenience and is never the object. Signatures cover the canonical bytes and never the carrier framing, and carrier metadata must not be copied inside the signed bytes.

5. **Task to transaction correlation.** Many carrier tasks may serve one transaction. The transaction aggregate is the commercial source of truth, task state does not determine transaction state, and a task failure or cancellation is a carrier event whose commercial consequence, if any, requires an explicit signed and authorized A202 transition. Correlation travels as `transaction_id` in the extension payload; carrier identifiers correlate nothing.

6. **Plain HTTPS binding.** A minimal binding for a party that does not run A2A: HTTPS only, `POST` of the same canonical bytes, and the same fail-closed capability check by preflight document or by a declared `A202-Extensions` header field, refused with the same code under HTTP status `412`.

## 3. Alternatives considered

**Do nothing.** Leave every implementer to bind objects to a carrier privately. This is where problem 1 already leads, and it produces implementations that are individually conformant and mutually unusable. It also leaves the capability check undefined, which means the specification's own fail-closed principle is unenforceable at the first point of contact with a counterparty. Rejected.

**Define a A202-native transport.** Rejected. It duplicates work that carrier protocols already do well, it adds session mechanics the specification has deliberately excluded, and it would tie the specification to a transport of its own, where carrier neutrality deliberately leaves it able to ship as an extension to a carrier protocol that already defines transport.

**Carry objects as structured data and re-serialize on receipt.** Rejected. Canonicalization is byte-level. A structured value is re-serialized by the carrier and by every library between it and the verifier, so the receiver ends up verifying the output of its own serializer rather than the sender's object. The failure is silent and intermittent, which is the worst available property for a signature check.

**Correlate by the carrier's own grouping identifier.** Rejected. It makes commercial correlation depend on carrier state, and it creates exactly the path this proposal closes elsewhere, along which a carrier lifecycle event acquires commercial consequence.

**Check capability at the first commercial act rather than at negotiation.** Rejected, for the disclosure reason in problem 1. The first object a party sends is often an invitation or a mandate presented for verification, and both disclose participation before any check has run.

**Give each failure condition its own refusal code.** Rejected. The four conditions have one correct outcome. Four codes that must be handled identically will eventually be handled differently, and the branch that diverges is a branch that fails open.

## 4. Compatibility

**No change to any existing object.** No field is added, removed, or reinterpreted in the kernel schema, the mandate schema, or any transaction profile. No state, transition, or guard changes. No existing fixture changes classification. An implementation conformant before this proposal remains conformant after it.

**One code is added:** `A202-EXTENSION-UNSUPPORTED`, in the same registry as the codes in [pilot transaction state machine v0.1](../negotiation/pilot-transaction-state-machine-v0.1.md) section 10. It is returned only in conditions that are currently undefined, so no case that previously produced a code produces a different one.

**Two codes are reused, not redefined.** `A202-STREAM-MISMATCH` covers a carrier payload that names a different transaction from the object envelope. Carrier framing found inside signed bytes is refused by ordinary kernel schema validation, because the envelope and payload shapes are closed and unknown fields already fail; no code is added for it.

Under [RELEASES.md](../RELEASES.md) section 2 this is a **MINOR** change: it adds capability and an error code for a case that was previously undefined, and invalidates no conformant implementation.

**Migration.** None is required for an implementation that does not use a carrier binding. An implementation that adopts one publishes a declaration and implements the capability check; there is no transitional mode in which the check is advisory, because an advisory fail-closed check is not one.

**Forward compatibility.** The extension URI carries the specification minor version, and A2A requires a new URI for a breaking extension change, so a future breaking revision of this binding is a new URI rather than a reinterpretation of this one. Parties that support only the older URI are refused rather than silently downgraded.

## 5. Fixtures

Fixtures are added to [conformance/manifest-v0.1.json](../conformance/manifest-v0.1.json) and run by [conformance/run-conformance.py](../conformance/run-conformance.py). The declaration fixtures introduce a manifest fixture kind for carrier declarations, which the runner gains under this proposal.

| Fixture | Direction | Expected | What it distinguishes |
|---|---|---|---|
| `valid-extension-declaration.json` | allow | valid | A declaration carrying the v0.1 extension URI, a `required` flag, and a parseable `read_versions` and `write_version` pair is accepted, and the exchange may proceed. The fixture filename names no carrier, because fixture paths travel into the manifest and the carrier is named only where the boundary rules permit |
| `negative/declaration-missing.json` | refuse | `A202-EXTENSION-UNSUPPORTED` | A counterparty declaration with no entry for the A202 extension URI fails closed, and no commercial object is transmitted. An implementation that proceeds, or that downgrades to a bare exchange, fails |
| `negative/declaration-version-mismatch.json` | refuse | `A202-EXTENSION-UNSUPPORTED` | A declaration whose write version is absent from the counterparty's read versions fails closed. An implementation that selects a nearest version, or falls back to an earlier extension URI, fails |
| `negative/envelope-carries-carrier-metadata.json` | refuse | kernel validation refusal | An object whose signed bytes carry a carrier task identifier is refused by the closed envelope shape. This is the negative direction of the rule that signatures never cover framing |

One required behaviour cannot be expressed as a static document and is verified against a running implementation, in the manner of the runtime items already listed in [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md) section 15:

**Carrier task failure does not transition the transaction.** A signed offer is appended to a session stream; the carrier task that delivered it is then driven to a failed state, and separately to a cancelled state. The assertion is that the aggregate state, the session state, the session stream sequence, and the offer's own status are all unchanged in both runs, and that the offer remains acceptable until it expires or an authorized withdrawal event is appended. An implementation that retracts, expires, or hides the offer fails.

The allow direction and the refuse direction are both present for every rule this proposal introduces, which is the stage 3 requirement in [README.md](README.md) section 3. Stage 3 is not claimed here; the fixtures above are the plan against which it is attempted.

## 6. Origin

The proposal arose from specification review rather than from any implementation's experience, and no implementation experience informs it. Reviewers should weigh it accordingly: the disclosure argument in section 1 is reasoned from the existing invitation and disclosure rules, and the byte-identity argument is reasoned from the canonicalization rules, but neither has been tested against a counterparty that got it wrong in the field.

The external mechanics it binds to were read from the A2A specification and its interface definition at version 1.0 on 27 July 2026. Where a carrier detail could not be verified from those sources, the binding states the requirement at the level of the declaration and leaves the detail to the carrier.
