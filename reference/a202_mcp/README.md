# A202 MCP server

**Status:** Informative in full. This directory carries a demonstration server and states no requirement of its own. The rules it applies are normative in the specification documents it cites, and where this code and a specification document disagree, the document is the definition and this code is wrong.

**Date:** 31 July 2026

**Scope:** `a202-scope/bilateral/0.1`, the role scope registered in [conformance-role-scopes-v0.1.md](../../conformance/conformance-role-scopes-v0.1.md) section 3.1

An MCP server giving an agent the seven capabilities two organisations need in order to buy and sell from each other directly: issue a mandate, check what an agent may do under it, approve an act that needs a person, form an agreement, exchange obligations, verify a record, and read the transaction record back. It wraps [`a202_reference`](../README.md) and adds a party's local state, the mandate constraint evaluator, and the tool surface.

## Quickstart

The package reads the schemas, profiles, and conformance runner in this repository, so it runs from a checkout rather than from an index.

```bash
git clone <this repository>
cd <repository>/reference
uv run --python 3.12 --with mcp --with jsonschema --with cryptography python -m a202_mcp
```

The server speaks MCP over stdio and prints nothing on start, which is correct: stdout is the protocol channel.

With pip instead of uv:

```bash
python3 -m pip install mcp jsonschema referencing cryptography
python3 -m a202_mcp
```

`mcp` requires Python 3.10 or later. The tool handlers import nothing from the SDK and run on Python 3.9, which is what the reference implementation targets and where its own tests run.

## Connect it to an agent client

The same block works for Claude Code, as `.mcp.json` in a project or through `claude mcp add-json`, and for Claude Desktop, in `claude_desktop_config.json`. Replace the two paths.

```json
{
  "mcpServers": {
    "a202": {
      "command": "uv",
      "args": [
        "run", "--python", "3.12",
        "--with", "mcp", "--with", "jsonschema", "--with", "cryptography",
        "--directory", "/path/to/repository/reference",
        "python", "-m", "a202_mcp"
      ],
      "env": { "A202_MCP_STATE_DIR": "/path/to/state" }
    }
  }
}
```

Drop the `env` line to keep everything in memory for the life of the process. The server declares instructions describing the call order, so a client that reads them hands the model the sequence without being told it.

Packaging metadata is in [pyproject.toml](pyproject.toml), which declares the console script `a202-mcp`. The wheel carries this package and not the repository it reads, so the checkout is still named:

```bash
PYTHONPATH=/path/to/repository/reference \
  uvx --from ./reference/a202_mcp a202-mcp
```

An installed-from-an-index invocation with no checkout is not available: `a202_reference`, the schemas, and the conformance runner are all read from this tree.

## Tool reference

| Tool | What it does | Effect |
|---|---|---|
| `issue_mandate` | Issues and signs the mandate an agent acts under: permitted acts, spending limit, scope, validity window | Records |
| `verify_mandate` | Decides whether an act is permitted, against schema, signature, validity, status, scope, constraints, and approval rules. Answers allow, deny, or require_approval, and reports the act's hash. Its result is what the recording tools require | Reads |
| `issue_approval` | Records a named principal's approval of one exact action hash | Records |
| `create_agreement` | Forms an agreement directly with a known counterparty: offer, acceptance, agreement, commitment, and the two formation events | Records |
| `record_obligation` | One act of the obligation exchange: `issue`, `assert`, or `respond` | Records |
| `verify_evidence` | Runs the seven-step verification procedure over a record, yours or a counterparty's | Reads |
| `get_transaction_record` | Returns the hash-chained record and the state it reaches | Reads |

The three reading tools declare `readOnlyHint`. No tool declares `destructiveHint`, because the record is append only, and none declares `openWorldHint`, because the server makes no network call.

The usual order is `issue_mandate`, then `verify_mandate` before each act, then `create_agreement` and `record_obligation` three times, each carrying the allow it was given, then `verify_evidence`. `issue_approval` enters only when `verify_mandate` answers `require_approval`.

A recording tool with no decision, a stale one, a denied one, or one made over a different act records nothing and says which. There is no way to record an act by asserting that a mandate permitted it.

