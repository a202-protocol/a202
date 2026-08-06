# A202-0012: Payload definitions for the organization, agent, and principal

**Status:** Fixtures and compatibility. Stage 3 of the five stages in [README.md](README.md) section 3. The schema definitions and fixtures are implemented, and the suite passes with them in place.

**Date:** 28 July 2026

**Status of this document:** Informative in full. It states no requirement on an implementation. The normative text this proposal adopts lands in [schemas/v0.1/commercial-kernel.schema.json](../schemas/v0.1/commercial-kernel.schema.json) and is described by [schemas/canonical-commercial-model-v0.1.md](../schemas/canonical-commercial-model-v0.1.md), which marks its own normative sections.

## 1. Problem

[A202-0010](A202-0010-model-completion.md) defined payloads for the five deferred types that normative rules leaned on, and honestly recorded ten that remained envelope-only. Three of those ten are the first objects any implementation constructs.

The authority chain in [commercial-mandate-v0.1.md](../authority/commercial-mandate-v0.1.md) section 2 runs from an organization, through a principal, to a mandate, to an agent key. The invitation flow in [counterparty-invitation-v0.1.md](../discovery/counterparty-invitation-v0.1.md) step 7 requires an invited party to register an organization, designate a principal, and bind an agent key before it can act at all. Every envelope object's `created_by` names an organization and an agent. So an implementer must construct all three on day one, and until now the specification told them only that the objects exist and what they are for, leaving every field to invention. Two implementations would have produced two incompatible shapes for the object at the root of the authority chain.

Three design questions had to be answered rather than guessed, and each has a wrong answer that looks natural:

1. **Does a party carry an assurance level?** It is the obvious field to add and it must not be there. [commercial-mandate-v0.1.md](../authority/commercial-mandate-v0.1.md) section 11.4 already places assurance on the `InvitationAcceptance`, and section 7 of the invitation document makes it reported and never inferred. A second home for assurance is a second answer to how strongly a counterparty is known, and a self-declared one is not an answer at all.
2. **Does a principal carry a name?** A principal is usually a named human. A name, an address, or an employee number in a shared object is personal data travelling to every counterparty that resolves the reference, which is what the invitation document's `channel_ref` and `channel_hash` pattern exists to avoid.
3. **Does an agent carry its capabilities?** [a2a-binding-v0.1.md](../bindings/a2a-binding-v0.1.md) section 2 puts the capability declaration in the carrier's own AgentCard and forbids inferring support from any other field. Restating it in the kernel would create a second declaration that can disagree with the first.

## 2. Change

Three closed payload definitions, each with its identifier prefix pinned in its schema branch, and one shared `partyStatus` enum of `active`, `suspended`, and `revoked`.

**`organizationPayload`** carries `legal_name`, `jurisdiction`, `registry_identifiers`, `status`, and `identity_evidence_refs`. Registry identifiers are scheme-and-value pairs, such as an LEI or a company number, and the schema states that a claim's presence verifies nothing: verification is an `ExternalIdentityAssertion` in the evidence references, and a relying party treating an unverified registry identifier as established has inferred assurance rather than read it. The legal name lives in the payload, never in the identifier, which stays opaque under canonical model section 3. **No assurance field**, per question 1.

**`agentPayload`** carries `represented_organization_id`, `operator_organization_id`, `endpoint`, `key_ids`, and `status`. The two organization references are separate so that a hosted agent is visibly hosted: they are equal for a self-operated agent and differ otherwise, and the disclosure matches the key-custody disclosure the invitation document already requires. The endpoint is HTTPS-only or null, and the schema records that reachability confers no authority. **No capability declaration**, per question 3.

**`principalPayload`** carries `organization_id`, `role`, `status`, `authority_evidence_refs`, and `contact_ref`. The role is what a relying party needs in order to judge whether the issuer could bind the organization, and it is the value a mandate's approval rules already match an approver against. `contact_ref` is an opaque `chn_` pointer to a contact record the organization holds, never the contact value. **No personal data**, per question 2.

Canonical model section 5.6 moves the three types from the deferred list to the defined list, leaving ten deferred.

## 3. What this proposal does not do

It does not define `external_identity_assertion`, which is the object that would carry a verified registry claim rather than a claimed one, and it does not define the remaining market and audit types. It does not add a status endpoint to an agent or an organization: revocation reaches a relying party through the mandate status endpoint and through `RevocationRecord`, and adding a third channel would create a third answer to whether a party is active. It states nothing about how an organization is admitted to a venue, which is an operator concern under [CHARTER.md](../CHARTER.md) section 3.

## 4. Compatibility

Under [RELEASES.md](../RELEASES.md) section 2 this is a **MAJOR-shaped tightening** applied pre-1.0: three object types that previously validated as envelope-only now validate their payloads. Nothing in the published fixture set or the reference implementation constructed one, so nothing in this repository changes behaviour. An implementation that had invented its own party shapes re-validates against these, which is the cost of the shapes having been unspecified and is the reason to fix it before publication rather than after.

## 5. Fixture plan

Implemented: `valid-organization`, `valid-agent`, and `valid-principal` in the allow direction; `principal-carries-personal-data` refused with `A202-DISCLOSURE-DENIED`, `agent-endpoint-plain-http` refused with the newly registered `A202-ENDPOINT-INSECURE`, and `organization-carries-assurance-level` refused as a plain kernel validation refusal with no reason code of its own, on the pattern the carrier binding section 5.4 describes for carrier framing.
