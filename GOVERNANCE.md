# Governance

**Status:** Informative in full. This document describes how the project is run. It states no requirement on an implementation of the specification.

**Applies to:** the v0.x series. It is reviewed under the conditions in section 7.

## 1. Project status

A202 was initiated and is sponsored by Plural Worlds, referred to throughout this document as **the sponsor**.

The project is in its founding phase: it has a single maintainer and a single sponsor. This document records the constraints the sponsor has accepted for that phase, and section 7 defines the conditions under which the governance is reviewed and expanded. The processes below are the same ones that will apply as the contributor base grows, so that growth changes who participates rather than how decisions are made.

## 2. Roles

**Maintainers** are named individuals. Maintainer status is held by a person, not by an organisation and not by a job title at the sponsor. A maintainer who leaves the sponsor does not automatically lose maintainer status, and a person who joins the sponsor does not automatically gain it. Current maintainers are listed in [MAINTAINERS.md](MAINTAINERS.md).

**Contributors** are anyone proposing a change. Section 4 applies to all of them identically.

Additional governance bodies, such as a technical steering committee or working groups, are established as the contributor base grows, under the review process in section 7.

## 3. How a change lands

1. Every normative change lands by pull request. There is no direct push to the default branch for normative content.
2. Every normative change is reviewed by someone other than its author. An author cannot approve their own change, whoever the author is.
3. A normative change requires a proposal under the process in [proposals/README.md](proposals/README.md) before the pull request is opened.
4. A change to schemas, fixtures, the manifest, or the runner requires the conformance suite to pass, and any change in the pass or fail classification of a fixture requires an explicit statement of why the specification now says something different.
5. Editorial changes that alter no normative statement may land by pull request without a proposal, and are still reviewed by someone other than the author.

While the project has a single maintainer, requirement 2 cannot be satisfied for that maintainer's own changes. Such changes note on the pull request that independent review was not available. The requirement takes effect when a second maintainer is named in [MAINTAINERS.md](MAINTAINERS.md).

Requirement 4 is enforced by continuous integration: the conformance suite and the reference test suites run on every pull request and on every push to the default branch, under `.github/workflows/checks.yml`. Where a fixture changes its pass or fail classification, the statement of why the specification now says something different remains the responsibility of the author and the review.

## 4. Sponsor employees follow the same process

A maintainer or contributor employed by the sponsor uses the same pull requests, the same proposals, and the same review requirement as anyone else.

Where a change originates in the sponsor's own implementation work, that origin is stated in the proposal, as context for reviewers.

## 5. Technical and commercial decisions are separate

The sponsor makes commercial decisions about its own products, pricing, customers, and roadmap. None of those are decisions of this project, none of them are recorded here, and none of them are a reason to accept or reject a technical change.

Conversely, a technical decision of this project is not a commitment by the sponsor to build anything, and the sponsor's implementation is not the definition of correct behaviour. Where the sponsor's implementation and this specification disagree, the specification is what a counterparty relies on.

The sponsor exercises no technical control outside the process in section 3. A change that is rejected is rejected in the open, on the pull request, with a stated reason.

## 6. What the sponsor reserves

Four rights are reserved to the sponsor. This list is exhaustive.

| Reserved right | Scope |
|---|---|
| **Legal compliance** | The sponsor may decline or remove content that exposes it to legal risk it is not willing to carry, including export control, sanctions, and defamation. Exercised in the open, with the category of concern stated |
| **Security embargo** | The sponsor may delay publication of a change that would disclose an unpatched vulnerability before coordinated disclosure completes. See [SECURITY.md](SECURITY.md) |
| **Trademark stewardship** | The sponsor holds and defends the project's names and marks, and controls their use in a way that could imply endorsement. Trademark control is not editorial control over the specification text. The terms are in [TRADEMARK.md](TRADEMARK.md) |
| **Funding** | The sponsor decides what it funds, and may stop funding at any time. Funding decisions are not a channel for directing the specification outside the process in section 3 |

Everything not on this list is decided by the process in section 3.

## 7. When this document is reviewed

This governance is designed for a project with one sponsor and no external maintainers, and it is reviewed when that stops being true. Any one of the following triggers a review:

1. **Three independent implementations** of the specification exist, built by parties that are not the sponsor.
2. **Two external maintainers** hold maintainer status, from different organisations, neither of them the sponsor.
3. **A stable 1.0 approaches.** Version 1.0 carries a compatibility commitment that outlives any single sponsor, and the governance has to be capable of holding that commitment before the version claims it.
4. **A standards body adopts the work**, in whole or in part, at which point that body's process governs the adopted part and this document states the boundary.

A review under any of these produces either an amended governance document or a statement of why the current one still holds.

An antitrust policy is required before competing organisations participate in a structured way, and is drafted as part of the legal work that precedes that participation.
