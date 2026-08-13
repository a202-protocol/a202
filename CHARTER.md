# Charter

**Status:** Informative in full. This document defines the project's purpose, scope, and non-goals. It states no requirement on an implementation. Normative requirements are carried only by the specification documents in `schemas/`, `authority/`, `discovery/`, `negotiation/`, and `conformance/`, each of which marks its own normative sections.

**Version:** 0.1

## 1. Purpose

A202, the Verifiable Agreement Protocol for Agent-Led Commerce, is an open, carrier-neutral specification of commercial authority, negotiation state, and verifiable conformance for transactions between independent organisations, including transactions conducted on their behalf by software agents.

Two organisations that have never transacted before need to agree on more than a message format. They need a shared answer to a small number of questions with direct commercial consequence:

- Who is this counterparty, and who inside it authorised this act?
- What exactly was that party permitted to commit to, and was the act inside that permission?
- What state is this transaction in, and what changed it?
- What did the other side learn, and what did it not?
- If this is disputed a year from now, what can be reconstructed, by whom, from what?

Existing agent, payment, and identity specifications answer parts of the first and none of the rest. Existing document standards describe the artefacts of a completed trade rather than the authority and state that produced it. A202 specifies the missing layer: typed objects for authority, typed state for the transaction, explicit rules for what may be disclosed to whom, and an executable conformance suite that turns each of those into a check an implementation either passes or fails.

The specification is carrier-neutral by construction. It defines meaning, not transport. Objects defined here may be carried, wrapped, or referenced by another protocol without changing what they mean.

## 2. Scope

The specification covers the following object families. Each is present in this repository today.

| Family | Location | What it specifies |
|---|---|---|
| Canonical commercial model | `schemas/` | The common object envelope, canonicalisation and signature rules, the object inventory, money and quantity representation, the transaction profile boundary, event stream rules, and the invariants that schema validation cannot express |
| Transaction profiles | `schemas/` | How a commercial domain adds vocabulary, evidence requirements, and execution mappings without changing the kernel |
| Mandates and authority | `authority/` | Delegated commercial authority, its constraint vocabulary, delegation narrowing, approval binding, suspension and revocation, and the authority rules for a party onboarded by invitation |
| Invitations and onboarding | `discovery/` | How an organisation with no prior presence and possibly no agent infrastructure enters one named transaction, acquires its own authority, and is bounded to that transaction |
| Transaction states | `negotiation/` | The aggregate and session state machines, guarded transitions, per-stream concurrency, replay, and error codes |
| Auction event semantics | `negotiation/` | Event semantics and disclosure rules for competitive bidding, the authority requirement on every bid, award as a transition distinct from acceptance, rule freezing, and the isolation property with its verification approach |
| Conformance | `conformance/` | The executable fixture set, the manifest, the normative runner, and the conformance grade dimensions, bands, and object shape |

## 3. Non-goals

The following are outside the specification. They are named because each is adjacent enough that a reader would otherwise reasonably expect to find it here.

1. **Agent profiles and listings.**
2. **Marketplace and matching.**
3. **Settlement orchestration.**
4. **Reputation.**
5. **Turn-taking and impasse.**
6. **Operator implementation mechanism.**

A non-goal is a statement about this specification's scope. It is not a claim that the excluded capability is unimportant, and it does not prevent a later version from taking one of these up through the proposal process.

## 4. Design principles

These six principles explain why the specification is shaped as it is. Where a requirement in a specification document looks arbitrary, it usually follows from one of them.

**Fail closed.** An unrecognised value, an unresolvable reference, an unreachable status endpoint, or an unregistered constraint type produces a refusal, never a permissive default. Unavailability is not permission. Where a rule is enforced in two layers, each layer fails closed on its own, so that widening one without the other cannot let an act through.

**Explicit typed state.** Commercial meaning is carried by typed objects and named states, never by prose in a free-text field and never by the absence of an object. Only a signed, authorised event moves state. A message, a model output, an adapter callback, and a database write do not.

**Assurance is reported, never inferred.** An identity assurance level, a conformance grade, and a level of authority are each held because they were established and recorded, not because time passed or because previous transactions succeeded. Absence of an assessment reads as unassessed everywhere it is consumed, never as a pass.

**Disclosure minimalism.** A party learns what it needs in order to act and to verify, and nothing more. Disclosure is a declared policy with a default of revealing nothing across counterparties, every disclosure is a recorded event, and a refusal must not itself become a disclosure. Structures are allowlists rather than denylists, because a denylist refuses only the leaks somebody anticipated.

**Deterministic verification.** Every claim the specification makes is checkable by replaying signed records and recomputing hashes, by an authorised party with no privileged access to the operator. Replay of the same valid inputs produces the same result. No model output may serve as deterministic authority.

**Carrier neutrality.** The specification defines commercial meaning independently of any transport, agent framework, identity provider, payment rail, or enterprise system. The kernel contains no field that is meaningful in only one commercial domain, and that property is tested by a fixture rather than asserted.

## 5. Conformance language

The specification documents use `MUST`, `MUST NOT`, `REQUIRED`, `SHOULD`, `SHOULD NOT`, and `MAY` in the sense of RFC 2119 and RFC 8174, and only inside sections marked normative.

Schema validity is necessary and not sufficient. An implementation that passes every schema and violates an invariant listed in the canonical model is not conformant. The conformance suite exists because that gap is real and is otherwise invisible.
