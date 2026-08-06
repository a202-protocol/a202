"""The published schemas and the published conformance runner, loaded once.

Every rule this package applies is a rule one of those two already states. No
schema identifier, host, or path is written here: the schema set is
`a202_reference.schemas`, and the checks JSON Schema cannot express are the
repository's own conformance runner, located through the root
`a202_reference.schemas` already resolved. A rename of the schema host, or a
move of the schema directory, therefore reaches this package without changing
a line of it.

Objects this package emits are admitted to the local record only after they
pass both layers, so a tool never records something the public gate would
refuse.
"""

from __future__ import annotations

import importlib.util

from a202_reference.schemas import REPO_ROOT, SchemaSet

SCHEMAS = SchemaSet()

# The runner's filename is hyphenated, so it is loaded by path rather than
# imported. This is the one seam between this package and the conformance
# directory, and it exists so that the cross-object rules are applied by the
# code that judges the published fixtures rather than by a copy of it that
# could drift.
_RUNNER_PATH = REPO_ROOT / "conformance" / "run-conformance.py"
_spec = importlib.util.spec_from_file_location("a202_conformance_runner", _RUNNER_PATH)
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)

_PROFILES = runner.profile_registry()
_REGISTRY = runner.build_registry()

# The mandate spec version is read from the schema that constrains it rather
# than restated, on the same rule as everything else in this module.
MANDATE_SPEC_VERSION = SCHEMAS.mandate_validator.schema["properties"]["spec_version"]["const"]

RULE_SET_ID = "a202-rules/pilot"
DIRECT_FORMATION_RULES_VERSION = "1.3"
"""The rules version that registers `agreement.direct`. Versions 1.0 to 1.2
are immutable and the transition is illegal under each of them, so a record
this package writes states the version it was made under."""


def registered_profiles() -> list[str]:
    """The transaction profile identifiers that resolve. One that is absent
    fails closed at emission rather than being passed through."""
    return sorted(_PROFILES)


def rules_ref(version: str = DIRECT_FORMATION_RULES_VERSION) -> dict:
    """A hash-addressed reference to one rule set version.

    The hash comes from the registry rather than from the caller, so a record
    cannot name a version and a hash that disagree.
    """
    entry = runner.RULE_SETS.get((RULE_SET_ID, version))
    if entry is None:
        raise ValueError(f"no registered rule set version {version}")
    return {
        "rule_set_id": RULE_SET_ID,
        "version": version,
        "rules_hash": entry["rules_hash"],
    }


def resolve_rules(ref):
    """Resolve a rules reference, or None where it does not resolve.

    A caller treats None as unresolvable rather than as permissive, which is
    what the seven-step procedure requires of an unavailable rule set.
    """
    return runner.resolve_rules(ref)


SCHEMA_REFUSAL = "A202-POLICY-DENIED"
"""The code a caller receives when the published schema refused a document and
no normative check named a more specific one.

The specification defines no reason code for a schema refusal, because the
closed envelope and payload shapes are themselves the rule. A caller still
needs one registered code to branch on, so the deterministic refusal code
carries it and the validator's own messages travel beside it as prose. A
validator message is not a reason code, and a caller handed one has been given
a sentence to regular-expression.
"""


def _review(errors: list[str], codes: list[str]) -> tuple[list[str], list[str]]:
    """Registered codes and schema messages, kept apart.

    Order within the codes is preserved and duplicates are dropped, so two
    layers refusing for one reason produce one code.
    """
    registered: list[str] = []
    for code in codes:
        if code not in registered:
            registered.append(code)
    if errors and not registered:
        registered.append(SCHEMA_REFUSAL)
    return registered, errors


def _normative(doc: dict, kind: str, context: dict | None = None) -> tuple[list, list]:
    """The published cross-field checks, or a refusal where they could not run.

    The checks read a document a counterparty wrote, and a member of a type
    they did not anticipate raises out of them. A raised check is a check that
    did not pass, so it refuses here rather than escaping as a traceback to a
    caller who asked whether a document was acceptable.
    """
    try:
        return runner.normative_checks(doc, kind, _PROFILES, _REGISTRY, context), []
    except Exception as raised:  # noqa: BLE001
        return [SCHEMA_REFUSAL], [
            f"the published checks could not be run on this document: {raised}"
        ]


def kernel_refusals(obj: dict, context: dict | None = None) -> tuple[list[str], list[str]]:
    """Reason codes and schema messages for one shared object.

    Schema validity is necessary and not sufficient, so both layers run.
    `context` carries the other objects the caller holds, so that a
    cross-object rule runs only where the object it needs was disclosed.
    """
    errors = SCHEMAS.kernel_errors(obj)
    codes, raised = _normative(obj, "kernel", context)
    return _review(errors + raised, codes)


def mandate_refusals(doc: dict) -> tuple[list[str], list[str]]:
    """Reason codes and schema messages for one mandate."""
    errors = SCHEMAS.mandate_errors(doc)
    codes, raised = _normative(doc, "mandate")
    return _review(errors + raised, codes)


def object_context(objects: list[dict]) -> dict:
    """The context shape the runner's cross-object checks read."""
    return {
        "objects_by_id": {obj["id"]: obj for obj in objects if obj.get("id")},
        "objects_by_hash": {
            obj["content_hash"]: obj for obj in objects if obj.get("content_hash")
        },
        "stated": {},
    }
