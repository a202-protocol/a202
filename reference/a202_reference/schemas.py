"""Schema loading and validation against the published v0.1 schemas.

The absolute schema identifiers resolve on a reserved domain, so they are
mapped to the local files through a referencing registry rather than fetched.
Profile resolution fails closed: an identifier absent from the registry is a
refusal, never a passthrough, because an unresolvable profile is a set of
terms nobody validated.
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_DIR = REPO_ROOT / "schemas" / "v0.1"
PROFILE_DIR = SCHEMA_DIR / "profiles"


def _load(path: Path) -> dict:
    with path.open() as handle:
        return json.load(handle)


class SchemaSet:
    """The published schemas, loaded once, with fail-closed profile lookup."""

    def __init__(self, schema_dir: Path = SCHEMA_DIR) -> None:
        self.schema_dir = schema_dir
        self.profile_dir = schema_dir / "profiles"
        registry = Registry()
        for path in list(schema_dir.glob("*.json")) + list(self.profile_dir.glob("*.json")):
            schema = _load(path)
            registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
        self.registry = registry
        self.kernel_validator = Draft202012Validator(
            _load(schema_dir / "commercial-kernel.schema.json"),
            registry=registry,
            format_checker=FormatChecker(),
        )
        self.mandate_validator = Draft202012Validator(
            _load(schema_dir / "commercial-mandate.schema.json"),
            registry=registry,
            format_checker=FormatChecker(),
        )
        self.profiles: dict[str, dict] = {}
        for path in self.profile_dir.glob("*.schema.json"):
            schema = _load(path)
            stem = path.name.removesuffix(".schema.json")
            name, _, version = stem.rpartition("-")
            self.profiles[f"a202-profile/{name}/{version}"] = schema

    def kernel_errors(self, doc: dict) -> list[str]:
        return [
            f"{list(error.path)}: {error.message}"
            for error in self.kernel_validator.iter_errors(doc)
        ]

    def mandate_errors(self, doc: dict) -> list[str]:
        return [
            f"{list(error.path)}: {error.message}"
            for error in self.mandate_validator.iter_errors(doc)
        ]

    def resolve_profile(self, profile_id: str) -> dict | None:
        """An unregistered profile identifier resolves to nothing.

        Callers treat None as the refusal A202-PROFILE-UNKNOWN rather than as
        an absent constraint.
        """
        return self.profiles.get(profile_id)

    def profile_terms_errors(self, profile_id: str, profile_terms: dict) -> list[str] | None:
        """Validate profile terms, or None when the profile does not resolve."""
        schema = self.resolve_profile(profile_id)
        if schema is None:
            return None
        validator = Draft202012Validator(
            schema, registry=self.registry, format_checker=FormatChecker()
        )
        return [
            f"{list(error.path)}: {error.message}"
            for error in validator.iter_errors(profile_terms)
        ]
