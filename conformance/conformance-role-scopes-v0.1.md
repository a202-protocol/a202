# Conformance role scopes v0.1

**Status:** Experimental, adopted through proposal [A202-0006](../proposals/A202-0006-bilateral-conformance-role-scopes.md). Mixed. Sections 2, 3, 4, 5, 6, 7, and 8 are **normative**. Sections 1, 9, and 10 are **informative** and state no requirement on an implementation.

**Date:** 27 July 2026

**Revised:** 30 July 2026, under [A202-0015](../proposals/A202-0015-fixture-minimality-orphan-codes-and-grade-scope.md): the fixture plan of [A202-0006](../proposals/A202-0006-bilateral-conformance-role-scopes.md) section 5 implemented, so that the three refusal codes in section 8 are raised by an evaluator rather than named in a table. A conformance-grade family joins section 4.3 and section 5.3, family identifiers are stated for the grade object's coverage members, and item 6 of section 2 names the fixtures it requires. No scope identifier, capability, or section assignment changes. Also revised 30 July 2026, under [A202-0014](../proposals/A202-0014-bilateral-formation-and-scope-repair.md): the bilateral scope made true against the claim in section 4.4, following the specification review of 30 July 2026. The direct formation path enters the bilateral scope, the fixture families are split by authorship so that no bilateral family holds an operator-issued object, the partition is made total and disjoint over every fixture on disk, the invariants named in section 5.2 are cited by reason code rather than by nickname, and the appeal-route claim in section 7.1 is stated as the open question it is. The two scope identifiers mean what they meant. Previously revised 28 July 2026, under [A202-0009](../proposals/A202-0009-enforcement-fidelity.md): the fixture partition restated by family pattern so that it covers the whole manifest and stops going stale as the set grows.

**Scope:** Synthetic pilot transactions only

**Depends on:** [conformance grades v0.1](conformance-grades-v0.1.md), [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md), [commercial mandate v0.1](../authority/commercial-mandate-v0.1.md), [obligation v0.1](../agreement/obligation-v0.1.md), [evidence verification v0.1](../evidence/evidence-verification-v0.1.md), [pilot transaction state machine v0.1](../negotiation/pilot-transaction-state-machine-v0.1.md), and the fixture set, [manifest](manifest-v0.1.json), and [runner](run-conformance.py) in this directory

**No external body recognises anything defined here.** A scope identifier defined in this document names a set of specification sections and fixtures. It is not an accreditation, a certification class, or a licence, and no material may describe it as one.

## 1. What this document is for

The specification set defines capabilities of two different kinds and does not currently say which is which.

Some capabilities are exercised by exactly two organisations. A principal issues a mandate and the counterparty verifies it, checks its status endpoint, and refuses an act outside it. Two parties form an agreement over one offer hash, decompose it into obligations, assert and respond to performance, and verify each other's records by executing the published verification procedure. Nothing in any of that requires a third party to be present, to hold a key, or to sign anything.

Other capabilities do not exist without an operator. An invitation acceptance is authored by a control plane under the operator's own mandate, because the claimant has no mandate with which to author anything. A negotiation session stream is created and ordered by something that is neither of the two parties. An award among rival sessions contends on a stream that no single participant holds. A determination issued by a venue is issued by the venue.

Both kinds are specified here, and a grade issued against the specification set today does not say which of the two it covers. This document names the two sets so that a grade can say, and so that two organisations can point at a bounded surface and adopt it between themselves.

The division is descriptive. It reclassifies nothing, changes no rule, and states no preference for either scope. A capability is in the operated scope because the specification says an operator authored, ordered, or issued something, and for no other reason.

## 2. Conformance language

`MUST`, `MUST NOT`, `REQUIRED`, `SHOULD`, `SHOULD NOT`, and `MAY` are normative within this experimental specification.

An implementation that issues or consumes a conformance grade conforms to this document when it:

1. names exactly one role scope identifier from section 3 in the `scope` field of every grade it issues;
2. refuses a grade whose role scope identifier does not resolve in the registry in section 3, under section 3.2;
3. reports, under section 6, every dimension that the named scope does not cover as unassessed rather than as a band;
4. treats the absence of a grade in a scope as unassessed rather than as a pass, under section 6.4;
5. returns the refusal codes in section 8 for the failures they name;
6. passes the conformance-grade family of [manifest-v0.1.json](manifest-v0.1.json), which is the row of that name in section 4.3 and in section 5.3: two grades in the allow direction, one per scope, and five refusals covering each of the three codes in section 8.

This document adds no object, no field, no state, no transition, and no guard. It defines a closed registry for a field that already exists.

## 3. The role scope registry

### 3.1 Registered identifiers

Two role scopes are registered in v0.1. The registry is closed in v0.1.

