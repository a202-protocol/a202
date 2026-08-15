# A202-0021: A witnessed record chain as a registered evidence type

**Status:** Draft, not yet submitted; held for founder review. Written to enter at stage 1, problem statement, of [README.md](README.md) section 3. Section 2 drafts the change stage 2 would adopt. Nothing is implemented: no schema, specification document, fixture, or runner rule has been edited.

**Date:** 15 August 2026

**Status of this document:** Informative in full. It states no requirement on an implementation. The normative material this proposal amends is carried by [evidence-verification-v0.1.md](../evidence/evidence-verification-v0.1.md), which marks its own normative sections, and by [schemas/v0.1/commercial-kernel.schema.json](../schemas/v0.1/commercial-kernel.schema.json).

## 1. Problem

[evidence-verification-v0.1.md](../evidence/evidence-verification-v0.1.md) section 1 draws a deliberate line: verification is public and specified in full, and bundle construction is not. How records are gathered, ordered, packaged, held, exported, and disclosed is outside this specification. That line is what lets an A202 record be checked without operator access, and nothing here moves it.

Other specifications sit on the far side of that line and do exactly the work A202 declines to do. An evidence-witness protocol records the events of a transaction as a hash-chained sequence, seals the chain by its own procedure, publishes a verification procedure for it, and exports it in a form built for a dispute reviewer. A party to an A202 transaction that also ran such a witness will, sooner or later, present the sealed chain as evidence: in a `Dispute`, in a `Determination`'s `evidence_relied_on`, or on a `PerformanceEvent`, to show what its systems recorded happening around an act.

The registry in section 3.1 has no member for that thing. The registered types describe a statement standing on nothing further (`attestation`), a certificate, an inspection, a delivery confirmation, a measurement, a receipt answering a settlement instruction (`adapter_receipt`), a report produced under section 5, and a document whose bytes are themselves the evidence (`signed_document`). A witnessed chain is none of these. Its value is not that someone signed it, but that its internal hash chain and seal can be recomputed under a published external procedure by anyone holding the bytes; the type is what would tell a verifier that such a procedure exists to run.

Because the registry is closed and fails closed (section 3.1.1), a presenting party today has three bad options. It can label the chain `signed_document`, in which case a verifier checks the A202 object's own hash and signature, reports `verified`, and never learns that the chain has a procedure of its own that might have failed. It can label it `attestation`, which is false on its face: an attestation stands on nothing further, and a chain stands on its chain. Or it can label it `adapter_receipt`, whose meaning is fixed by [settlement-handoff-v0.1.md](../fulfillment/settlement-handoff-v0.1.md) section 4 as an answer to a settlement instruction, which a chain of discovery, intent, authorization, and fulfillment events is not. Three presenting parties would pick three types for the same bytes, on the layer whose whole purpose is that one procedure checks everything.

The commercial situation is the ordinary one. A supplier's agent, under a commercial mandate, accepts a purchase order in an A202 session; the buyer's checkout ran under an evidence-witness protocol that sealed the authorization and later appended a fulfilment record. The buyer disputes performance. The supplier presents the witnessed chain to show what the buyer's own witness recorded about delivery. Under the registry as it stands, there is no honest way to say what kind of thing was presented, and no rule telling the verifier what to do with it.

## 2. Change

1. **The registry in [evidence-verification-v0.1.md](../evidence/evidence-verification-v0.1.md) section 3.1 gains one member.** In the words that would land, as a new row of the table:

   | `evidence_type` | What it evidences |
   |---|---|
   | `witnessed_record_chain` | A hash-chained record of transaction events produced under an external witness protocol and sealed by that protocol's own procedure, referenced by the hash of the exported chain bytes. It evidences that a witness recorded a sequence of events, and it evidences neither the authority behind any recorded event nor the truth of any event's content: the same limit [settlement-handoff-v0.1.md](../fulfillment/settlement-handoff-v0.1.md) section 4.2 places on a receipt |

2. **The kernel schema's `evidenceTypeId` enum gains the same member**, appended, in the same change. Section 3.1 already requires this: the table and the enum are one registry expressed twice, and a member present in one and absent from the other is a defect in whichever was not updated.

