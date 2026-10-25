"""monzo_login: starting `monzo-mcp auth` for a client with no terminal.

The child process is replaced; what is pinned is what it is started with and
what is written before it starts.
"""

import json
import os
import stat
import sys

import pytest

from monzo_mcp import auth, config
from monzo_mcp.tools import login_tools


class _FakeChild:
    def __init__(self, args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.stdin = self
        self.written = ""
        self.terminated = False
        self.running = True
        _FakeChild.started.append(self)

    def write(self, text):
        self.written += text

    def close(self):
        pass

    def poll(self):
        return None if self.running else 0

    def terminate(self):
        self.terminated = True
        self.running = False

    def wait(self, timeout=None):
        return 0


@pytest.fixture(autouse=True)
def fake_popen(monkeypatch):
    _FakeChild.started = []
    monkeypatch.setattr(login_tools.subprocess, "Popen", _FakeChild)
    monkeypatch.setattr(login_tools, "_login_process", None)
    monkeypatch.delenv("MONZO_CLIENT_ID", raising=False)
    monkeypatch.delenv("MONZO_CLIENT_SECRET", raising=False)
    return _FakeChild


def test_without_a_client_it_explains_and_starts_nothing():
    result = login_tools.start_login()
    assert "error" in result
    assert _FakeChild.started == []


def test_extension_settings_are_saved_owner_only_and_auth_is_started(monkeypatch):
    monkeypatch.setenv("MONZO_CLIENT_ID", "oauth2client_x")
    monkeypatch.setenv("MONZO_CLIENT_SECRET", "secret_y")
    result = login_tools.start_login()

    assert result["status"] == "browser_opened"
    saved = json.loads(config.MONZO_CLIENT_PATH.read_text())
    assert saved == {"client_id": "oauth2client_x", "client_secret": "secret_y"}
    if os.name == "posix":
        assert stat.S_IMODE(config.MONZO_CLIENT_PATH.stat().st_mode) == 0o600

    (child,) = _FakeChild.started
    assert child.args == [sys.executable, "-m", "monzo_mcp.cli", "auth"]
    # Answers "Re-use existing credentials?" with yes
    assert child.written == "y\n"
    # The child saves tokens where this server reads them
    assert child.kwargs["env"]["MONZO_MCP_CONFIG_DIR"] == str(config.CONFIG_DIR)
    assert child.kwargs["env"]["MONZO_MCP_DB_PATH"] == str(config.DB_PATH)
    # Never this server's stdout, which carries JSON-RPC
    assert child.kwargs["stdout"] is not None and child.kwargs["stdout"] is not sys.stdout


def test_an_earlier_auth_client_is_reused(monkeypatch):
    config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config.MONZO_CLIENT_PATH.write_text(json.dumps({"client_id": "c", "client_secret": "s"}))
    assert login_tools.start_login()["status"] == "browser_opened"
    assert len(_FakeChild.started) == 1


def test_a_second_login_stops_the_first(monkeypatch):
    monkeypatch.setenv("MONZO_CLIENT_ID", "c")
    monkeypatch.setenv("MONZO_CLIENT_SECRET", "s")
    login_tools.start_login()
    login_tools.start_login()
    first, second = _FakeChild.started
    assert first.terminated and not second.terminated


def test_cached_tokens_are_dropped(monkeypatch):
    monkeypatch.setenv("MONZO_CLIENT_ID", "c")
    monkeypatch.setenv("MONZO_CLIENT_SECRET", "s")
    auth._cached_tokens = {"access_token": "old"}
    login_tools.start_login()
    assert auth._cached_tokens is None