| Identifier | Name | What an assessment against it establishes |
|---|---|---|
| `a202-scope/bilateral/0.1` | Bilateral scope | The implementation issues, verifies, and refuses the objects that two organisations exchange directly, with no operator present and no operator-issued object in any chain it relies on |
| `a202-scope/operated/0.1` | Operated scope | The implementation issues, orders, verifies, and refuses the objects and streams whose authorship, ordering, or issuance the specification set assigns to an operator or a control plane |

A role scope identifier is a long-lived commitment. It is resolved by consumers of a grade, so an identifier registered here is never reused for a different meaning and never removed once a grade has been issued against it.

### 3.2 An unrecognised identifier fails closed

1. A grade's `scope` field MUST name exactly one role scope identifier from section 3.1, alongside whatever transaction profile and transport coverage that field also carries under [conformance-grades-v0.1.md](conformance-grades-v0.1.md) section 4. This document is the registry for the role part of that field and changes nothing else about it.
2. A consumer that reads a role scope identifier which does not resolve in section 3.1 MUST refuse the grade with `A202-GRADE-SCOPE-UNKNOWN`. It MUST NOT fall back to the other registered scope, to a nearest match, or to an unscoped reading.
3. A grade naming no role scope identifier, or naming more than one, MUST be refused with `A202-GRADE-SCOPE-INVALID`. A grade that covers both scopes is two grades.
4. Refusal is refusal of the grade, not a band 0. A grade that cannot be read tells a relying party nothing, and recording it as a failure would tell it something false.

This matches the treatment of every other closed registry in the set: an unregistered transaction profile, constraint type, constraint operator, evidence type, or due condition type fails closed rather than resolving to a default.

### 3.3 Adding a scope

Adding a role scope identifier is a change to this registry and requires a proposal under [proposals/README.md](../proposals/README.md). Under [RELEASES.md](../RELEASES.md) section 2 an addition that leaves both registered identifiers meaning what they mean today is a MINOR change. Changing what a registered identifier covers is a MAJOR change, because a grade already issued against it would afterwards claim something its assessment did not establish.

## 4. The bilateral scope

`a202-scope/bilateral/0.1`

### 4.1 Capabilities in this scope

1. **Mandate issuance and verification.** Issuing a root or delegated mandate, parsing a counterparty's mandate, verifying the issuer signature, verifying the chain, proving monotonic narrowing at every hop, evaluating the constraint vocabulary, and refusing an act outside `actions`, `scope`, or a constraint.
2. **Revocation status checking.** Resolving a mandate's status endpoint over HTTPS, respecting the cache bound, and denying when the endpoint does not resolve.
3. **Approval binding.** Binding a human approval to one exact action hash, and refusing a reused or altered one.
4. **Agreement formation between two parties.** An offer that is current and unexpired, carrying a session identifier the offeror minted and the counterparty adopted; an acceptance over the exact offer hash; entry to `agreement_pending` through `agreement.direct` with no publication, qualification, or negotiation room; an agreement whose terms hash equals the accepted offer's; and both parties' signatures over the same agreement bytes.
5. **Obligation exchange.** Deriving obligations from a committed agreement, typed due conditions, assertion by the obligor with at least one evidence reference, response by the obligee bound to the assertion hash, partial acceptance with a named remainder, rejection with a registered reason code, and the guarded transitions between those states.
6. **Evidence reference resolution and the seven-step verification procedure.** Emitting evidence references in the structured shape, and executing steps 1 to 7 of [evidence-verification-v0.1.md](../evidence/evidence-verification-v0.1.md) section 4 over records a counterparty produced, with the three-valued output and the selective disclosure rules.
7. **Settlement handoff.** Issuing a settlement instruction triggered by a commercial act hash, refusing an unregistered rail, refusing a custodial route, and treating an adapter receipt as evidence rather than as authority.
8. **Refusal behaviour on everything above.** Malformed, hostile, unregistered, and unanticipated input against every object family in this scope.

### 4.2 Specification sections in this scope

