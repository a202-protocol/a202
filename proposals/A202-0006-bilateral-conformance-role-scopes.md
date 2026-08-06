# A202-0006: Named conformance role scopes, and a bilateral scope two parties can adopt alone

**Status:** Fixtures and compatibility. Stage 3 of the five stages in [README.md](README.md) section 3. The fixture plan in section 5 is implemented in the schemas, the runner's rule sets, the fixture set, and the manifest under [A202-0015](A202-0015-fixture-minimality-orphan-codes-and-grade-scope.md), and the suite passes with the changes in place.

**Date:** 27 July 2026

**Status of this document:** Informative in full. It states no requirement on an implementation. The normative text this proposal adopts is carried by [conformance/conformance-role-scopes-v0.1.md](../conformance/conformance-role-scopes-v0.1.md), which marks its own normative sections.

**Adopts:** [conformance role scopes v0.1](../conformance/conformance-role-scopes-v0.1.md)

## 1. Problem

The specification set defines capabilities of two kinds and does not say which is which.

Some of them are exercised by exactly two organisations: a mandate is issued and verified, an offer is accepted, an agreement is formed over one hash, obligations are asserted and responded to, and either party executes the published verification procedure over the other's records. Others do not exist without an operator: an invitation acceptance is authored by a control plane because the claimant has no mandate with which to author anything, a session stream is created and ordered by something that is neither party, an award contends on a stream no participant holds, and a determination issued by a venue is issued by the venue.

Both are specified, in the same set, at the same level of detail, with no marker between them. Three things follow, and each of them is a property of the specification rather than of anybody's product.

**The first adoption step is larger than it needs to be.** A reader working out what to implement finds the state machine's two levels of state, the concurrency and isolation rules of section 8, the invitation onboarding path, and the auction event semantics, all normative, none marked as presupposing anything. The reasonable inference is that the whole set arrives together, so the smallest adoption is the largest one. Nothing in the set contradicts that inference, and nothing in it says which parts two parties could implement between themselves this month.

**Two parties cannot name what they adopted.** Consider two organisations that have transacted for years on purchase orders and email: a buyer, and a calibration services supplier it already knows. They do not need a venue, a directory, an invitation, or a competitive event. They need the buyer's procurement director to issue a mandate the supplier's agent can verify and refuse against, an agreement formed over one hash, obligations that decompose it, and a record each can verify from bytes two years later. All of that is specified today. What is not specified is a name for it. Each party has to describe the surface it implemented in prose, the two prose descriptions will differ, and neither can point at a fixture subset and say "this is what we both pass".

**A grade cannot say what it covers.** [conformance-grades-v0.1.md](../conformance/conformance-grades-v0.1.md) section 4 gives the grade object a `scope` field described as "transaction profiles, transports, and roles covered", with the example that a grade earned as a bidder says nothing about behaviour as an event operator. The field is right and the registry behind it does not exist. Any string satisfies it. Two implementations can each hold a grade whose `scope` reads plausibly and which cover different halves of the set, and a relying party comparing them is comparing two sentences.

The consequence for dimension B is sharper than for the others. Dimension B covers "rival non-inference, denied-action visibility, close-reason discipline, refusal codes that carry aggregate state, timing and error-code side channels". Half of that has no meaning between two parties: there are no rivals to fail to infer. An implementation assessed with no third party present either reports a band in B that overstates what was measured, or reports B as unassessed and loses the part that was genuinely measured. Neither is right, and the object gives no way to say which was meant.

## 2. Proposal summary

Adopt [conformance role scopes v0.1](../conformance/conformance-role-scopes-v0.1.md), which defines:

