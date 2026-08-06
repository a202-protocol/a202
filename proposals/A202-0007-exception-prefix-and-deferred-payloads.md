# A202-0007: Register the `exc_` prefix, and record the deferral of three payload definitions

**Status:** Experimental. Stage 2 of the five stages in [README.md](README.md) section 3. The change is concrete and is explicitly not stable; an implementation may build against it knowing it may change.

**Date:** 27 July 2026

**Status of this document:** Informative in full. It states no requirement on an implementation. The normative text this proposal describes lands in [schemas/canonical-commercial-model-v0.1.md](../schemas/canonical-commercial-model-v0.1.md), which marks its own normative sections.

## 1. Problem

This is housekeeping. It closes one identifier gap and records one absence honestly, and it is raised as a proposal because both touch a normative document.

**An object type with no registered prefix.** `exception` is a member of the `object_type` enum in the kernel schema and appears in the object inventory of [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md) section 5.5 as "claimed failure, variance, or remediation path". It has no entry in the identifier prefix table of section 3. The generic identifier pattern admits any three-letter prefix, so two implementations can mint `exc_` and `exn_` for the same object type and both validate. Identifiers are opaque and long lived, and a prefix that diverges before publication diverges permanently, because every reference already written under one form stays written.

The commercial situation is ordinary. A buyer opens an exception against a supplier's delivery, and the object identifier travels into a dispute's `subject_id`, into a determination's inputs, into an obligation's record, and into any evidence bundle either party exports. If the two implementations mint different prefixes, nothing fails at validation. What fails is a year later, when a party filtering a bundle by identifier prefix silently sees none of the counterparty's exceptions and reports a clean record.

The gap was found and recorded while drafting [A202-0002](A202-0002-obligation.md), whose section 4.5 registers `prf_` for `performance_event`, states that `exception` has the same gap, and says explicitly that it is out of that proposal's scope and is recorded so it is not lost. This proposal picks it up.

**Three object types with no payload definition.** `Exception`, `EvidenceManifest`, and `AuditBundle` are named in the object inventory with a purpose, an owner, and a sharing rule each, and none of the three has a defined payload. [A202-0004](A202-0004-evidence-verification.md) section 4.3 records the second and third as an open item and states that the verification procedure does not need them, because it runs against whatever set of objects a verifier holds.

The risk is not that they are undefined. It is that they are named in a way that reads as defined. An implementer who finds `EvidenceManifest` in the inventory, sees "hash-addressed inventory of transaction evidence", and finds `evidence manifest present` as a guard in the state machine's `performance.declared` row, has three pieces of evidence that the object is specified and no statement anywhere that it is not. What that implementer builds is a shape of its own devising that the counterparty's implementation will not parse.

## 2. Proposal

Two edits to [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md), stated in the words that would land. They are landing in the same change set as this proposal, so the register and the record arrive together rather than the record pointing forward at a register that does not exist yet.

### 2.1 One row in the prefix table of section 3

| Object | Prefix |
|---|---|
| Exception | `exc_` |

The row is added in the position the inventory order implies, with the other lifecycle objects between Performance event and Dispute. It registers a prefix and states nothing about the object's payload.

### 2.2 A dated deferral note beneath the inventory

A subsection headed **Three payload shapes deferred, recorded 27 July 2026** lands beneath the inventory table, as section 5.6 of the canonical model. It states, in substance and largely in these words:

> `exception`, `evidence_manifest`, and `audit_bundle` are members of the `object_type` enum in `v0.1/commercial-kernel.schema.json` and are named in the inventory above with a purpose, an owner, and a sharing rule each. None of the three has a payload definition in v0.1, and no conditional in the kernel schema constrains their payloads.
>
> The consequence is stated here rather than left to be discovered: schema validation of those three payloads is not claimable in v0.1. An object of one of those types validates against the common envelope and nothing else, so an implementation that reports it as schema-valid is reporting that the envelope validated. Their payload shapes are deferred to a later proposal.

The landed note also restates, next to the prefix row it registers, why the registration does not wait for the payload definition, and records that `evidence_manifest` and `audit_bundle` carry no registered prefix because neither appears as a reference inside another object's payload in v0.1.

### 2.3 The note is informative, and that is deliberate

Section 5 of the canonical model is marked informative in that document's status header, so the note lands as informative text and states no requirement. It is written in ordinary prose for that reason, and it records an absence rather than creating a rule.

That is a choice a reviewer should test rather than wave through. The alternative is to carry the prohibition on inference as a normative sentence, which would have to land in section 14 rather than in section 5.5, because a requirement cannot be stated in an informative section. This proposal does not take that path, on the ground that the prohibition adds nothing an implementation is not already bound by: section 2 of the canonical model already states that schema validity is necessary and not sufficient, and section 14 already states that unknown object types or required fields fail validation. What is missing is not a rule but the plain statement that these three payloads do not exist, and that statement belongs next to the rows that name them.

If review concludes the prohibition should be normative, it becomes a rule in section 14 with its own fixture, and this proposal is the wrong shape for it.

## 3. Alternatives considered

**Do nothing.** Leave the prefix unregistered and the absence unrecorded. Rejected on the divergence argument in section 1: a prefix registered before the first release costs one table row, and a prefix registered after two implementations have minted different ones costs a migration of identifiers that were supposed to be immutable. The unrecorded absence is rejected on the second argument: an object that reads as specified and is not is worse than an object that is plainly missing, because the first produces confident work and the second produces a question.