| Document | Sections in scope | What an implementation demonstrates |
|---|---|---|
| [canonical-commercial-model-v0.1.md](../schemas/canonical-commercial-model-v0.1.md) | 2 and 15 in their bilateral reading, 3, 4, 7, 8, 9 other than the `kernel_annotations` clause of step 4, 9.1, 9.2, 10, 10.1, 13, 14, and the invariants in 12 other than those named in section 5.2 of this document | Envelope, canonicalisation, signature rules, money and quantity representation, profile resolution, action and policy ordering with each party evaluating its own actions, agreement formation and amendment, and the private strategy boundary |
| [commercial-mandate-v0.1.md](../authority/commercial-mandate-v0.1.md) | 2, 3, 3.1, 3.2, 3.3, 4, 5, 6, 6.1, 7, 8, 9, and required negative tests 1 to 26 in section 12 | The whole authority chain other than the invitation-onboarded path |
| [obligation-v0.1.md](../agreement/obligation-v0.1.md) | 2, 3, 3.1, 4, 5, 5.1, 5.2, 5.4, 5.5, 6, 6.1, 6.2, and 7 | The complete obligation lifecycle. Every act in it is signed by the obligor or the obligee |
| [evidence-verification-v0.1.md](../evidence/evidence-verification-v0.1.md) | 2, 3, 3.1, 3.2, 4 steps 1 to 7, 5, 6, and 8 | The evidence reference shape and the verification procedure, subject to the two limits in section 4.4 |
| [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) | 1, 3 for `draft` and for the states from `agreement_pending` onward, 5 for the `agreement.direct` row and for the transitions from `agreement_pending` onward, 5.2, 5.3, 6, 6.1, 6.2 other than the operated selection stated in its last three paragraphs, 7, 8.1, 9, 10, and required tests 4 to 6, 8 to 14, 22 to 25, 26, and 27 in section 11 | Direct formation, the session state machine, the offer rules, the commitment, performance, amendment and termination transitions, the dual-held transaction record, and replay |
| [determination-v0.1.md](../disputes/determination-v0.1.md) | 2 in its bilateral reading, 3 other than a dispute whose respondent is the venue operator, 4, 4.1, 4.2, 4.3, 5, 6, and 9 | Raising a dispute against a counterparty, issuing a determination as the determiner the rules in force name, and checking whether a determination follows from its rules and inputs |
| [settlement-handoff-v0.1.md](../fulfillment/settlement-handoff-v0.1.md) | 2, 2.1, 2.2, 2.3, 3, 3.1, 3.2, 4, 4.1, 4.2, 5, 6, and 7 | The handoff interface. A payment rail is an external system, not an operator, and no rule in these sections requires a party other than the payer and the payee |
| [transaction-profile-extension-model-v0.1.md](../schemas/transaction-profile-extension-model-v0.1.md) | Profile resolution and validation as exercised by section 8 of the canonical model | Two parties referencing the same profile version, and failing closed on one that does not resolve |
| [conformance-grades-v0.1.md](conformance-grades-v0.1.md) | 2, 3, 4, 5, and 6, read under section 6 of this document | Grade emission and consumption, with the dimension reading this document fixes |

### 4.3 Fixtures in this scope

The partition is by family pattern, not by enumerated filename. A fixture added to a family below joins this scope with no change to this document; only a fixture that starts a new family requires a placement decision, which is made by the proposal that adds it. An earlier revision enumerated filenames with restated counts, and the enumeration was stale within a day of the fixture set growing; the pattern form is what stops that recurring.

The manifest is the source for how many fixtures each scope holds; a count restated here would go stale on the next addition, which is the defect this revision removed.

The patterns in this section and in section 5.3 are read as filename globs against the fixture set, and together they are **total and disjoint**: every fixture on disk matches at least one pattern, and no fixture matches a pattern in both sections or two patterns in one. A fixture matching no pattern is ungradeable in either scope, and a fixture matching two is gradeable under a claim its authorship does not support. Both were true of this partition before this revision, and both are checkable mechanically, which is the only form in which the property survives.

