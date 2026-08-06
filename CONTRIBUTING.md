# Contributing

**Status:** Informative in full.

## Pre-release status

No release has been made. The contents are `v0.1` working documents under the release policy in [RELEASES.md](RELEASES.md).

**External contributions are welcome**, under the terms and process below.

## Licensing and patent terms

The whole repository is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE).

One licence covers everything: the specification text, the schemas, the fixtures, the manifest, the runner, and the informative documents. The single exception is the two typefaces vendored for the documentation site under `.mkdocs/assets/fonts/`, which are under the SIL Open Font License 1.1 with their licence texts alongside them. They are site machinery, not part of the specification set.

- **Patents.** Section 3 of the licence is an express patent grant from every contributor, covering the claims their contribution practises, and it terminates for any party that brings a patent claim alleging the work infringes. No separate patent instrument accompanies the specification.
- **Contribution terms.** Contributions are accepted under the same licence, inbound the same as outbound, with a developer certificate of origin sign-off on each commit. There is no contributor licence agreement.
- **Names and marks.** Section 6 of the licence grants no trademark rights, and a contribution accepted under the licence conveys none. The A202 name is held separately from the copyright licence, on the terms in [TRADEMARK.md](TRADEMARK.md).
- **Foundation transfer.** Nothing about the licence forecloses a later transfer of the work to a foundation or a standards body; the terms of such a transfer would be settled if and when one is proposed.

## Every change follows the proposals process

Work on the specification proceeds through the process in [proposals/README.md](proposals/README.md), and lands under the review rules in [GOVERNANCE.md](GOVERNANCE.md) section 3. That applies to a maintainer and an external contributor identically.

The forms that carry the process are in place already: `.github/ISSUE_TEMPLATE/proposal.yml` for a proposal, `.github/ISSUE_TEMPLATE/defect.yml` for a defect in what is already written, and `.github/PULL_REQUEST_TEMPLATE.md` for a change that lands. Each asks for what the process asks for, including the proposal a change lands under and, where a fixture changes its pass or fail classification, the statement of why the specification now says something different. The conformance suite and both test suites run on every pull request under `.github/workflows/checks.yml`, so a contributor learns that a change breaks the suite from the pull request rather than from a reviewer.

## What is in scope for this repository

Only the open protocol: normative semantics, schemas, fixtures, the conformance manifest and runner, and the informative material that explains them. The boundary is stated in [CHARTER.md](CHARTER.md) sections 2 and 3, and these rules apply to every change:

1. **Normative semantics live here and only here.** If a counterparty must parse it, implement it, or verify against it, it belongs in this repository. A normative rule that exists in two places has no single source of truth, so a rule that lands here is removed from wherever else it was stated.
2. **No commercial material.** Strategy, pricing, monetization, customer references, competitor comparisons, and positioning against any other specification or product are out of scope, in a single sentence inside an otherwise technical document as much as in a whole file. A proposal that introduces them is closed with that reason.
3. **No mechanism design.** The published surface is the property a participant is guaranteed, the interface and wire format a counterparty implements against, the procedure by which the property is independently verified, and the conformance tests with the public fixture set. Operator implementation mechanism sits outside that surface, as [CHARTER.md](CHARTER.md) section 3 states.
4. **No build status.** A specification states what a conformant implementation must do. It does not report what any particular implementation has or has not built.
5. **No path or link leaves this repository.** Every relative link and every referenced path must resolve inside this tree, which `.github/scripts/check-links.py` enforces on every change.

## Writing rules

- Write precisely. Prefer a concrete commercial example to an abstract restatement. Avoid slogans, canned contrasts, and vague superlatives.
- The normative keywords `MUST`, `MUST NOT`, `REQUIRED`, `SHALL`, `SHALL NOT`, `SHOULD`, `SHOULD NOT`, `RECOMMENDED`, `MAY`, and `OPTIONAL` are used only in sections marked normative. In an informative section, state the same point in ordinary prose.
- Every document carries a status header stating which of its sections are normative and which are informative. A document that is entirely informative says so.

## Reporting a vulnerability

Do not open an issue or a pull request. Report privately to security@a202.org. See [SECURITY.md](SECURITY.md).
