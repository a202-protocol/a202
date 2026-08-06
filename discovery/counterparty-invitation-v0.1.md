# Counterparty invitation v0.1

**Status:** Experimental working specification. Mixed. Sections 2, 4, 5, 6, 7, 8, 9, 10, and 12 are **normative**. Sections 1, 3, and 11 are **informative** and state no requirement on an implementation.

**Date:** 26 July 2026

**Scope:** Synthetic pilot onboarding only

## 1. Purpose

This specification defines how an organization that has never registered with A202, and may have no agent infrastructure at all, enters one named transaction because a counterparty invited it.

A202 v0.1 previously assumed both parties were already registered. Every entry point to the transaction state machine began after an organization, a principal, a root mandate, and an agent key existed. Nothing said how they came to exist for a party that did not seek them out.

The specification answers three questions and refuses a fourth.

1. How does an unregistered party receive and prove a right to participate?
2. How does that party acquire commercial authority without the operator manufacturing it?
3. How can the operator host a party that has no infrastructure, without becoming that party?

The refused question is whether an invitation can shortcut authority. It cannot. An invitation is a grant of participation. Authority is issued only by the invited party's own principal.

### 1.1 Relationship to the kernel

Invitation is onboarding, not commerce. It creates no offer, no agreement, no commitment, and no obligation. Its only effect on the transaction aggregate is that a candidate counterparty comes to exist where none existed.

It is market-neutral: no field here is meaningful in only one transaction profile. Adding these objects is a kernel change but not a transaction-profile change, so the kernel's market-neutrality property is unaffected. The neutrality probe in [canonical-commercial-model-v0.1.md](../schemas/canonical-commercial-model-v0.1.md) section 8 tests profiles, not object count.

## 2. Conformance language

`MUST`, `MUST NOT`, `REQUIRED`, `SHOULD`, `SHOULD NOT`, and `MAY` are normative within this experimental specification.

An implementation conforms to this specification when it:

1. validates `counterparty_invitation` and `invitation_acceptance` objects against `../schemas/v0.1/commercial-kernel.schema.json`;
2. enforces every invariant in section 9;
3. enforces the transitions in section 6 and in `../negotiation/pilot-transaction-state-machine-v0.1.md` section 5;
4. enforces the invited-party mandate rules in `../authority/commercial-mandate-v0.1.md` section 11;
5. passes the invitation fixtures in `../conformance/manifest-v0.1.json`.

## 3. The bootstrap problem

An unregistered party cannot sign an `ActionEnvelope`. The envelope's `created_by` is an `ActorRef` requiring an organization, an agent, and a mandate. The invited party has none of the three. This is not an oversight in the envelope design; it is the design working, and it is the reason invitation needs its own specification rather than a new action type.

Three resolutions were available.

| Resolution | Effect |
|---|---|
| Relax `ActorRef` so an unauthenticated actor may author objects | Creates a second, weaker authoring path into the kernel. Every later reader has to ask which path an object came through. Rejected. |
| Have the operator issue the invited party an organization, principal, and mandate | Completes the chain by forging it. Rejected: if the operator can complete a counterparty's authority chain, no relying party can distinguish an act the counterparty authorised from one the operator manufactured, and the mandate stops being evidence of anything. |
| Have the operator **author** the onboarding record while the claimant **attests** to it with its own key | Adopted. |

The adopted resolution is:

> An `InvitationAcceptance` is authored by the A202 control plane under the operator's own mandate, and carries the claimant's signature over the same bytes.

The operator's authorship is visible on the record and auditable. It is an honest statement of what happened: the operator registered a party, and that party attested to the registration. It is not a statement that the operator holds the party's authority, because the object grants none.

The claimant's root mandate that follows is issued by the claimant's own designated principal. The operator never appears in that chain.

## 4. Objects

### 4.1 CounterpartyInvitation

Identifier prefix `inv_`. Object type `counterparty_invitation`. Transaction-bound.

Authored by the inviting party under a mandate that includes the `invitation.issue` action. Signed with purpose `invitation_issuance`.