| Family | Pattern | What it exercises |
|---|---|---|
| Mandate | `valid-commercial-mandate.json`, `negative/mandate-*.json` | Parse, interval, boundedness, scope, subject, constraint registries, status transport |
| Delegation chain | `valid-mandate-delegation-chain.json`, `negative/delegation-chain-*.json` | Monotonic narrowing on every axis of the mandate specification section 7 |
| Offer | `valid-offer*.json`, `negative/offer-*.json` | Terms structure, money and percentage representation, profile resolution, private-field boundary, and the session identifier the offeror mints |
| Agreement | `valid-agreement-*.json`, `negative/agreement-*.json` | Dual signature, terms-hash recomputation, amendment through a fresh offer and acceptance, and direct formation with no venue |
| Obligation | `valid-obligation*.json`, `negative/obligation-*.json` | Due-condition typing, assertion and response binding, partial acceptance, rejection registry |
| Evidence and verification | `valid-evidence-*.json`, `valid-verification-report-*.json`, `negative/evidence-*.json` | The reference shape, the seven-step procedure, chains, replay, reports over a party-held record, selective disclosure |
| Dispute and determination | `valid-dispute.json`, `valid-determination.json`, `negative/dispute-*.json`, `negative/determination-*.json` | Raising against a counterparty, subject binding, grounds, supersession, effect, state result, with a party determiner throughout |
| Settlement | `valid-settlement-instruction.json`, `negative/settlement-*.json` | Rail registry, trigger binding, custody refusal |
| Termination | `valid-consensual-termination.json`, `negative/termination-*.json` | Consensual close by both signatures, obligation release, rules-version replay |
| Carrier declaration | `valid-extension-declaration.json`, `negative/declaration-*.json` | Capability declaration, version compatibility, uniform refusal |
| Key record | `valid-key-record.json`, `negative/key-record-*.json` | Registered suites, public members only, lifecycle interval |
| Approval | `valid-approval.json` | Binding one exact action hash to a named principal |
| Party family | `valid-organization.json`, `valid-agent.json`, `valid-principal.json`, `negative/organization-*.json`, `negative/agent-*.json`, `negative/principal-*.json` | The objects at the root of the authority chain: legal-entity reference, agent binding and custody disclosure, and a principal carrying a role without personal data |
| Envelope annotation | `negative/action-envelope-with-kernel-annotations.json`, `negative/envelope-*.json` | The closed envelope, in its refuse direction |
| Policy decision | `negative/policy-deny-visible-to-counterparty.json` | Denied-action privacy toward the counterparty, on a decision the acting party issued about its own action |
| Conformance grade | `valid-conformance-grade-bilateral-scope.json`, `negative/grade-scope-*.json`, `negative/grade-bilateral-*.json` | A grade naming this scope, and the refusals of section 3.2 and section 6.3 read on one |

A family's **identifier**, used by the `established_from` and `held_out_coverage` members of the grade object under section 4.1 of [conformance-grades-v0.1.md](conformance-grades-v0.1.md), is its name in the Family column above, lowercased with spaces replaced by hyphens: `delegation-chain`, `evidence-and-verification`, `party-family`. A grade that names a family from the other scope's table is the overclaim of section 6.3.

The three scope-refusal negatives sit here rather than in section 5.3 because none of them names a scope that resolves, so none can be placed by the scope it claims, and the duty they exercise is item 2 and item 5 of section 2, which binds any grade consumer. Refusing an unreadable grade requires no operator-issued object, no ordered stream, and no third participant, so the authorship test in section 5.4 does not reach them and they stay here. The two overclaim negatives name the bilateral scope and are placed by that, on the same rule as the valid grade above them.

The envelope-annotation and policy-decision rows straddle the boundary and are placed here for the reason given in section 4.4. The appeal fixtures are not in this scope even though they are determination-shaped: an appeal runs on the route the issuing venue resolves, which is the operated capability named in section 5.

The carrier-declaration row named `negative/extension-*.json` until this revision, and the fixtures it meant to name are `negative/declaration-*.json`. The pattern matched nothing and the two fixtures matched no pattern, so the family was in neither scope. The delegation-chain fixtures were renamed from `negative/mandate-chain-*.json` in the same revision, because that name was matched by the mandate row's pattern as well as by its own and the two families are graded through different fixture kinds.

### 4.4 Nothing in this scope requires an operator

Every inclusion above was checked against the document that defines it, using one test: does the specification require a party other than the two to author an object, to sign one, to order a stream, or to issue a status? Where the answer is yes for any part of a section, that part is named below rather than left inside a general claim.

