# Evidence verification v0.1

**Status:** Experimental, adopted through proposal [A202-0004](../proposals/A202-0004-evidence-verification.md). Mixed. Sections 2, 3, 4, 5, 6, and 8 are **normative**. Sections 1 and 7 are **informative** and state no requirement on an implementation.

**Date:** 27 July 2026

**Revised:** 30 July 2026, under [A202-0016](../proposals/A202-0016-casing-short-form-and-amendment-corrections.md): section 3 admits the identifier-only short form that the schema, the fixture set, and the runner already carried, marks the field table by form, and states in a new section 3.3 the fail-closed constraints under which the short form resolves. Previously revised 28 July 2026, under [A202-0011](../proposals/A202-0011-registry-and-waiver-corrections.md): section 3.1 now enumerates the registered evidence types, which other documents already cited this section as defining. The closure rule is unchanged and moves to section 3.1.1.

**Scope:** Synthetic pilot transactions only

**Depends on:** [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md), [commercial mandate v0.1](../authority/commercial-mandate-v0.1.md), [pilot transaction state machine v0.1](../negotiation/pilot-transaction-state-machine-v0.1.md), [obligation v0.1](../agreement/obligation-v0.1.md), [determination and dispute v0.1](../disputes/determination-v0.1.md)

## 1. Purpose

Evidence has to outlive any single operator. A record that can only be checked by the party that produced it is not evidence about that party, and a commitment to portability that keeps the checking algorithm private is a commitment nobody can act on.

So verification is public. This document states, as numbered steps, exactly what a third party does to check a bundle of A202 records, using nothing but the bundle, the schemas, the rules versions the bundle references, and the keys it declares. No operator access is required at any step.

Bundle construction is not specified here. How records are gathered, ordered, packaged, held, exported, and disclosed is outside this specification. The asymmetry is deliberate: verification must be public or the record is not portable, and construction need not be for the record to be checkable.

The posture the procedure encodes is that a relying party verifies. It does not trust. Every step either recomputes something or resolves something, and any step that cannot be completed produces a stated gap in the report rather than an assumption in the relying party's favour.

## 2. Conformance language

`MUST`, `MUST NOT`, `REQUIRED`, `SHOULD`, `SHOULD NOT`, and `MAY` are normative within this experimental specification.

An implementation conforms when it:

1. emits evidence references in the shape defined in section 3;
2. produces records against which the procedure in section 4 can be executed in full by a party with no operator access;
3. produces verification reports in the shape defined in section 5;
4. supports selective disclosure under section 6;
5. returns the refusal codes in section 8 for the failures they name;
6. passes the verification fixtures in `../conformance/manifest-v0.1.json`.

A verifier conforms when it executes every step in section 4 in order, and reports what it could not check as not checkable rather than as either verified or failed.

## 3. Evidence reference

An evidence reference is the shape used across the protocol wherever one object points at evidence. Obligations, disputes, determinations, offers, invitations, and mandates all use this shape, so that a verifier resolves one thing rather than a different thing per object family.

A reference takes one of two forms. The **full form** is the object below. The **short form** is the `evidence_id` alone, carried as a bare identifier string, admitted only where section 3.3 admits it and constrained there.

| Field | Type | Rule |
|---|---|---|
| `evidence_id` | `evd_` identifier | REQUIRED in both forms. The `Evidence` object referenced. In the short form it is the whole reference |
| `content_hash` | `sha256Hex` | REQUIRED in the full form. The content hash of the referenced evidence, lowercase hexadecimal SHA-256. Multibase is not accepted in v0.1. Not carried by the short form, which is why section 3.3 constrains where the short form resolves |
| `evidence_type` | registered type identifier | REQUIRED in the full form. From the registered evidence type list. An unregistered value fails closed with `A202-EVIDENCE-TYPE-UNKNOWN`. Not carried by the short form; where the referenced `Evidence` object is co-present the type resolves from that object's own `evidence_type`, and where it is not the reference is not checkable |
| `locator_hint` | string or null | OPTIONAL in the full form. Where a copy may be found. Never load bearing. See section 3.2. Not carried by the short form |
| `signed_by` | `partyRef` | REQUIRED in the full form. The party whose signature covers the referenced evidence. Not carried by the short form; where the referenced `Evidence` object is co-present the signing party resolves from that object's own `signatures`, and where it is not the reference is not checkable |

