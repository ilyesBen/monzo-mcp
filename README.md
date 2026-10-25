# monzo-mcp

[![CI](https://github.com/ilyesBen/monzo-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/ilyesBen/monzo-mcp/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)

A read-only [MCP](https://modelcontextprotocol.io) server for the [Monzo](https://monzo.com) banking API. It lets Claude (or any MCP client) read balances, pots and transactions, search your history and break down spending, for **personal, joint and business** accounts.

It handles full OAuth with automatic token refresh, and keeps a local SQLite cache so your history survives Monzo's 90-day access limit.

**Using Claude Desktop?** Install the one-click extension instead: see [Connect Monzo to Claude Desktop](docs/claude-desktop.md).

This is a fork of [partymola/monzo-mcp](https://github.com/partymola/monzo-mcp) that adds business accounts, a Claude Desktop extension and browser sign-in, and returns less bank detail to the model. See [What this fork changes](#what-this-fork-changes).

## Tools

| Tool | What it does | Data source |
|---|---|---|
| `monzo_list_accounts` | Accounts with their type (personal, joint, business) and status | Live API |
| `monzo_get_balance` | Current balance and spend today for one account | Live API |
| `monzo_list_pots` | Pots and their balances for one account | Live API |
| `monzo_sync` | Sync transactions into the local cache | Live API → SQLite |
| `monzo_list_transactions` | List and filter cached transactions | Local cache |
| `monzo_search_transactions` | Search by merchant, payee, description or notes | Local cache |
| `monzo_spending` | Spending by category and top merchants for a month | Local cache |
| `monzo_login` | Sign in through the browser, for clients with no terminal | OAuth |

**Read-only.** No tool can move money, change pots or edit transactions. Every data tool is declared read-only to the client (`readOnlyHint`), and the only non-GET requests the server makes are the OAuth token exchange and refresh. `tests/test_read_only.py` fails if that changes. `monzo_login` only signs you in and saves tokens on your machine; it changes nothing at Monzo.

Balance and pot tools take `account_type` and default to `personal`. Pass `business` or `joint` for those accounts.

## How syncing works

The server only runs while your MCP client is open, and there is no background job. The cache tools sync automatically the first time they are called each day (UTC), then answer from the cache. Call `monzo_sync` for anything newer.

A failed automatic sync is silent and counts as that day's attempt. If results look stale, call `monzo_sync` yourself, which reports the error.

## Requirements

- Python 3.13 or later. With [uv](https://docs.astral.sh/uv/) you don't need it installed: uv fetches it.
- A Monzo account, and an OAuth client you register yourself (below). The Monzo developer API is for your own accounts only.

## 1. Register a Monzo OAuth client

Do this on a computer with your phone to hand. (Claude Desktop users: the [Desktop guide](docs/claude-desktop.md#step-1-create-your-monzo-oauth-client) has the same steps in more detail.)

1. **Sign in to the developer site.** Go to [developers.monzo.com](https://developers.monzo.com) and enter your Monzo email address. Open the emailed link **in the same browser** you started in; if your mail app opens it elsewhere, copy and paste it instead.
2. **Approve data access in the Monzo app.** Signing in sends an access request to the app. It often doesn't arrive as a notification, so open the app, approve the request and confirm with your PIN or biometrics. Then refresh the developer site. Until you approve, every action there fails with `forbidden.insufficient_permissions`, and you need to approve again each time you sign in.
3. **Create the client.** Go to **Clients → New OAuth Client** and set:
   - **Redirect URL:** `http://localhost:6600/callback`, exactly as written.
   - **Confidentiality:** **Confidential**. Only confidential clients get refresh tokens; without one you have to sign in again every few hours.
   - Name, description: anything. Logo: blank.
4. **Copy the Client ID** (starts with `oauth2client_`) **and Client secret** for the next step.

Signing in with the server later (`monzo-mcp auth` or `monzo_login`) sends a **second, separate** request to the app, which must also be approved.

## 2. Install and authenticate

### Option A: straight from GitHub with uvx

```sh
uvx --python 3.13 --from git+https://github.com/ilyesBen/monzo-mcp monzo-mcp auth
claude mcp add --scope user monzo -- \
  uvx --python 3.13 --from git+https://github.com/ilyesBen/monzo-mcp monzo-mcp
```

Credentials and the cache are stored in `~/.config/monzo-mcp/` (or `$XDG_CONFIG_HOME/monzo-mcp/`), so they survive reinstalls.

### Option B: clone (recommended for development)

```sh
git clone https://github.com/ilyesBen/monzo-mcp.git
cd monzo-mcp
uv venv --python 3.13 .venv
uv pip install -e .
.venv/bin/monzo-mcp auth
claude mcp add --scope user monzo -- "$PWD/.venv/bin/monzo-mcp"
```

Credentials and the cache are stored in the clone (`config/` and `monzo.db`), both gitignored. On Windows the script is `.venv\Scripts\monzo-mcp.exe`.

`--scope user` makes the server available in every Claude Code project.

### `auth` step by step

`monzo-mcp auth` asks for the Client ID and secret, opens your browser and emails you a sign-in link. If the link misbehaves, copy it and paste it into the same browser rather than letting your mail app open it. Then **approve the access request in the Monzo app**.

**Sync within 5 minutes of approving.** For 5 minutes after approval Monzo returns up to about 11 months of history; after that, only the last 90 days, with no error to tell you. Call `monzo_sync` straight away. See [Monzo's access window](#monzos-access-window).

### Claude Desktop

Use the extension: download [`monzo.mcpb`](https://github.com/ilyesBen/monzo-mcp/releases/latest/download/monzo.mcpb), double-click it, and enter your Client ID and secret. Then ask Claude to *"log in to Monzo"*, which runs `monzo_login`. The full walkthrough is in [docs/claude-desktop.md](docs/claude-desktop.md).

The extension stores its data in `~/.config/monzo-mcp/`, the same place as the uvx install, so Claude Code and Claude Desktop can share one sign-in.

### Other MCP clients

For Cursor and similar clients, add this to the client's MCP config:

```json
{
  "mcpServers": {
    "monzo": {
      "command": "uvx",
      "args": ["--python", "3.13", "--from", "git+https://github.com/ilyesBen/monzo-mcp", "monzo-mcp"]
    }
  }
}
```

## CLI

```
monzo-mcp              Start the MCP server (stdio)
monzo-mcp auth         Interactive OAuth setup (opens the browser)
monzo-mcp --version    Print the installed version
```

## Configuration

All optional:

| Variable | Default | Purpose |
|---|---|---|
| `MONZO_MCP_CONFIG_DIR` | `config/` in a clone, else `~/.config/monzo-mcp/config/` | OAuth client and token files |
| `MONZO_MCP_DB_PATH` | `monzo.db` in a clone, else `~/.config/monzo-mcp/monzo.db` | SQLite transaction cache |
| `MONZO_MCP_CALLBACK_HOST` | `localhost` | Interface the `auth` callback listener binds to. The redirect URI is unaffected. |

Set the same values for `auth` and for the server, or the server won't find the tokens `auth` saved. `auth` writes two files to the config directory: `monzo_client.json` (client ID and secret) and `monzo_tokens.json` (access and refresh tokens).

## Monzo's access window

Monzo's Strong Customer Authentication limits how far back the API reads:

- **Within 5 minutes of approving in the app:** up to about 11 months of history.
- **After that:** the last 90 days only.
- **Every 90 days** you need to run `monzo-mcp auth` and approve again.

The cache keeps everything already synced, so history older than 90 days is never lost once you have it. To backfill a range, pass `since` to `monzo_sync` (`2026-01-01` or `2026-01-01T14:30:00Z`). Beyond 90 days that only works inside the 5-minute window.

## Privacy

Whatever a tool returns is sent to your MCP client's model. Summaries (`monzo_spending`) send totals and merchant names; list and search send full transactions.

- For bank transfers, list and search return the **payee's name only**. Sort codes, account numbers and Monzo user IDs stay in the local cache.
- Tokens, the client secret and the cache never leave your machine. Credential files and the cache are created owner-only (mode 0600) on macOS and Linux.
- The cache is plain SQLite. Anyone who can read the file can read your transactions.

## What this fork changes

Forked from [partymola/monzo-mcp](https://github.com/partymola/monzo-mcp) at commit `76a42b2` (v0.10.0). Changes:

- **Business accounts.** `uk_business` accounts are synced and selectable as `account_type="business"`. Upstream skips them.
- **Payee name only.** List and search no longer return payees' sort codes and account numbers.
- **Install from GitHub.** Installed packages store data in `~/.config/monzo-mcp/` rather than inside the package, where a reinstall would delete it.
- **Owner-only cache.** The SQLite cache is created with mode 0600.
- **Claude Desktop extension and `monzo_login`.** A one-click `.mcpb` extension, and a tool that runs the `auth` flow from inside a client with no terminal.
- **Shared sign-in.** Monzo allows one live token per client, so two MCP clients sharing the token file used to log each other out on refresh. The server now re-reads the file and retries once.
- **Read-only declared and pinned.** Data tools carry `readOnlyHint`, and a test fails on any new non-GET request.
- **No Docker image or MCP registry entry.** Upstream publishes those under its own name; this fork installs from source or GitHub only.

Details are in [CHANGELOG.md](CHANGELOG.md).

## Troubleshooting

- **`forbidden.insufficient_permissions`** - an access request is waiting for approval in the Monzo app. Approve it and retry.
- **"SCA required" or only 90 days of history** - run `monzo-mcp auth`, approve in the app, then call `monzo_sync` within 5 minutes.
- **The server says it isn't configured after `auth` succeeded** - `auth` and the server are using different data directories. Check `MONZO_MCP_CONFIG_DIR` and `MONZO_MCP_DB_PATH` match for both, or that both run from the same install.
- **`No open personal account found`** - your login only has a business or joint account. Pass `account_type="business"` (or `"joint"`).
- **`auth` sits on "Waiting for callback..." after you approve** - the callback was not delivered. Press Ctrl-C and run it again.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md). Tests are fully offline: no real API calls, tokens or cache.

```sh
uv pip install -e ".[dev]"
.venv/bin/python -m pytest
.venv/bin/ruff check src tests && .venv/bin/ruff format --check src tests
scripts/build-mcpb.sh   # builds build/monzo.mcpb (needs Node.js for the mcpb CLI)
```

Pushing a tag `vX.Y.Z` that matches `pyproject.toml` runs the tests, builds `monzo.mcpb` and attaches it to a GitHub Release.

## License

GPL-3.0-or-later, as upstream. See [LICENSE](LICENSE). Original work © the monzo-mcp contributors; changes in this fork are listed above and in the changelog.
