"""Two MCP clients sharing one token file.

Monzo allows one live access token per client, and a refresh token works
once. When one process refreshes, the other's cached tokens stop working;
these pin that it recovers from the file instead of asking to re-authorise.
"""

import io
import json
import time
import unittest
import urllib.error

import pytest

from monzo_mcp import api, auth


class _Resp:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._body


def _401():
    return urllib.error.HTTPError("https://api.monzo.com/x", 401, "no", None, io.BytesIO(b""))


@pytest.fixture
def files():
    auth.MONZO_TOKENS_PATH.parent.mkdir(parents=True, exist_ok=True)
    auth.MONZO_CLIENT_PATH.write_text(json.dumps({"client_id": "cid", "client_secret": "s"}))

    def write_tokens(access, refresh, expiry):
        auth.MONZO_TOKENS_PATH.write_text(
            json.dumps({"access_token": access, "refresh_token": refresh, "expiry": expiry})
        )

    return write_tokens


def test_an_expired_token_is_taken_from_the_file_if_another_process_refreshed(files, monkeypatch):
    files("tok_new", "r2", time.time() + 3600)
    auth._cached_tokens = {"access_token": "tok_old", "refresh_token": "r1", "expiry": 0}
    auth._cached_creds = {"client_id": "cid", "client_secret": "s"}

    def no_network(*a, **k):
        raise AssertionError("refreshed with a spent refresh token")

    monkeypatch.setattr("urllib.request.urlopen", no_network)
    assert auth.refresh_token() == "tok_new"


def test_a_401_rereads_the_file_and_retries_once(files, monkeypatch):
    files("tok_new", "r2", time.time() + 3600)
    auth._cached_tokens = {
        "access_token": "tok_old",
        "refresh_token": "r1",
        "expiry": time.time() + 3600,
    }
    auth._cached_creds = {"client_id": "cid", "client_secret": "s"}
    sent = []

    def fake_urlopen(req, timeout=None):
        sent.append(req.get_header("Authorization"))
        if req.get_header("Authorization") == "Bearer tok_old":
            raise _401()
        return _Resp({"accounts": []})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    assert api.get("/accounts") == {"accounts": []}
    assert sent == ["Bearer tok_old", "Bearer tok_new"]


def test_a_second_401_still_asks_to_reauthorise(files, monkeypatch):
    files("tok", "r", time.time() + 3600)
    calls = []

    def always_401(req, timeout=None):
        calls.append(req.get_method())
        raise _401()

    monkeypatch.setattr("urllib.request.urlopen", always_401)
    with pytest.raises(api.MonzoAuthError, match="monzo-mcp auth"):
        api.get("/accounts")
    assert calls == ["GET", "GET"]


if __name__ == "__main__":
    unittest.main()