The full form is the shape an implementation emits unless section 3.3 states otherwise. Every field marked REQUIRED in the full form is required whenever the full form is used: a reference carrying some of them and not others is not a short form, it is an incomplete full form, and it is refused.

### 3.1 The registered evidence types

This table is the registry. Other documents cite this section as the place the list is defined, so the list is written here rather than left to be read out of a schema enum. The registry is closed in v0.1.

| `evidence_type` | What it evidences |
|---|---|
| `attestation` | A statement by a party about a fact it asserts, signed by that party and standing on nothing further |
| `third_party_certificate` | A certificate issued by a party other than the two, such as an accreditation or a conformity certificate |
| `inspection_result` | The recorded outcome of an inspection carried out against a stated method |
| `delivery_confirmation` | Confirmation that a thing arrived, or that a service was rendered, at a stated place and time |
| `measurement_record` | Measured values produced by an instrument or procedure, with the conditions under which they were taken |
| `adapter_receipt` | An `AdapterReceipt` presented as evidence of what an external system reported. It evidences the report and never the authority behind it, per [settlement-handoff-v0.1.md](../fulfillment/settlement-handoff-v0.1.md) section 4.2 |
| `verification_report` | A report produced under section 5 of this document, referenced as evidence in a later dispute or determination |
| `signed_document` | A document signed by one or more parties, where the document itself is the evidence rather than a claim about it |

A type states what kind of thing the evidence is. It states nothing about whether the evidence is true, whether its issuer was authoritative, or whether it verifies: those are the verification result under section 4 and the reporting rules under section 5, and a type that resolves is not thereby a claim that verified.

Adding a member to this registry is a change to this table and requires a proposal under [proposals/README.md](../proposals/README.md). The kernel schema's `evidenceTypeId` enum carries the same eight values and MUST be changed in the same proposal; the two are one registry expressed twice, and a member present in one and absent from the other is a defect in whichever was not updated.

### 3.1.1 The type list is closed

`evidence_type` resolves in the registry in section 3.1. An unregistered type fails closed at validation and independently at verification, matching the treatment of mandate constraint types and transaction profiles: adding a member to a schema enum without a verifier that knows what it means MUST NOT cause the evidence to be treated as verified.

Where a type does not resolve, the reference is not verified and it is not failed either. It is reported as not checkable under section 5, and the relying party decides what to do with a gap it can see.

### 3.2 The locator hint is never load bearing

`locator_hint` may help a verifier find a copy of the evidence. It never establishes anything.

1. Verification MUST NOT depend on `locator_hint` resolving. A bundle whose hints are all stale is still fully verifiable from the bytes it contains.
2. A verifier MUST NOT treat evidence retrieved through a hint as verified because it was retrieved. It is verified because its content hash matches and its signature verifies, and by nothing else.
3. A hint MUST NOT carry a secret, a bearer token, a credential, or personal data. It is an ordinary field of a shared object and the private-data rules of [canonical-commercial-model-v0.1.md](../schemas/canonical-commercial-model-v0.1.md) section 13 apply to it unchanged.

Content addressing is what makes evidence portable. If the location mattered, then the party controlling the location would control the evidence, which is the dependency this whole document exists to remove.

### 3.3 The identifier-only short form

The short form is a bare `evd_` identifier where the full form's object would stand. It carries no content hash, so it establishes less than the full form does, and the rules below are what keep the difference visible rather than letting it pass as equivalent.

