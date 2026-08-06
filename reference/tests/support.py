"""Shared helpers for the reference implementation tests.

The conformance runner is imported from its file path, because its filename
is hyphenated. The tests reuse its registries and normative checks so that
what this package emits is judged by the same code that judges the published
fixtures, rather than by a copy that could drift.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REFERENCE_DIR = REPO_ROOT / "reference"
sys.path.insert(0, str(REFERENCE_DIR))

_RUNNER_PATH = REPO_ROOT / "conformance" / "run-conformance.py"
_spec = importlib.util.spec_from_file_location("run_conformance", _RUNNER_PATH)
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)

FIXTURES = REPO_ROOT / "conformance" / "fixtures" / "v0.1"