## Walkthrough

An agent holds a mandate from its principal and completes a calibration purchase with a supplier it already knows. Both parties are synthetic, and both status endpoints use the reserved `.invalid` domain.

### 1. The principal issues the agent's mandate

**Call** `issue_mandate`

```json
{
  "issuer": {
    "organization_id": "org_northstar",
    "principal_id": "prn_northstar_procurement_director",
    "key_id": "key_northstar_principal_01"
  },
  "subject": {
    "agent_id": "agt_northstar_buyer_01",
    "key_id": "key_northstar_agent_01"
  },
  "represented_organization_id": "org_northstar",
  "valid_from": "2026-08-20T00:00:00Z",
  "valid_until": "2026-09-20T00:00:00Z",
  "status_endpoint": "https://status.northstar.invalid/v1/mandates/buyer-01/status",
  "actions": ["offer.accept", "agreement.sign", "settlement.instruct"],
  "scope": {
    "transaction_ids": ["txn_calibration_demo_01"],
    "counterparty_organization_ids": ["org_delta"],
    "geographies": ["NL"]
  },
  "spending_limit": { "currency": "EUR", "amount": "4000.00" }
}
```

**Result**

```json
{
  "outcome": "issued",
  "mandate_id": "mnd_fc29029f675fc2532b23939f",
  "mandate": { "spec_version": "a202-mandate/0.1", "id": "mnd_fc29029f675fc2532b23939f", "...": "the whole signed document, including its proof" },
  "role_scope": "a202-scope/bilateral/0.1"
}
```

The spending limit is in the signed document as two constraints, so both appear in the audit record and in any later delegation check:

```json
[
  { "id": "c_total_amount",   "type": "commercial.decimal", "path": "$.proposed_terms.core.total.amount",   "operator": "maximum", "value": "4000.00", "on_failure": "deny" },
  { "id": "c_total_currency", "type": "commercial.string",  "path": "$.proposed_terms.core.total.currency", "operator": "equals",  "value": "EUR",     "on_failure": "deny" }
]
```

The supplier's principal issues its own agent a mandate the same way, scoped to the same transaction and carrying `offer.submit`.

### 2. Each agent verifies its own act

Nothing is recorded that was not verified first. Each party verifies the act it is about to take, and carries the result into the recording call. The buyer accepts and the supplier submits, so the two acts are different documents and neither decision covers the other.

**Call** `verify_mandate`

```json
{
  "mandate_id": "mnd_fc29029f675fc2532b23939f",
  "status": { "status": "active", "retrieved_at": "2026-08-20T09:59:30Z" },
  "proposed_action": {
    "action_type": "offer.accept",
    "transaction_id": "txn_calibration_demo_01",
    "counterparty_organization_id": "org_delta",
    "proposed_terms": { "...": "the same terms the agreement will carry" }
  }
}
```

**Result**

```json
{
  "proof": "verified",
  "validity_interval": "verified",
  "status": "verified",
  "decision": "allow",
  "reason_codes": []
}
```

The same call with a total of `"4800.00"`:

```json
{
  "decision": "deny",
  "reason_codes": ["A202-POLICY-DENIED"],
  "constraints": [
    { "id": "c_total_amount",   "result": "unsatisfied", "code": "A202-POLICY-DENIED" },
    { "id": "c_total_currency", "result": "satisfied",   "code": null }
  ]
}
```

The agent is told which constraint refused it, not merely that something did. A denied act cannot then be recorded: `create_agreement` takes the decision itself, and only an allow is written.

The supplier verifies its own act in the same shape, with `"action_type": "offer.submit"` and `org_northstar` as counterparty. Keep both results.

### 3. The two parties form the agreement

**Call** `create_agreement`