1. **It is admitted only where it is already written.** The short form is accepted on `evidence_refs` of an `Offer` and of a `CommercialMandate`, on `assurance_evidence_refs` of an `InvitationAcceptance`, on `identity_evidence_refs` of an `Organization`, and on `authority_evidence_refs` of a `Principal`. These are the members that existed before the reference shape did. Every family defined with the shape requires the full form: `evidence_refs` on a `PerformanceEvent` and on a `Dispute`, and `evidence_relied_on` on a `Determination`. A short form in one of those is refused at validation, on the rule of section 3 that a reference missing a REQUIRED full-form field is an incomplete reference and not a short one.
2. **It resolves only where its target is co-present.** A short-form reference is resolvable only where the referenced `Evidence` object is in the same bundle, or in the same transaction record, as the object carrying the reference. Resolved that way the hash chain is unbroken and nothing is taken on trust: the referencing object's own `content_hash` covers the identifier and is recomputed at step 1, and the referenced `Evidence` object's `content_hash` and `signatures` are checked at steps 1 and 2 like any other object in the set.
3. **An absent target is not checkable, never accepted.** A short-form reference whose target is not co-present MUST be reported as `not_checkable` under section 5, and named as an unresolved reference under section 4 step 7. It MUST NOT be reported as verified on the strength of the identifier, and it is not reported as failed either: the target may exist and simply not have been disclosed, which under section 6 is the normal case. The object carrying the reference is not thereby invalid. What is unestablished is the reference, and the report says so.
4. **A resolution does not travel.** Two sets can carry different `Evidence` objects under one identifier and each verify internally, because nothing in the short form binds bytes. A verifier MUST NOT carry a short-form resolution from one bundle into another, and MUST NOT treat a short-form reference as evidence that any particular bytes were referenced. Only the full form's `content_hash` makes a reference portable, which is why the full form exists.
5. **Nothing new takes the short form.** An object family defined after the reference shape takes the full form, and an implementation SHOULD emit the full form on the members of rule 1 as well. The short form is retained because closing it would invalidate objects that are valid today, which [A202-0004](../proposals/A202-0004-evidence-verification.md) section 4.1 recorded as a MAJOR change deliberately not taken there.

The reason for retaining a weaker form at all is stated rather than left to be inferred. An identifier alone can be pointed at different bytes later, and that is exactly the substitution the content hash removes. What the short form still supports is the check a verifier can actually run on a co-present target, and what it does not support is a claim about bytes nobody holds. Rules 3 and 4 are what keep the second from being read out of the first.

## 4. The verification procedure

A verifier executes the following steps in order, against the bundle it holds. Every step is executable by a third party with the bundle, the referenced schemas, the referenced rule set versions, and the declared keys, and with no access to any operator.

A step that fails produces a finding with the refusal code named in section 8 and the verifier continues to the following steps, so that the report states everything that is wrong rather than only the first thing.

### Step 1: canonicalise and check content hashes

Serialise every object under JSON Canonicalization Scheme, RFC 8785, omitting `content_hash`, `signatures`, and `kernel_annotations` from the bytes hashed, exactly as required by [canonical-commercial-model-v0.1.md](../schemas/canonical-commercial-model-v0.1.md) section 4. Recompute the SHA-256 of those bytes and compare it to the declared `content_hash`.

Check every hash the bundle asserts, not only object content hashes: `terms_hash` on an agreement, `accepted_offer_hash`, `offer_hash` on an acceptance, `assertion_hash` on an obligation response, `invitation_hash` on an acceptance, `subject_hash` on a dispute, `inputs_hash` on a determination, and the `content_hash` inside every evidence reference.

Any mismatch is `A202-EVIDENCE-HASH-MISMATCH`.

### Step 2: verify every signature

For each object, verify every entry in `signatures` against the declared key and the declared purpose.

1. Verify the signature value over the canonical bytes from step 1.
2. Check that `purpose` is the purpose appropriate to the object and the act. A signature valid over the bytes but issued for a different purpose does not count as a signature for this one.
3. Resolve key status at `signed_at` and at verification time, and report both. An expired or revoked key does not erase a signature that was valid when it was created.
4. Check signature count requirements: an agreement carries at least two, an invitation acceptance carries both a claimant `invitation_claim` signature and an operator `object_issuance` signature.

Any failure is `A202-EVIDENCE-SIGNATURE-INVALID`. A key whose status cannot be resolved at either point is reported as not checkable for that point, and the signature is not thereby verified.

