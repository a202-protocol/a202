# Commercial mandate v0.1

**Status:** Experimental working specification. Mixed. Sections 2, 3, 4, 5, 6, 7, 8, 9, 11, and 12 are **normative**. Sections 1 and 10 are **informative** and state no requirement on an implementation.

**Date:** 25 July 2026

**Revised:** 26 July 2026. Added section 12, which bounds the root mandate of a party onboarded by invitation and forbids the operator from ever issuing it. Previous revision 25 July 2026 after conformance review.

**Security boundary:** Synthetic pilot authority only

## 1. Purpose

A commercial mandate states which organization an agent represents, which commercial actions it may take, under which constraints, for which transaction or market scope, and when human approval is required.

The mandate does not prove that a legal entity exists or that the issuer has legal power under applicable law. External identity and governance evidence supports those questions. A202 evaluates what the presented evidence and mandate mean within a pilot transaction.

## 2. Authority chain

```text
external organization evidence
  -> A202 Organization
  -> authorized Principal
  -> root CommercialMandate
  -> optional delegated CommercialMandate
  -> Agent key
  -> signed ActionEnvelope
  -> transaction action
```

Every link MUST be verifiable. Missing, expired, suspended, revoked, or scope-incompatible links fail closed.

## 3. Required fields

The normative machine schema is `../schemas/v0.1/commercial-mandate.schema.json`.

| Field | Meaning |
|---|---|
| `id` | Immutable mandate identifier |
| `issuer` | Principal and organization issuing authority |
| `subject` | Exactly one of: an agent, or a delegated principal |
| `represented_organization_id` | Organization represented in actions |
| `parent_mandate_id` | Delegation source, or explicit null |
| `valid_from` and `valid_until` | Closed authority interval |
| `status_endpoint` | Current suspension and revocation source. HTTPS only. |
| `actions` | Explicit allowed action names |
| `scope` | Transaction, capability category, counterparty, and geography limits |
| `constraints` | Deterministically evaluated commercial and disclosure rules. At least one. |
| `approval_rules` | Conditions requiring named human or role approval |
| `delegation` | Whether and how authority may be delegated |
| `evidence_refs` | Identity, role, policy, or authorization evidence |
| `proof` | Issuer signature over canonical content |

Actions are deny by default. An omitted action is not allowed.

### 3.1 Scope must bound authority

`scope` MUST contain `transaction_ids`, `categories`, or both. `counterparty_organization_ids` and `geographies` narrow an existing boundary; they cannot establish one.

A mandate scoped only to a country is not transaction-scoped. It authorizes an agent to act on any transaction of any value in that country, which is the control point A202 claims to solve rather than an example of it. This is rejected at validation.

### 3.2 A mandate with no constraints is rejected

An empty `constraints` array confers unbounded authority within the allowed actions. Deliberate absence of a limit MUST be expressed as an explicit permissive constraint so that it appears in the audit record and in any delegation-narrowing check.

### 3.3 Status endpoint transport

`status_endpoint` MUST use HTTPS. Cached status is the only channel by which a revocation reaches a relying party, and the pilot caps that cache at 60 seconds. Status served over plain HTTP is forgeable by a network attacker, which would make revocation unenforceable.

## 4. Constraint vocabulary

Each constraint contains `id`, `type`, `path`, `operator`, `value`, and `on_failure`.

Registered v0.1 types:

| Type | Applies to |
|---|---|
| `commercial.decimal` | Money amounts, percentages, decimal quantities |
| `commercial.integer` | Counts and whole-number limits |
| `commercial.string` | Currency codes, unit codes, enumerated terms |
| `commercial.boolean` | Binary terms |
| `commercial.timestamp` | Dates and deadlines |
| `commercial.set` | Membership over a declared set |
| `disclosure.path` | Presence or absence of a field in an outbound action |
| `evidence.reference` | Required evidence and its verification result |
| `counterparty.reference` | Counterparty organization identity |
| `geography.reference` | Site, delivery, or performance geography |

Registered v0.1 operators:

| Operator | Evaluation |
|---|---|
| `equals` | Proposed value equals required value |
| `not_equals` | Proposed value differs |
| `one_of` | Proposed value is in the allowed set |
| `none_of` | Proposed value is absent from the denied set |
| `minimum` | Numeric decimal is at or above the limit |
| `maximum` | Numeric decimal is at or below the limit |
| `matches` | String matches the registered regular expression |
| `present` | Required path exists |
| `absent` | Prohibited path does not exist |
| `before` | Timestamp is before the limit |
| `after` | Timestamp is after the limit |
| `evidence_verified` | Referenced evidence has a valid verification result |