**Define the three payloads in this proposal.** Rejected as a different proposal wearing this one's title. `Exception` carries a claimed failure, a variance, and a remediation path, each of which touches the dispute path, the obligation transition table, and the aggregate's `exception_open` state. `AuditBundle` carries an event root and replay metadata, which touches the replay duplication that [A202-0008](A202-0008-replay-single-source.md) is separately resolving. Bundling them here would produce a proposal whose compatibility analysis and fixture set are dominated by work this one is not doing, and would delay a prefix registration that is independently useful.

**Register a prefix for all three at once.** Rejected for `EvidenceManifest` and `AuditBundle`, accepted for `Exception`. The difference is that `exception` is already an `object_type` enum member that an implementation can mint today, so the divergence is live. The other two would be prefixes for objects nobody can construct, chosen now and possibly wrong once the payload is designed. A prefix is a long-lived commitment and choosing one for an undesigned object spends that commitment early for no benefit.

**Record the deferral in a proposal only, and leave the specification silent.** Rejected. The reader who needs the statement is reading the object inventory, not the proposal directory. A deferral that lives only in a proposal is a deferral the person it protects will not find.

**Tighten the identifier pattern so that any unregistered prefix fails validation.** Rejected for v0.1, and worth stating as a real option. It would close the class of gap rather than this instance, and it would make every future object type a schema change to the pattern as well as a table row. It would also invalidate any currently valid object minted with a prefix that is legitimately unregistered today, which is a MAJOR change under [RELEASES.md](../RELEASES.md) section 2 and is not what this proposal is.

## 4. Compatibility

**Nothing currently valid becomes invalid.** The prefix registration constrains what an implementation mints from now on. It does not narrow the identifier pattern, does not reclassify any object, and does not invalidate an identifier already written. Its purpose is to prevent divergent minting rather than to invalidate anything.

**The deferral note states an absence, not a restriction on an existing shape.** An implementation that already refuses to guess at an undefined payload is unaffected. One that infers a shape was relying on something the specification never stated, and the note says so rather than changing what was stated.

Under [RELEASES.md](../RELEASES.md) section 2 the change set is **MINOR**, on the strength of the prefix row: it registers an identifier prefix for an object type that had none. The deferral note on its own alters no normative statement and is PATCH-class under the same table; the two land together and the higher increment governs. Neither invalidates a conformant implementation.

**No code is added.** An object minted under a prefix that contradicts the registered one is refused by the ordinary identifier and object type rules; adding a code for it would create a second name for a refusal that already has one.

**Migration.** None for an implementation that mints no exception object. An implementation that has been minting exceptions under a different prefix is not migrating from a previous version of this specification, because no prefix was registered; it is adopting the registration for the first time, and any identifier it already issued stays valid under the pattern it was issued against.

**Ordering.** This proposal is independent of every other open proposal. It carries no dependency and nothing depends on it, other than the later payload proposal that the deferral note points at.

## 5. Fixture plan

There is one honest thing to say here, and it is the reason this section is short.

**Schema-level enforcement of the `exc_` binding requires the payload conditional, which is the deferred work.** A fixture that refuses an exception object minted under the wrong prefix needs a schema conditional keyed on `object_type: exception` that constrains the `id` pattern, in the way the obligation payload conditional constrains `^obl_`. There is no exception payload conditional, and adding one is the payload definition this proposal explicitly defers. Writing a conditional that constrains only the identifier, and leaves the payload unconstrained, would be a partial payload definition arriving through the back door and would have to be revisited by the proposal that defines the payload properly.

So the registration is carried by the prefix table in the canonical model now, and its fixtures land with the payload proposal. Concretely, that proposal is expected to carry a positive fixture for a well-formed exception object minted under `exc_`, and a negative fixture refusing one minted under any other prefix, in the way the obligation fixtures exercise `^obl_`.

**The deferral note is not fixture-expressible while the absence it records persists.** A fixture presenting an exception object with an invented payload would validate today, because nothing constrains that payload, and that is precisely the condition being recorded. Writing a fixture that asserts the object validates would freeze the gap into the manifest as intended behaviour. Writing one that asserts it is refused would assert a rule that does not exist. Neither is a fixture worth having, and the correct fixture arrives with the payload definition.

The process rule in [README.md](README.md) section 3 is that a rule which cannot be turned into a fixture is a rule whose semantics are not yet decided. That rule is doing its work here, and the honest reading is the second half of it: the prefix registration has decided semantics and a blocked fixture, while the three payloads have no semantics yet, which is why this proposal defers them rather than describing them. Stage 3 is not reachable for this proposal until the payload proposal lands, and that ordering is stated rather than worked around.

## 6. Origin

The prefix gap was found while drafting [A202-0002](A202-0002-obligation.md) and is recorded in its section 4.5, which registers `prf_` for `performance_event`, states that `exception` has the same gap, and leaves it out of scope. The undefined payloads of `EvidenceManifest` and `AuditBundle` are recorded in [A202-0004](A202-0004-evidence-verification.md) section 4.3 as an open item.

Both arose from specification review rather than from any implementation's experience. No object of any of the three types has been constructed against this set. This is context for reviewers rather than an argument.
