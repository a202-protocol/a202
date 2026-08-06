# Transaction profile extension model v0.1

**Status:** Experimental working specification. Mixed. Sections 2, 3, 4, 5, 6, 7, and 8 are **normative**. Sections 1, 9, 10, and 11 are **informative** and state no requirement on an implementation.

**Date:** 25 July 2026

**Scope:** Synthetic and non-binding validation only

**Relates to:** [Canonical commercial model v0.1](canonical-commercial-model-v0.1.md)

## 1. Purpose

This specification defines how a commercial domain adds vocabulary, rules, evidence requirements, and execution mappings without changing the common A202 commercial kernel.

A transaction profile describes one bounded commercial interaction. It is not a market launch, an industry ontology, an ERP connector, or evidence that organizations want the product.

## 2. Layer model

| Layer | Contains | Must not contain |
|---|---|---|
| Commercial kernel | Identity references, authority references, common proposal envelope, acceptance, agreement, obligations, event ordering, audit | Domain-specific term names, preferred rails, market-specific workflow assumptions |
| Transaction profile | Typed commercial terms, controlled vocabularies, evidence requirements, domain policy hooks, obligation templates | Private strategy, participant-specific preferences, transport credentials |
| Participant policy | Limits, approvals, disclosure rules, risk tolerances, counterparty rules | Shared defaults presented as bilateral agreement |
| Protocol adapter | Mapping to and from external interaction protocols | Independent commercial authority or state transitions |
| Execution adapter | Mapping to ERP, payment, logistics, provisioning, or other systems | Authority inferred from connectivity or a successful API call |
| Operated A202 service | Verification, policy execution, canonical ordering, isolation, adjudication, replay | Undisclosed participant reasoning or silent modification of signed terms |

## 3. Profile package

A complete profile package MUST contain:

1. **Manifest**
   - stable profile identifier;
   - semantic version;
   - status and owner;
   - referenced kernel versions;
   - human-readable name and bounded transaction purpose;
   - compatibility and supersession information.
2. **Terms schema**
   - machine-validatable `profile_terms`;
   - required and optional fields;
   - controlled units, currencies, time zones, and vocabularies;
   - no unrestricted field used to hide a material commercial term.
3. **Semantic definitions**
   - commercial meaning of every term;
   - default behavior, if any;
   - which omissions are invalid;
   - examples and counterexamples.
4. **Evidence rules**
   - claims requiring evidence;
   - acceptable issuer or verifier classes;
   - freshness, scope, status, and audience requirements;
   - explicit statement that verifiability does not establish truth by itself.
5. **Policy hooks**
   - profile facts made available to deterministic participant policy;
   - typed failure reasons;
   - actions that require approval;
   - no model output used as deterministic authority.
6. **Obligation and acceptance mapping**
   - how accepted terms create commitments and measurable obligations;
   - required performance events;
   - acceptance, exception, remediation, and termination conditions.
7. **Execution mapping**
   - external documents, systems, or rails that may receive authorized instructions;
   - expected semantic loss for each mapping;
   - idempotency and receipt rules;
   - fields that cannot be exported without review.
8. **Threat addendum**
   - domain-specific disclosure, manipulation, collusion, fraud, safety, and market-integrity risks;
   - consequence limits and mandatory human review.
9. **Conformance fixtures**
   - at least one valid offer;
   - missing and malformed material terms;
   - expired or stale terms where relevant;
   - invalid evidence;
   - private-field leakage;
   - unauthorized and approval-required actions;
   - execution mapping loss.

The v0.1 profile schemas in `v0.1/profiles/` are incomplete probes. They contain terms schemas but not every package artifact required for a production candidate.

## 4. Kernel invariants

A transaction profile MUST NOT:

- add a domain-specific field, enum, or constant to the kernel schema;
- redefine organization, agent, principal, mandate, offer, acceptance, agreement, commitment, obligation, evidence, policy decision, or audit semantics;
- permit a proposal to bypass the signed `ActionEnvelope`;
- create a new authoritative transition without an explicit kernel-version decision;
- infer delegated authority from identity, system connectivity, payment ability, or possession of data;
- place private objectives, reservation values, rankings, prompts, or reasoning traces in shared terms;
- require one agent framework, ERP, identity provider, payment rail, or settlement method;
- treat an adapter receipt as acceptance, agreement, performance, or settlement unless an authorized typed event establishes that meaning;
- use unstructured prose as the only representation of a material term that controls price, scope, liability, performance, acceptance, or termination.

