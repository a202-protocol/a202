"""A202's bilateral capabilities, exposed as MCP tools.

A thin wrapper over a202_reference. Canonicalization, schema validation,
signing, and the seven-step verification procedure are that package's; the
cross-object rules are the repository's published conformance runner's. What
is added here is a party's local state, the mandate constraint evaluator of
commercial-mandate-v0.1.md section 4, and the seven tools an agent calls.

Everything exposed sits inside the bilateral role scope
`a202-scope/bilateral/0.1`. There is no room, no session stream, no award, and
no operated determination, because none of those exists between two parties
with no operator.
"""

from .state import KeyUnavailable, LocalState
from .tools import BY_NAME, ROLE_SCOPE, TOOLS

__all__ = [
    "BY_NAME",
    "KeyUnavailable",
    "LocalState",
    "ROLE_SCOPE",
    "TOOLS",
]