| Inclusion | Why it holds without an operator | The part that does not, and where it goes |
|---|---|---|
| Mandate chain | A root mandate is issued by the represented organisation's own principal, and every delegation is issued by the parent's subject. Section 11.1 of the mandate document forbids the operator from appearing in an invited party's chain at any depth, so the chain is never operator-completed in either scope | The invitation-onboarded root mandate of section 11, and required negative tests 27 to 32, are in the operated scope: they presuppose an invitation, a control-plane authored acceptance, or operator key custody |
| Evidence verification steps 1 to 7 | The document states that every step is executable by a third party holding the bundle, the schemas, the referenced rule set versions, and the declared keys, with no operator access at any step | Step 2 item 4 requires an invitation acceptance to carry an operator `object_issuance` signature. That clause is inert in this scope because no invitation acceptance is in it. Step 5 item 4 requires the referenced `PolicyDecision` to resolve. See the next row |
| Policy decision resolution at step 5 | Section 9.1 of the canonical model states who discharges the evaluator role: each party evaluates its own proposed actions and issues its own decision, bound to its own `action_hash` and signed under its own key. A control plane is that role deployed by an operator, never a fourth participant. A verifier resolves the decisions it holds | A decision the verifier was not given is reported as `not_checkable` under step 7, never as verified. A bilateral verification report therefore states this gap explicitly rather than closing it |
| Envelope annotation refusal | An agent-authored `action_envelope` carrying `kernel_annotations` is refused by the closed envelope shape, and either party executes that check on bytes it received | The allow direction, an object carrying annotations written after signing, presupposes a control plane and is in the operated scope. Section 9.1 rule 3 of the canonical model states that a bilaterally emitted object carries no annotations at all, because there is no ordering service whose observations they would record |
| Denied-decision privacy | The first of the two denied-decision rows of section 12 of the canonical model, that a `deny` decision is private to the actor and is disclosed to no counterparty, refused with `A202-DISCLOSURE-DENIED`. A counterparty that receives one has received a disclosure, and either party checks this on what it receives | The second row, that a `deny` decision consumes no sequence number in a shared stream, refused with the same code, is in the operated scope. It is a property of a service that assigns sequence numbers; on the record of section 8.1 of the state machine a denied action is simply never countersigned in. The invariant was one row carrying both meanings until 30 July 2026, and this scope had to split a row against itself to state the division |
| Aggregate entry at `agreement.direct` | Two parties who already found each other enter at `draft` and reach `agreement_pending` with no publication, no qualification, and no negotiation room. The guards are offer currency, an acceptance over the exact offer hash, and both parties' signatures, all of which the two parties hold. Rules version 1.3 registers the transition | The refuse direction where a session stream already exists on the transaction is in the operated scope, because the record it is refused against contains a stream an operator ordered |
| Aggregate transitions from `agreement_pending` onward | Commitment, performance, acceptance, settlement, exception, amendment, and termination are moved by acts of the two parties | `request.published`, `qualification.started`, `negotiation.opened`, and the five invitation self-loops are in the operated scope |
| Session state machine | The session transitions are guarded by offer currency, signatures, and approval binding, all of which the two parties hold. The session identifier is minted by the offeror on its own offer and adopted by the counterparty, under section 9.2 of the canonical model | Session stream creation, ordering, and per-stream isolation are in the operated scope. Bilaterally there is no session stream at all, and the transaction record is the dual-held chain of section 8.1 of the state machine |
| Settlement handoff | The payer and the payee are the two parties. A rail adapter is an external execution system, and the specification already states that connectivity to it confers no authority | An instruction naming an operator as payee for onward transmission is refused in both scopes by the non-custodial rule |
| Determination checking and party issuance | Step 6 of the verification procedure checks whether a stated outcome follows from referenced rules and inputs, and a party executes it on any determination it holds. Section 4 of the determination document requires a `determiner` and leaves who that is to the rules in force; where no venue is present the rules the parties reference name one of them, and the ordinary case is the respondent conceding the question against itself. The effect is still read from the rules and never from the determiner, so a party cannot concede itself more than the rules granted | Issuance of a determination by a venue operator, the appeal route it resolves, and a dispute whose respondent is the venue operator are in the operated scope |

One row left this table on 30 July 2026. `offer.selected` was included here on the reading that with exactly one session on the transaction, selection is an act of the selecting party over an offer it holds. That reading requires a session, and a session is created by `negotiation.opened`, which is an operator act; the transition's own required side effect in section 5 of the state machine freezes a single-award selection version, which resolves which of several rooms wins. The whole transition is now in the operated scope. Where a transaction was formed directly there are no rooms, no rivals, and nothing to select among, so a bilateral implementation that never emits `offer.selected` has skipped nothing it needed.

An implementation assessed in this scope MUST NOT be required to hold, produce, or resolve any operator-issued object in order to pass. A fixture that cannot be executed without one is not in this scope.

That sentence was false when it was written. Until 30 July 2026 the bilateral scope had no route past `draft` that did not run through publication, qualification, and a negotiation room; the determination and evidence families it claimed were authored and signed by the operator in every fixture; the offer it claimed carried control-plane annotations and a session identifier only an operator could mint; and the `PolicyDecision` its own row above says each party issues was assigned to the control plane by the object inventory. [A202-0014](../proposals/A202-0014-bilateral-formation-and-scope-repair.md) is the repair, and the property is now checkable rather than asserted: no fixture matching a pattern in section 4.3 carries an object authored, signed, ordered, or annotated by an operator.

## 5. The operated scope

`a202-scope/operated/0.1`

### 5.1 Capabilities in this scope

