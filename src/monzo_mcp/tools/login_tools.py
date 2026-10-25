"""Starting the Monzo login from a client with no terminal, such as Claude Desktop.

The flow itself is `monzo-mcp auth`, run as a child process: it binds the
callback port, opens the browser, waits for Monzo's redirect and saves the
tokens. Reusing it keeps one implementation of the state check and the token
exchange. The tool returns as soon as the browser is open, because the user
still has to follow Monzo's emailed link, which can take longer than a client
waits for a tool call.

Nothing here talks to Monzo's data API. The only requests the child makes are
the sign-in page in the browser and the token exchange.
"""

import os
import subprocess
import sys

from mcp.types import ToolAnnotations

from .. import auth, config
from ..helpers import format_response
from ..mcp_instance import mcp

# Not read-only in MCP's sense: it opens a browser and saves tokens on this
# machine. It changes nothing at Monzo.
LOGIN = ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=True)

_login_process = None


def _client_credentials():
    """The client to log in with: the environment first, then an earlier `auth`."""
    client_id = os.environ.get("MONZO_CLIENT_ID", "").strip()
    client_secret = os.environ.get("MONZO_CLIENT_SECRET", "").strip()
    if client_id and client_secret:
        return {"client_id": client_id, "client_secret": client_secret}
    if config.MONZO_CLIENT_PATH.exists():
        return auth._load_json(config.MONZO_CLIENT_PATH)
    return None


def _stop_previous_login():
    """Free the callback port held by an earlier attempt that never finished."""
    global _login_process
    if _login_process is not None and _login_process.poll() is None:
        _login_process.terminate()
        try:
            _login_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _login_process.kill()
    _login_process = None


def start_login() -> dict:
    global _login_process

    creds = _client_credentials()
    if not creds:
        return {
            "error": (
                "No Monzo OAuth client is configured. In Claude Desktop, add the Client ID "
                "and Client secret in Settings > Extensions > Monzo > Configure. Elsewhere, "
                "run: monzo-mcp auth"
            )
        }

    config.CONFIG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    auth._save_json(config.MONZO_CLIENT_PATH, creds)
    _stop_previous_login()

    # The child inherits the resolved paths explicitly, so it saves the tokens
    # exactly where this server will read them.
    env = dict(os.environ)
    env["MONZO_MCP_CONFIG_DIR"] = str(config.CONFIG_DIR)
    env["MONZO_MCP_DB_PATH"] = str(config.DB_PATH)

    # stdout is this server's JSON-RPC channel, so the child's output goes to a
    # log file instead. Owner-only: it holds the authorisation URL.
    log_path = config.CONFIG_DIR / "login.log"
    log_fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    with os.fdopen(log_fd, "w") as log:
        _login_process = subprocess.Popen(
            [sys.executable, "-m", "monzo_mcp.cli", "auth"],
            stdin=subprocess.PIPE,
            stdout=log,
            stderr=subprocess.STDOUT,
            env=env,
            creationflags=flags,
            text=True,
        )
    # Answers `auth`'s "Re-use existing credentials?" prompt with yes: the
    # client file was written just above.
    _login_process.stdin.write("y\n")
    _login_process.stdin.close()

    # Tokens this process cached belong to the session being replaced.
    auth._cached_tokens = None
    auth._cached_creds = None

    return {
        "status": "browser_opened",
        "next_steps": [
            "In the browser, enter your email and follow the link Monzo sends you.",
            "Approve the access request in the Monzo app.",
            "Then call monzo_sync within 5 minutes to fetch up to about 11 months of "
            "history. After 5 minutes only the last 90 days are available.",
        ],
    }


@mcp.tool(annotations=LOGIN)
async def monzo_login() -> str:
    """Sign in to Monzo in the browser (for clients without a terminal, e.g. Claude Desktop).

    Opens Monzo's sign-in page. The user follows the emailed link and then
    approves access in the Monzo app. Call monzo_sync within 5 minutes of the
    approval to fetch up to about 11 months of history.

    Use this when another tool reports that Monzo is not configured, or that
    the token is invalid or expired. It changes nothing in the Monzo account.
    """
    return format_response(start_login())