Required failure modes:

- `deny`;
- `require_approval`.

Both registries are closed in v0.1. An unregistered type or operator is rejected at schema validation **and** evaluates to `deny` at runtime. Both layers are required and are tested independently: adding a type to the schema enum without an evaluator implementation MUST NOT cause an action to be allowed.

## 5. Pilot mandate example

```json
{
  "spec_version": "a202-mandate/0.1",
  "id": "mnd_northstar_buyer_01",
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
  "parent_mandate_id": null,
  "valid_from": "2026-07-25T00:00:00Z",
  "valid_until": "2026-08-25T00:00:00Z",
  "status_endpoint": "https://sandbox.a202.invalid/v1/mandates/mnd_northstar_buyer_01/status",
  "actions": [
    "intent.publish",
    "invitation.issue",
    "invitation.revoke",
    "qualification.request",
    "clarification.send",
    "offer.submit",
    "offer.accept",
    "agreement.sign",
    "settlement.instruct"
  ],
  "scope": {
    "transaction_ids": [
      "txn_calibration_demo_01"
    ],
    "categories": [
      "services.calibration"
    ],
    "counterparty_organization_ids": [
      "org_delta",
      "org_meridian"
    ],
    "geographies": [
      "NL"
    ]
  },
  "constraints": [
    {
      "id": "c_total_price",
      "type": "commercial.decimal",
      "path": "$.proposed_terms.core.total.amount",
      "operator": "maximum",
      "value": "4000.00",
      "on_failure": "deny"
    },
    {
      "id": "c_currency",
      "type": "commercial.string",
      "path": "$.proposed_terms.core.total.currency",
      "operator": "equals",
      "value": "EUR",
      "on_failure": "deny"
    },
    {
      "id": "c_prepayment",
      "type": "commercial.decimal",
      "path": "$.proposed_terms.profile_terms.payment.prepayment_percent",
      "operator": "maximum",
      "value": "20",
      "on_failure": "deny"
    },
    {
      "id": "c_budget_disclosure",
      "type": "disclosure.path",
      "path": "$.message.private_budget_ceiling",
      "operator": "absent",
      "value": true,
      "on_failure": "deny"
    }
  ],
  "approval_rules": [
    {
      "id": "a_new_counterparty",
      "when": {
        "path": "$.counterparty_organization_id",
        "operator": "none_of",
        "value": [
          "org_delta",
          "org_meridian"
        ]
      },
      "approver": {
        "organization_id": "org_northstar",
        "role": "procurement_director"
      },
      "expires_after_seconds": 3600
    }
  ],
  "delegation": {
    "allowed": false,
    "maximum_depth": 0
  },
  "evidence_refs": [
    "evd_northstar_org_identity_01",
    "evd_northstar_principal_role_01"
  ],
  "proof": {
    "key_id": "key_northstar_principal_01",
    "algorithm": "ES256",
    "created_at": "2026-07-25T00:00:00Z",
    "purpose": "mandate_issuance",
    "signature": "synthetic-placeholder-signature-value"
  }
}
```

The example uses the reserved `.invalid` domain and a placeholder signature. It MUST NOT be treated as a usable credential.

Constraint paths address the canonical terms structure defined in `../schemas/canonical-commercial-model-v0.1.md` section 8. A constraint that targets a profile-specific term addresses it under `profile_terms`, so a mandate written for one transaction profile cannot silently bind a different one.

## 6. Evaluation algorithm

For each proposed action:

1. Parse and schema-validate the `ActionEnvelope` and the mandate.
2. Authenticate the subject key and agent status.
3. Verify the mandate signature.
4. Resolve the mandate status endpoint.
5. Verify `valid_from <= now < valid_until`.
6. Resolve every parent mandate and verify the chain.
7. Confirm that each child action and constraint is equal to or narrower than its parent.
8. Confirm that the action appears in `actions`.
9. Confirm transaction, category, counterparty, and geography scope.
10. Resolve the transaction profile and validate the proposed terms against it.
11. Evaluate every constraint in stable order.
12. Evaluate approval rules.
13. Evaluate the transaction-state guard for the target stream.
14. Return one `PolicyDecision` bound to the envelope's `action_hash`:
    - `allow`;
    - `deny`;
    - `require_approval`.
