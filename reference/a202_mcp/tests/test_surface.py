"""The tool surface itself: what is exposed, how it is described, and what
deliberately is not exposed."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

from a202_mcp import gate
from a202_mcp.tools import BY_NAME, ROLE_SCOPE, SERVER_INSTRUCTIONS, TOOLS

OPERATED_CAPABILITIES = (
    "invitation",
    "session",
    "room",
    "award",
    "auction",
    "determination",
    "publish",
    "qualification",
)

# The markers and the allowlist are assembled rather than written out, so that
# this file does not fail its own sweep and does not have to be exempted from
# it: an exempted file is where a host would end up. The separator alone is the
# marker, because a scheme-specific one matches only the scheme somebody
# thought of.
_MARKERS = (":" + "//", "a202" + ".invalid")
_ALLOWED_ENDPOINTS = (
    "status.a202" + ".invalid/v1/mandates/one/status",
    "status.northstar" + ".invalid/",
    "status.delta" + ".invalid/",
    "status.a202" + ".invalid/one",
)


def _offending_lines(lines, allowed) -> list:
    """Every line stating a host or a URL that the allowlist does not cover."""
    offending = []
    for number, line in enumerate(lines, start=1):
        if not any(marker in line for marker in _MARKERS):
            continue
        if any(entry in line for entry in allowed):
            continue
        offending.append((number, line.strip()))
    return offending


EXPECTED = [
    "create_agreement",
    "get_transaction_record",
    "issue_approval",
    "issue_mandate",
    "record_obligation",
    "verify_evidence",
    "verify_mandate",
]


class SurfaceTest(unittest.TestCase):
    def test_seven_tools_are_exposed(self):
        self.assertEqual(sorted(BY_NAME), EXPECTED)

    def test_every_tool_declares_a_title_a_description_and_a_handler(self):
        for tool in TOOLS:
            self.assertTrue(tool["title"].strip(), tool["name"])
            # The calling model decides from the description alone, so a
            # one-line description is not enough to decide from.
            self.assertGreater(len(tool["description"]), 200, tool["name"])
            self.assertTrue(callable(tool["handler"]), tool["name"])

    def test_every_tool_declares_the_four_behaviour_hints(self):
        for tool in TOOLS:
            annotations = tool["annotations"]
            for hint in (
                "readOnlyHint",
                "destructiveHint",
                "idempotentHint",
                "openWorldHint",
            ):
                self.assertIn(hint, annotations, tool["name"])
                self.assertIsInstance(annotations[hint], bool, tool["name"])
            # Nothing here reaches an external system: the server makes no
            # network call, and the status endpoint is resolved by the caller.
            self.assertFalse(annotations["openWorldHint"], tool["name"])
            # Nothing is destroyed. The record is append only.
            self.assertFalse(annotations["destructiveHint"], tool["name"])

    def test_the_read_only_tools_are_the_ones_that_record_nothing(self):
        read_only = {
            tool["name"] for tool in TOOLS if tool["annotations"]["readOnlyHint"]
        }
        self.assertEqual(
            read_only,
            {"verify_mandate", "verify_evidence", "get_transaction_record"},
        )

    def test_every_declared_property_carries_a_description(self):
        for tool in TOOLS:
            schema = tool["inputSchema"]
            self.assertEqual(schema["type"], "object", tool["name"])
            for name, member in schema.get("properties", {}).items():
                self.assertTrue(
                    member.get("description"),
                    f"{tool['name']}.{name} has no description",
                )

    def test_every_required_argument_is_a_declared_property(self):
        for tool in TOOLS:
            schema = tool["inputSchema"]
            declared = set(schema.get("properties", {}))
            for name in schema.get("required", []):
                self.assertIn(name, declared, f"{tool['name']}.{name}")

    def test_the_input_schemas_are_serialisable_json_schema(self):
        for tool in TOOLS:
            rendered = json.loads(json.dumps(tool["inputSchema"]))
            self.assertEqual(rendered, tool["inputSchema"], tool["name"])

    def test_the_call_order_is_stated_without_reading_the_specification(self):
        # A developer who has never read the specification learns the order
        # from the server instructions and from the descriptions themselves.
        for name in EXPECTED:
            self.assertIn(name, SERVER_INSTRUCTIONS, name)
        self.assertIn("issue_approval", BY_NAME["verify_mandate"]["description"])
        self.assertIn("verify_mandate", BY_NAME["issue_approval"]["description"])
        self.assertIn("record_obligation", BY_NAME["create_agreement"]["description"])

    def test_every_recording_tool_names_the_codes_it_refuses_with(self):
        # A description that says an act can be refused, without saying with
        # which code, leaves the caller nothing to branch on.
        for name in ("issue_mandate", "create_agreement", "record_obligation",
                     "issue_approval", "verify_mandate"):
            self.assertIn("A202-", BY_NAME[name]["description"], name)

    def test_no_operated_capability_is_named_as_a_tool(self):
        for name in BY_NAME:
            for capability in OPERATED_CAPABILITIES:
                self.assertNotIn(capability, name)

    def test_the_scope_identifier_resolves_in_the_published_registry(self):
        self.assertIn(ROLE_SCOPE, gate.runner.REGISTERED_ROLE_SCOPES)

    def test_the_sweep_catches_a_planted_url_of_any_scheme(self):
        # The sweep is only worth running if it matches what it claims to. A
        # marker of "http" plus the separator matched no https line at all,
        # which is how a planted https host survived a sweep that passed.
        planted = [
            "SCHEMA = " + '"https' + ":" + '//schemas.example/v0.1/kernel.json"',
            "ENDPOINT = " + '"http' + ":" + '//plain.example/status"',
            'HOST = "a202' + '.invalid"',
            'status_endpoint="https' + ":" + '//status.a202' + '.invalid/v1/mandates/one/status"',
            "nothing here states a host",
        ]
        offending = _offending_lines(planted, _ALLOWED_ENDPOINTS)
        self.assertEqual([number for number, _ in offending], [1, 2, 3])

    def test_no_schema_host_is_written_into_this_package(self):
        # Identifiers come from the schema set, so a rename of the host reaches
        # this package with no change to it. The sweep covers the tests too,
        # because a host written into a fixture is a host written into the
        # package. The allowlist holds the synthetic mandate status endpoints
        # the tests present as input: a status endpoint is data a caller
        # supplies, not a schema identifier this package resolves.
        directory = importlib.util.find_spec("a202_mcp").submodule_search_locations[0]
        for path in sorted(Path(directory).rglob("*.py")):
            offending = _offending_lines(
                path.read_text().splitlines(), _ALLOWED_ENDPOINTS
            )
            self.assertEqual(
                offending,
                [],
                f"{path.name} states a host or URL: {offending}",
            )

    def test_the_mandate_spec_version_comes_from_the_schema(self):
        constrained = gate.SCHEMAS.mandate_validator.schema["properties"]["spec_version"]
        self.assertEqual(gate.MANDATE_SPEC_VERSION, constrained["const"])

    def test_tool_results_are_json_serialisable(self):
        from a202_mcp.tools import handle_get_transaction_record

        from .support import committed_transaction

        state, formed, _buyer, _supplier = committed_transaction()
        rendered = json.dumps(
            handle_get_transaction_record(state, formed["transaction_id"])
        )
        self.assertIn("agreement.direct", rendered)

    def test_an_unknown_tool_name_raises_rather_than_refusing(self):
        from a202_mcp.state import LocalState
        from a202_mcp.tools import call

        with self.assertRaises(KeyError):
            call(LocalState(), "settle_invoice", {})

    def test_a_missing_argument_returns_a_reason_code_not_a_traceback(self):
        from a202_mcp.state import LocalState
        from a202_mcp.tools import call

        result = call(LocalState(), "issue_mandate", {"issuer": {}})
        self.assertEqual(result["outcome"], "refused")
        self.assertTrue(result["reason_codes"])


class ServerBindingTest(unittest.TestCase):
    def setUp(self):
        if importlib.util.find_spec("mcp") is None:
            self.skipTest("the MCP SDK is not installed in this environment")

    def test_the_declared_surface_matches_the_tool_table(self):
        from a202_mcp.server import declared_tools

        declared = {tool.name: tool for tool in declared_tools()}
        self.assertEqual(sorted(declared), EXPECTED)
        for name, tool in declared.items():
            self.assertEqual(tool.description, BY_NAME[name]["description"])
            self.assertEqual(tool.input_schema, BY_NAME[name]["inputSchema"])
            self.assertEqual(tool.title, BY_NAME[name]["title"])

    def test_the_stdio_server_binds_the_same_handlers(self):
        from a202_mcp.server import build_server
        from a202_mcp.state import LocalState

        server = build_server(LocalState())
        self.assertEqual(server.name, "a202")
        self.assertIn("issue_mandate", server.instructions)


if __name__ == "__main__":
    unittest.main()
