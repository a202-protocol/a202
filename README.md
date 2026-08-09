# A202: the Verifiable Agreement Protocol for Agent-Led Commerce

**Status:** Informative in full.

A202 is verifiable commerce for agent-to-agent or agent-led transactions: an open specification of commercial authority, negotiation state, and verifiable conformance for transactions between independent organisations, including transactions conducted on their behalf by software agents.

It defines typed objects for delegated commercial authority, a state machine for the transaction and for each bilateral session inside it, rules for what may be disclosed to whom, and an executable conformance suite that turns each of those into a check an implementation either passes or fails.

The full statement of purpose, scope, and non-goals is in [CHARTER.md](CHARTER.md).

Created and developed by A. A. Musse. See [MAINTAINERS.md](MAINTAINERS.md).

## Status

**Released, pre-1.0.**

- `v0.1.0` is the first tagged release of the set: a tag, a digest for every schema file, the conformance manifest, and release notes, published together. See [RELEASES.md](RELEASES.md) and [CHANGELOG.md](CHANGELOG.md). Before 1.0 a MINOR increment may break compatibility, and any break carries migration notes.
- The name is **A202**, spoken "A two-oh-two", and in full **A202, the Verifiable Agreement Protocol for Agent-Led Commerce**. The long form is a descriptor and not an expansion: the letters do not stand for it. The `202` is HTTP 202 Accepted, which [A202-0017](proposals/A202-0017-submission-success-status.md) makes the status an accepted submission returns, because acceptance is the primitive the rest of the specification is built on. The `A202-` reason-code prefix, the `A202-NNNN` proposal identifiers, and the `a202-commercial/0.1` specification version string all follow from the name.
- **A202**™ is a trademark of Plural Worlds. Permitted use of the name is stated in [TRADEMARK.md](TRADEMARK.md).
- Schema `$id` values resolve under `https://schemas.a202.org`. Fixture hosts use reserved `.invalid` names, because test data must never resolve.
- **Licensed under the Apache License, Version 2.0.** One licence covers the whole repository: specification text, schemas, fixtures, manifest, runner, and informative documents. The licence carries an express patent grant from each contributor. See [LICENSE](LICENSE) and [CONTRIBUTING.md](CONTRIBUTING.md).
- External contributions are accepted on the terms in [CONTRIBUTING.md](CONTRIBUTING.md): inbound contributions under the same licence, with a developer certificate of origin sign-off.

## Layout

| Path | Contents |
|---|---|
| `CHARTER.md` | Purpose, scope, non-goals, design principles |
| `GOVERNANCE.md` | How the project is run, and what the sponsor does and does not control |
| `MAINTAINERS.md` | Who maintains this repository |
| `CONTRIBUTING.md` | Contribution status, and the terms a contribution is accepted under |
| `SECURITY.md` | Private coordinated disclosure |
| `THREAT-MODEL.md` | Adversaries assumed, properties defended, and what is deliberately not defended |
| `CODE_OF_CONDUCT.md` | Expected conduct |
| `TRADEMARK.md` | The A202 name, and what use of it is and is not permitted |
| `RELEASES.md` | Versioning, what a release consists of, compatibility policy |
| `CHANGELOG.md` | What changed, and where the release notes required by `RELEASES.md` accumulate |
| `.github/` | Review routing, the pull request and issue forms, and the workflow that runs the suite on every change |
| `proposals/` | The `A202` change proposal process |
| `schemas/` | Canonical commercial model, transaction profile extension model, and the JSON schemas |
| `authority/` | Commercial mandate: delegated authority, constraints, delegation, approval, revocation |
| `discovery/` | Counterparty invitation: how an unregistered party enters one named transaction |
| `negotiation/` | Transaction and session state machines, and auction event semantics |
| `conformance/` | Fixtures, manifest, normative runner, and the conformance grade definitions |

Each specification document carries a status header stating which of its sections are normative and which are informative.

## Running the conformance suite

The runner validates every fixture named in the manifest against the schemas, then applies the invariants that JSON Schema cannot express. Schema validity is not conformance, which is the reason the runner exists.

It needs `jsonschema>=4.18`. If that is not on the system interpreter, a virtual environment is enough:

```bash
python3 -m venv .venv && .venv/bin/pip install "jsonschema>=4.18"
```

Run it from the repository root:

```bash
python3 conformance/run-conformance.py --verbose
```

The expected result is every fixture passing and none failing, with the totals the manifest carries: the manifest is the single source for the count, and the runner prints it on every run. The runner also asserts that each negative fixture is refused for the reason code the manifest declares for it, wherever the normative layer raises codes at all. Run it before and after any schema change.

Every negative fixture is minimal: removing the single offending element must leave a document that validates cleanly. A negative fixture that fails for an incidental reason tests nothing, so verify that when adding one.

The suite does not depend on anyone remembering to run it. It runs, together with the reference implementation tests and the MCP server tests, on every pull request and on every push to the default branch, under `.github/workflows/checks.yml`. [GOVERNANCE.md](GOVERNANCE.md) section 3.4 requires the suite to pass for any change to schemas, fixtures, the manifest, or the runner, and that workflow is what turns the requirement into a gate.

## Where to start reading

1. [CHARTER.md](CHARTER.md) for what this is and what it deliberately is not.
2. [schemas/canonical-commercial-model-v0.1.md](schemas/canonical-commercial-model-v0.1.md) for the object model, the envelope, and the invariants schema validation cannot express.
3. [negotiation/pilot-transaction-state-machine-v0.1.md](negotiation/pilot-transaction-state-machine-v0.1.md) for what moves state and what does not.
4. [conformance/manifest-v0.1.json](conformance/manifest-v0.1.json) for the fixtures that decide whether an implementation agrees with either of the above.
