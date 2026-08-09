# Threat model

**Status:** Informative in full. This document states no requirement of its own. Every rule it describes is normative in the specification document it cites, and where this document and a specification document disagree, the document is the definition and this summary is wrong.

**Date:** 31 July 2026

## 1. What this document is

[SECURITY.md](SECURITY.md) declares five classes of defect in scope for a vulnerability report. This document is the analysis behind that list: the adversaries the specification assumes, the properties it defends against them, where each defence is written down, and what is out of scope.

It is a threat model of the specification, not of any implementation. An implementation has an attack surface of its own, such as key storage, parsing, transport, and deployment, and owes its users its own threat model. What belongs here is the layer above: the ways the specification as written could permit, or fail to prevent, an outcome no conformant party agreed to. A defect at that layer is exploitable against every implementation at once, which is why it is the layer this repository accepts reports for.

## 2. What is defended

Four properties. Each is a claim a counterparty must be able to rely on without trusting the party asserting it, and each is stated here together with the mechanism-independent form in which the specification carries it.

1. **Authority.** An act takes commercial effect only under a valid, unexpired, unrevoked chain of mandates, and only inside the scope that chain grants. The chain rules are in [authority/commercial-mandate-v0.1.md](authority/commercial-mandate-v0.1.md).
2. **Disclosure control.** A party learns what its declared disclosure policy entitles it to learn, and nothing more: not through content, and not through sequence numbers, reason codes, refusal shapes, or response timing. The default across counterparties is that nothing is revealed. The rules are in the canonical model's event stream and private strategy sections and, for competitive events, in [negotiation/auction-event-semantics-v0.1.md](negotiation/auction-event-semantics-v0.1.md) section 6, which states isolation as a property with a verification approach.
3. **Commitment integrity.** A party is bound only to bytes it signed. Signatures are computed over canonical bytes, checked against a declared purpose, and an agreement exists only when both parties have signed the same content. Formation rules are in the canonical model; the signing rules are in [schemas/canonical-commercial-model-v0.1.md](schemas/canonical-commercial-model-v0.1.md) section 4.
4. **Replayability.** A record replays to the state it claims and to no other, by an authorised party with no privileged access to anyone's infrastructure. The replay rules are in the state machine and the canonical model's event stream section; the verification procedure over evidence is [evidence/evidence-verification-v0.1.md](evidence/evidence-verification-v0.1.md) section 4.

