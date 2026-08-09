# Changelog

**Status:** Informative in full. This file records what changed and when. It states no requirement on an implementation of the specification, and where it and a specification document disagree, the document is the definition and this file is stale.

## What this file is for

[RELEASES.md](RELEASES.md) section 3.4 requires a release to carry release notes naming every `A202` identifier the release carries, and, for a MAJOR release, migration notes. This is the file those notes accumulate in, written as changes land.

An entry is added under **Unreleased** by the pull request that lands the change. At a release the Unreleased heading is replaced by the version and the date, the tag is cut on that commit, and a fresh Unreleased section is opened above it. A release is a tag, schema digests, the manifest, and these notes, published together, per RELEASES.md section 3.

Entries name the proposal identifier because the proposal is where the reasoning is. The entry says what changed; `proposals/A202-NNNN-short-title.md` says why.

## Unreleased

No change has landed since v0.1.0.

## v0.1.0 — 9 August 2026

The first tagged release of the specification set. The specification documents, the schemas, the fixtures, the manifest, and the runner are released together under one version number, as RELEASES.md section 1 requires, and the four parts RELEASES.md section 3 requires are published together: this tag, the schema digests in [schemas/digests-v0.1.json](schemas/digests-v0.1.json), the conformance manifest at [conformance/manifest-v0.1.json](conformance/manifest-v0.1.json), and these notes.

This is a `0.x` release. Under RELEASES.md section 4, the compatibility guarantee becomes binding at 1.0; before it, a MINOR increment may break compatibility, and any break carries migration notes. There is nothing to migrate from here, because there is no earlier release.

An implementation of this set declares a read version and a write version, both `0.1.0`, per RELEASES.md section 4.

### Proposals carried

| Proposal | Change | Stage |
|---|---|---|
| [A202-0001](proposals/A202-0001-carrier-bindings.md) | A2A and plain HTTPS carrier bindings | 3. Fixtures and compatibility |
| [A202-0002](proposals/A202-0002-obligation.md) | Obligation shape, due condition, and acceptance rule | 3. Fixtures and compatibility |
| [A202-0003](proposals/A202-0003-determination.md) | Determination and dispute family | 3. Fixtures and compatibility |
| [A202-0004](proposals/A202-0004-evidence-verification.md) | Evidence reference shape and public verification procedure | 3. Fixtures and compatibility |
| [A202-0005](proposals/A202-0005-settlement-handoff.md) | Rail-neutral settlement handoff | 3. Fixtures and compatibility |
| [A202-0006](proposals/A202-0006-bilateral-conformance-role-scopes.md) | Named conformance role scopes, and a bilateral scope two parties can adopt alone | 3. Fixtures and compatibility |
| [A202-0007](proposals/A202-0007-exception-prefix-and-deferred-payloads.md) | Register the `exc_` prefix, and record the deferral of three payload definitions | 2. Experimental |
| [A202-0008](proposals/A202-0008-replay-single-source.md) | One normative home for replay. Raised and not yet executed: no edit has been made to any document under it | 2. Experimental |
| [A202-0009](proposals/A202-0009-enforcement-fidelity.md) | Enforcement fidelity: every claimed check is a real check | 3. Fixtures and compatibility |
| [A202-0010](proposals/A202-0010-model-completion.md) | Model completion: amendment, consensual termination, release, and the payloads the normative rules lean on | 3. Fixtures and compatibility |
| [A202-0011](proposals/A202-0011-registry-and-waiver-corrections.md) | The evidence-type registry written down, and the waiver states the text already promised | 3. Fixtures and compatibility |
| [A202-0012](proposals/A202-0012-party-family-payloads.md) | Payload definitions for the organization, the agent, and the principal | 3. Fixtures and compatibility |
| [A202-0013](proposals/A202-0013-transaction-event-allowlist.md) | The transaction stream typed, closing the last open event payload | 3. Fixtures and compatibility |
| [A202-0014](proposals/A202-0014-bilateral-formation-and-scope-repair.md) | Bilateral formation, and the scope partition made true | 3. Fixtures and compatibility |
| [A202-0015](proposals/A202-0015-fixture-minimality-orphan-codes-and-grade-scope.md) | Minimal fixtures, codes that are raised rather than declared, and a grade scope that can be written | 3. Fixtures and compatibility |
| [A202-0016](proposals/A202-0016-casing-short-form-and-amendment-corrections.md) | The value an object carries named, the short form the fixtures already use admitted, and the amendment rule stated where the inventory defers it | 3. Fixtures and compatibility |
| [A202-0017](proposals/A202-0017-submission-success-status.md) | The status an accepted submission returns, and that no status is acceptance | Adopted |