```json
{
  "transaction_id": "txn_calibration_demo_01",
  "buyer": {
    "organization_id": "org_northstar",
    "agent_id": "agt_northstar_buyer_01",
    "mandate_id": "mnd_fc29029f675fc2532b23939f",
    "key_id": "key_northstar_agent_01"
  },
  "supplier": {
    "organization_id": "org_delta",
    "agent_id": "agt_delta_supplier_01",
    "mandate_id": "mnd_1f0c2e...",
    "key_id": "key_delta_agent_01"
  },
  "offeror_role": "supplier",
  "offer_valid_until": "2026-08-21T09:00:00Z",
  "buyer_decision": { "...": "the allow the buyer got in step 2" },
  "supplier_decision": { "...": "the allow the supplier got in step 2" },
  "terms": {
    "profile": "a202-profile/calibration-service/0.1",
    "core": {
      "description": "Calibration and digital certificates for 20 pressure transmitters",
      "quantity": "20",
      "unit_code": "H87",
      "unit_name": "piece",
      "total": { "currency": "EUR", "amount": "3200.00" }
    },
    "profile_terms": {
      "completion": { "business_days_after_collection": 15, "business_calendar": "NL" },
      "payment": { "prepayment_percent": "20", "balance_trigger": "buyer_acceptance" },
      "acceptance": {
        "certificate_required": true,
        "machine_readable_result_required": true,
        "qualification_standard": "ISO/IEC 17025:2017"
      },
      "rework": { "included_attempts": 1 }
    }
  }
}
```

**Result**

```json
{
  "outcome": "recorded",
  "transaction_id": "txn_calibration_demo_01",
  "session_id": "ses_16827ecbdeec1fc8b85403e4",
  "offer_id": "off_3450da4007b413d2786f79f0",
  "acceptance_id": "acc_0b0bb5d8755e07548d1c8a85",
  "agreement_id": "agr_560714f0a81ff6ea52fd0939",
  "commitment_id": "cmt_76ea12847c520f9d17baa5f2",
  "terms_hash": "fe2cb66583211e3b34a4483aae4441609fd70ca3559b175983180ca933a4992b",
  "state": "committed",
  "rules_version": "1.3"
}
```

### 4. The obligation is issued, performed, and answered

Every one of the three acts carries its own party's allow decision, obtained exactly as in step 2. The act documents are stated in each tool's description; for the issue below the obligee verifies `{"action_type": "obligation.activated", "transaction_id": ..., "counterparty_organization_id": "org_delta", "proposed_terms": {"core": {"quantity": "20", "unit_code": "H87", "total": {"currency": "EUR", "amount": "3200.00"}}}, "agreement_id": ...}`. Where a decision does not match, the refusal states the document to verify.

**Call** `record_obligation` with `act: "issue"`

```json
{
  "act": "issue",
  "decision": { "...": "the obligee's allow for this act" },
  "agreement_id": "agr_560714f0a81ff6ea52fd0939",
  "obligor": { "...the supplier party..." },
  "obligee": { "...the buyer party..." },
  "term_path": "$.terms.core.quantity",
  "quantity": "20",
  "unit_code": "H87",
  "due_condition": { "type": "due_at_time", "at": "2026-09-10T12:00:00Z" },
  "consideration": { "currency": "EUR", "amount": "3200.00" }
}
```

**Result**

```json
{ "outcome": "recorded", "act": "issue", "state": "in_performance",
  "obligation": "obl_0859550fccaacb1b15329007" }
```

**Call** `record_obligation` with `act: "assert"`

```json
{
  "act": "assert",
  "decision": { "...": "the obligor's allow for performance.declared" },
  "obligation_id": "obl_0859550fccaacb1b15329007",
  "obligor": { "...the supplier party..." },
  "obligee": { "...the buyer party..." },
  "asserted_quantity": "20",
  "evidence": [
    {
      "evidence_type": "third_party_certificate",
      "claim": "Calibration certificates issued for 20 transmitters under ISO/IEC 17025:2017",
      "artifact_hash": "9f2c...",
      "issuer": { "organization_id": "org_delta" },
      "verification": {
        "status": "verified",
        "verified_at": "2026-09-08T14:00:00Z",
        "verifier_organization_id": "org_northstar"
      }
    }
  ]
}
```

**Result**

```json
{ "outcome": "recorded", "act": "assert", "state": "acceptance_pending",
  "assertion": "prf_50efaa929f0f77414c78ac01",
  "evidence_ids": ["evd_e813da3191df3e69e4059a00"] }
```