### Step 3: check version chains

For every object that carries versions, follow `previous_version_id` from the earliest version to the latest.

1. `version` starts at 1 and increases by 1 with no gaps.
2. Version 1 carries a null `previous_version_id`, and every later version names one.
3. No two objects name the same `previous_version_id`. Two successors to one version is a fork, and a fork means two objects claim to be current.

The same rule applies to determination supersession chains under [determination-v0.1.md](../disputes/determination-v0.1.md) section 5: linear, no gaps, no forks.

Any gap or fork is `A202-EVIDENCE-CHAIN-GAP`.

### Step 4: check per-stream sequence continuity

For each stream disclosed to the verifier, check continuity within that stream and only within it.

1. `sequence` increases by 1 from the stream's first disclosed event.
2. `previous_event_hash` on each event equals the `content_hash` of the preceding event **in the same stream**.
3. The first disclosed event of a stream either carries a null `previous_event_hash`, meaning the stream is disclosed from its start, or names a predecessor the verifier does not hold, which is reported as a disclosed boundary rather than as a gap.

Sequence numbers are per stream. A verifier MUST NOT expect continuity across streams, and MUST NOT infer anything from the sequence numbers of one stream about the activity on another. Cross-stream ordering from `kernel_annotations.received_at` is presentation only and is never used to authorise anything.

A discontinuity inside a disclosed stream is `A202-EVIDENCE-CHAIN-GAP`. A stream that was not disclosed is not a gap; it is out of scope for this report and is stated as such under section 6.

### Step 5: replay guarded transitions

Replay the disclosed events in sequence order, applying session events then aggregate events, against the state machines in [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) and, for obligations, against the transition table in [obligation-v0.1.md](../agreement/obligation-v0.1.md) section 6.1.

For every transition, check all of:

1. the transition is legal from the `from_state` the record carries;
2. the guard stated for that transition held, against the rules version in force at the time the event appended, not against the current one;
3. the actor was authorised: the mandate referenced by the event resolves, covered the action, and was active at append time;
4. the referenced `PolicyDecision` resolves and is bound to the event's `action_hash`;
5. the recomputed `to_state` equals the recorded one.

An illegal or unguarded transition is `A202-EVIDENCE-TRANSITION-ILLEGAL`. This is the replay-time counterpart of `A202-STATE-TRANSITION-DENIED`, which is what a live implementation returns when it refuses the transition in the first place. Both exist because a transition can be refused at the time or discovered afterwards, and the two are different findings.

### Step 6: check every determination

For every determination in the bundle, check that its stated outcome follows from its referenced rules and inputs, under [determination-v0.1.md](../disputes/determination-v0.1.md) section 4.3.

1. `question.rules_ref` resolves to an exact rule set version, and it is the version in force at the time of the subject act.
2. Every entry in `outcome.rules_applied` resolves inside that version.
3. `outcome.inputs_hash` recomputes over the canonically ordered input set.
4. Every entry in `outcome.evidence_relied_on` resolves and verifies under steps 1 to 3 of this procedure.
5. The stated `finding` follows from the rules applied and the evidence relied on.
6. `effect` does not exceed what the referenced rules granted, under section 6 of that document.

A determination whose outcome does not follow is `A202-DETERMINATION-NOT-FOLLOWING`. One whose effect exceeds its grant is `A202-DETERMINATION-EFFECT-OVERCLAIM`.

Where the rule set version does not resolve, the determination is reported as not checkable, never as verified. An unresolvable rule set is the case where a verifier most wants to conclude something, and it is exactly the case where it may not.

### Step 7: report what could not be checked

State every gap explicitly.

1. **Undisclosed streams.** Name each stream the bundle references but does not contain.
2. **Unresolved references.** Name each evidence reference, rule set version, mandate, policy decision, or key status that did not resolve.
3. **Unreferenced evidence.** Name each evidence object present in the bundle that nothing in the bundle references. Unreferenced evidence is not a failure and is not support for anything either.
4. **Unregistered types.** Name each evidence type, condition type, constraint type, or profile that did not resolve in its registry.

