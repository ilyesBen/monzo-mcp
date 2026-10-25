"""Path resolution and constants for the Monzo MCP server.

All paths are derived from environment variables or the package location.
No hardcoded personal paths.
"""

import os
from pathlib import Path

# Package root: monzo-mcp/ (three levels up from this file)
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent


def _default_data_root(package_root: Path, env) -> Path:
    """Where credentials and the cache live when no override is set.

    A source checkout keeps them beside the code, where .gitignore covers
    them. An installed package (pip, uvx) resolves the package root into the
    interpreter's lib directory, which a reinstall replaces, so it uses a
    per-user directory instead.
    """
    if (package_root / "pyproject.toml").exists():
        return package_root
    base = env.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "monzo-mcp"


_DATA_ROOT = _default_data_root(_PACKAGE_ROOT, os.environ)

# Config directory: stores OAuth credentials and tokens (gitignored)
CONFIG_DIR = Path(os.environ.get("MONZO_MCP_CONFIG_DIR", _DATA_ROOT / "config"))

# SQLite database path
DB_PATH = Path(os.environ.get("MONZO_MCP_DB_PATH", _DATA_ROOT / "monzo.db"))

# Credential file paths
MONZO_CLIENT_PATH = CONFIG_DIR / "monzo_client.json"
MONZO_TOKENS_PATH = CONFIG_DIR / "monzo_tokens.json"

# Monzo API
MONZO_API_BASE = "https://api.monzo.com"
MONZO_AUTH_URL = "https://auth.monzo.com/"
MONZO_TOKEN_URL = "https://api.monzo.com/oauth2/token"
MONZO_CALLBACK_PORT = 6600

# Interface the OAuth callback server binds to. The redirect URI stays
# http://localhost:<port>/callback regardless - this is only what the listener
# accepts on. Widen it only when the callback arrives on another interface,
# such as a published container port.
MONZO_CALLBACK_HOST = os.environ.get("MONZO_MCP_CALLBACK_HOST", "localhost")
