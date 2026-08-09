---
description: "What A202 is, what the name means, what the protocol covers and deliberately does not, and how it relates to AP2, ACP, A2A, and MCP. A direct answer to each question, with links to the normative documents."
---

# What is A202?

**Status:** Informative in full. This page answers the questions a reader
or a software agent asks first, in plain terms. Every rule it mentions is
normative in the specification document it links to, and where this page
and a specification document disagree, the document is the definition.

## What is A202?

A202, the Verifiable Agreement Protocol for Agent-Led Commerce, is an
open, carrier-neutral specification of commercial authority, negotiation
state, and verifiable conformance for transactions between independent
organisations, including transactions conducted on their behalf by
software agents. It defines typed objects for delegated commercial
authority, a state machine for the transaction and for each bilateral
session inside it, rules for what may be disclosed to whom, and an
executable conformance suite that turns each of those rules into a check
an implementation either passes or fails.

In one sentence: **A202 specifies how two organisations that have never
transacted before — or their agents — reach commitments that either side
can later prove, from the record alone.**

## What does the name mean?

The name is **A202**, spoken "A two-oh-two". The long form, *A202, the
Verifiable Agreement Protocol for Agent-Led Commerce*, is a descriptor and
not an expansion: the letters do not stand for it. The `202` is HTTP 202
Accepted, the status an accepted submission returns under
[A202-0017](../proposals/A202-0017-submission-success-status.md), because
acceptance is the primitive the rest of the specification is built on.

## What problem does it solve?

When software agents transact for organisations, the questions that
matter are not how messages travel but what they commit anyone to. A202
gives both sides a shared, checkable answer to five questions no message
transport answers: **who authorised this act** ([commercial
mandate](../authority/commercial-mandate-v0.1.md)), **what state the
transaction is in and what changed it** ([transaction state
machine](../negotiation/pilot-transaction-state-machine-v0.1.md)),
**what was agreed and what is owed**
([obligation](../agreement/obligation-v0.1.md)), **what each side was
allowed to learn** ([canonical commercial
model](../schemas/canonical-commercial-model-v0.1.md)), and **what can be
proven a year later, by whom, from what**
([evidence verification](../evidence/evidence-verification-v0.1.md)).

## What is A202 not?

- **Not a payment protocol.** A202 stops at the [settlement
  handoff](../fulfillment/settlement-handoff-v0.1.md): an authorised
  instruction to a payment rail. It moves no money.
- **Not a transport.** A202 is carrier-neutral: it defines what objects
  mean, not how they travel. Objects may be carried by
  [A2A](carriers.md), exposed over [MCP](carriers.md), or referenced by
  another protocol without changing what they mean.
- **Not an identity scheme.** Parties bring their own keys; A202 defines
  what a signature over canonical bytes commits the signer to.
- **Not an agent framework.** A202 constrains what agents may commit
  their principals to, whatever software the agents are built with.

The full statement of scope and non-goals is the [charter](../CHARTER.md).

## How does A202 relate to AP2, ACP, A2A, and MCP?

AP2 (the Agent Payments Protocol) and ACP (the Agentic Commerce Protocol)
answer payment-shaped questions: proving a purchaser authorised a payment,
and executing checkout. A202 specifies the layer those protocols assume:
how the agreement being paid for was formed, under whose authority, with
what negotiation history and disclosure record, and how any of it is
verified. A2A and MCP are carriers A202 objects travel over — see [A202
with A2A and MCP](carriers.md) and the [comparison page](comparison.md)
for the field-by-field picture.

## Who is behind A202, and under what terms?

A202 was created by A. A. Musse and is sponsored by [Plural
Worlds](https://pluralworlds.com), under
a published [governance document](../GOVERNANCE.md) that states what the
sponsor does and does not control. The whole repository — specification
text, schemas, fixtures, and reference implementation — is licensed under
the [Apache License, Version 2.0](../LICENSE), which carries an express
patent grant from each contributor. **A202**™ is a trademark of Plural
Worlds; permitted use is stated in [TRADEMARK.md](../TRADEMARK.md).

## What is its status?

**Released, pre-1.0.** `v0.1.0` is the current release under the release
policy in [RELEASES.md](../RELEASES.md): a tag, a digest for every schema
file, the conformance manifest, and release notes, published together.
The conformance suite currently holds 148 executable fixtures,
and every normative change lands under a numbered, public
[proposal](../proposals/README.md).

## Where does an agent start?

- Machine-readable map of this site: [llms.txt](https://a202.org/llms.txt),
  full text at [llms-full.txt](https://a202.org/llms-full.txt).
- Schemas resolve under `https://schemas.a202.org`.
- Reference implementation and [MCP server](../reference/a202_mcp/README.md):
  `pip`-installable from the [repository](https://github.com/a202-protocol/a202);
  the npm package is
  [`a202-protocol`](https://www.npmjs.com/package/a202-protocol).
- A human starts with the [introduction](introduction.md).
