# Reference implementation

**Status:** Informative in full. This directory carries a minimal reference implementation of the wire and states no requirement of its own. The rules it implements are normative in the specification documents it cites, and where this code and a specification document disagree, the document is the definition and this code is wrong.

**Date:** 27 July 2026

## What this is

A small Python package, `a202_reference`, implementing the parts of the specification set that a party needs in order to exchange and verify objects:

- **Canonicalization**: RFC 8785 serialization for the JSON subset the kernel emits, and content hash computation, per [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md) section 4.
- **Schema validation**: kernel and mandate validation against [schemas/v0.1/](../schemas/v0.1/README.md), with transaction profile resolution that fails closed on an unregistered identifier.
- **Object emission**: construction of shared objects on the common envelope, with type-prefixed identifiers per the prefix table in canonical model section 3, computed content hashes, and signatures.
- **Signatures**: ES256 creation and verification over the canonical bytes, with the declared purpose checked as part of verification.
- **Evidence verification**: the seven-step procedure of [evidence verification v0.1](../evidence/evidence-verification-v0.1.md) section 4, producing a per-check report in the three-valued output of section 5. The report type deliberately has no overall boolean.
- **Carrier extension declaration handling**: building, parsing, and checking capability declarations per the carrier binding, [bindings/a2a-binding-v0.1.md](../bindings/a2a-binding-v0.1.md), with every failure mode returning the single refusal `A202-EXTENSION-UNSUPPORTED`.

## What this is not

It is not an operator. It contains no negotiation venue, no session ordering service, no policy evaluation beyond the published normative checks, no scoring, ranking, or award logic, no held-out assessment material, and no network server or client. Everything in it is a pure function over objects the caller holds, plus local file access to the schemas in this repository.

It is not production software. Keys are handled in memory, no storage is provided, and the package exists so that an implementer can see one correct, checkable reading of the wire rules rather than to be deployed.

## Running the tests

From this directory:

```bash
python3 -m unittest discover -v
```

Discovery from this directory collects the tests of `a202_mcp` alongside this package's own; `python3 -m unittest discover -s tests -t .` runs this package's 34 in isolation.

The test suite includes a test that executes the public conformance suite, `python3 conformance/run-conformance.py` from the repository root, and asserts that every fixture behaves as the manifest declares. It also includes a sweep, `tests/test_fixture_sweep.py`, which routes every evidence-bundle fixture in the manifest through `a202_reference.verifier` directly rather than through the runner subprocess, and asserts that this reading of the seven-step procedure agrees with the manifest: a positive bundle produces no failed check, and a negative bundle whose offence lies inside the procedure produces the corresponding failed check. A bundle whose offence lies outside the procedure is skipped with a stated reason, and the sweep prints how many bundles it swept and how many it skipped, because a sweep that quietly ignored most of the set would report agreement it had not established. Neither test is normative; the runner and the specification documents are.

## Dependencies

Python 3.9 or later, `jsonschema` 4.18 or later with `referencing`, and `cryptography` for ES256 signatures. The tests use the standard library `unittest` runner.