1. **Invitation onboarding through a control plane.** Issuing an invitation, delivering a claim secret on a channel, authoring an `InvitationAcceptance` under the operator's own mandate while the claimant attests to the same bytes, and bounding the invited party's own root mandate to the invitation's transaction.
2. **Operator key custody.** Custodying a subject key and requiring a bound principal approval for every act under it.
3. **Negotiation rooms and session streams.** Creating a session and its stream on `negotiation.opened`, ordering appends per stream, and returning a sequence conflict that carries the sequence of that stream only.
4. **Isolation across concurrent counterparties.** The property that no participant infers the existence, activity, or terms of another from content, sequence numbers, refusal codes, or timing, and the session event allowlist that carries it.
5. **Awards.** Selection among rival sessions, single-award integrity under contention, award as a transition distinct from acceptance, rule freezing at open, and the declared disclosure policies of a competitive event.
6. **Operated determination issuance.** Determinations issued by a venue, the appeal route resolved from the rules in force, and disputes whose respondent is the venue operator.
7. **Publication and qualification.** Moving a request to `published` and `qualifying`, and the directory and qualification side effects those transitions require.
8. **Control-plane annotation.** Attaching `kernel_annotations` to a minted object after signing, recording the policy decision, the session, the session sequence, and the received time outside the hashed bytes and outside every signature.
9. **Refusing the direct formation path where a negotiation is open.** A transaction carrying a session stream may not enter at `agreement.direct`, and the record that refusal is checked against holds a stream an operator ordered.

### 5.2 Specification sections in this scope

| Document | Sections in scope | Why an operator is required |
|---|---|---|
| [counterparty-invitation-v0.1.md](../discovery/counterparty-invitation-v0.1.md) | The whole document | Section 3 states the adopted resolution: the `InvitationAcceptance` is authored by the control plane under the operator's own mandate, and section 4.2 requires the operator's `object_issuance` signature alongside the claimant's. Without a control plane the record cannot exist |
| [commercial-mandate-v0.1.md](../authority/commercial-mandate-v0.1.md) | 11, 11.1, 11.2, 11.3, 11.4, and required negative tests 27 to 32 in section 12 | Each of these is a rule about a party onboarded by invitation or about an operator-custodied key |
| [auction-event-semantics-v0.1.md](../negotiation/auction-event-semantics-v0.1.md) | The whole document | Bid authority, award, disclosure policy, rule freezing, and isolation are all properties of an event run for several bidders by a party that is none of them |
| [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) | 2, 3 for `published`, `qualifying`, and `negotiating`, 5 for the publication, qualification, negotiation-opening, invitation, and `offer.selected` rows, 5.1, 6.2 for the operated selection stated in its last three paragraphs, 8 other than 8.1, and required tests 1, 2, 3, 7, 15, 16, 17, and 18 to 21 in section 11 | Two levels of state exist for confidentiality across concurrent counterparties. Per-stream concurrency and isolation are properties of the ordering service. Tests 1 to 3 traverse the publication, qualification, and negotiation entry path, which is why they are here and not in section 4 |
| [canonical-commercial-model-v0.1.md](../schemas/canonical-commercial-model-v0.1.md) | 2 and 15 in their operated reading, 11, 12.1, the `kernel_annotations` row of section 3 in its allow direction, the `kernel_annotations` clause of step 4 of section 9, and the invariants of section 12 refused with `A202-INVITATION-EXPIRED`, `A202-INVITATION-SCOPE-EXCEEDED`, `A202-INVITATION-CLAIM-UNSIGNED`, `A202-ASSURANCE-UNSUPPORTED`, and `A202-CUSTODY-APPROVAL-REQUIRED`, together with the session-stream row and the policy-decision reason-code row refused with `A202-DISCLOSURE-POLICY-VIOLATION` and the shared-sequence row refused with `A202-DISCLOSURE-DENIED` | Stream kinds, the session event allowlist, and control-plane authored annotations presuppose a control plane. The invariants are cited by refusal code and by row rather than by nickname, so that the division between this table and section 4.2 can be checked against section 12 rather than interpreted |
| [determination-v0.1.md](../disputes/determination-v0.1.md) | 2 in its operated reading, 7, 7.1, 7.2, 7.3, 7.4, and any determination whose `determiner` or `respondent_party` is the venue operator | An appeal route is resolved and operated by the party that issued the determination |
| [conformance-grades-v0.1.md](conformance-grades-v0.1.md) | 2, 3, 4, 5, and 6 in their operated reading, under section 6 of this document | The dimensions cover behaviour that only exists where an operator does |

### 5.3 Fixtures in this scope

The partition is by family pattern, on the same maintenance rule as section 4.3.

The manifest is the source for how many fixtures this scope holds, on the same rule as section 4.3.

