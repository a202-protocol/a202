# Security

**Status:** Informative in full.

## Reporting a vulnerability

**Do not open an issue, a pull request, or a discussion for a suspected vulnerability.** A specification defect that lets an implementation be induced to disclose a counterparty's activity, accept an unauthorised commitment, or forge an authority chain is exploitable against every implementation at once, so disclosure must be coordinated.

There are two private reporting routes; use either.

1. **Email security@a202.org.** That address reaches the maintainers listed in [MAINTAINERS.md](MAINTAINERS.md) and nobody else. It carries no encryption of its own, so include only information that is safe to send unencrypted, and note anything you are withholding.
2. **GitHub private vulnerability reporting**, from the Security tab of this repository, which is the route most researchers try first. It is encrypted in transit, visible only to the maintainers, and it gives the maintainers a private fork in which to develop the fix and a route to a CVE identifier where one is warranted.

A report through either route gets the same handling, described below.

## What is in scope

A report is in scope if it identifies a way in which the specification as written permits, or fails to prevent, one of the following:

- an act that takes effect without a valid, unexpired, unrevoked authority chain behind it;
- disclosure of one counterparty's existence, activity, or terms to another, including through sequence numbers, reason codes, response timing, or the shape of a refusal;
- a commitment that binds a party that did not sign the bytes it is said to have agreed to;
- a record that cannot be replayed to the state it claims, or that can be replayed to a different one;
- a permissive default where the specification requires a closed failure.

Defects in a particular implementation belong to that implementation's own reporting channel, not here, unless the specification is what led the implementation into the defect.

The analysis behind this list, including the adversaries assumed, where each defence is specified, and what is out of scope, is [THREAT-MODEL.md](THREAT-MODEL.md).

## What to expect

1. **Acknowledgement.** You receive confirmation that the report arrived and is being assessed.
2. **Assessment.** The maintainers determine whether the specification is at fault, which versions are affected, and whether a change is required.
3. **Coordination.** Where a fix affects deployed implementations, disclosure is coordinated with them so that a corrected version exists before the defect is described publicly.
4. **Disclosure.** The defect, the affected versions, and the change are published together. Reporters are credited unless they ask not to be.

Please give the maintainers a reasonable period to coordinate before publishing. What counts as reasonable depends on how many implementations are affected and how hard the fix is, and it is agreed with you rather than imposed.

## Security embargo is a reserved right

Delaying publication of a change in order to complete coordinated disclosure is one of the four rights reserved to the sponsor in [GOVERNANCE.md](GOVERNANCE.md) section 6. It is named here so that a contributor whose change is held back knows which rule is being exercised.

An embargo covers timing. It does not cover the content of the eventual disclosure, and it is not a mechanism for declining to fix a defect.