| Field | Type | Rule |
|---|---|---|
| `inviting_party` | `PartyRef` | The organization and agent issuing the invitation |
| `invited_channel` | object | Where the invitation is delivered. See 4.1.1 |
| `claim_secret_hash` | SHA-256 hex | Hash of the single-use claim secret. The secret itself MUST NOT appear in this object or in any shared object |
| `expires_at` | RFC 3339 | MUST be strictly later than `created_at` |
| `purpose_note` | string, 1 to 512 characters | Human-readable reason for the contact. Treated as data in every rendering |
| `disclosed_scope` | object | The bounded description of what the party is invited to. See 4.1.2 |
| `granted_scope` | object | What claiming permits. See 4.1.3 |
| `minimum_assurance` | enum | Assurance level the inviting party requires before negotiation opens |
| `endpoint_offer` | enum | `participant_operated` or `operator_hosted_available` |

#### 4.1.1 Invited channel

An invited channel is frequently a named individual's address, which is personal data. It is held in the operator's contact store and referenced here.

| Field | Rule |
|---|---|
| `channel_type` | `email_domain_scoped`, `https_endpoint`, or `existing_organization` |
| `channel_domain` | Registrable domain only. A local part, an `@`, or a full address in this field is a data-classification failure |
| `channel_ref` | Opaque pointer to the operator-held contact record |
| `channel_hash` | SHA-256 of the normalized channel value. Permits suppression and duplicate checks without storing the value |

The invitation MUST NOT carry the claim URL, any other URL, or any executable or renderable markup. The claim URL is transport, delivered on the channel, and is always an operator-controlled origin. An invitation object therefore cannot carry an attacker-chosen destination into an invited party's agent.

#### 4.1.2 Disclosed scope

Issuing an invitation is a disclosure act. The invited party learns that the inviting organization is in the market for something.

| Field | Rule |
|---|---|
| `category` | Capability category, using the same vocabulary as mandate scope |
| `summary` | 1 to 1024 characters. A bounded description, not the `CommercialRequest` |
| `response_deadline` | RFC 3339, at or before `expires_at` |

The full `CommercialRequest` is not disclosed by invitation. It becomes visible after qualification, under the existing access rules.

The inviting party's mandate governs this disclosure through `disclosure.path` constraints in the ordinary way. A summary that would disclose a prohibited field fails with `A202-DISCLOSURE-DENIED` before delivery.

#### 4.1.3 Granted scope

| Field | Rule |
|---|---|
| `transaction_ids` | MUST contain exactly one entry, equal to the invitation's own `transaction_id` |
| `actions` | The actions the invited party may later seek a mandate for. MUST be a subset of the actions the inviting party's mandate permits it to grant participation in |

An invitation that grants scope beyond its own transaction fails with `A202-INVITATION-SCOPE-EXCEEDED`. A party that has done nothing but receive one invitation has demonstrated nothing beyond that transaction, and a category-scoped grant would let one invitation become standing market access.

### 4.2 InvitationAcceptance

Identifier prefix `ina_`. Object type `invitation_acceptance`. Transaction-bound.

Authored by the A202 control plane under the operator mandate, per section 3. Requires at least two signatures: the claimant's key with purpose `invitation_claim`, and the operator's key with purpose `object_issuance`. An acceptance carrying only one of the two is not an onboarding record.

| Field | Type | Rule |
|---|---|---|
| `invitation_id` | `inv_` reference | The invitation being claimed |
| `invitation_hash` | SHA-256 hex | MUST equal the invitation's `content_hash`. Binds the claim to exact bytes, as an `Acceptance` binds an offer |
| `claimant` | object | `organization_id`, `agent_id`, `principal_id`, all newly registered or pre-existing and authorized |
| `channel_proof` | object | `method`, `verified_at`, and an optional evidence reference |
| `assurance` | enum | `self_asserted`, `credential_verified`, or `entity_bound` |
| `assurance_evidence_refs` | array | MUST be non-empty for any level above `self_asserted` |
| `key_custody` | enum | `self` or `operator_custodied` |
| `endpoint_mode` | enum | `participant_operated` or `operator_hosted` |
| `issuance_approval_id` | `apr_` or null | REQUIRED and non-null when `key_custody` is `operator_custodied` |
| `root_mandate_id` | `mnd_` reference | The mandate issued by the claimant's own principal |