Stage names are the five in [proposals/README.md](proposals/README.md) section 3. A proposal at stage 2 is explicitly not stable, and an implementation building against it is told so here as well as there.

Seventeen proposal identifiers, `A202-0001` through `A202-0017`, allocated in sequence and none reused. They are the first of the two identifier forms [proposals/README.md](proposals/README.md) section 2 distinguishes: four digits after the prefix is a proposal, uppercase words after the prefix is a reason code.

### Reason codes carried

Seventy-seven reason codes, which is the whole registry. [negotiation/pilot-transaction-state-machine-v0.1.md](negotiation/pilot-transaction-state-machine-v0.1.md) section 10 declares its table, together with the additions in [negotiation/auction-event-semantics-v0.1.md](negotiation/auction-event-semantics-v0.1.md) section 8.1 and [conformance/conformance-role-scopes-v0.1.md](conformance/conformance-role-scopes-v0.1.md) section 8, the complete registry, and a code resolving in none of the three is one an implementation MUST NOT invent. The three tables are named here in full so that the release notes and the registry can be compared without reading the documents.

Sixty-seven in the state machine table:

`A202-STATE-TRANSITION-DENIED`, `A202-SEQUENCE-CONFLICT`, `A202-STREAM-MISMATCH`, `A202-OFFER-STALE`, `A202-OFFER-EXPIRED`, `A202-APPROVAL-REQUIRED`, `A202-APPROVAL-HASH-MISMATCH`, `A202-AGREEMENT-HASH-MISMATCH`, `A202-AGREEMENT-AMENDMENT-UNACCEPTED`, `A202-MANDATE-INACTIVE`, `A202-MANDATE-INTERVAL-INVALID`, `A202-MANDATE-UNBOUNDED`, `A202-MANDATE-SCOPE-TOO-BROAD`, `A202-MANDATE-SUBJECT-AMBIGUOUS`, `A202-MANDATE-DELEGATION-INCOHERENT`, `A202-MANDATE-DELEGATION-WIDENING`, `A202-MANDATE-CONSTRAINT-UNKNOWN`, `A202-MANDATE-STATUS-INSECURE`, `A202-ENDPOINT-INSECURE`, `A202-MANDATE-STATUS-UNRESOLVED`, `A202-ANNOTATION-FORGED`, `A202-DISCLOSURE-POLICY-VIOLATION`, `A202-TERMS-INVALID`, `A202-HASH-FORMAT-INVALID`, `A202-POLICY-DENIED`, `A202-DISCLOSURE-DENIED`, `A202-EVIDENCE-UNVERIFIED`, `A202-PROFILE-UNKNOWN`, `A202-PROFILE-TERMS-INVALID`, `A202-INVITATION-UNCLAIMABLE`, `A202-INVITATION-EXPIRED`, `A202-INVITATION-SCOPE-EXCEEDED`, `A202-INVITATION-HASH-MISMATCH`, `A202-INVITATION-CLAIM-UNSIGNED`, `A202-INVITATION-SECRET-DISCLOSED`, `A202-ASSURANCE-UNSUPPORTED`, `A202-CUSTODY-APPROVAL-REQUIRED`, `A202-OBLIGATION-CONDITION-UNKNOWN`, `A202-OBLIGATION-CONDITION-CYCLIC`, `A202-OBLIGATION-SUBJECT-UNREFERENCED`, `A202-OBLIGATION-ASSERTION-UNEVIDENCED`, `A202-OBLIGATION-RESPONSE-UNAUTHORIZED`, `A202-OBLIGATION-RESPONSE-HASH-MISMATCH`, `A202-OBLIGATION-REMAINDER-MISSING`, `A202-OBLIGATION-TERMS-MUTATED`, `A202-OBLIGATION-REJECTION-REASON-UNKNOWN`, `A202-DISPUTE-OUT-OF-WINDOW`, `A202-DISPUTE-GROUNDS-UNKNOWN`, `A202-DISPUTE-SUBJECT-UNREFERENCED`, `A202-DETERMINATION-EFFECT-OVERCLAIM`, `A202-DETERMINATION-SUPERSESSION-UNREASONED`, `A202-DETERMINATION-SUPERSESSION-FORKED`, `A202-DETERMINATION-NOT-FOLLOWING`, `A202-APPEAL-GROUNDS-UNKNOWN`, `A202-EVIDENCE-HASH-MISMATCH`, `A202-EVIDENCE-SIGNATURE-INVALID`, `A202-EVIDENCE-CHAIN-GAP`, `A202-EVIDENCE-TRANSITION-ILLEGAL`, `A202-EVIDENCE-TYPE-UNKNOWN`, `A202-EVIDENCE-REPORT-INVALID`, `A202-EVIDENCE-DISCLOSURE-INCOMPLETE`, `A202-SETTLEMENT-RAIL-UNKNOWN`, `A202-SETTLEMENT-TRIGGER-ABSENT`, `A202-SETTLEMENT-IDEMPOTENCY-CONFLICT`, `A202-SETTLEMENT-RECEIPT-UNMATCHED`, `A202-SETTLEMENT-CUSTODY-REFUSED`, `A202-EXTENSION-UNSUPPORTED`.

