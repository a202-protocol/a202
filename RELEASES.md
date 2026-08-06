# Release policy

**Status:** Mixed. Sections 2, 3, and 4 are **normative**. Sections 1, 5, and 6 are **informative**.

## 1. The specification set versions as one thing

The specification documents, the schemas, the fixtures, the manifest, and the runner version together, as a single set, under one version number.

They are versioned together because they are only meaningful together. A schema without the invariants that schema validation cannot express is an incomplete statement of the rules. An invariant without a fixture is a rule nobody can be held to. A fixture without the runner is a file. Versioning them separately would let an implementer combine a schema from one release with fixtures from another and believe they had a coherent target.

Individual objects inside the set carry their own identifiers. A transaction profile versions independently of the kernel, as the canonical model states. Neither of those is a separate release.

## 2. Semantic versioning

The set uses semantic versioning, `MAJOR.MINOR.PATCH`, interpreted against what a conformant implementation has to do.

| Increment | When |
|---|---|
| **MAJOR** | A change that can make a previously conformant implementation non-conformant. Removing or narrowing a permission, adding a requirement, tightening a schema, changing the meaning of an existing field, or reclassifying a fixture from positive to negative |
| **MINOR** | A change that adds capability without invalidating a conformant implementation. Adding an optional field, adding a new object type, adding a fixture that exercises previously unspecified behaviour, adding an error code for a case previously undefined |
| **PATCH** | A change that alters no normative statement. Editorial corrections, clarifications whose meaning is unchanged, and fixes to examples |

A change that is genuinely ambiguous between MAJOR and MINOR is treated as MAJOR. An implementer who upgrades expecting compatibility and does not get it has been told something false by the version number, which is the one failure the scheme exists to prevent.

## 3. What a release is

A release is not a commit. A release MUST consist of all four of the following, published together:

1. **A tag** on the released commit, of the form `vMAJOR.MINOR.PATCH`.
2. **A digest for every schema file** in the release, so that an implementer can verify that the schema it validates against is the schema that was released. Any schema whose digest differs from the released digest is not that release.
3. **The conformance manifest** as released, naming every fixture in the set and its expected classification.
4. **Release notes** naming every `A202` identifier carried by the release, and, for a MAJOR release, the migration notes required by section 4.

A release whose conformance suite does not pass against its own schemas and fixtures MUST NOT be tagged.

## 4. Compatibility

An implementation declares two versions, and they may differ.

| Declaration | Meaning |
|---|---|
| **Read version** | The versions of the specification set whose objects the implementation accepts and validates |
| **Write version** | The single version of the specification set whose objects the implementation produces |

An implementation MUST declare both. A counterparty needs to know what it may send as well as what it will receive, and an implementation that declares one number is telling only half of that.

An implementation MAY read more versions than it writes. It MUST NOT write a version it cannot read.

### Before 1.0

Pre-1.0 releases may make breaking changes on a MINOR increment, which is the standard meaning of a `0.x` version.

A breaking change before 1.0 MUST still carry migration notes: what changed, which objects are affected, what an implementation has to do differently, and whether previously issued objects remain valid. The freedom is to break compatibility, not to break it silently.

### At and after 1.0

Version 1.0 is the point at which the compatibility guarantee in section 2 becomes binding. A breaking change after 1.0 requires a MAJOR increment, migration notes, and a stated period during which the previous MAJOR version continues to be a valid target.

The governance under which 1.0 is declared is reviewed before it is declared. See [GOVERNANCE.md](GOVERNANCE.md) section 7.

## 5. Pre-release status

No release has been made. The current contents are `v0.1` working documents, not a tagged release of the set. The policy above applies from the first release.

## 6. Where the release notes accumulate

The notes section 3.4 requires are written as changes land, in [CHANGELOG.md](CHANGELOG.md), under an Unreleased heading. At a release that heading is replaced by the version and the date, the tag is cut on that commit, and a fresh Unreleased section is opened above it.

They accumulate as changes land, so that each entry names the proposal the change landed under and states what an implementer has to do differently.
