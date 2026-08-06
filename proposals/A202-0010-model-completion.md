# A202-0010: Model completion: amendment, consensual termination, release, and the payloads normative rules lean on

**Status:** Fixtures and compatibility. Stage 3 of the five stages in [README.md](README.md) section 3. Every change in this proposal is implemented in the schemas, the runner's rule sets, the fixture set, the manifest, and the reference implementation, and the suite passes with the changes in place.

**Date:** 28 July 2026

**Status of this document:** Informative in full. It states no requirement on an implementation. The normative text this proposal adopts is carried by the documents it names, each of which marks its own normative sections.

## 1. Problem

The same review that produced [A202-0009](A202-0009-enforcement-fidelity.md) found a second class: lifecycle paths a first deployment needs in its first month that the model did not define, and object payloads that normative rules lean on with no defined shape.

1. **No amendment path.** The obligation specification says changed terms are "a new obligation under an amended agreement"; the canonical model said agreements are amended "in future spec". No amendment object, event, or rule existed, while the version-chain machinery would accept a re-versioned agreement with different terms that nobody re-accepted.
2. **No consensual termination.** The only route to `terminated` ran through `exception_open`, so two parties who agreed to walk away had to manufacture a false fault record first.
3. **No obligation exit on termination.** An obligation in `pending`, `due`, `asserted`, `rejected`, or `disputed` when the transaction ended had no transition out, and stayed stranded on a transaction that no longer existed.
4. **Nineteen of thirty-four object types had no payload schema and three were disclosed.** Among the undisclosed were `approval`, the object the entire operator-custody control binds through, together with `commitment`, `evidence`, `revocation_record`, and `key_record`.
5. **The mandate was simultaneously an envelope object and not one.** The canonical model required every shared object to carry the envelope; `commercial_mandate` sat in the kernel enum; the mandate schema and every fixture said otherwise, and the kernel schema refused the valid mandate fixture.
6. **Key lifecycle was unresolvable.** Verification must resolve key status at signed time and verification time, and `KeyRecord` had no payload, no status vocabulary, and no fixture: nothing defined to resolve against.
7. **Signature metadata was unprotected.** A signature covered the object's canonical bytes only, so its own `purpose` and `signed_at` members could be rewritten after the fact: a signature issued for one act could be presented for another, and a signed time could be backdated to before a key's revocation, with neither edit detectable from the bytes.

## 2. Change

1. **Amendment**, canonical model section 10.1. An amendment is a superseding agreement version reached through a fresh offer and a fresh acceptance, dual-signed, appending `agreement.amended` with no aggregate state change. A later version naming its predecessor's acceptance or offer is refused with `A202-AGREEMENT-AMENDMENT-UNACCEPTED`. Obligations keep referencing the version they derived from; removed duties end by the obligee's waiver, added duties are new obligations.
2. **Consensual termination**, state machine sections 5 and 5.2. `termination.agreed` moves any eligible committed state, and `exception_open`, to `terminated`, guarded by both parties' signatures over one termination record hash that names the disposition of every open obligation.
3. **Release**, obligation specification section 6. A terminal `released` state, reached from every non-terminal state by `obligation.released` when an authorized termination names the obligation. Distinct from `waived` because the release is carried by the dual-signed termination record, and from `discharged` because nothing was performed.
4. **Rules version 1.2** registers the two new transitions for replay. Versions 1.0 and 1.1 are immutable, so a record made under them replays against what was legal then; a fixture replays `termination.agreed` against 1.0 and it is illegal there.
5. **Payload definitions** for `approval`, `commitment`, `evidence`, `revocation_record`, and `key_record`, each closed, each with its identifier prefix pinned in its schema branch. `clr_`, `key_`, and `rev_` join the prefix table. The canonical model's section 5.6 now states the full defined-and-deferred division rather than an under-inclusive list of three.
6. **The mandate is standalone**, canonical model section 3.1. `commercial_mandate` leaves the kernel enum; the mandate remains a standalone signed document under its own schema, referenced by `mnd_` identifier, and the reason, that the mandate terminates the authority chain that envelope objects are verified against, is stated rather than implied.
7. **Protected signature members**, canonical model section 4 rule 5. The signature value covers the canonical bytes plus the entry's own `algorithm`, `key_id`, `purpose`, and `signed_at`, so relabeling or backdating a signature is a verification failure. The reference implementation implements the construction, with regression tests for the relabeled-purpose and backdated-time attacks, and key status resolves against the new `KeyRecord` version chain.

## 3. Compatibility

Pre-release, pre-1.0. Additions dominate: new transitions under a new rules version, new payload definitions for types that previously validated as envelope-only, a new terminal state, and new fixtures. Three changes are breaking in shape and are the migration surface: the mandate leaves the kernel enum (no fixture or implementation used it in envelope form; the kernel schema refused the only mandate fixture that exists), the signature construction adds protected members (the published fixtures carry placeholder signatures and are unaffected; any real signer re-signs), and `evidence`/`approval`-family objects now validate their payloads (objects minted against the old unconstrained forms were never schema-checkable and re-validate against the new shapes). Records made under earlier rules versions replay unchanged, which is the point of registering 1.2 rather than editing 1.0.

## 4. Fixture plan

Implemented, not planned: `valid-approval`, `valid-key-record`, `key-record-private-key-member`, `valid-agreement-amendment`, `agreement-amendment-reuses-acceptance`, `valid-consensual-termination`, and `termination-agreed-under-prior-rules`. The reference test suite adds the two signature-attack regressions and derives the conformance total from the manifest.

## 5. Ordering

Depends on [A202-0009](A202-0009-enforcement-fidelity.md) only in that both touch the same documents and this proposal's fixtures rely on the reason-code assertion that proposal added to the runner. Nothing else depends on this proposal.
