"""The reference package's own gate: the public conformance suite passes.

The suite is executed programmatically, exactly as an implementer runs it.
The expected total is derived from the manifest rather than hardcoded here,
because the manifest is the single source for what the suite contains: a
restated count is a count that goes stale the first time the set grows. A
suite that silently shrank still fails here, because the passed total is
asserted against the manifest's own entry count, not against the runner's
report of itself.
"""

import json
import re
import subprocess
import sys
import unittest

from .support import REPO_ROOT


class ConformanceSuiteTest(unittest.TestCase):
    def test_suite_passes_completely(self):
        with open(REPO_ROOT / "conformance" / "manifest-v0.1.json") as handle:
            manifest = json.load(handle)
        expected_total = len(manifest["positive"]) + len(manifest["negative"])

        completed = subprocess.run(
            [sys.executable, "conformance/run-conformance.py"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        match = re.search(r"(\d+) passed, (\d+) failed", completed.stdout)
        self.assertIsNotNone(match, completed.stdout)
        self.assertEqual(int(match.group(1)), expected_total, completed.stdout)
        self.assertEqual(int(match.group(2)), 0, completed.stdout)


if __name__ == "__main__":
    unittest.main()