Onboarding is complete when this object exists. Before it exists the party cannot act; after it exists the party can act only within its own root mandate.

## 5. Claim flow

```text
1. Inviting agent proposes invitation.issue in a signed ActionEnvelope.
2. Policy evaluator checks the inviting mandate, disclosure constraints,
   rate limit, and suppression list. Deny is private to the inviter.
3. Kernel mints the CounterpartyInvitation and appends invitation.issued.
4. Operator generates the single-use claim secret, stores only its hash
   on the object, and delivers the secret on the invited channel.
5. Invited party presents the secret at the operator claim endpoint.
6. Operator verifies the secret, the channel proof, and expiry, all with
   uniform responses on every failure.
7. Invited party registers an Organization, designates a Principal, and
   binds an Agent key, either self-held or operator-custodied.
8. The claimant's Principal issues the root CommercialMandate, bounded
   to this transaction. Under operator custody, this requires a human
   Approval bound to the mandate content hash.
9. Kernel mints the InvitationAcceptance, carrying the claimant's
   signature and the operator's, and appends invitation.claimed.
10. The claimed party is now a qualification candidate. Nothing else has
    changed. No offer, no session, no obligation.
```

Step 4 is the only point at which the claim secret exists outside the claimant's possession, and it is never written to a shared object. Step 6 is the enumeration boundary. Step 8 is the authority boundary.

### 5.1 Uniform failure

The claim endpoint MUST return an indistinguishable response for an unknown secret, an expired invitation, a revoked invitation, an already-consumed invitation, and a secret presented against the wrong channel. Response body, status code, and timing MUST NOT differ.

A distinguishable failure turns the claim endpoint into an oracle that tells an attacker which invitations exist and which are live. The response is `A202-INVITATION-UNCLAIMABLE` in every case, and the specific reason is recorded only in the operator record.

### 5.2 Claiming into an existing organization

An invitation whose `channel_type` is `existing_organization` targets a party A202 already knows. Claiming it MUST require authorization from that organization's existing principal, through the ordinary approval path.

Without this rule, an invitation would be a mechanism for attaching an attacker-controlled key to somebody else's registered organization. With it, an invitation to an existing party is a notification rather than an onboarding, which is the correct behaviour.

## 6. State and events

Invitation events are appended to the **transaction** stream.

| Current aggregate state | Event | Guard | Next |
|---|---|---|---|
| `published` | `invitation.issued` | Inviting mandate permits `invitation.issue`; disclosure constraints pass; rate limit and suppression pass; `expires_at` later than `created_at`; granted scope equals this transaction | `published` |
| `qualifying` | `invitation.issued` | As above | `qualifying` |
| `published` | `invitation.claimed` | Secret matches; invitation live; channel proof verified; root mandate issued and bounded to this transaction | `published` |
| `qualifying` | `invitation.claimed` | As above | `qualifying` |
| `published` or `qualifying` | `invitation.declined` | Declining party controls the channel | unchanged |
| `published` or `qualifying` | `invitation.expired` | Authoritative clock passed `expires_at` | unchanged |
| `published` or `qualifying` | `invitation.revoked` | Inviting mandate permits `invitation.revoke` | unchanged |

None of these transitions change aggregate state. An invitation is a fact about the market around a transaction, not a step in the transaction.

`invitation.claimed` is how a candidate comes to exist when the request audience is invited rather than public. The existing `published` to `qualifying` guard, "at least one candidate and qualification profile exist", is satisfied by a claimed invitation exactly as it is satisfied by a directory response.

### 6.1 Invitation is denied outside the pre-qualification window

Issuing an invitation from `draft` fails with `A202-STATE-TRANSITION-DENIED`. A request that is not published has no audience, and inviting a party to an unpublished request would disclose it outside the state machine.

Issuing an invitation once the aggregate has reached `negotiating` also fails. A late entrant would join a market that is already moving, which raises fairness and timing-disclosure questions this specification does not resolve. This is a v0.1 bound, listed in section 11, not a permanent position.