1. **Two named role scopes.** `a202-scope/bilateral/0.1` and `a202-scope/operated/0.1`, each a named set of existing specification sections and existing fixtures.
2. **A precise assignment.** For every specification document in the set, which of its sections fall in which scope, and, where a section straddles, which part goes where and why. Fixtures are assigned by manifest grouping: twenty-two of the thirty-eight published fixtures in the bilateral scope, sixteen in the operated scope, none in both and none in neither.
3. **An authorship test.** A capability is in the operated scope when the specification requires a control plane to author or sign an object, requires a stream neither party alone holds to be ordered, grades a property that is only meaningful with a third participant, or assigns issuance to a venue. Nothing is in the operated scope for any other reason.
4. **A closed registry for the grade object's `scope` field.** A grade names exactly one role scope. An unresolvable identifier is refused, a grade naming zero or two is refused, and refusal is refusal of the grade rather than a band 0.
5. **A scoped reading of the dimensions.** All five dimensions are still reported. A band is established only from the sections and fixtures the named scope contains, a dimension with no coverage in the scope is explicitly null, and a bilateral band in dimension B is stated not to be a claim about rival non-inference.
6. **Two-party gradeability, with its ceiling stated.** What two organisations can establish about each other by each running the public suite and the verification procedure against the other, and what they cannot claim: any band that requires inputs the subject was not given.
7. **Three refusal codes.** `A202-GRADE-SCOPE-UNKNOWN`, `A202-GRADE-SCOPE-INVALID`, and `A202-GRADE-SCOPE-OVERCLAIM`.

The adopted document moves no rule, changes no guard, adds no object, and states no preference between the scopes.

## 3. Alternatives considered

**Do nothing.** Leave the two kinds of capability unmarked and the `scope` field free-form. Rejected on three grounds. The adoptability gap persists, and it is a gap in the specification rather than in anybody's reading of it: a document set that does not say which of its parts presuppose an operator has not said something it knows. The `scope` field stays unverifiable, so grades remain incomparable in exactly the dimension the field exists to disambiguate. And dimension B keeps its ambiguity, which is the failure mode the grade document is otherwise careful about everywhere: an unassessed thing reading as assessed.

**Write a separate bilateral specification document that restates the normative text.** Rejected, and it is the alternative that looks most attractive at first. It would give two parties one document to implement instead of nine. It also duplicates every rule it restates, and the boundary rule of this repository is explicit that a normative rule stated in two places has no single source of truth. The duplication would drift, and it would drift silently, because both copies would be validly published. The set has already recorded one instance of this problem in replay and is resolving it by collapsing rather than by adding a second copy.

**Label each fixture with a scope and define no named scopes.** Rejected. Per-fixture labels answer "can I run this without an operator" and do not answer "what did this grade assess". A grade would then carry a set of labels rather than a name, two assessors would choose different subsets, and comparing two grades would mean comparing two sets. Named scopes with a fixture assignment give both: the fixture-level answer is derivable from the scope, and the scope is what the grade names.

**Make the bilateral scope a transaction profile.** Rejected on a definitional ground rather than a preferential one. A transaction profile adds domain vocabulary, evidence requirements, and execution mappings under [transaction-profile-extension-model-v0.1.md](../schemas/transaction-profile-extension-model-v0.1.md). A role scope selects which kernel capabilities an assessment covered. Expressing one as the other would put a conformance concept into the profile registry, would make every scope change a profile change, and would break the property that the kernel contains nothing meaningful in only one profile.

**Define the bilateral scope only, and leave the remainder implicit.** Rejected. An implicit complement is not a scope: a grade could not name it, and the reading "not bilateral" would have to be inferred from the absence of a claim. The set refuses that inference everywhere else, and naming both scopes costs one table.

**Define three or more scopes, splitting verification from issuance.** Deferred rather than rejected. There is a real argument that a party that verifies but never issues is the common case for a relying party, and that it deserves its own name. It is recorded as an open question in the adopted document rather than settled here, because a registry of narrow scopes is a registry nobody reads, and adding one later is a MINOR change while removing one is not.

## 4. Compatibility

### 4.1 What breaks

No existing object gains, loses, or reinterprets a field other than the grade's own `scope`, whose narrowing is section 4.2. No state, transition, or guard changes. No specification section is moved or rewritten. No fixture changes classification, and this proposal added none when it was written: the assignment in the adopted document partitioned the published fixture set without touching any of them. The seven grade fixtures of section 5 landed later, under [A202-0015](A202-0015-fixture-minimality-orphan-codes-and-grade-scope.md), and they exercise the new field rather than reclassifying an existing fixture.

