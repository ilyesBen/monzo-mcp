"""The server only ever reads from Monzo.

Two halves: what each tool declares to the client, and what the code can
send. The second is a source reading, because a write would be a new request
somewhere, and no behavioural test can cover a request nobody wrote yet.
"""

import asyncio
import re
from pathlib import Path

import monzo_mcp
from monzo_mcp.cli import mcp

SRC = Path(monzo_mcp.__file__).parent


def _tools():
    return {t.name: t for t in asyncio.run(mcp.list_tools())}


def test_every_data_tool_is_declared_read_only():
    for name, tool in _tools().items():
        if name == "monzo_login":
            continue
        assert tool.annotations is not None, name
        assert tool.annotations.read_only_hint is True, name
        assert tool.annotations.destructive_hint is False, name


def test_login_is_declared_non_destructive():
    # It saves tokens on this machine, so it is honestly not read-only in
    # MCP's sense, but it changes nothing at Monzo.
    login = _tools()["monzo_login"]
    assert login.annotations.destructive_hint is False


def test_the_only_non_get_requests_go_to_the_token_endpoint():
    """Every explicit HTTP method in the package is a POST to MONZO_TOKEN_URL."""
    found = []
    for path in SRC.rglob("*.py"):
        for line in path.read_text().splitlines():
            if re.search(r"method\s*=", line):
                found.append((path.name, line.strip()))
    assert found, "expected the two token-endpoint POSTs"
    for name, line in found:
        assert 'method="POST"' in line and "MONZO_TOKEN_URL" in line, (name, line)


def test_no_http_client_besides_urllib_is_used():
    # A second HTTP client would walk past the check above.
    banned = (
        "import requests",
        "import httpx",
        "import aiohttp",
        "HTTPConnection(",
        "HTTPSConnection(",
    )
    for path in SRC.rglob("*.py"):
        text = path.read_text()
        for needle in banned:
            assert needle not in text, (path.name, needle)