| Family | Pattern | What it exercises |
|---|---|---|
| Invitation | `valid-counterparty-invitation.json`, `valid-invitation-acceptance.json`, `negative/invitation-*.json` | Control-plane authored onboarding, claim binding, assurance, custody approval |
| Session event | `valid-session-*.json`, `negative/session-event-*.json` | The session-stream allowlist shapes, their registered reference prefixes, and verification over a stream an operator ordered |
| Auction | `negative/auction-*.json` | Close-reason discipline, disclosure-bearing refusals, stream registry, award units |
| Stream disclosure | `valid-transaction-event-references.json`, `negative/transaction-event-*.json`, `negative/stream-*.json`, `negative/policy-deny-award-disclosing-reason.json` | The transaction-stream allowlist, rival non-inference on streams an ordering service holds, the refusal to read continuity across two such streams, and award state kept out of reason codes |
| Annotated offer | `valid-annotated-offer.json` | The allow direction of `kernel_annotations`: a control plane records the policy decision, the session, the session sequence, and the received time after signing, outside the hashed bytes |
| Direct formation contention | `negative/direct-formation-*.json` | The guard that keeps the direct entry path out of an open negotiation: a transaction carrying a session stream may not enter at `agreement.direct` |
| Appeal | `valid-appeal-determination-superseding.json`, `negative/appeal-*.json` | The appeal route a venue resolves, and operated determination issuance: grounds, window, supersession |
| Conformance grade | `valid-conformance-grade-operated-scope.json` | A grade naming this scope, with dimension A explicitly null because the operated coverage of authority handling is the invitation-onboarded path this assessment did not exercise |

Family identifiers are formed as section 4.3 states, from the Family column above: `session-event`, `stream-disclosure`, `direct-formation-contention`. The grade refusals themselves are fixtured in section 4.3, for the reason given there.

### 5.4 The authorship test

A capability is in this scope when at least one of the following holds, and for no other reason.

1. The specification requires an object to be authored or signed by a control plane or an operator, as the invitation acceptance is.
2. The specification requires a stream that neither party alone holds to be ordered, as the transaction stream and the session streams are.
3. The property being graded is only meaningful with a third participant, as rival non-inference and single-award contention are.
4. The specification assigns issuance to a venue, as an operated determination and its appeal route are.

Custody of a key is placed here by test 1: an operator-custodied key acts only under an approval the invited organisation's own principal bound to the exact action hash, and the custody arrangement is a fact about the operator.

## 6. Grading alignment

### 6.1 One grade, one scope

A grade is issued against exactly one role scope. The scope is named in the grade's `scope` field, and the identifiers in section 3.1 are the registry for the role part of that field.

A consumer MUST evaluate the role scope identifier before it evaluates `dimensions`, in the same way it MUST evaluate `expires_at` before relying on `dimensions` under [conformance-grades-v0.1.md](conformance-grades-v0.1.md) section 4.

### 6.2 A grade claims nothing outside its scope

1. A grade against `a202-scope/bilateral/0.1` makes no claim about any capability in section 5. It says nothing about invitation onboarding, key custody, session stream ordering, isolation across concurrent counterparties, awards, or operated determination issuance.
2. A grade against `a202-scope/operated/0.1` makes no claim about any capability in section 4 that its assessment did not exercise.
3. A relying party MUST NOT infer a band in one scope from a band in the other, and a grade MUST NOT be presented in a way that invites the inference.

### 6.3 Dimensions are read within the named scope

All five dimensions are still reported. A grade MUST report dimensions A to E under [conformance-grades-v0.1.md](conformance-grades-v0.1.md) section 2, and this document does not change that.

1. A band in a dimension is established only from the sections and fixtures the named scope contains. A dimension with no coverage in the named scope is reported as unassessed, explicitly null, never omitted and never inferred.
2. Dimension B, disclosure and isolation, has a materially different meaning in each scope. In the bilateral scope it covers denied-action visibility to the counterparty, private field leakage in shared objects, and refusal codes that carry no state the recipient may not see. It does not cover rival non-inference, which has no meaning where there are no rivals. A band 1 in dimension B on a bilateral grade MUST NOT be read as a statement about rival non-inference.
3. A grade that reports a band established from fixtures outside the named scope is refused with `A202-GRADE-SCOPE-OVERCLAIM`. This is the case where a bilateral assessment reports an operated dimension, and it fails rather than being narrowed on the reader's behalf.
4. `held_out_coverage` reports coverage and case count within the named scope, and coverage in one scope is not coverage in the other.

### 6.4 Absence in a scope is unassessed

A subject holding a grade in one scope and no grade in the other is unassessed in the second. A consumer MUST read the absence as unassessed and MUST NOT read it as a pass, as a fail, or as a statement that the subject does not implement that scope.

This is the same rule the set applies to a null dimension and to a check that could not be executed. Absence of an assessment reads as unassessed everywhere it is consumed.

## 7. Two-party gradeability

### 7.1 What two organisations can establish about each other

Two organisations with no third party present can each establish the following about the other, and MAY issue a grade stating it.