### 6.2 Isolation

An invited party learns that it was invited, by whom, and to what. It MUST NOT be able to learn that anyone else was invited, how many were, or whether any of them responded.

- Invitation events are readable by the inviting party and the operator.
- An invited party reads only its own invitation and its own acceptance.
- The invited party never reads the transaction stream. Its invitation is delivered to it, and its later activity is confined to its own session stream.
- Claim response timing, error codes, and delivery latency MUST NOT vary with the number of invitations issued on the same transaction.

This follows the reasoning in [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) section 8. Invitation deliberately does not get its own stream kind: a per-invitation stream would need sequencing, and any counter shared across invitations on one transaction is a covert channel of exactly the kind the per-session design exists to prevent.

## 7. Assurance

Assurance is reported. It is never inferred, and it is never raised by the passage of time or by successful transactions.

| Level | Established by | What it does not establish |
|---|---|---|
| `self_asserted` | Control of the invited channel | That the organization exists, that the claimant works there, or that anyone may bind it |
| `credential_verified` | A verified credential under the A202 VC profile | That the issuer is authoritative for the claim, or that a legal entity exists |
| `entity_bound` | Registry evidence such as GLEIF or vLEI, verified per the integration plan | Power to bind. Section 10 of the mandate specification already refuses this mapping |

An invited party enters at `self_asserted`. Raising the level requires presenting evidence, which produces a new acceptance version.

The level MUST be disclosed to the counterparty, and a mandate MAY set a floor with an `evidence.reference` or `commercial.string` constraint so that a buyer can refuse to negotiate below a level it chooses. `minimum_assurance` on the invitation is the inviting party's declared floor; the mandate constraint is what enforces it.

Declaring a level above `self_asserted` with no supporting evidence fails with `A202-ASSURANCE-UNSUPPORTED`.

## 8. Hosted endpoints and key custody

The operator MAY host an endpoint and custody a signing key for an invited party that has no infrastructure. Without this the invitation path reaches only parties that already run agent software, which is the smaller half of any real market.

Four rules bound it.

1. **An operator-custodied key MUST NOT sign a commercial act without a human `Approval`, issued by a named principal of the invited organization, bound to that exact action hash.** A hosted party operates in per-act approval mode until it presents a key it controls. The `Approval` object already binds one action hash and already invalidates on a one-byte change, so this reuses an enforced primitive rather than introducing a trusted path. The reason code is `A202-CUSTODY-APPROVAL-REQUIRED`.

2. **Custody and endpoint mode are disclosed to the counterparty.** A buyer negotiating with an operator-custodied supplier can see that it is doing so, and can set a mandate constraint refusing it.

3. **The operator runs no negotiation strategy for a hosted party.** The hosted endpoint renders proposals and collects human decisions. It does not evaluate, counter, concede, or optimize. The policy evaluator MUST NOT call a language model, which is already required by the mandate specification section 6, and the hosted endpoint inherits that prohibition.

4. **Operator signing without a bound approval is an incident, not an error.** It cannot occur through the write path, so its occurrence means the write path was bypassed. It opens an incident record rather than returning a reason code to a caller.

The conflict of interest is real: the operator runs the venue and would be holding one participant's key. Rules 1 and 3 are structural limits, not disclosures. Rule 2 is the disclosure. The residual risk, that the operator's key store is compromised and acts are forged, is bounded by rule 1: a forged signature alone does not move state, because the bound principal approval is missing.

## 9. Invariants that schema validation cannot express