These properties are not features beside the specification. They are the reason it exists, and the [charter's](CHARTER.md) design principles (fail closed, explicit typed state, assurance reported never inferred, disclosure minimalism, deterministic verification) are the general form of the defences enumerated below.

## 3. Adversaries assumed

Ordered by how much of the design each one stresses. Every adversary below is assumed to have read every published document, including this one.

| Adversary | Capability assumed | Primary target |
|---|---|---|
| **Strategic counterparty** | Fully conformant, patient, unlimited transactions, analyses everything it is sent and everything it is refused | Disclosure control |
| **Forging counterparty** | Authors and signs arbitrary objects with keys it legitimately holds | Commitment integrity |
| **Over-reached agent** | Holds a legitimate agent key; is compromised, mis-instructed, or induced to act beyond what its principal intended | Authority |
| **Hostile evidence author** | Supplies evidence, free-text notes, and profile terms crafted to influence a human approver or a downstream agent | Authority and commitment integrity |
| **Venue or operator** | Runs the venue: sees every object, orders every event, custodies keys for onboarded parties | All four |
| **Malicious implementer** | Ships an implementation that passes the published conformance suite and behaves differently on inputs the suite does not contain | The conformance claim itself |
| **Specification supply-chain adversary** | Tampers with a schema, a fixture, or a release artefact in transit or at its host | All four, against every implementation at once |
| **Network observer** | Observes traffic volume and timing on the carrier; cannot break the carrier's transport security | Disclosure control. This adversary is *not* defended; see section 7 |

The operator appears in this list deliberately. The specification's verification principle is that every claim is checkable by replaying signed records and recomputing hashes with no privileged access to the operator. A venue that asks to be trusted instead of checked is not implementing this specification.

## 4. Threats and where the specification answers them

Grouped by the property under attack. The right-hand column names the refusal code or verification path a reader can follow into the fixtures; the [conformance manifest](conformance/manifest-v0.1.json) is the single source for what the suite contains.

### 4.1 Against authority

| Threat | The specification's answer | Refused with / checked by |
|---|---|---|
| Acting under an expired, suspended, or revoked mandate | Every link in the chain must be verifiable; missing, expired, suspended, revoked, or scope-incompatible links fail closed | `A202-MANDATE-INACTIVE` |
| Delegation that widens authority | A child mandate can only narrow its parent. Narrowing is monotonic and checked, not assumed | `A202-MANDATE-DELEGATION-WIDENING` |
| Reusing a human approval | An approval is bound to the hash of one action in one transaction. Changing one byte of the action invalidates it; it cannot be reused across actions or transactions | Mandate specification section 8 and its fixtures |
| An operator signing on behalf of a party it custodies keys for | A custodied subject's act requires an approval bound to the principal, enforced whether or not the mandate carries the rule. A forged operator signature alone moves nothing | `A202-CUSTODY-APPROVAL-REQUIRED` |
| A constraint the evaluator cannot evaluate | An unevaluable constraint denies. Unavailability is not permission | Fail-closed principle, mandate specification |
| An invited party acting beyond the transaction it was invited into | Invitation-derived authority is bounded to the named transaction | `A202-INVITATION-SCOPE-EXCEEDED` |
| Injection through free text into an approver or an agent | Commercial meaning is never carried by prose. Free-text fields are bounded, non-load-bearing data; the evidence locator hint is explicitly never load-bearing; typed fields cannot invoke anything | Explicit-typed-state principle; evidence specification section 3.2 |

### 4.2 Against disclosure control

| Threat | The specification's answer | Refused with / checked by |
|---|---|---|
| Inferring a rival's existence, activity, or terms in a sealed event | Isolation stated as a property covering content, sequence numbers, reason codes, and response timing, with a verification approach a losing bidder can run over its own replayable export | Auction event semantics section 6 |
| A refusal that is itself a disclosure | Disclosure is a declared policy defaulting to nothing across counterparties; a refusal must not reveal what the policy withholds. Concretely: under a sealed policy, a late bid is refused with the ordinary state-transition refusal, because the award-specific code would disclose that an award has happened | `A202-DISCLOSURE-POLICY-VIOLATION`; auction event semantics section 4 |
| Undeclared or asymmetric disclosure by a venue | Any disclosure an event makes must be declared before rules freeze, applied symmetrically, and recorded as an event | Auction event semantics sections 4 and 5 |
| Reservation values or strategy leaking into shared objects | The private strategy boundary: strategy never enters a shared object, and structures are allowlists, so a field nobody anticipated cannot leak by default | Canonical model section 13 |

### 4.3 Against commitment integrity

| Threat | The specification's answer | Refused with / checked by |
|---|---|---|
| Binding a party to bytes it never signed | Signatures are over RFC 8785 canonical bytes with the declared purpose checked at verification. An agreement requires both parties' signatures over the same content | Canonical model sections 4 and 10 |
| Amount drift through number representation | Money is a base-10 string with an ISO 4217 currency, never a float, so canonicalisation cannot change a price | Canonical model section 7 |
| Mutating terms between offer and acceptance | Responses carry the content hash of what they respond to; a mutated document no longer matches | `A202-OBLIGATION-TERMS-MUTATED`, `A202-OBLIGATION-RESPONSE-HASH-MISMATCH` |
| Reusing an old acceptance to form a new agreement or amendment | Acceptance is bound to what it accepted; an amendment that reuses a prior acceptance is a negative fixture in the published suite | Agreement formation rules, canonical model section 10 |
| A determination claiming more effect than the rules granted | The effect is read from the referenced rule set, never from the determiner's claim, and both layers of the check fail closed on their own. Where the rules resolve to nothing, the effect is advisory, never inferred upward | `A202-DETERMINATION-EFFECT-OVERCLAIM` |

### 4.4 Against replayability

| Threat | The specification's answer | Refused with / checked by |
|---|---|---|
| Rewriting history | Objects are never edited; a new version points at its predecessor and both stay verifiable. Replay recomputes every hash and signature rather than trusting a declared one | Canonical model; evidence verification steps 1 to 3 |
| Splicing or reordering an event stream | Per-stream sequence continuity, checked | `A202-SEQUENCE-CONFLICT`, `A202-STREAM-MISMATCH` |
| Smuggling state change through an event type replay does not check | The transaction event stream is an allowlist; an event outside it is not part of the record | Canonical model section 11 |
| A gap in an evidence chain presented as verified | The verification output is three-valued per check (verified, failed, not checkable) and has no overall boolean, so a gap cannot be rounded up to a pass | `A202-EVIDENCE-CHAIN-GAP`; evidence verification section 5 |
| Hiding tampering behind selective disclosure | Selective disclosure states what was withheld; the report carries the gap as scope, never as silence | Evidence verification section 6 |

### 4.5 At the carrier and settlement boundaries

| Threat | The specification's answer | Refused with / checked by |
|---|---|---|
| Capability downgrade: a counterparty pretending the extension is absent to fall back to unverifiable behaviour | Capability negotiation fails closed. Every failure mode (undeclared, malformed, version-mismatched) produces the same single refusal | `A202-EXTENSION-UNSUPPORTED`, [bindings/a2a-binding-v0.1.md](bindings/a2a-binding-v0.1.md) |
| Settlement executed without commercial authority | The specification's entire payments surface is a handoff: a settlement instruction is an authorised, signed object, and the rail's response returns as a typed receipt in evidence. Moving the money is the rail's job and the rail's risk model | [fulfillment/settlement-handoff-v0.1.md](fulfillment/settlement-handoff-v0.1.md) |
| Tampered schemas or fixtures at their host | A release carries a digest for every schema file, and the manifest names every fixture with its expected classification. A schema whose digest differs is not that release. Implementations declare read and write versions, so a downgrade is visible | [RELEASES.md](RELEASES.md) sections 3 and 4 |

## 5. Verifying these claims

Nothing in section 4 asks to be believed. The checks are runnable:

1. **Run the conformance suite** from the repository root. The suite is deliberately weighted toward negative fixtures, behaviour under hostile and malformed input, and the [manifest](conformance/manifest-v0.1.json) is the single source for its contents and counts. The runner asserts not only that a negative fixture is refused but that it is refused for the reason code the manifest declares, wherever the normative layer raises codes. Every negative fixture is minimal: remove the single offending element and the document validates cleanly, so each fixture tests exactly one rule.
2. **Read the grade definitions** in [conformance/conformance-grades-v0.1.md](conformance/conformance-grades-v0.1.md). Passing the published set is the floor, not the claim. Band 2 requires passing a held-out case set exercising the same invariants; band 3 requires an assessor constructing inputs outside any set. The bands exist because the malicious implementer of section 3 is assumed: an implementation can be written to the published fixtures, which is precisely why the published fixtures are not the whole assessment. Publication is one way: a fixture that enters the published set never returns to a held-out set.
3. **Read the reference implementation** in [reference/README.md](reference/README.md). It is informative, one checkable reading of the wire rules, and its test sweep routes the manifest's evidence-bundle fixtures through the verification procedure directly, independently of the runner, stating a reason for every bundle it skips, so the two readings check each other rather than sharing one path.

## 6. The mechanism boundary

The charter's non-goal 6 draws a line this document keeps: how an operator implements isolation (sequencing, contention handling, timing and error normalisation) is not published here. What is published is the property such an implementation must exhibit, the interface a counterparty implements against, and the procedure by which the property is independently verified.

The trade-off is that an unpublished mechanism receives less external review than a published one. The specification compensates by not asking the reviewer to trust the mechanism. Isolation is defined over what a participant can observe and replay, and the verification procedure runs against a participant's own export. A mechanism defect that violates the property is detectable at the boundary where the property is stated, and reportable under [SECURITY.md](SECURITY.md), without the mechanism ever being disclosed.

## 7. What is not defended

Each of the following is a stated scope decision.

- **Collusion agreed outside the system.** Two bidders who agree their prices by telephone produce a record indistinguishable from two who did not. The auction event semantics state this in section 7, and no A202 claim should ever be read as detecting it.
- **Traffic analysis by a network observer.** Disclosure control is defined against participants. An observer correlating traffic volume and timing on the carrier is outside the specification's reach; transport confidentiality belongs to the carrier.
- **Key compromise, beyond its consequences.** The specification defines suspension, revocation, and the fail-closed evaluation of a dead chain. It does not defend the key itself; custody, rotation, and storage are implementation concerns.
- **Identity truth.** A202 consumes external identity and governance evidence and records the assurance level established from it; it does not prove a legal entity exists or that an issuer holds legal power. Assurance is reported, never inferred, and absence of assessment reads as unassessed, but the quality of the external assertion is the assertion issuer's to defend.
- **Settlement execution.** Once the handoff instruction leaves, the movement of money is governed by the rail.
- **Legal enforceability.** The record is designed to be reconstructable and attributable. Whether a given jurisdiction enforces what it records is a question for counsel, not for a schema.
- **Implementation defects.** An implementation that mishandles a rule the specification states correctly is defended against only insofar as the conformance suite catches it. Its remaining defects belong to its own reporting channel.

## 8. Review status

This threat model describes a pre-1.0 specification. As of its date, `v0.1.0` is the only tagged release, no external security review of the specification has taken place, and no independent implementation exists. The conformance suite tests the specification's own reading of itself: the reference implementation and the runner were built against the same documents by the same project, so their agreement is a consistency check rather than independent confirmation.

External review is welcome. A reader who finds a way through any property in section 2 should report it privately per [SECURITY.md](SECURITY.md).