3. **Section 3.1 gains a new subsection 3.1.2, "Types with an external procedure",** in the words that would land:

   > A `witnessed_record_chain` is the one registered type whose referenced artifact carries a verification procedure of its own, published by the witness protocol that produced it. For an `Evidence` object of this type:
   >
   > 1. `artifact_hash` MUST be the SHA-256 over the exported chain bytes exactly as presented, so that step 1 of section 4 checks the reference against the bytes and nothing else. The chain's own internal seal identifier is not a substitute for it: a seal identifies the chain to its own verifier, and `artifact_hash` identifies the bytes to this one.
   > 2. `claim` SHOULD state the witness protocol's identifier and version and the chain's own seal identifier, so that a verifier that implements the external procedure knows which one to run and against what.
   > 3. A verifier MAY re-verify the chain under the external procedure. Where it does, the outcome is a separate per-check result under section 5, named as the external procedure's result, and MUST NOT be folded into, or reported in place of, the A202 checks of steps 1 to 7. Where the verifier does not implement the external procedure, the external check is reported as `not_checkable` under step 7, and the A202 checks are reported on their own merits, exactly as an unregistered type is handled today.
   > 4. Neither result stands in for the other. An A202-verified `Evidence` object of this type says that a party presented these bytes, signed for them, and stated this claim; it does not say the chain verifies. An externally verified chain says the witness's record is internally consistent; it does not say any A202 object referencing it is.

   Rule 3 is the load-bearing one. It extends the existing discipline of section 5, that three outcomes are never collapsed, across the boundary between two procedures, and it reuses `A202-EVIDENCE-REPORT-INVALID` unchanged for a report that collapses them.

4. **An informative annex, "Annex A: evidence-witness protocols",** is added to [evidence-verification-v0.1.md](../evidence/evidence-verification-v0.1.md) in the form the settlement-handoff annexes take: it records, at the level of objects and not of fields, how a witness protocol's exported chain lines up with the type above, checked against a stated version on a stated date, and creates no requirement on that protocol. Its first entry is drafted in section 6 below.

No transition, guard, state, or existing type changes. No refusal code is added. The reference shape of section 3 is untouched: a `witnessed_record_chain` is referenced in the full form like every other type, and the short form is not extended to it, by section 3.3 rule 5.

## 3. Alternatives considered

**Reuse `signed_document`.** The chain is signed, and the bytes are the evidence, so the row's words fit. Its meaning does not. `signed_document` tells a verifier that once the A202 checks pass there is nothing further to run; a witnessed chain is precisely the case where there is, and where the further procedure may fail on bytes whose A202 wrapper is impeccable. A type is what a verifier reads to decide what to do, and a type that hides a procedure from it defeats the registry's reason for being closed.

**Reuse `adapter_receipt`.** A receipt answers an instruction, must reference the instruction identifier and idempotency key it answers, and is refused unmatched. A chain answers nothing; it records. Forcing it through the receipt rules would either fail the refusal in [settlement-handoff-v0.1.md](../fulfillment/settlement-handoff-v0.1.md) section 4.1 or require weakening that refusal for one type, which is the wrong trade.

**Reuse `attestation`.** An attestation stands on nothing further. That is the opposite of a chain's claim to be believed, and a type that says the opposite of what the thing is cannot be repaired by wording.

**Register the external procedure's outcome inside the A202 `verification` object.** That is, let `verification.status` on the `Evidence` payload carry the chain's own result. Rejected because it collapses two procedures into one field: a `verified` there would be unreadable, since a consumer could not tell whether the A202 verifier or the external one produced it, and section 5 rule 4 exists to prevent exactly that reading.

**Register one type per witness protocol.** Rejected. The type says what kind of thing the evidence is, and every witness chain is the same kind of thing: bytes with an external procedure. Which procedure is a property of the claim and the annex, not of the registry, and a registry that grew a member per protocol would put every future protocol's arrival on this specification's release cadence.

**Do nothing.** Chains are presented anyway, under three different labels, and verifiers handle them three different ways. The registry stays honest and the record does not.

## 4. Compatibility

Under [RELEASES.md](../RELEASES.md) section 2 the change is MINOR-shaped by the closest rule in the table: it adds an enum member for a case previously unexpressible, and no previously conformant implementation emitted it, because no schema accepted it. The honest caveat is the same one every enum addition carries and that section 3.1.1 makes explicit: a verifier pinned to the earlier registry reports the new type as unregistered and the reference as `not_checkable`, which is the behaviour section 3.1.1 already requires and is not a failure. Nothing that validated before this change stops validating. The migration surface is empty for existing implementations and one item for a presenting party: relabel a chain it had been presenting under a borrowed type.

