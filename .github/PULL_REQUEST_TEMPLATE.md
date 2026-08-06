<!--
Every normative change lands by pull request, under a proposal, and is reviewed
by someone other than its author. The rules are in GOVERNANCE.md section 3 and
the proposal process is in proposals/README.md.

Delete the sections that do not apply. Do not delete section 1.
-->

## 1. What kind of change is this

- [ ] **Normative.** It alters what a conformant implementation has to do, may do, or must refuse. A proposal is required.
- [ ] **Editorial.** It alters no normative statement: a typographical fix, a clarification whose meaning is unchanged, a corrected internal link, or an example that exercises no new behaviour.
- [ ] **Repository machinery.** Workflows, templates, or other files outside the specification set.

If it is unclear which of the first two this is, it is normative. That rule is in proposals/README.md section 1.

## 2. Which proposal does it land under

Proposal: `A202-NNNN`, at `proposals/A202-NNNN-short-title.md`

State the stage the proposal is at, and whether this pull request moves it to a later stage.

<!-- Editorial and machinery changes: write "none required" and say why in one line. -->

## 3. What changed

Describe the change in terms of what an implementation or a counterparty can now do, or can no longer do.

## 4. Conformance

- [ ] The conformance suite passes: `python3 conformance/run-conformance.py`
- [ ] The reference tests pass: `python3 -m unittest discover -s tests -t .` from `reference/`
- [ ] The MCP server tests pass: `python3 -m unittest discover -s a202_mcp/tests -t .` from `reference/`

Does any fixture change its pass or fail classification?

- [ ] No fixture changes classification.
- [ ] A fixture changes classification, and the statement of why the specification now says something different is below. GOVERNANCE.md section 3.4 requires it.

<!-- If a fixture changed classification, state which one, in which direction, and what the specification now says. -->

## 5. Compatibility

What breaks, for whom, and what a migration looks like. Write "nothing breaks" if nothing does, rather than leaving this empty. RELEASES.md section 2 decides the increment from this answer, and a change that is ambiguous between MAJOR and MINOR is treated as MAJOR.

## 6. Scope

- [ ] This change introduces no commercial material, no competitive comparison, no pricing, no customer reference, and no implementation mechanism behind a published property. The boundary is in CONTRIBUTING.md and CHARTER.md sections 2 and 3.
- [ ] Every link and path added by this change resolves inside this repository.

## 7. Review

- [ ] This change is reviewed by someone other than its author, per GOVERNANCE.md section 3.2, or the reason that requirement cannot currently be met is stated on this pull request.