If a proposed profile cannot conform to these rules, one of three conclusions is required:

1. the proposed interaction is not supported by the current kernel;
2. the proposed term is not truly domain-specific and a versioned kernel change should be considered;
3. the horizontal-kernel hypothesis has failed or needs narrowing.

Silent kernel expansion is not permitted.

## 5. Domain vocabulary

A profile may define:

- product, service, route, location, capacity, inventory, or license descriptors;
- domain-specific time windows;
- quality, availability, service-level, inspection, or acceptance measures;
- pricing components and adjustment formulas;
- liability, remedy, credit, or cancellation terms;
- evidence types and qualification requirements;
- obligation templates;
- mapping rules to established domain standards.

Controlled vocabularies SHOULD reuse an appropriate existing standard when one can express the required meaning. A profile author MUST record reuse, profile, extension, or creation decisions and any semantic loss.

## 6. Domain policy

Profile schemas express terms. They do not decide whether a party should accept them.

Participant policy evaluates typed profile facts against participant-controlled rules. Examples include:

- require approval above a private monetary threshold;
- deny a collection window outside an authorized date range;
- require a named evidence class for a regulated service;
- require human approval for an uncapped liability term;
- prohibit disclosure of a private reservation value.

A shared `PolicyDecision` MAY disclose `allow`, `deny`, or `require_approval` only to the audience required by the workflow. The underlying private threshold or rule MUST remain private unless deliberately disclosed.

## 7. Profile registration

Registration means that an identifier resolves to a versioned schema and metadata. It does not certify commercial quality, legal sufficiency, safety, market adoption, or suitability for production.

A profile is eligible for the experimental registry when:

- its package is complete for the claimed maturity;
- the unchanged kernel validates its common envelope;
- all material terms are typed;
- evidence and policy hooks are explicit;
- private and shared fields are classified;
- conformance fixtures pass;
- expected execution-mapping loss is documented;
- the threat addendum identifies consequence limits;
- an owner and reversal condition are named.

The governance choice between central curation, federated publication, and self-assertion with conformance testing remains open.

## 8. Versioning

- A profile versions independently of the kernel.
- Adding an optional term is a profile change, not automatically a compatible change.
- Changing a term's meaning, default, unit, evidence rule, or obligation mapping is a breaking profile change.
- An agreement MUST retain the exact profile identifier and version used.
- An active negotiation MUST NOT change profile version without an authorized proposal accepted by every affected party.
- A superseded profile remains resolvable for verification and replay.

## 9. Example domain boundaries

| Domain probe | Profile-specific terms | Common kernel behavior |
|---|---|---|
| Calibration service | Completion calendar, certificate requirement, acceptance result, included rework | Authority, proposal, evidence reference, acceptance, obligations, audit |
| Freight spot capacity | Lane, collection window, equipment, liability regime | Authority, proposal, conditional commitment, performance evidence, exception |
| Cloud capacity reservation | Region, resource class, capacity period, service level, usage commitment, service credits | Authority, proposal, agreement, recurring obligation, acceptance, settlement instruction |

These examples are architecture probes. They do not select a commercial market or establish market demand.

## 10. Open questions

- Can established domain document standards serve directly as `profile_terms`, or is a A202 mapping required?
- How should profiles express amendments, options, partial acceptance, and multi-party commitments?
- Which domains require state beyond the v0.1 bilateral session and single-award aggregate?
- How should profile conflicts be resolved when each party proposes a different standard or version?
- Which entity governs names, versions, deprecations, and conformance claims?

Which profile elements belong to this specification, and which behaviours belong to an implementation that operates a venue, is settled and is stated in the scope and non-goals sections of [CHARTER.md](../CHARTER.md). It is not an open question of this document.

## 11. Reversal conditions

Revisit this model if:

- domain profiles routinely require kernel changes;
- material commercial meaning cannot be expressed without domain-specific state machines;
- established standards are more interoperable when used without a A202 profile;
- profile packages create more integration work than direct bilateral mappings;
- participants reject A202 identifiers or profile governance;
- conformance passes syntactically while materially different interpretations remain possible.