Seven added by the auction event table. Its eighth row, `A202-DISCLOSURE-POLICY-VIOLATION`, restates a code the state machine table already registers and is counted once:

`A202-AUCTION-CLOSED`, `A202-AUCTION-FORMAT-UNSUPPORTED`, `A202-BID-NO-IMPROVEMENT`, `A202-LOT-UNKNOWN`, `A202-LOT-ALREADY-AWARDED`, `A202-SCORING-RULE-FROZEN`, `A202-ROUND-NOT-OPEN`.

Three added by the role scope table:

`A202-GRADE-SCOPE-UNKNOWN`, `A202-GRADE-SCOPE-INVALID`, `A202-GRADE-SCOPE-OVERCLAIM`.

Fifty-nine of the seventy-seven are exercised by a negative fixture that declares them in the manifest. The remaining eighteen are conditions a static document cannot express — expiry, revocation, idempotency, concurrent append, an unresolvable status endpoint, a late bid — which is the third limitation `schemas/v0.1/README.md` records: there are no runtime fixtures, because those conditions need state rather than a document.

Six of the eighteen are raised by the reference implementation or the MCP server: `A202-STREAM-MISMATCH`, `A202-APPROVAL-REQUIRED`, `A202-APPROVAL-HASH-MISMATCH`, `A202-MANDATE-INACTIVE`, `A202-MANDATE-STATUS-UNRESOLVED`, `A202-POLICY-DENIED`. Three are named in the runner's own logic without being a declared expectation in the manifest: `A202-SETTLEMENT-CUSTODY-REFUSED`, `A202-BID-NO-IMPROVEMENT`, `A202-LOT-ALREADY-AWARDED`. The remaining nine are stated by the specification documents and raised by nothing in this repository: `A202-SEQUENCE-CONFLICT`, `A202-OFFER-STALE`, `A202-INVITATION-UNCLAIMABLE`, `A202-INVITATION-HASH-MISMATCH`, `A202-SETTLEMENT-IDEMPOTENCY-CONFLICT`, `A202-SETTLEMENT-RECEIPT-UNMATCHED`, `A202-AUCTION-CLOSED`, `A202-SCORING-RULE-FROZEN`, `A202-ROUND-NOT-OPEN`. A reader judging what this release establishes should read that last group as registered and unexercised.