## 5. Fixture plan

Planned, not implemented; stage 3 is where these land.

**Allow direction.** A `Dispute` whose `evidence_refs` carries a full-form reference to a co-present `Evidence` object of type `witnessed_record_chain`, whose `artifact_hash` equals the SHA-256 of a co-present exported chain byte string, validates; the runner recomputes the reference `content_hash` and the artifact hash at step 1 and reports both `verified`, and reports the external procedure `not_checkable`, because the runner implements no witness protocol's procedure and says so.

**Refuse direction.** The same object with an `artifact_hash` that does not match the presented bytes fails at step 1 with `A202-EVIDENCE-HASH-MISMATCH`. And a verification report over the allow fixture that presents a single `verified` covering both the A202 checks and the external procedure — or that carries no per-check entry for the external procedure at all — is refused with `A202-EVIDENCE-REPORT-INVALID`, which is what makes rule 3 of the new subsection checkable in both directions.

A third fixture, mechanical: an `Evidence` object naming `witnessed_record_chain` validates against the amended enum, and the negative fixture that today exercises `A202-EVIDENCE-TYPE-UNKNOWN` continues to use a value that remains unregistered, so the type-unknown path stays covered.

## 6. Annex A, first entry: the A-Comm Evidence Protocol

**Informative.** Drafted here for stage 2; would land in [evidence-verification-v0.1.md](../evidence/evidence-verification-v0.1.md) as the first entry of the annex described in section 2 item 4. It records how the objects line up so that an implementer holding both can see where the mapping is available and where it is lossy. It creates no requirement on the other specification and asserts no equivalence.

**Checked 15 August 2026** against the A-Comm Evidence Protocol (AEP) draft v1.0.3-rc.2.

AEP records a commerce journey as a sequential hash chain of typed artifacts, canonicalised under RFC 8785 and hashed with SHA-256, sealed at its authorization artifact, signed with Ed25519 by the recording implementation, and exported for dispute review as a bundle that a third party re-verifies under AEP's own published verification procedure. AEP describes itself as a witness: it records, and by its own terms assigns no weight, outcome, or liability.

At the level verified, the correspondence is:

| A202 | Nearest AEP construct |
|---|---|
| `Evidence` of type `witnessed_record_chain`, `artifact_hash` over the exported bundle bytes | The exported dispute bundle |
| The seal identifier stated in `claim` | The chain's sealed bundle hash |
| The external procedure of section 3.1.2 rule 3 | AEP's chain re-verification on export |
| `Evidence.issuer` | The recording implementation named by the chain's signing key |
| A `PerformanceEvent`'s evidence reference | A post-seal fulfilment artifact appended to the chain |

The mapping is stated at the level of the objects and not at the level of fields, for the reason the settlement-handoff annexes give: a binding written against field names would become false the first time either specification revised one.

Both specifications canonicalise under RFC 8785 into SHA-256 expressed as lowercase hexadecimal, so a hash carried across the boundary in either direction is recomputable by the other side's verifier without translation. The reverse direction, in which an AEP chain references an A202 `CommercialMandate`, `Agreement`, or `Determination` by identifier and content hash, is a matter for that specification and is not stated here.

What AEP covers that A202 deliberately does not restate: how the record is constructed, ordered, sealed, held, and exported; the privacy handling of the record; the classification of each recorded signal by how it can be checked; and the presentation of the record to a dispute reviewer. A202 states none of these, by section 1 of the evidence-verification document, and defers to the witness on all of them. The division of ownership is that the witness owns the record of what happened, and A202 owns the commercial state: what was authorised, what was negotiated, what was accepted, and what is therefore owed. A determination under [determination-v0.1.md](../disputes/determination-v0.1.md) may rely on a witnessed chain as evidence like any other; the chain does not become a determination by being sealed, and a determination does not become a record of events by being replayable.

## 7. Origin

Raised on 15 August 2026 alongside a comment filed by the editor on the AEP v1.0.3 review round, which asked that specification whether its evidence chain could reference an organisation-issued commercial mandate, a negotiated agreement, and an externally made determination by identifier and content hash. This proposal is the reciprocal: the type under which such a chain is admitted as evidence on this side, so that the composition can be verified from either direction and neither specification takes a dependency on the other. The pilot scenario in section 1 is the one used to test the fit. This is context for reviewers rather than an argument.
