# A202-0011: Write the evidence-type registry down, and reach the waiver states the text already promised

**Status:** Fixtures and compatibility. Stage 3 of the five stages in [README.md](README.md) section 3. Both changes are implemented, and the suite passes with them in place.

**Date:** 28 July 2026

**Status of this document:** Informative in full. It states no requirement on an implementation. The normative text this proposal amends is carried by [evidence/evidence-verification-v0.1.md](../evidence/evidence-verification-v0.1.md) and [agreement/obligation-v0.1.md](../agreement/obligation-v0.1.md), each of which marks its own normative sections.

## 1. Problem

Two small defects, each of the same kind: a document promises something and the place it points at does not deliver it.

**The evidence-type registry had no written home.** [obligation-v0.1.md](../agreement/obligation-v0.1.md) section 4 rule 3 requires a due condition to name "an evidence type from the registered evidence type list defined in evidence-verification-v0.1.md section 3". Section 3 of that document said only "From the registered evidence type list" and never enumerated one. The eight values existed solely as an enum in `commercial-kernel.schema.json`. An implementer following the citation arrived at a definition that was not there, and a reader wanting to know what `measurement_record` means had nowhere to look. The registry also had no stated amendment rule, so nothing said that the prose list and the schema enum must move together.

**A waiver was unreachable from the states that need it.** The obligation transition table permitted `obligation.waived` only from `pending` and `due`. Section 5.4 of the same document says, of a rejected obligation, that "the path forward is a further assertion, a waiver, a determination, or expiry", naming a transition the table did not contain. An obligee that wished to release its counterparty after seeing an assertion had no way to say so: it could accept performance it had not received, or reject and wait out a deadline it did not want to enforce. The first puts a false record on the transaction; the second leaves the obligation owed until expiry, which is worse for the obligor the release was meant to benefit.

## 2. Change

1. **Section 3.1 of the evidence document becomes the registry**, enumerating all eight types with a sentence each on what the type evidences. The closure rule moves to a new section 3.1.1, unchanged in meaning. The registry states that it and the kernel schema's `evidenceTypeId` enum are one registry expressed twice, that adding a member requires a proposal changing both, and that a member present in one and absent from the other is a defect. The section also states plainly that a resolving type is not a claim that the evidence verified, which keeps type resolution and verification result separate where a reader might merge them.
2. **The waiver row widens to `pending`, `due`, `asserted`, and `rejected`**, with the reasoning recorded next to the rejection rule that already promised it. A waiver is deliberately **not** available from `disputed`: a contested question is already before a determiner, and a unilateral release while it is open would moot a determination the other party is entitled to receive. An obligee that wishes to release a disputed obligation withdraws its position through the dispute path, and the determination records what happened.

## 3. Compatibility

The registry enumeration alters no normative statement: the eight values, their closure, and their fail-closed treatment are unchanged, and the schema is untouched. It is PATCH-class under [RELEASES.md](../RELEASES.md) section 2, and is carried in a proposal only because it sits alongside a transition change.

The waiver widening is **MINOR**: it adds legal transitions and invalidates nothing. An implementation that refused a waiver from `asserted` or `rejected` was refusing an act the specification's own rejection text described as available, and no previously valid record becomes invalid. No new state, object, field, or reason code is introduced.

## 4. Fixture plan

Implemented: `valid-obligation-waived-after-assertion` exercises the allow direction from `asserted`, and `obligation-waiver-signed-by-obligor` confirms that widening the reachable states did not widen who may sign one: the obligee rule holds for a waiver exactly as it holds for an acceptance, and the fixture is refused with `A202-OBLIGATION-RESPONSE-UNAUTHORIZED`.
