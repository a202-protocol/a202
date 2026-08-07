---
description: "A202 compared with AP2 (Agent Payments Protocol), ACP (Agentic Commerce Protocol), and UCP (Universal Commerce Protocol): what each protocol answers, what each assumes, and how they compose. Field-by-field, as of August 2026."
---

# A202 compared with AP2, ACP, and UCP

**Status:** Informative in full. This page describes other projects as
accurately as we can state them from their published documents, **as of
August 2026**; each moves on its own schedule, and where this page and a
project's own documents disagree, its documents are the definition. Where
this page and an A202 specification document disagree, the A202 document
is the definition.

## Four protocols, four questions

The agentic-commerce specifications now in circulation answer different
questions, and for the most part they are not competing answers to the
same one.

**[AP2](https://ap2-protocol.org/)**, the Agent Payments Protocol,
answers: *can this agent prove its principal authorised this payment?*
Originated by Google in September 2025 and contributed to the [FIDO
Alliance](https://fidoalliance.org/fido-alliance-to-develop-standards-for-trusted-ai-agent-interactions/)
in spring 2026, its v0.2 defines two SD-JWT mandate types — a Checkout
Mandate binding what the agent was authorised to buy, and a Payment
Mandate binding the payment authorisation — each usable in open
(pre-authorised, human-not-present) or closed form. Its specification
states its non-goals plainly: the commerce protocol itself, dispute
resolution procedures, delegation details, and negotiation are out of
scope.

**[ACP](https://github.com/agentic-commerce-protocol/agentic-commerce-protocol)**,
the Agentic Commerce Protocol, answers: *how does an agent execute a
checkout against a merchant?* Maintained by OpenAI and Stripe (latest
stable release 2026-04-17), it defines a merchant-hosted Checkout API, a
narrowly scoped delegated payment token, and a product feed
specification. It is in production behind ChatGPT Instant Checkout. Trust
rides on the platform and the scoped token; the protocol defines no
user-signed authority artifact a counterparty can hold.

**[UCP](https://ucp.dev/)**, the Universal Commerce Protocol, answers:
*how do agent surfaces and merchants integrate once instead of N×N
times?* Announced by Google with Shopify, Etsy, Target, Walmart and
others in January 2026, it specifies catalog search, cart, checkout,
identity linking, and order management, with REST, JSON-RPC, A2A, and MCP
bindings, and takes AP2 as an optional mandate extension. It ships its
own [conformance tooling](https://github.com/Universal-Commerce-Protocol/conformance)
for those capability APIs.

**A202** answers the question the other three assume an answer to: *how
was the agreement being paid for formed, under whose commercial
authority, through what negotiation, with what disclosed to whom — and
how does anyone verify any of that later, from the record alone?* A202
is deliberately not a payment protocol: it ends at a [settlement
handoff](../fulfillment/settlement-handoff-v0.1.md), an authorised
instruction to exactly the rails the other three serve.

## Field by field

| Concern | A202 | AP2 v0.2 | ACP (2026-04-17) | UCP |
|---|---|---|---|---|
| Delegated commercial authority | [Commercial mandate](../authority/commercial-mandate-v0.1.md): typed, signed, constraint-scoped, covering what may be *negotiated and agreed*, not only paid | Payment-scoped: Checkout and Payment mandates (SD-JWT) | None; scoped payment token | Via the AP2 extension, payment-scoped |
| Negotiation | Offer state, [auction event semantics](../negotiation/auction-event-semantics-v0.1.md), per-session disclosure rules | Out of scope (stated) | None; fixed prices | None; merchant-declared discounts |
| Transaction state | Two state machines, [aggregate and per bilateral session](../negotiation/pilot-transaction-state-machine-v0.1.md); only signed, authorised events move state | Delegated to carrier | Merchant-hosted session status | Merchant-hosted checkout lifecycle |
| Agreement and obligation objects | [Agreement](../schemas/canonical-commercial-model-v0.1.md) and [obligation](../agreement/obligation-v0.1.md) as first-class signed objects | Hash-bound checkout contents inside mandates | Order confirmation | Order object, webhook lifecycle |
| Disclosure rules | Declared policy, default reveal-nothing across counterparties, every disclosure a recorded event | SD-JWT selective disclosure at credential level | None | None |
| Evidence and disputes | [Evidence verification](../evidence/evidence-verification-v0.1.md) by replay; [determination](../disputes/determination-v0.1.md) objects | Non-repudiable mandates; dispute procedures and retention out of scope (stated) | Deferred to card rails / merchant of record | Not specified |
| Payment execution | Out of scope by design: [settlement handoff](../fulfillment/settlement-handoff-v0.1.md) to rails | The core subject | The core subject (delegate payment) | Payment handler architecture |
| Catalog and checkout surface | Out of scope | Out of scope (stated) | Product feed, Checkout API | Catalog, cart, checkout capabilities |
| Conformance | [Executable suite](../conformance/conformance-grades-v0.1.md), 148 fixtures, graded per [role scope](../conformance/conformance-role-scopes-v0.1.md); schema validity necessary but not sufficient | None published | Examples and sample requests | Conformance repo for capability APIs |
| Transport stance | Carrier-neutral; [A2A binding](../bindings/a2a-binding-v0.1.md), [MCP server](../reference/a202_mcp/README.md) | Transport-agnostic; deployed as a UCP extension | HTTPS APIs | REST, JSON-RPC, A2A, MCP bindings |
| Governance | Public [governance](../GOVERNANCE.md), numbered public [proposals](../proposals/README.md), sponsor limits stated | FIDO Alliance working groups | OpenAI + Stripe maintainers, SEP process | Google-led multi-vendor open source |
| Licence | Apache 2.0 | Apache 2.0 | Apache 2.0 | Apache 2.0 |

## How they compose

Nothing above is an either/or. A transaction can be discovered and
carried on UCP or ACP surfaces, authorised for payment under AP2
mandates, and still need what A202 specifies: the mandate that authorised
the *negotiation*, the signed events that moved the *agreement* to
formed, the disclosure record of the bargaining, and the evidence a
dispute is decided from. Concretely:

- A202's [settlement handoff](../fulfillment/settlement-handoff-v0.1.md)
  is an authorised instruction shaped to hand a formed agreement to a
  payment layer — an AP2 mandate exchange or an ACP delegated payment is
  a natural recipient.
- A202 objects are carrier-neutral, and UCP's A2A and MCP bindings are
  carriers like any other: an A202 agreement can be referenced from a
  UCP checkout without changing what either means.
- Where AP2 scopes out dispute procedures and retention, A202's
  [evidence](../evidence/evidence-verification-v0.1.md) and
  [determination](../disputes/determination-v0.1.md) documents specify
  exactly that layer.

## What this page does not compare

[A2A and MCP](carriers.md) are carriers, not commerce protocols; the
composition is described on its own page. The "Vibe Commerce Protocol"
appearing in the ACWorld paper
([arXiv:2608.02441](https://arxiv.org/abs/2608.02441), August 2026) is
the action-validation mechanism of a benchmark environment for evaluating
shopping agents, not an interoperability standard, so it does not fit the
table above.

Corrections to this page are welcome through the ordinary
[contribution process](../CONTRIBUTING.md); inaccuracy about another
project is a defect.