1. **The published suite result.** Each runs the published fixture set, the manifest, and the runner in this directory against the objects the other emits, restricted to the bilateral scope families in section 4.3. The set is open and the runner is normative, so both parties execute the same checks.
2. **The verification procedure result.** Each executes steps 1 to 7 of [evidence-verification-v0.1.md](../evidence/evidence-verification-v0.1.md) section 4 over the records the other produced, and produces a report with per-check results in the three-valued output.
3. **Refusal behaviour on the negative direction.** Each presents the refused cases in the bilateral families and observes whether the other refuses with the stated code or guesses.

A grade issued on that basis is a statement by the party that issued it, about one implementation, scoped to one specification version and one role scope. It is not certification by any body.

Section 6 of [conformance-grades-v0.1.md](conformance-grades-v0.1.md) makes every grade a determination and every determination appealable, and section 4 of [determination-v0.1.md](../disputes/determination-v0.1.md) makes `appeal_route_ref` REQUIRED on the determination that carries it. The grounds and the effect rules of that document apply to a peer-issued grade as they apply to any determination. **The appeal route does not.** An appeal route is resolved and operated by the party that issued the determination, and section 5.2 of this document places that capability in the operated scope; where the issuer is the counterparty, the route resolves to the counterparty. This document does not state what a peer issuer puts in `appeal_route_ref`, and it does not claim that a peer-issued grade is appealable on the same terms as one a venue issued. The question is open and is the fourth item in section 10. Until it is answered, a peer-issued grade is a determination whose appeal route is unresolved, which is a stated gap rather than a resolved one.

### 7.2 What two organisations cannot claim

1. A result established entirely from the published set is band 1 for the dimensions it covered, and MUST NOT be reported as band 2 or band 3.
2. Bands 2 and 3 require the subject to be measured on inputs it was not given. A party that was given every input it was measured on has not been measured at those bands, whoever ran the suite. This document states the constraint and does not state how such inputs come about, which is outside it.
3. A self-run result is not a grade, under [conformance-grades-v0.1.md](conformance-grades-v0.1.md) section 5 rule 1. A peer-run result is a grade issued by the peer, and a relying party weighs it knowing who ran it.
4. Neither party may report a band in any dimension of the operated scope on the strength of a bilateral assessment. That is the overclaim refused in section 6.3.

### 7.3 The floor this sets

Two organisations that each hold a band 1 bilateral grade issued by the other have established that each refuses the published negative cases in the bilateral families and that each produces records the other can verify from bytes. They have established nothing about behaviour under inputs neither of them constructed, and the grade says so by carrying the band rather than a summary.

## 8. Refusal codes

All fail closed. These extend the table in [pilot-transaction-state-machine-v0.1.md](../negotiation/pilot-transaction-state-machine-v0.1.md) section 10.

| Code | Meaning |
|---|---|
| `A202-GRADE-SCOPE-UNKNOWN` | A grade names a role scope identifier that does not resolve in the registry in section 3.1 |
| `A202-GRADE-SCOPE-INVALID` | A grade names no role scope identifier, or names more than one |
| `A202-GRADE-SCOPE-OVERCLAIM` | A grade reports a band in a dimension established from sections or fixtures outside the scope it names |

A refusal under any of the three is a refusal of the grade. It is not a band 0 and MUST NOT be recorded as one, because an unreadable grade is an absence of assessment rather than a failed one.

## 9. What this document does not do

It does not create a new conformance level, a certification, or a tier. It does not state that either scope is a step toward the other, and an implementation may be assessed in either, both, or neither.

It does not describe how an assessment is operated, how held-out material comes about, how an assessor is chosen, or what an assessment costs. None of that is protocol.

It does not move any rule between documents. Every section cited above stays where it is and means what it meant.

## 10. Open questions

- Whether a subject holding grades in both scopes, at different bands and different issue dates, is evaluated by a relying party as two independent statements or as one. The existing open question in [conformance-grades-v0.1.md](conformance-grades-v0.1.md) section 7 asks the same thing about profiles and transports, and one answer should serve both.
- Whether the bilateral scope should be split further, so that a party that verifies but never issues can be graded separately from one that does both. The argument for is that verification is the capability a relying party most needs. The argument against is that a registry of narrow scopes is a registry nobody reads.
- Whether a grade issued by a counterparty should record the assessment relationship in the object, given that a peer assessor is not disinterested. Recording it exposes the relationship; not recording it lets a reader assume independence that does not exist.
- How a dispute over a peer-issued grade resolves when both parties to it are also the parties to the transaction the grade covers, and what a peer issuer puts in the REQUIRED `appeal_route_ref` of the determination that carries the grade. The appeal route in section 7 of the determination document assumes an issuer that is not the counterparty, and section 5.2 of this document places operating one in the operated scope. Section 7.1 states the gap rather than closing it, because closing it means designing an appeal path for two parties with no third between them, and that is a proposal rather than a sentence.