The same call with `"evidence": []`:

```json
{ "outcome": "refused",
  "reason_codes": ["A202-OBLIGATION-ASSERTION-UNEVIDENCED"] }
```

Nothing was recorded, and the result arrives with `isError` set, so a client cannot read it as success.

**Call** `record_obligation` with `act: "respond"`

```json
{
  "act": "respond",
  "decision": { "...": "the obligee's allow for acceptance.granted" },
  "assertion_id": "prf_50efaa929f0f77414c78ac01",
  "responder": { "...the buyer party..." },
  "counterparty": { "...the supplier party..." },
  "response_type": "accept"
}
```

**Result**

```json
{ "outcome": "recorded", "act": "respond", "state": "settlement_pending",
  "response": "obr_82dd70b9d39693f2120a69c4" }
```

### 5. The record, and what a counterparty can check for itself

**Call** `get_transaction_record`

```text
1  agreement.direct       draft              -> agreement_pending
2  agreement.committed    agreement_pending  -> committed
3  obligation.activated   committed          -> in_performance
4  performance.declared   in_performance     -> acceptance_pending
5  acceptance.granted     acceptance_pending -> settlement_pending

chain: linked
state: settlement_pending
```

**Call** `verify_evidence` with `{"transaction_id": "txn_calibration_demo_01", "rules_version": "1.3"}`

```json
{
  "results": { "verified": 55, "failed": 0, "not_checkable": 0 },
  "streams_disclosed": ["transaction:txn_calibration_demo_01"],
  "undisclosed_streams": ["ses_16827ecbdeec1fc8b85403e4"],
  "unresolved_references": []
}
```

The session identifier appears under `undisclosed_streams` because the objects name a session and no session stream was disclosed. Bilaterally there is no session stream at all: the offeror minted the identifier, the counterparty adopted it, and nothing ordered it. The verifier states the gap rather than closing it, which is what it does with every gap.

Two more results are worth running:

- The same call with `"rules_version": "1.2"` fails the first transition with `A202-EVIDENCE-TRANSITION-ILLEGAL`. Version 1.2 never registered `agreement.direct`, and a record replays against the version in force when it appended.
- Changing one byte of the agreement's terms and verifying the modified bundle fails step 1 with `A202-EVIDENCE-HASH-MISMATCH`, and the signatures over it fail with it.

## Approvals

Where a mandate carries an approval rule, an act that matches it is held rather than allowed. The loop is three calls.

**Call** `verify_mandate` with the act. It is held, and the result names the exact act:

```json
{
  "decision": "require_approval",
  "reason_codes": ["A202-APPROVAL-REQUIRED"],
  "approval_rules_matched": ["a_large_commitment"],
  "action_hash": "799f3e8418dba1c2201d20d0f2c4188994409a3cb00fbc566709ece4bab88441",
  "approval": "not_presented"
}
```

**Call** `issue_approval` with that hash. The approving principal signs with its own key, not the agent's:

```json
{
  "transaction_id": "txn_calibration_demo_02",
  "action_hash": "799f3e8418dba1c2201d20d0f2c4188994409a3cb00fbc566709ece4bab88441",
  "requested_by": { "...the buyer party..." },
  "approver": {
    "principal_id": "prn_northstar_procurement_director",
    "role": "procurement_director",
    "key_id": "key_northstar_principal_01"
  },
  "expires_at": "2026-08-20T11:00:00Z"
}
```

**Call** `verify_mandate` again with the identical `proposed_action` and the returned `approval_id`:

```json
{ "decision": "allow", "approval": "verified", "reason_codes": [] }
```

The second call is what the recording tool is given, and it must be made after the person has approved, not before. A decision is only good for 60 seconds when a recording tool takes it, which is the same bound the mandate document puts on cached revocation status: a decision made before a human was asked, and cached across the wait, is a decision about a mandate that may have been revoked while the wait was happening. Verify, ask, approve, verify again, then record.

Four things do not release the hold, and each returns the code that says why: an approval over a different act, which is `A202-APPROVAL-HASH-MISMATCH`; an expired one; one whose decision is `rejected`; and one from a role the rule did not name. An approval never releases a `deny`, because a denied constraint is a limit rather than a question.