| Invariant | Reason code |
|---|---|
| An invitation's `expires_at` is strictly later than its `created_at` | `A202-INVITATION-EXPIRED` |
| `granted_scope.transaction_ids` contains exactly the invitation's own `transaction_id` | `A202-INVITATION-SCOPE-EXCEEDED` |
| An acceptance's `invitation_hash` equals the referenced invitation's `content_hash` | `A202-INVITATION-HASH-MISMATCH` |
| An acceptance carries both a claimant `invitation_claim` signature and an operator `object_issuance` signature | `A202-INVITATION-CLAIM-UNSIGNED` |
| An assurance level above `self_asserted` is supported by at least one evidence reference | `A202-ASSURANCE-UNSUPPORTED` |
| `key_custody: operator_custodied` carries a non-null `issuance_approval_id` | `A202-CUSTODY-APPROVAL-REQUIRED` |
| The claim secret never appears in a shared object | `A202-INVITATION-SECRET-DISCLOSED` |
| A raw channel address never appears in a shared object | `A202-DISCLOSURE-DENIED` |
| An invited party's root mandate is scoped to the invitation's transaction only | `A202-INVITATION-SCOPE-EXCEEDED` |
| A single-use invitation is claimed at most once | `A202-INVITATION-UNCLAIMABLE` |

## 10. Abuse and anti-abuse

Invitation is an outbound messaging surface addressed at parties who did not ask to hear from it. An implementation MUST enforce every control below. They are mandatory rather than advisory, because each of them is the only thing standing between a legitimate onboarding path and a bulk-messaging channel with a signature on it.

| Control | Requirement |
|---|---|
| Mandate gate | `invitation.issue` is an explicit mandate action, deny by default like every other action |
| Rate limit | Per inviting organization, per transaction, and per invited domain. Exceeding it is a `deny`, private to the inviter |
| Suppression | A declined channel is suppressed permanently for that inviting organization. `channel_hash` makes this checkable without storing addresses |
| Permanent decline | An invited party can decline without claiming and without registering anything |
| Content bound | `purpose_note` and `summary` are length-bounded, carry no URL and no markup, and are marked as data wherever an agent renders them |
| Retention | An unclaimed invitation and its contact record are deleted after expiry plus a retention window set by privacy review |

The content bound narrows the prompt-injection surface. It does not close it. An invited party's agent still reads attacker-influenced free text, and the only structural defense here is that the text cannot carry a destination.

## 11. Open questions

- What channel proof is sufficient for `self_asserted`? A domain-scoped address is the current position. A shared mailbox at a large consumer provider is materially weaker and may need a lower sub-level.
- Should invitation be permitted once the aggregate reaches `negotiating`? Section 6.1 currently denies it. Permitting a late entrant needs a fairness rule and a timing-disclosure analysis first.
- Should the inviting party learn that an invitation was delivered, opened, or declined? Delivery and claim are needed. Open, and declined with a reason, may disclose more about the invitee than the invitation disclosed about the inviter.
- Does operator key custody create a controller or processor relationship, and in which jurisdiction? This is a legal question rather than a protocol question and is not answered here.
- Is per-act approval usable in practice, or does it make hosted participation too slow to adopt? This is a measurement that only deployment can settle.

## 12. Required tests

An implementation MUST be verified against each of the following. The first nine are static fixtures, in `../conformance/`:

1. Valid counterparty invitation.
2. Valid invitation acceptance.
3. Claim secret present in the shared object.
4. Expiry at or before issue.
5. Granted scope beyond the invitation's transaction.
6. Raw channel address in the shared object.
7. Assurance above `self_asserted` with no evidence.
8. Operator custody with no issuance approval.
9. Acceptance with a single signature.

The remainder require runtime state and cannot be expressed as static documents. They are verified against a running implementation:

10. End-to-end onboarding: an organization with no prior A202 presence receives an invitation, claims it, issues its own root mandate, negotiates, and reaches an agreement.
11. Invited party's root mandate scoped by category rather than transaction is refused.
12. Operator-custodied key attempts a commercial act with no bound approval and is refused.
13. Approval bound to a different action hash does not authorize the act.
14. Claim replayed after consumption is refused, with a response indistinguishable from an unknown secret.
15. Claim after expiry is refused, with the same indistinguishable response.
16. Claim against an existing organization without that organization's principal authorization is refused.
17. **Isolation:** an invited supplier cannot determine how many other invitations were issued on the same transaction, from response content, error codes, or timing.
18. Declined channel is suppressed and a second invitation from the same inviting organization is refused.
19. Rate limit exceeded produces a `deny` that is private to the inviter and consumes no shared sequence.
20. An invitation issued from `draft`, and one issued from `negotiating`, are both refused.