Two negative fixtures declare no code, `negative/envelope-carries-carrier-metadata.json` and `negative/evidence-ref-short-form-where-full-form-required.json`. Both are refused by the closed schema shape, which is the rule in each case, and the runner asserts that the schema layer did refuse them, so an absent declaration cannot cover a fixture nothing refuses.

One further `A202` token ships inside fixture payload content and resolves in none of the three tables: `A202-MANDATE-PREPAYMENT-LIMIT`, in the `reason_codes` of `conformance/fixtures/v0.1/negative/policy-deny-visible-to-counterparty.json`. It is not a registered code, no layer reads it, and the fixture's declared offence and declared code are elsewhere and unaffected. It is named here because these notes name every `A202` token the release carries, and a reader comparing the set against the registry would otherwise find it unaccounted for.

### Schema digests

Five schema files, digested with SHA-256 over the bytes of each file and recorded in [schemas/digests-v0.1.json](schemas/digests-v0.1.json), which RELEASES.md section 3.2 requires:

| File | `$id` |
|---|---|
| `schemas/v0.1/commercial-kernel.schema.json` | `https://schemas.a202.org/v0.1/commercial-kernel.schema.json` |
| `schemas/v0.1/commercial-mandate.schema.json` | `https://schemas.a202.org/v0.1/commercial-mandate.schema.json` |
| `schemas/v0.1/conformance-grade.schema.json` | `https://schemas.a202.org/v0.1/conformance-grade.schema.json` |
| `schemas/v0.1/profiles/calibration-service-0.1.schema.json` | `https://schemas.a202.org/v0.1/profiles/calibration-service-0.1.schema.json` |
| `schemas/v0.1/profiles/freight-spot-0.1.schema.json` | `https://schemas.a202.org/v0.1/profiles/freight-spot-0.1.schema.json` |

The digest of the conformance manifest is recorded in the same file, so that the fixture set section 3.3 requires a release to name is as verifiable as the schemas. `.github/scripts/check-schema-digests.py` runs on every pull request and every push to the default branch, so a schema or manifest edit that does not regenerate the digests fails there rather than at the next release.

Released schemas are served from the `$id` hosts above with a long immutable cache, because a released schema never changes bytes.

### Conformance set

148 fixtures, 32 positive and 116 negative, all classified as the manifest declares by `conformance/run-conformance.py`. The reference implementation carries 34 tests and the MCP server 108, and both run alongside the suite on every pull request under `.github/workflows/checks.yml`.

### Repository machinery

- Continuous integration runs the conformance suite and both test suites on every pull request and on every push to the default branch, which is what makes [GOVERNANCE.md](GOVERNANCE.md) section 3.4 a gate rather than a stated rule.
- A link check enforces the rule in [CONTRIBUTING.md](CONTRIBUTING.md) that no path or link leaves this repository.
- A digest check enforces RELEASES.md section 3.2 the same way: the recorded digest of every schema file, and of the manifest, is compared against the bytes in the tree on every pull request and every push to the default branch.
- Code owners, a pull request template, and issue forms shaped like the proposal process, so that a proposal arrives in the form it will be reviewed in.
- The documentation site: `mkdocs.yml` arranges the tracked tree, the staging script under `.mkdocs/` mirrors it into the docs directory, and the Docs workflow builds the site on every change. The pages under `docs/` are the only content authored for the site, they are informative in full, and where one of them and a specification document disagree, the document is the definition.