An unscoped grade does become invalid, which is the whole of the change and the reason for the classification below.

Under [RELEASES.md](../RELEASES.md) section 2 this is a **MAJOR** change. It was classified MINOR when this proposal was written, on the reading that a registry and three refusal codes for conditions that were previously undefined only add capability. The classification was corrected on 30 July 2026 under [A202-0015](A202-0015-fixture-minimality-orphan-codes-and-grade-scope.md): section 4.2 below states that the unscoped grade "stops being valid rather than being reinterpreted", which is a requirement added to a field that already existed, and section 2 of RELEASES.md defines MAJOR as removing or narrowing a permission or adding a requirement and resolves an ambiguous case as MAJOR rather than as MINOR.

The observation in section 4.2 stands and is what makes the correction cost nothing: no grade has been issued under this specification set, because no release has been made, so there is no population of grades whose `scope` becomes unreadable and nobody is owed a migration.

### 4.2 The `scope` field gains a closed registry

The field exists today and is unconstrained. After this proposal it carries exactly one role scope identifier from the registry, alongside the transaction profile and transport coverage it already carries, which this proposal does not touch.

| Before | After |
|---|---|
| Any string satisfies the role part of `scope` | The role part names one registered identifier |
| An unreadable role value is read as best the consumer can | An unresolvable identifier is refused with `A202-GRADE-SCOPE-UNKNOWN`, with no fallback to the other scope and no unscoped reading |
| A grade covering both kinds of capability is expressible | A grade covering both is two grades |

The narrowing applies to grades issued after the change. No grade has been issued under this specification set, because no release has been made, so there is no population of grades whose `scope` becomes unreadable. If that were not so, this would be a MAJOR change and would need migration notes rather than a registry.

### 4.3 Effect on the grade dimensions

| Dimension | Effect |
|---|---|
| A, authority handling | Fully covered in the bilateral scope. The invitation-onboarded mandate rules and operator key custody are covered in the operated scope |
| B, disclosure and isolation | Split, and this is the substantive change. The bilateral reading covers denied-action visibility, private field leakage, and refusal codes that carry no state the recipient may not see. Rival non-inference is in the operated scope, and a bilateral band in B is not a claim about it |
| C, commitment integrity | Covered in the bilateral scope except award subordination and single-award contention, which are properties of an ordering service |
| D, evidence | Fully covered in the bilateral scope. The verification procedure states that no step requires operator access, so nothing in D depends on one |
| E, adversarial failure behaviour | Covered in whichever scope the input belongs to. A band in E is established from the refusal behaviour of the families the named scope contains |

### 4.4 Effect on existing documents

No document is edited by this proposal. The adopted document cites sections of other documents and states which scope each falls in; the cited documents are unchanged and continue to mean what they mean.

Two straddles are worth naming here because a reviewer should test them specifically.

**Policy decision resolution.** Step 5 item 4 of the verification procedure requires the referenced `PolicyDecision` to resolve. Each party issues its own decisions over its own action hashes, so the bilateral scope holds. A decision the verifier was not given is reported as `not_checkable` at step 7, which is the existing rule and not a new exception. The alternative reading is that step 5 therefore cannot be fully executed bilaterally and that the whole of section 4 belongs in the operated scope. The adopted document takes the first reading and states the limit rather than hiding it.

**The `kernel_annotations` refusal.** `negative/action-envelope-with-kernel-annotations.json` refuses an agent-authored envelope carrying control-plane metadata. The refusal is a closed-shape check either party runs on bytes it received, so it is in the bilateral scope. The allow direction, an object legitimately carrying annotations written after signing, presupposes a control plane and is in the operated scope. The two directions of one rule are in different scopes, which is unusual enough to be worth a reviewer's attention.

### 4.5 Migration

None. No implementation has issued a grade under this set, and no object shape changes. An implementation that wants a scoped grade names a scope in the field that already exists.

## 5. Fixture plan

Fixtures are added to [conformance/manifest-v0.1.json](../conformance/manifest-v0.1.json) and run by [conformance/run-conformance.py](../conformance/run-conformance.py). They exercise the grade object's `scope` field, which had no fixture coverage when this proposal was written.

