"""Entry point: `python -m a202_mcp`.

State is in memory unless a directory is named, by `--state-dir` or by the
environment variable A202_MCP_STATE_DIR. Shared objects, mandates, and public
keys are written there. Private keys are not: they live in memory for the life
of the process and are never written, returned, or logged.
"""

from __future__ import annotations

import argparse
import asyncio
import os

from .state import LocalState


def main() -> None:
    parser = argparse.ArgumentParser(prog="a202_mcp", description=__doc__)
    parser.add_argument(
        "--state-dir",
        default=os.environ.get("A202_MCP_STATE_DIR"),
        help="directory for shared objects, mandates, and public keys. "
             "In memory when absent.",
    )
    arguments = parser.parse_args()

    # Imported here rather than at module scope so that the tool layer, and
    # its tests, run in an environment with no SDK installed.
    try:
        from .server import serve
    except ImportError:
        raise SystemExit(
            "the MCP SDK is not installed: pip install mcp (Python 3.10 or later)"
        )

    asyncio.run(serve(LocalState(arguments.state_dir)))


if __name__ == "__main__":
    main()