15. Sign and persist the decision before any external transmission.

The evaluator MUST use decimal arithmetic for money and percentages. It MUST NOT call a language model.

### 6.1 Checks the schema cannot perform

These are enforced by the evaluator and covered by fixtures in `../conformance/`:

| Check | Reason code |
|---|---|
| `valid_from` strictly earlier than `valid_until` | `A202-MANDATE-INTERVAL-INVALID` |
| Child mandate narrower than parent on every axis | `A202-MANDATE-DELEGATION-WIDENING` |
| Unregistered constraint type or operator denies at runtime | `A202-MANDATE-CONSTRAINT-UNKNOWN` |
| Status endpoint reachable and fresh within the cache window | `A202-MANDATE-STATUS-UNRESOLVED` |
| Mandate still active at append time, not only at proposal time | `A202-MANDATE-INACTIVE` |
| An invited party's root mandate is bounded to the invitation's transaction | `A202-INVITATION-SCOPE-EXCEEDED` |
| An operator-custodied subject key carries an approval bound to the action hash | `A202-CUSTODY-APPROVAL-REQUIRED` |

If the status endpoint cannot be resolved, the decision is `deny`. Unavailability is not permission.

## 7. Delegation

A child mandate MUST:

- reference one parent mandate;
- have a shorter or equal validity interval;
- contain a subset of parent actions;
- contain equal or narrower scope;
- retain every parent `deny` constraint;
- tighten but never loosen a numeric limit;
- never increase delegation depth;
- use a subject permitted by the parent delegation rule.

Failure to prove monotonic narrowing returns `A202-MANDATE-DELEGATION-WIDENING`.

`delegation.allowed` and `delegation.maximum_depth` MUST be coherent: `allowed: false` requires depth `0`, and `allowed: true` requires depth of at least `1`. An incoherent pair is rejected rather than interpreted.

## 8. Approval

An approval MUST bind:

- exact action hash;
- transaction;
- approver identity and role;
- decision;
- created time;
- expiry time;
- any conditions;
- approver signature.

Changing one byte of the action invalidates the approval. An approval cannot be reused across actions or transactions.

## 9. Suspension and revocation

- `active`: New actions may be evaluated.
- `suspended`: New actions fail. The record can return to active through an authorized event.
- `revoked`: New actions fail permanently for this mandate version.
- `expired`: New actions fail because time is outside the validity interval.

Status changes MUST produce signed `RevocationRecord` events. Cached status responses MUST include an expiry no longer than 60 seconds in the pilot, and MUST be retrieved over HTTPS.

## 10. Interoperability notes

This section is an interoperability aid. It records how objects defined here line up with purchase-authorization constructs in an adjacent specification, so that an implementer holding both can see where a mapping is available and where it is lossy. It defines no requirement and asserts no equivalence.

### 10.1 Purchase authorization mandates

**Checked 25 July 2026:** AP2 v0.2 defines two mandate types, Checkout Mandate and Payment Mandate, both bound to purchase authorization. It does not define authority over disclosure, qualification, negotiation concessions, non-payment commercial terms, performance, or acceptance. A A202 commercial mandate therefore has no equivalent there and is not interchangeable with either type.

Where an implementation carries both, the nearest correspondence is:

| A202 | Nearest purchase-authorization construct |
|---|---|
| `CommercialMandate` | Open authorization source for commercial actions |
| Accepted `Agreement` hash | Checkout or purchase-detail binding input |
| `SettlementInstruction` | Payment mandate input |
| `PolicyDecision` | Deterministic constraint evaluation receipt |
| `AdapterReceipt` | Checkout or payment receipt reference |

The mapping is deliberately lossy, and each row names the nearest construct rather than an equivalent one. An implementation that relies on it must state the loss rather than let it pass silently.

## 11. Authority for a party onboarded by invitation

A party that enters through a [counterparty invitation](../discovery/counterparty-invitation-v0.1.md) has no principal, no mandate, and no key when the invitation arrives. This section states what it may hold once it claims.

### 11.1 The operator never issues it

The root mandate of an invited party MUST be issued by a principal the invited organization designated. The A202 operator MUST NOT appear anywhere in the chain, at any depth, as issuer or as delegator.

This is the load-bearing rule of the whole onboarding path. If the operator can complete a counterparty's authority chain, then "the kernel refuses the act because the mandate was revoked" becomes "the kernel refuses the act unless the operator prefers otherwise," and the control point A202 claims stops existing. The operator may author the onboarding record, because the claimant has no mandate with which to author anything, and it may custody a key. It may not be the source of authority.

