"""The server driven over stdio by a real MCP client.

The whole bilateral flow is run through the transport rather than through the
handlers: a client subprocess-launches `python -m a202_mcp`, lists the tools,
and calls them in the order the server's own instructions state. What this
adds over the handler tests is the transport itself, the declared schemas as a
client actually receives them, and the refusal convention on the wire.

Skipped where the MCP SDK is not installed, because the SDK requires a Python
version later than the one the reference implementation targets.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

from .support import ACTIONS, CONSIDERATION, BUYER, SUPPLIER, TERMS, TRANSACTION, stamp

REFERENCE_DIR = Path(__file__).resolve().parent.parent.parent

HAVE_SDK = importlib.util.find_spec("mcp") is not None

BUYER_ISSUER = {
    "organization_id": "org_northstar",
    "principal_id": "prn_northstar_procurement_director",
    "key_id": "key_northstar_principal_01",
}
SUPPLIER_ISSUER = {
    "organization_id": "org_delta",
    "principal_id": "prn_delta_managing_director",
    "key_id": "key_delta_principal_01",
}

EVIDENCE = [
    {
        "evidence_type": "third_party_certificate",
        "claim": "Calibration certificates issued for 20 transmitters",
        "artifact_hash": "b" * 64,
        "issuer": {"organization_id": "org_delta"},
        "verification": {
            "status": "verified",
            "verified_at": "2026-09-08T14:00:00Z",
            "verifier_organization_id": "org_northstar",
        },
    }
]


def _mandate_arguments(issuer, subject_agent, subject_key, actions, organization):
    return {
        "issuer": issuer,
        "subject": {"agent_id": subject_agent, "key_id": subject_key},
        "represented_organization_id": organization,
        "valid_from": stamp(-1),
        "valid_until": stamp(24),
        "status_endpoint": "https://status.a202.invalid/v1/mandates/one/status",
        "actions": actions,
        "scope": {"transaction_ids": [TRANSACTION]},
        "spending_limit": {"currency": "EUR", "amount": "4000.00"},
    }


def _core(quantity, total=None):
    core = {"quantity": quantity, "unit_code": "H87"}
    if total is not None:
        core["total"] = total
    return {"core": core}


@unittest.skipUnless(HAVE_SDK, "the MCP SDK is not installed in this environment")
class StdioClientTest(unittest.TestCase):
    def test_the_whole_flow_over_the_transport(self):
        import anyio

        anyio.run(self._flow)

    async def _flow(self):
        from mcp import ClientSession, StdioServerParameters, stdio_client

        with tempfile.TemporaryDirectory() as directory:
            parameters = StdioServerParameters(
                command=sys.executable,
                args=["-m", "a202_mcp", "--state-dir", directory],
                cwd=str(REFERENCE_DIR),
                env=dict(os.environ, PYTHONPATH=str(REFERENCE_DIR)),
            )
            async with stdio_client(parameters) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    self._check_handshake(session)
                    tools = await session.list_tools()
                    self._check_tool_surface(tools.tools)
                    await self._check_flow(session)

    def _check_handshake(self, session):
        self.assertEqual(session.server_info.name, "a202")
        self.assertIn("issue_mandate", session.instructions)
        self.assertIn("verify_mandate", session.instructions)

    def _check_tool_surface(self, tools):
        by_name = {tool.name: tool for tool in tools}
        self.assertEqual(
            sorted(by_name),
            [
                "create_agreement",
                "get_transaction_record",
                "issue_approval",
                "issue_mandate",
                "record_obligation",
                "verify_evidence",
                "verify_mandate",
            ],
        )
        for tool in tools:
            self.assertTrue(tool.title)
            self.assertGreater(len(tool.description), 200)
            self.assertEqual(tool.input_schema["type"], "object")
            self.assertIsNotNone(tool.annotations)
            self.assertIs(tool.annotations.open_world_hint, False)
        self.assertIs(by_name["verify_evidence"].annotations.read_only_hint, True)
        self.assertIs(by_name["create_agreement"].annotations.read_only_hint, False)

    async def _call(self, session, name, arguments, expect_error=False):
        result = await session.call_tool(name, arguments)
        self.assertEqual(
            bool(result.is_error), expect_error, f"{name} returned {result.structured_content}"
        )
        self.assertTrue(result.content, f"{name} returned no content block")
        return result.structured_content

    async def _decide(self, session, mandate_id, act):
        """What an agent does before every act: verify, then carry the result."""
        decision = await self._call(
            session,
            "verify_mandate",
            {
                "mandate_id": mandate_id,
                "status": {"status": "active", "retrieved_at": stamp()},
                "proposed_action": act,
            },
        )
        self.assertEqual(decision["decision"], "allow", decision["reason_codes"])
        self.assertEqual(len(decision["action_hash"]), 64)
        return decision

    async def _check_flow(self, session):
        buyer_mandate = await self._call(
            session,
            "issue_mandate",
            _mandate_arguments(
                BUYER_ISSUER,
                BUYER["agent_id"],
                BUYER["key_id"],
                list(ACTIONS),
                "org_northstar",
            ),
        )
        supplier_mandate = await self._call(
            session,
            "issue_mandate",
            _mandate_arguments(
                SUPPLIER_ISSUER,
                SUPPLIER["agent_id"],
                SUPPLIER["key_id"],
                list(ACTIONS),
                "org_delta",
            ),
        )
        buyer = dict(BUYER, mandate_id=buyer_mandate["mandate_id"])
        supplier = dict(SUPPLIER, mandate_id=supplier_mandate["mandate_id"])

        supplier_decision = await self._decide(
            session,
            supplier["mandate_id"],
            {
                "action_type": "offer.submit",
                "transaction_id": TRANSACTION,
                "counterparty_organization_id": buyer["organization_id"],
                "proposed_terms": TERMS,
            },
        )
        buyer_decision = await self._decide(
            session,
            buyer["mandate_id"],
            {
                "action_type": "offer.accept",
                "transaction_id": TRANSACTION,
                "counterparty_organization_id": supplier["organization_id"],
                "proposed_terms": TERMS,
            },
        )

        # An act nobody verified is refused, and says so.
        unauthorized = await self._call(
            session,
            "create_agreement",
            {
                "transaction_id": TRANSACTION,
                "buyer": buyer,
                "supplier": supplier,
                "terms": TERMS,
                "offer_valid_until": stamp(12),
                "buyer_decision": {},
                "supplier_decision": supplier_decision,
            },
            expect_error=True,
        )
        self.assertIn("A202-POLICY-DENIED", unauthorized["reason_codes"])

        formed = await self._call(
            session,
            "create_agreement",
            {
                "transaction_id": TRANSACTION,
                "buyer": buyer,
                "supplier": supplier,
                "terms": TERMS,
                "offer_valid_until": stamp(12),
                "buyer_decision": buyer_decision,
                "supplier_decision": supplier_decision,
            },
        )
        self.assertEqual(formed["state"], "committed")

        issue_decision = await self._decide(
            session,
            buyer["mandate_id"],
            {
                "action_type": "obligation.activated",
                "transaction_id": TRANSACTION,
                "counterparty_organization_id": supplier["organization_id"],
                "proposed_terms": _core("20", CONSIDERATION),
                "agreement_id": formed["agreement_id"],
            },
        )
        issued = await self._call(
            session,
            "record_obligation",
            {
                "act": "issue",
                "agreement_id": formed["agreement_id"],
                "obligor": supplier,
                "obligee": buyer,
                "term_path": "$.terms.core.quantity",
                "quantity": "20",
                "unit_code": "H87",
                "due_condition": {"type": "due_at_time", "at": stamp(48)},
                "consideration": CONSIDERATION,
                "decision": issue_decision,
            },
        )
        self.assertEqual(issued["state"], "in_performance")

        assert_decision = await self._decide(
            session,
            supplier["mandate_id"],
            {
                "action_type": "performance.declared",
                "transaction_id": TRANSACTION,
                "counterparty_organization_id": buyer["organization_id"],
                "proposed_terms": _core("20", CONSIDERATION),
                "obligation_id": issued["obligation"],
            },
        )
        unevidenced = await self._call(
            session,
            "record_obligation",
            {
                "act": "assert",
                "obligation_id": issued["obligation"],
                "obligor": supplier,
                "obligee": buyer,
                "asserted_quantity": "20",
                "evidence": [],
                "decision": assert_decision,
            },
            expect_error=True,
        )
        self.assertIn(
            "A202-OBLIGATION-ASSERTION-UNEVIDENCED", unevidenced["reason_codes"]
        )

        asserted = await self._call(
            session,
            "record_obligation",
            {
                "act": "assert",
                "obligation_id": issued["obligation"],
                "obligor": supplier,
                "obligee": buyer,
                "asserted_quantity": "20",
                "evidence": EVIDENCE,
                "decision": assert_decision,
            },
        )
        self.assertEqual(asserted["state"], "acceptance_pending")

        respond_decision = await self._decide(
            session,
            buyer["mandate_id"],
            {
                "action_type": "acceptance.granted",
                "transaction_id": TRANSACTION,
                "counterparty_organization_id": supplier["organization_id"],
                "proposed_terms": _core("20", CONSIDERATION),
                "assertion_id": asserted["assertion"],
            },
        )
        answered = await self._call(
            session,
            "record_obligation",
            {
                "act": "respond",
                "assertion_id": asserted["assertion"],
                "responder": buyer,
                "counterparty": supplier,
                "response_type": "accept",
                "decision": respond_decision,
            },
        )
        self.assertEqual(answered["state"], "settlement_pending")

        report = await self._call(
            session,
            "verify_evidence",
            {"transaction_id": TRANSACTION, "rules_version": "1.3"},
        )
        self.assertEqual(report["results"]["failed"], 0)
        self.assertGreater(report["results"]["verified"], 0)

        record = await self._call(
            session, "get_transaction_record", {"transaction_id": TRANSACTION}
        )
        self.assertEqual(record["chain"], "linked")
        self.assertEqual(record["state"], "settlement_pending")
        self.assertEqual(
            [event["event_type"] for event in record["events"]],
            [
                "agreement.direct",
                "agreement.committed",
                "obligation.activated",
                "performance.declared",
                "acceptance.granted",
            ],
        )
        self.assertIsNone(record["events"][0]["previous_event_hash"])
        for earlier, later in zip(record["events"], record["events"][1:]):
            self.assertEqual(later["previous_event_hash"], earlier["content_hash"])
            self.assertEqual(later["sequence"], earlier["sequence"] + 1)


@unittest.skipUnless(HAVE_SDK, "the MCP SDK is not installed in this environment")
class ApprovalOverTheTransportTest(unittest.TestCase):
    def test_a_held_act_is_approved_and_then_allowed(self):
        import anyio

        anyio.run(self._flow)

    async def _flow(self):
        from mcp import ClientSession, StdioServerParameters, stdio_client

        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "a202_mcp"],
            cwd=str(REFERENCE_DIR),
            env=dict(os.environ, PYTHONPATH=str(REFERENCE_DIR)),
        )
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                arguments = _mandate_arguments(
                    BUYER_ISSUER,
                    BUYER["agent_id"],
                    BUYER["key_id"],
                    ["offer.accept"],
                    "org_northstar",
                )
                arguments["approval_rules"] = [
                    {
                        "id": "a_large_commitment",
                        "when": {
                            "path": "$.proposed_terms.core.total.amount",
                            "operator": "minimum",
                            "value": "3000.00",
                        },
                        "approver": {
                            "organization_id": "org_northstar",
                            "role": "procurement_director",
                        },
                        "expires_after_seconds": 3600,
                    }
                ]
                issued = (
                    await session.call_tool("issue_mandate", arguments)
                ).structured_content
                action = {
                    "action_type": "offer.accept",
                    "transaction_id": TRANSACTION,
                    "proposed_terms": {
                        "core": {"total": {"currency": "EUR", "amount": "3200.00"}}
                    },
                }
                presented = {
                    "mandate_id": issued["mandate_id"],
                    "status": {"status": "active", "retrieved_at": stamp()},
                    "proposed_action": action,
                }
                held = (
                    await session.call_tool("verify_mandate", presented)
                ).structured_content
                self.assertEqual(held["decision"], "require_approval")

                approval = (
                    await session.call_tool(
                        "issue_approval",
                        {
                            "transaction_id": TRANSACTION,
                            "action_hash": held["action_hash"],
                            "requested_by": dict(
                                BUYER, mandate_id=issued["mandate_id"]
                            ),
                            "approver": {
                                "principal_id": "prn_northstar_procurement_director",
                                "role": "procurement_director",
                                "key_id": "key_northstar_principal_01",
                            },
                        },
                    )
                ).structured_content
                allowed = (
                    await session.call_tool(
                        "verify_mandate",
                        dict(presented, approval_id=approval["approval_id"]),
                    )
                ).structured_content
                self.assertEqual(allowed["decision"], "allow")
                self.assertEqual(allowed["approval"], "verified")


if __name__ == "__main__":
    unittest.main()