Every one of these is reported as not checkable. None of them is reported as failed, and none of them is reported as verified.

The distinction is the point of the step. Reporting a gap as a failure makes a partial disclosure look like misconduct, and partial disclosure is the normal case. Reporting a gap as a pass makes an absence look like evidence, which is the failure mode that assurance reporting exists to prevent everywhere else in this specification set. Absence of a check reads as unchecked, exactly as absence of an assessment reads as unassessed.

## 5. Verification output

A verification report distinguishes three outcomes and never collapses them.

| Outcome | Meaning |
|---|---|
| `verified` | The check was executed and passed |
| `failed` | The check was executed and did not pass |
| `not_checkable` | The check could not be executed with what the verifier holds |

Rules:

1. A report MUST carry a per-check result, not only an overall one. The three outcomes MUST NOT be reduced to a boolean at any point in the report.
2. A report MUST state its scope: which streams, which objects, and which time range it covers. See section 6.
3. A report MUST name each refusal code from section 8 that was raised, together with the object it was raised against.
4. `not_checkable` MUST NOT be presented, coloured, summarised, or aggregated as either of the other two. A consumer that treats not checkable as verified has misconfigured its own bar, and the report MUST NOT make that reading easy.
5. A report is a statement by whoever produced it. It is not itself a determination, and it carries no effect under [determination-v0.1.md](../disputes/determination-v0.1.md) section 6. A report may of course be evidence in a dispute, referenced like any other evidence.

A report MUST NOT be reported as passing where any check returned `failed`. It MAY be reported as passing in scope where checks returned `verified` and `not_checkable`, provided the not checkable set is stated in the same report at the same prominence.

## 6. Selective disclosure

A bundle may disclose a subset of the streams and objects that exist. Verification of the subset MUST be possible without the remainder.

1. **The subset verifies on its own.** Every check in section 4 that can be executed against the disclosed subset MUST be executable without any undisclosed object. An implementation MUST NOT produce records whose verification requires an object it does not disclose to that verifier.
2. **The report states scope.** A report over a subset MUST state which streams and objects were in scope, and MUST list the undisclosed streams the bundle references. A report that does not state its scope is a report whose silence is indistinguishable from completeness.
3. **A boundary is not a gap.** A disclosed stream that begins mid stream, with a `previous_event_hash` naming an event the verifier does not hold, is a stated boundary. It is reported under section 4 step 7 and is not `A202-EVIDENCE-CHAIN-GAP`.
4. **Disclosure reveals nothing about what was withheld.** The number, size, sequence range, or timing of undisclosed streams MUST NOT be inferable from the disclosed subset beyond the fact that a named reference exists. This follows the same rule as the per-stream sequencing in the state machine: a counter that moves because of something a party may not see is a channel through which that party learns it anyway.
5. **Selective disclosure never weakens a check.** A check executed over a subset is executed in full or it is reported as not checkable. There is no reduced form of a check for a reduced bundle.

## 7. Human oversight evidence

This section is informative. It states no requirement on an implementation, and it is not a legal compliance assessment.

Human oversight of an agent acting commercially is evidenced by objects this specification set already defines. Nothing here adds an object; the point is to say which existing object carries which fact, so that a party building an oversight record knows what to export rather than inventing a parallel log.

### 7.1 Where oversight appears in the objects

- **The mandate carries the oversight design.** `approval_rules` state the conditions under which a named human or role must approve, and `actions`, `scope`, and `constraints` state the boundary inside which the agent may act at all. Both are set before the agent acts, by a principal, and both are part of the signed mandate.
- **The pause is a state.** A session reaching `paused_for_approval` is the recorded fact that an action was held for a named approver, and `approval.granted` or `approval.rejected` is the recorded fact of what that approver did.
- **The approval binds exact bytes.** An `Approval` binds one action hash, one transaction, an approver identity and role, a decision, a created and an expiry time, and the approver's signature. Changing one byte of the action invalidates it, and it cannot be reused across actions or transactions. Under operator key custody, every act requires such an approval from a named principal of the acting organisation.
- **The contest is recorded.** A determination records what was determined, on which rules, on which evidence, and by whom. An appeal produces a superseding determination and both remain in the record permanently.