## Where MCP ends and the A2A carrier binding begins

The two are different layers and neither substitutes for the other.

**MCP is the tool surface between an agent and its own A202 implementation.** It is local. A tool call is not a commercial act: it is how an agent asks its own software to construct, sign, record, or check one. Nothing in a tool call reaches a counterparty.

**A2A is the carrier between two agents.** [bindings/a2a-binding-v0.1.md](../../bindings/a2a-binding-v0.1.md) states how A202 objects travel over it: the extension is declared in the agent card, each object travels as one message part whose bytes are byte-identical to its canonical form, signatures cover those bytes and never the carrier framing, and correlation to a transaction is carried by `transaction_id` inside the signed object rather than by any task or context identifier. Declaration handling is implemented in [a202_reference/extension.py](../a202_reference/extension.py), which is where a party builds its own declaration and checks a counterparty's before sending anything.

The two meet at the object. Every object this server signs is exactly what the binding carries, because both are the canonical bytes of the canonical model, and this server writes nothing carrier-shaped into them. Section 6.2 of the binding holds here as it holds everywhere: a carrier event is not a commercial event, and neither is a tool call. What moves a transaction is a signed, authorized event that satisfies its guard.

The practical sequence for an implementer holding both: check the counterparty's declaration with `check_counterparty` from `a202_reference.extension`, use this server to produce and sign the object, send its canonical bytes over the carrier, and use `verify_evidence` on what comes back.

## Design notes

**Nothing is recorded that was not authorized.** Every recording tool takes the decision a prior `verify_mandate` call produced for that exact act, and writes it into the record as the policy decision the event cites. The decision recorded is the one that was made: its value, its reason codes, and the mandate it evaluated. Five things place it, and each refuses with the code that names it: the decision claims an allow, it was made over these exact act bytes, it evaluated a mandate this server holds, that mandate's subject is the acting agent, and it is no older than the status cache bound.

None of those five makes the verdict true. A presented decision is an unsigned document written by the party the mandate constrains, so the verdict is **recomputed** from the mandate and the act before anything is written, and a presented decision that disagrees with the recomputation is refused. What the presented decision is still needed for is what it alone carries: which approval released a hold, and the reasons the acting party recorded. One input is taken from it and only one, whether the status endpoint resolved, because this process makes no network call and that fact is the caller's to supply in either direction. A manufactured decision would be an attestation that a check happened when none did, which is worse than no decision at all, because a verifier reading the record cannot tell the two apart.

**Keys and state.** State is held in memory unless a directory is named, by `--state-dir` or `A202_MCP_STATE_DIR`. When a directory is named, shared objects, mandates, and public keys are written to it, so a record survives a restart and stays verifiable by a counterparty holding only the public half. Private keys are not written. They are generated on first use of a key identifier, held in memory for the life of the process, and never returned by a tool, never included in a result, and never placed in a log line or an error message. A restarted process refuses to sign under a key identifier it no longer holds rather than minting a second key under the same name: two keys under one identifier would make every earlier signature unverifiable against the later one. A demonstration surface that wrote private keys to a directory would be a worse one. The key bindings that tie a key identifier to the agent or principal that owns it are written to `keys/key-bindings.json` and are not themselves authenticated, so write access to a party's state directory permits misbinding an identity: tampering with a recorded object is caught by verification, and tampering with this file is not.

**Refusals are results, errors are errors.** A refused act returns `{"outcome": "refused", "reason_codes": [...]}` carrying the registered A202 codes that refused it, and the MCP result sets `isError`, because nothing was recorded and a caller reading it as success will carry on as though something was. A verification report never sets `isError`, however many checks failed: a report that finds a failure has succeeded at its job. An unknown tool name raises, which is a protocol error rather than a commercial one. Every result carries both `structuredContent` and the same JSON as a text block.

**No network call.** The server resolves nothing over the wire. A mandate's status endpoint is resolved by the caller, which passes the result and the time it was retrieved. Absent, older than the 60 second pilot cache bound, or anything other than `active` denies. Unavailability is not permission.