### 11.2 Bounded to the invitation

An invited party's root mandate MUST satisfy all of:

- `scope.transaction_ids` contains exactly the invitation's transaction, and `scope.categories` is absent;
- `actions` is a subset of the invitation's `granted_scope.actions`;
- `valid_until` is at or before the invitation's `expires_at` plus the transaction's own deadline, whichever is earlier;
- `delegation.allowed` is `false` and `maximum_depth` is `0`.

Failure returns `A202-INVITATION-SCOPE-EXCEEDED`.

A party that has received one invitation has demonstrated nothing beyond that transaction. A category-scoped root mandate would turn a single invitation into standing market access, which is the same failure that section 3.1 rejects for geography-only scope, arriving by a different route.

Standing authority is reached the ordinary way: the organization registers properly, presents evidence, and its principal issues a wider mandate. Invitation is an entry, not a shortcut.

### 11.3 Operator key custody requires per-act approval

When the subject key is operator-custodied, every action under the mandate requires a human `Approval` from a named principal of the invited organization, bound to that exact action hash.

The mandate MUST therefore carry an approval rule matching every action:

```json
{
  "id": "a_custodied_key_all_actions",
  "when": {
    "path": "$.action_type",
    "operator": "matches",
    "value": "^[a-z][a-z0-9_]*(\\.[a-z][a-z0-9_]*)+$"
  },
  "approver": {
    "organization_id": "org_helix",
    "role": "managing_director"
  },
  "expires_after_seconds": 3600
}
```

The evaluator MUST enforce the requirement independently of whether the rule is present. A missing rule is not permission, and the reason code is `A202-CUSTODY-APPROVAL-REQUIRED`.

Section 8 already establishes that changing one byte of an action invalidates its approval, and that an approval cannot be reused across actions or transactions. Custody inherits both properties, which is why this reuses `Approval` rather than adding a trusted signing path. A forged operator signature alone does not move state, because the bound principal approval is missing.

### 11.4 Assurance is a constraint input, not a mandate property

The assurance level of a counterparty is recorded on its `InvitationAcceptance`, not on its mandate. A relying party sets a floor with an ordinary constraint, for example an `evidence.reference` constraint with `evidence_verified`, or a `commercial.string` constraint over the counterparty's recorded level.

Assurance is reported and never inferred. A mandate does not become stronger because the transactions under it succeeded.

## 12. Required negative tests

An implementation MUST refuse each of the following. The first eight are expressed as static fixtures under `../conformance/fixtures/v0.1/negative/`:

1. Mandate with no constraints.
2. Scope bounded only by geography.
3. Incoherent delegation pair.
4. Inverted validity interval.
5. Status endpoint over plain HTTP.
6. Unknown constraint type.
7. Unknown constraint operator.
8. Ambiguous subject naming both an agent and a principal.

Delegation narrowing is additionally expressed as static fixtures of kind `mandate_chain`, each carrying a parent and child pair: a valid chain narrowed on every axis, and one widening fixture per axis for the validity interval, the action set, the scope, and a numeric limit. Each widening fixture is refused with `A202-MANDATE-DELEGATION-WIDENING`. Tests 20 to 22 below therefore have static counterparts; their runtime forms remain required because a live implementation must also refuse the act, not only the document pair.

The remainder require runtime state and cannot be expressed as static documents. They are verified against a running implementation:

9. Invalid issuer signature.
10. Subject key mismatch.
11. Expired root mandate.
12. Suspended child mandate.
13. Revoked agent key.
14. Missing action.
15. Counterparty outside scope.
16. Category outside scope.
17. Amount over limit.
18. Prepayment over limit.
19. Prohibited disclosure path.
20. Child validity exceeds parent.
21. Child action absent from parent.
22. Child constraint loosens a limit.
23. Approval expired.
24. Approval action-hash mismatch.
25. Mandate revoked between proposal and append.
26. Status endpoint unreachable.
27. Invited party's root mandate scoped by category rather than by the invitation's transaction.
28. Invited party's root mandate permitting delegation.
29. Invited party's root mandate carrying an action absent from the invitation's granted scope.
30. Operator named as issuer or delegator anywhere in an invited party's chain.
31. Operator-custodied key acting with no approval bound to the action hash.
32. Operator-custodied key acting with an approval bound to a different action hash.
