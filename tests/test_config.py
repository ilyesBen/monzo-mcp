"""Tests for config path resolution.

`config` computes its paths at import time from environment variables, so
these reload the module under a patched environment and assert on the reloaded
attributes. A cleanup reload restores the module to its default state so other
tests are unaffected.
"""

import importlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from monzo_mcp import config


def _reload_with_env(env):
    """Reload config with os.environ replaced by `env`; return the module."""
    with patch.dict(os.environ, env, clear=True):
        return importlib.reload(config)


class TestConfigOverrides(unittest.TestCase):
    def tearDown(self):
        # Restore the module to whatever the ambient environment produces so a
        # patched CONFIG_DIR/DB_PATH does not leak into later tests.
        importlib.reload(config)

    def test_config_dir_override(self):
        cfg = _reload_with_env({"MONZO_MCP_CONFIG_DIR": "/custom/cfg"})
        self.assertEqual(cfg.CONFIG_DIR, Path("/custom/cfg"))
        # Credential paths are derived from CONFIG_DIR, so they must follow it.
        self.assertEqual(cfg.MONZO_CLIENT_PATH, Path("/custom/cfg/monzo_client.json"))
        self.assertEqual(cfg.MONZO_TOKENS_PATH, Path("/custom/cfg/monzo_tokens.json"))

    def test_db_path_override(self):
        cfg = _reload_with_env({"MONZO_MCP_DB_PATH": "/custom/data/monzo.db"})
        self.assertEqual(cfg.DB_PATH, Path("/custom/data/monzo.db"))

    def test_callback_host_override(self):
        # The documented name for widening the callback bind. Renaming it
        # silently leaves the listener on localhost.
        cfg = _reload_with_env({"MONZO_MCP_CALLBACK_HOST": "0.0.0.0"})
        self.assertEqual(cfg.MONZO_CALLBACK_HOST, "0.0.0.0")

    def test_callback_host_defaults_to_loopback(self):
        cfg = _reload_with_env({})
        self.assertEqual(cfg.MONZO_CALLBACK_HOST, "localhost")

    def test_overrides_are_independent(self):
        # Overriding the DB path must not move CONFIG_DIR off its package default.
        cfg = _reload_with_env({"MONZO_MCP_DB_PATH": "/only/db.sqlite"})
        self.assertEqual(cfg.DB_PATH, Path("/only/db.sqlite"))
        self.assertEqual(cfg.CONFIG_DIR, cfg._DATA_ROOT / "config")

    def test_defaults_without_env(self):
        cfg = _reload_with_env({})
        self.assertEqual(cfg.CONFIG_DIR, cfg._DATA_ROOT / "config")
        self.assertEqual(cfg.DB_PATH, cfg._DATA_ROOT / "monzo.db")
        self.assertEqual(cfg.MONZO_CLIENT_PATH, cfg._DATA_ROOT / "config" / "monzo_client.json")
        self.assertEqual(cfg.MONZO_TOKENS_PATH, cfg._DATA_ROOT / "config" / "monzo_tokens.json")

    def test_package_root_is_repo_root(self):
        # _PACKAGE_ROOT is three levels up from src/monzo_mcp/config.py, i.e. the
        # repo root that holds pyproject.toml.
        cfg = _reload_with_env({})
        self.assertTrue((cfg._PACKAGE_ROOT / "pyproject.toml").exists())


class TestDefaultDataRoot(unittest.TestCase):
    """A source checkout keeps data beside the code; an install does not."""

    def test_a_checkout_keeps_data_in_the_repo(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "pyproject.toml").write_text("")
            self.assertEqual(config._default_data_root(root, {}), root)

    def test_an_installed_package_uses_the_user_config_dir(self):
        with tempfile.TemporaryDirectory() as d:
            site = Path(d) / "lib" / "python3.13"
            site.mkdir(parents=True)
            env = {"XDG_CONFIG_HOME": "/home/u/.cfg"}
            self.assertEqual(config._default_data_root(site, env), Path("/home/u/.cfg/monzo-mcp"))

    def test_without_xdg_it_falls_back_to_dot_config(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(
                config._default_data_root(Path(d), {}),
                Path.home() / ".config" / "monzo-mcp",
            )


class TestConfigConstants(unittest.TestCase):
    def test_api_constants(self):
        self.assertEqual(config.MONZO_API_BASE, "https://api.monzo.com")
        self.assertEqual(config.MONZO_AUTH_URL, "https://auth.monzo.com/")
        self.assertEqual(config.MONZO_TOKEN_URL, "https://api.monzo.com/oauth2/token")
        self.assertEqual(config.MONZO_CALLBACK_PORT, 6600)


if __name__ == "__main__":
    unittest.main()