**No overall boolean.** `verify_evidence` returns per-check results of `verified`, `failed`, or `not_checkable` and no summary boolean, because a report reduced to a boolean discards the not-checkable set, which is a refusal in its own right.

**Nothing operated.** There is no invitation onboarding, no key custody, no negotiation room, no session stream, no award, and no venue-issued determination. Those capabilities are specified in the same set and belong to `a202-scope/operated/0.1`. A bilateral implementation that never exercises one has skipped nothing it needed.

**Where the identifiers come from.** No schema host, schema path, or schema identifier is written anywhere in this package. A test sweeps every Python file in the package, including its tests, and fails on any line carrying a URL or the schema host, with an allowlist holding only the synthetic mandate status endpoints the tests present as input data. The schema set is `a202_reference.schemas.SchemaSet`; the mandate specification version is read from the constraint the mandate schema itself states; the registered profiles are the ones the schema directory resolves; the registered constraint types, constraint operators, evidence types, rejection reasons, role scopes, and rule set versions are the repository's conformance runner's; and the runner is located through the repository root that `a202_reference.schemas` already resolved. A rename of the schema host, or a move of the schema directory, reaches this package with no change to it.

**One gate, not two.** Every object this server emits passes the published kernel schema and the published cross-object checks before it enters the record, using the same runner that judges the published fixture set. An object this server records is an object the public gate accepts.

**One process, both roles.** A single server holds every key it is asked to sign with, which is what lets one machine demonstrate both sides of a bilateral exchange. Events carry both parties' signatures, which is the shape of the countersignature section 8.1 of the state machine describes, and the shape is all it is: nothing here establishes that two organisations independently held those keys or independently kept the record. A deployment where each organisation runs its own instance gets that property from the deployment.

### Recorded limitations

Each of these is known, is not fixed, and is stated here rather than left for a reader to discover.

1. A constraint's `type` is carried and checked against the registered list, and is not used to check that the operator suits it. A `commercial.integer` constraint does not enforce integrality, so a fractional value satisfies a whole-number limit.
2. The evaluator parses decimals with Python's full decimal grammar. `4e3`, `1_000`, and `+4000` are accepted as numbers and compare as their values, which is wider than the base-10 string grammar the canonical model states. Non-finite values are refused: `NaN` and `Infinity` deny.
3. `verify_evidence` executes the seven steps over whatever bundle it is given, including one carrying operated-scope objects, and stamps its result with `a202-scope/bilateral/0.1`. The stamp describes the surface this server exposes, not the provenance of the bundle it was handed. It is not a finding about the objects verified.
4. `get_transaction_record` on a transaction this server has never seen returns an empty record in state `draft`, which is the same shape as a transaction that exists and has not moved. The two are not distinguished.
5. `issue_approval` signs the approval and then puts it through the published gate, where `issue_mandate` runs the gate first and signs only what passed. A refused approval is not recorded either way, and the order is inconsistent between the two.

## Running the tests

From `reference/`:

```bash
python3 -m unittest discover -s a202_mcp -t . -v
```

Every tool handler is covered in the allow direction and in at least one refuse direction: a mandate over its spending limit, a mandate whose status did not resolve, a mandate altered after signing, an approval over a different act, an expired approval, an approval against a denied constraint, a second formation on one transaction, formation under a rules version that never registered it, an assertion with no evidence, a response signed by the obligor, a partial acceptance with no remainder, a tampered evidence bundle, and a record whose links do not form one chain.

`tests/test_review_regressions.py` holds the reproductions an adversarial review of this package produced, one class per finding: an agreement recorded under a mandate nobody issued, a decision reused across acts, an approval signed with the acting agent's own key, an approval replayed from another transaction, a constraint hold released by an approver from another organisation, hostile values that used to raise instead of denying, and a status result dated in the future.

Two of the tests drive the server the way a client does, over a stdio subprocess: they list the tools, run the whole flow through the transport, and check the refusal convention on the wire. They need the MCP SDK and skip without it:

```bash
uv run --python 3.12 --with mcp --with jsonschema --with cryptography \
  python -m unittest discover -s a202_mcp -t . -v
```
