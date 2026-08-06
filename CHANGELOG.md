# Changelog

**Status:** Informative in full. This file records what changed and when. It states no requirement on an implementation of the specification, and where it and a specification document disagree, the document is the definition and this file is stale.

## What this file is for

[RELEASES.md](RELEASES.md) section 3.4 requires a release to carry release notes naming every `A202` identifier the release carries, and, for a MAJOR release, migration notes. This is the file those notes accumulate in, written as changes land.

An entry is added under **Unreleased** by the pull request that lands the change. At a release the Unreleased heading is replaced by the version and the date, the tag is cut on that commit, and a fresh Unreleased section is opened above it. A release is a tag, schema digests, the manifest, and these notes, published together, per RELEASES.md section 3.

Entries name the proposal identifier because the proposal is where the reasoning is. The entry says what changed; `proposals/A202-NNNN-short-title.md` says why.

## Unreleased

No release has been made. The contents are `v0.1` working documents rather than a tagged release of the set, as RELEASES.md section 5 states.

The list below is the state a first release would carry.

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

### Conformance set

148 fixtures, 32 positive and 116 negative, all classified as the manifest declares by `conformance/run-conformance.py`. The reference implementation carries 34 tests and the MCP server 108, and both run alongside the suite on every pull request under `.github/workflows/checks.yml`.

### Repository machinery

- Continuous integration runs the conformance suite and both test suites on every pull request and on every push to the default branch, which is what makes [GOVERNANCE.md](GOVERNANCE.md) section 3.4 a gate rather than a stated rule.
- A link check enforces the rule in [CONTRIBUTING.md](CONTRIBUTING.md) that no path or link leaves this repository.
- Code owners, a pull request template, and issue forms shaped like the proposal process, so that a proposal arrives in the form it will be reviewed in.
- The documentation site: `mkdocs.yml` arranges the tracked tree, the staging script under `.mkdocs/` mirrors it into the docs directory, and the Docs workflow builds the site on every change. The pages under `docs/` are the only content authored for the site, they are informative in full, and where one of them and a specification document disagree, the document is the definition.