Implemented, not planned. All seven landed on 30 July 2026 under [A202-0015](A202-0015-fixture-minimality-orphan-codes-and-grade-scope.md), which also made the shape of the `scope` field concrete in section 4 of [conformance-grades-v0.1.md](../conformance/conformance-grades-v0.1.md), because a field described only in prose cannot be written against. Each of the three refusal codes in section 8 of the adopted document is now raised by an evaluator on a fixture rather than named in a table.

### 5.1 Allow direction

| Fixture | Expected | What it distinguishes |
|---|---|---|
| `valid-conformance-grade-bilateral-scope.json` | valid | A grade naming `a202-scope/bilateral/0.1`, reporting all five dimensions, with bands established only from the bilateral families and any uncovered dimension explicitly null |
| `valid-conformance-grade-operated-scope.json` | valid | The same in the operated scope, so that neither scope is the privileged one in the fixture set |

### 5.2 Refuse direction

| Fixture | Expected | What it refuses |
|---|---|---|
| `negative/grade-scope-unregistered.json` | `A202-GRADE-SCOPE-UNKNOWN` | A grade naming a role scope identifier absent from the registry. An implementation that falls back to the nearest registered scope, or that drops the role part and reads the grade unscoped, fails |
| `negative/grade-scope-absent.json` | `A202-GRADE-SCOPE-INVALID` | A grade naming no role scope. The unscoped grade is the state of the world today, and it stops being valid rather than being reinterpreted |
| `negative/grade-scope-two-scopes.json` | `A202-GRADE-SCOPE-INVALID` | A grade naming both registered scopes. A grade covering both is two grades, and accepting one would let a single assessment be reported as two |
| `negative/grade-bilateral-claims-operated-dimension.json` | `A202-GRADE-SCOPE-OVERCLAIM` | A grade naming the bilateral scope and reporting a band in dimension B established from the auction and session event families. This is the overclaim the whole proposal exists to make refusable |
| `negative/grade-bilateral-claims-invitation-coverage.json` | `A202-GRADE-SCOPE-OVERCLAIM` | A bilateral grade whose `held_out_coverage` names invitation onboarding. Held separately from the case above because a check written only against `dimensions` would miss it |

### 5.3 Cases requiring runtime state

These cannot be expressed as static documents and are verified against a running implementation, in the manner of the runtime items already listed in [canonical commercial model v0.1](../schemas/canonical-commercial-model-v0.1.md) section 15.

1. An implementation assessed in the bilateral scope passes every bilateral family with no operator-issued object present anywhere in the run. This is the negative direction of the scope definition itself: if any bilateral fixture cannot be executed without one, the assignment is wrong and the fixture is the finding.
2. A relying party presented with a bilateral grade and asked to evaluate an operated capability reports unassessed, not a fail and not a pass.
3. Two organisations each run the bilateral families against the other's emitted objects and each execute the verification procedure over the other's records, and the two resulting grades agree on the bands they both assessed. Disagreement means the suite is under-determined at that point, and the disagreement is the finding.

Both directions are present for every rule this proposal introduces, which is the stage 3 requirement in [README.md](README.md) section 3.

## 6. Origin

Drafted from three properties of the v0.1 set read together: the grade object's `scope` field and its stated example that a grade earned in one role says nothing about another; the statement in [CHARTER.md](../CHARTER.md) section 3 that operator implementation mechanism is a non-goal while the properties an operator must exhibit are published; and the statement in [evidence-verification-v0.1.md](../evidence/evidence-verification-v0.1.md) section 4 that every step of the verification procedure is executable with no operator access. The third is the one that made the division findable: a set with a procedure explicitly executable by two parties, and no name for the surface that procedure covers, has a name missing rather than a rule missing.

The dimension B reading in section 1 was found while checking whether a bilateral assessment could report all five dimensions honestly. It cannot, under the current wording, which is why section 6.3 of the adopted document states the reading rather than leaving it to an assessor.

This is context for reviewers rather than an argument.
