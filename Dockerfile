# Container for the reference MCP server in reference/a202_mcp, so that a
# registry checker or an agent host can start the server and speak MCP over
# stdio without preparing a Python environment. The server reads the
# schemas, profiles, and conformance runner from this repository, which is
# why the build context is the repository root and the working directory is
# reference/, exactly as reference/a202_mcp/README.md describes. The
# dependency set and Python version mirror .github/workflows/checks.yml,
# where the same server's tests run on every change.
FROM python:3.12-slim

WORKDIR /a202
COPY . .

RUN python -m pip install --no-cache-dir \
    "mcp>=2.0" "jsonschema>=4.18" "referencing>=0.30" "cryptography>=41"

WORKDIR /a202/reference

# Stdio transport: stdout is the protocol channel, and the server prints
# nothing on start.
ENTRYPOINT ["python", "-m", "a202_mcp"]
