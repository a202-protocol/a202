# A202 commercial schemas v0.1

**Status:** Informative in full. This document describes the schema files in this directory and states no requirement of its own. The rules it summarises are normative in [canonical-commercial-model-v0.1.md](../canonical-commercial-model-v0.1.md).

**Status of the schemas themselves:** Experimental pilot schemas.

## Files

- `commercial-kernel.schema.json`: market-neutral shared-object envelope, plus action-envelope, offer, acceptance, agreement, event, policy-decision, obligation, obligation-response, performance-event, dispute, determination, settlement-instruction, and adapter-receipt payloads, and the shared evidence reference shape.
- `commercial-mandate.schema.json`: commercial authority, scope, constraints, approvals, delegation, evidence references, and proof.
- `conformance-grade.schema.json`: the conformance grade of [../../conformance/conformance-grades-v0.1.md](../../conformance/conformance-grades-v0.1.md) section 4. Like a mandate, and unlike every object in the kernel, a grade is a standalone signed document rather than a common-envelope object: it states something about an implementation rather than performing an act inside a transaction. The role scope rules that carry reason codes are enforced by the runner rather than here, under [../../conformance/conformance-role-scopes-v0.1.md](../../conformance/conformance-role-scopes-v0.1.md) sections 3.2 and 6.3.
- `profiles/`: transaction profile schemas. The kernel resolves a profile identifier and never interprets a profile's terms.
The SHA-256 digest of every file in this directory is recorded one level up, in [../digests-v0.1.json](../digests-v0.1.json), which [../../RELEASES.md](../../RELEASES.md) section 3.2 requires a release to carry, alongside the digest of the conformance manifest that section 3.3 requires. A schema whose digest differs from the one recorded there is not that release. The digest covers the bytes of the file on disk, not the canonical form of [../canonical-commercial-model-v0.1.md](../canonical-commercial-model-v0.1.md) section 4, which covers commercial objects rather than schema documents. The file sits outside this directory because the runner registers every JSON file it finds here as a schema.

These schemas use JSON Schema Draft 2020-12. They are not production standards, legal instruments, verifiable credential schemas, or payment authorization schemas.

## The profile boundary

The kernel schema contains no field, enum member, or constant that is meaningful in only one transaction profile. That rule is normative in [canonical-commercial-model-v0.1.md](../canonical-commercial-model-v0.1.md) section 8.

`terms` has three parts:

- `profile`, a registered identifier;
- `core`, identical for every transaction type;
- `profile_terms`, opaque to the kernel and validated against the profile's own schema.

`profiles/freight-spot-0.1.schema.json` exists only as a neutrality probe. Its fixture has to validate against the unchanged kernel schema. If adding a transaction profile ever requires a kernel change, the kernel is not canonical.

An earlier revision of the kernel pinned `terms.profile` to the calibration-service constant and required calibration-specific fields. Under that schema no other transaction could be expressed. The probe exists so this cannot recur unnoticed.

## Schema validity is not conformance

Several specification rules are cross-field or registry-dependent and cannot be expressed in JSON Schema: interval ordering, profile resolution, and the visibility rules for denied decisions. They are listed in [canonical-commercial-model-v0.1.md](../canonical-commercial-model-v0.1.md) section 12 and enforced by `../../conformance/run-conformance.py`.

Run the suite before and after any schema change:

```bash
python3 conformance/run-conformance.py --verbose
```

## Known limitations of v0.1

- There are no RFC 8785 canonicalization vectors.
- There are no signature vectors.
- There are no runtime fixtures. Revocation, expiry, delegation narrowing, and idempotency need state rather than a static document, so they cannot be covered by the fixture set in its current form.
- There is no automated compatibility report for a schema change.
