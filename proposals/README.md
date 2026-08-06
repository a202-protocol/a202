# Change proposals

**Status:** Mixed. Section 2 is **normative** on the process. Sections 1, 3, 4, and 5 are **informative**.

An A202 Change Proposal is the unit in which this specification changes.

## 1. When a proposal is required

**Every normative change requires a proposal.** A normative change is any change that alters what a conformant implementation has to do, may do, or must refuse. That includes:

- adding, removing, or changing a `MUST`, `MUST NOT`, `SHOULD`, or `MAY` statement;
- adding, removing, or changing a field, an enum member, or a constraint in any schema;
- adding, removing, or reclassifying a conformance fixture, or changing what the runner checks;
- adding or changing an error code, or changing the conditions under which one is returned;
- changing a state, a transition, or a guard.

A proposal is not required for a change that alters no normative statement: fixing a typographical error, clarifying wording whose meaning is unchanged, correcting a broken internal link, or improving an example that exercises no new behaviour. Those land as ordinary pull requests, still reviewed by someone other than the author.

If it is unclear which of the two a change is, it is a proposal.

## 2. Identifiers

Each proposal carries an identifier of the form `A202-NNNN`, allocated in sequence starting at `A202-0001` and never reused. A withdrawn or rejected proposal keeps its number, because the record of what was considered and declined is as useful as the record of what was accepted.

A proposal lives in this directory, at `A202-NNNN-short-title.md`. Its identifier is cited by every pull request that implements it, and by the release notes of the release that first carries it.

Proposal identifiers are distinguishable from reason codes by form: a proposal identifier is `A202-` followed by four digits, and a reason code is `A202-` followed by uppercase words.

## 3. Stages

A proposal moves through five stages. It may be withdrawn or rejected at any of them, and it may be sent back to an earlier one.

| Stage | What exists at the end of it |
|---|---|
| **1. Problem statement** | A statement of the problem in terms of what an implementation or a counterparty cannot currently do, or can currently do wrongly. No proposed solution is required yet |
| **2. Experimental** | A concrete proposed change: the specification text, the schema change, and the intended semantics. Marked experimental, and explicitly not stable. An implementation may build against it, knowing it may change |
| **3. Fixtures and compatibility** | Conformance fixtures that exercise the new behaviour in both the allow and the refuse direction, and a written compatibility analysis stating what breaks, for whom, and what a migration looks like. A proposal that cannot be expressed as a fixture is a proposal whose semantics are not yet decided |
| **4. Release candidate** | The change is frozen. No further semantic edits, only corrections. It is carried in a release candidate so that implementers can build against exactly the bytes that will ship |
| **5. Released** | The change is in a tagged release and is covered by the compatibility policy in [RELEASES.md](../RELEASES.md) |

A rule that cannot be turned into a fixture distinguishing a conformant implementation from a non-conformant one is a rule no one can be held to, which is why stage 3 is where proposals are most often sent back.

## 4. What a proposal contains

1. **Identifier and title.**
2. **Status**: one of the five stages above, plus `withdrawn` or `rejected`.
3. **Problem.** What goes wrong today, stated concretely, with an example of the commercial situation in which it goes wrong.
4. **Proposal.** The specification change, in the words that would land.
5. **Alternatives considered.** Including doing nothing, and why each was not chosen.
6. **Compatibility.** What breaks, for whom, and the migration.
7. **Fixtures.** The fixtures that verify the change, in both directions.
8. **Origin.** Where the proposal came from, including whether it arose from a particular implementation's experience. This is context for reviewers rather than an argument.

## 5. Review

Review rules are in [GOVERNANCE.md](../GOVERNANCE.md) section 3. In summary: every normative change lands by pull request, and is reviewed by someone other than its author, whoever the author is.

Anyone may raise a proposal, on the terms in [CONTRIBUTING.md](../CONTRIBUTING.md). The process is the same for a maintainer, listed in [MAINTAINERS.md](../MAINTAINERS.md), and an external contributor.