### 7.2 Mapping to the oversight concerns of EU AI Act Article 14

Each row names an oversight concern and the object in this specification set that evidences it. The mapping is informative. It is not a legal compliance assessment, it is not advice, and it does not state that any implementation satisfies any obligation. Whether Article 14 applies to a given deployment, and what it requires of it, is a question for the deployer and its advisers.

| Oversight concern | Objects that evidence it | Where specified |
|---|---|---|
| Oversight is assigned to identified natural persons before the system is used | `approval_rules` on the `CommercialMandate`, naming the approver organisation and role; the `Principal` that issued the mandate | [commercial-mandate-v0.1.md](../authority/commercial-mandate-v0.1.md) sections 3 and 8 |
| Oversight measures are matched to the system's autonomy and to its context of use | Mandate `actions`, `scope`, and `constraints`, with monotonic narrowing along the delegation chain; per-act approval where the acting key is operator custodied | [commercial-mandate-v0.1.md](../authority/commercial-mandate-v0.1.md) sections 3.1, 4, 7, and 11.3 |
| The conduct of the system can be monitored while it operates | Per-stream signed event records with guarded transitions; one `PolicyDecision` bound to each `action_hash`, recording allow, deny, or approval required | [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) sections 5 and 8; [canonical-commercial-model-v0.1.md](../schemas/canonical-commercial-model-v0.1.md) section 9 |
| Intervention is possible and, when it happens, it is recorded | `paused_for_approval` with `approval.granted` and `approval.rejected`; the `Approval` object bound to one action hash; `RevocationRecord` for suspension and revocation; `determination` and appeal records | [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) section 6.1; [commercial-mandate-v0.1.md](../authority/commercial-mandate-v0.1.md) sections 8 and 9; [determination-v0.1.md](../disputes/determination-v0.1.md) sections 4 and 7 |

Two limits of the mapping are worth stating plainly. The objects evidence that an oversight design existed and that particular interventions happened. They do not evidence that the design was adequate, that the person named was competent to exercise it, or that the intervention was correct. And an object exists because a party created it: a record showing no interventions is consistent with an agent that needed none and with an oversight arrangement nobody used.

## 8. Refusal codes

All fail closed. These extend the table in [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) section 10.

| Code | Meaning |
|---|---|
| `A202-EVIDENCE-HASH-MISMATCH` | A recomputed hash differs from the declared one, at step 1 |
| `A202-EVIDENCE-SIGNATURE-INVALID` | A signature does not verify over the canonical bytes, was issued for a different purpose, or a required signature is absent, at step 2 |
| `A202-EVIDENCE-CHAIN-GAP` | A version chain or a disclosed stream has a gap, or a chain forks, at steps 3 and 4 |
| `A202-EVIDENCE-TRANSITION-ILLEGAL` | A replayed transition was not legal, its guard did not hold, or its actor was not authorised, at step 5 |
| `A202-EVIDENCE-TYPE-UNKNOWN` | An evidence reference names a type that does not resolve in the registered list, at step 1 and at step 7 |
| `A202-DETERMINATION-NOT-FOLLOWING` | A determination's stated outcome does not follow from its referenced rules and inputs, at step 6 |
| `A202-EVIDENCE-REPORT-INVALID` | A verification report states no scope, collapses `not_checkable` into `verified` or `failed`, or reduces the per-check results to a boolean, against section 5 |
| `A202-EVIDENCE-DISCLOSURE-INCOMPLETE` | A disclosed subset cannot be verified without an object that was not disclosed to that verifier, against section 6 rule 1 |

`A202-DETERMINATION-NOT-FOLLOWING` and `A202-DETERMINATION-EFFECT-OVERCLAIM` are defined in [determination-v0.1.md](../disputes/determination-v0.1.md) section 9 and are reused here unchanged rather than duplicated under a verification-specific name.

A refusal code in a verification report names a check that was executed and failed. A check that could not be executed produces a `not_checkable` result under section 5 and no refusal code.
