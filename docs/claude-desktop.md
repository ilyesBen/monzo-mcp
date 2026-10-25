# Connect Monzo to Claude Desktop

Follow these steps to ask Claude Desktop questions about your Monzo account, such as "what did we spend on software last month?" or "what's our balance?". It takes about 10 minutes and you only do it once. It works for personal, joint and business accounts.

Claude can only read your Monzo data. It cannot move money, change pots or edit transactions.

## What you need

- **Claude Desktop**, installed and signed in. Download it from [claude.ai/download](https://claude.ai/download).
- **The Monzo app** on your phone, signed in to the account you want to connect.
- **The `monzo.mcpb` file.** [**Click here to download it**](https://github.com/ilyesBen/monzo-mcp/releases/latest/download/monzo.mcpb). The link always gets the newest version.

You don't need to install anything else.

## Step 1: Create your Monzo OAuth client

Monzo only lets you connect your own account, through a "client" you create yourself on Monzo's developer site. Do this on a computer, with your phone next to you.

### 1a. Sign in to the developer site

1. On your computer, go to [developers.monzo.com](https://developers.monzo.com) and click **Sign in with your Monzo account**.
2. Enter the email address you use for Monzo. Monzo emails you a sign-in link.
3. **Open the link in the same browser on your computer.** If it opens inside your email app, or on your phone, copy it and paste it into the browser tab where you started. Opening it anywhere else can fail with a "state mismatch" or authorisation error.

You're now on the developer site, but **you can't do anything yet**. You still need to approve it in the app.

### 1b. Approve data access in the Monzo app

As soon as you sign in, Monzo sends a request to your phone asking you to allow access to your data.

1. **Open the Monzo app on your phone.** The request often doesn't appear as a notification, so open the app even if nothing popped up. Look for the request on the home screen.
2. Tap to **approve** access, then confirm with your PIN, Face ID or fingerprint.
3. Go back to the developer site on your computer and **refresh the page**.

> If anything on the developer site shows `forbidden.insufficient_permissions`, this approval hasn't happened yet. Open the app, approve, then refresh. You need to approve again each time you sign in to the developer site.

### 1c. Create the client

1. On the developer site, go to **Clients** and click **New OAuth Client**.
2. Fill in the form:

   | Field | What to enter |
   |---|---|
   | **Name** | `Claude Desktop` |
   | **Logo URL** | Leave blank |
   | **Redirect URLs** | `http://localhost:6600/callback`, exactly as written: no `s` in `http`, no trailing slash |
   | **Description** | Anything, e.g. `Read-only access for Claude` |
   | **Confidentiality** | **Confidential**. Only confidential clients stay signed in; otherwise you'd have to sign in again every few hours. |

3. Click **Submit**.
4. Open the new client and keep the page open. You need its **Client ID** (it starts with `oauth2client_`) and **Client secret** in Step 2.

> 🔒 **Treat the client secret like a password.** Don't paste it into Slack, email or shared documents.

> **You'll approve in the app twice in total:** once now, for the developer site, and once in Step 3, when Claude signs in. They're separate requests, and each one must be approved.

## Step 2: Install the extension

1. Make sure Claude Desktop is open.
2. Double-click the **`monzo.mcpb`** file you downloaded. Claude Desktop shows an install screen for **Monzo**.
   - If double-clicking doesn't open Claude, go to Claude's **Settings → Extensions → Advanced settings → Install Extension…** and choose the file.
3. Click **Install**.
   - Claude may warn that the extension isn't signed or verified. That's expected for an internal tool; click **Install** again to confirm.
4. When Claude asks for the **Monzo Client ID** and **Monzo Client secret**, paste them from Step 1 and click **Save**.
5. Make sure the switch next to **Monzo** is turned **on**.

The first start can take a minute while Claude sets the extension up. Your client secret is saved in your computer's secure password storage (Keychain on Mac, Credential Manager on Windows), not in a plain file.

## Step 3: Sign in to Monzo

Have your phone ready: the last part is time-sensitive.

1. Start a new chat and ask Claude: *"Log in to Monzo."*
2. Claude asks permission to use the `monzo_login` tool. Click **Allow**. Your browser opens Monzo's sign-in page.
3. Enter your email address and open the link Monzo emails you. If the link opens in your email app, copy it and paste it into the same browser instead.
4. **Open the Monzo app and approve the new access request**, then confirm with your PIN or biometrics. This is a second request, separate from the one in Step 1b, and it may not arrive as a notification either.
5. **Straight away**, tell Claude: *"Sync Monzo."* For 5 minutes after you approve, Monzo shares about 11 months of history. After that, only the last 90 days.

## Step 4: Check it works

1. Click the **+** or **🔨 tools** button below the message box. You should see **Monzo** listed, with tools such as `monzo_get_balance`.
2. Ask Claude: *"Using Monzo, what's my balance?"* For a business account, say *"business balance"*.
3. To stop Claude asking permission every time, click **Always allow**.

You're done. 🎉

## Things to try

- "What did we spend last month, by category?"
- "How much do we spend on eating out per month?"
- "Search Monzo for payments to AWS this year."
- "What are our biggest payees over the last 3 months?"
- "Find subscriptions we might not need."

## If something goes wrong

| What you see | What to do |
|---|---|
| Double-clicking the file does nothing | Install it from Claude's **Settings → Extensions → Advanced settings → Install Extension…** instead. |
| **Monzo** isn't in the tools list | In **Settings → Extensions**, check the Monzo switch is on. Then quit Claude completely (⌘ Q on Mac, or **Quit** from the system tray on Windows) and reopen it. |
| `insufficient_permissions` on developers.monzo.com | Open the Monzo app, approve the access request (Step 1b), then refresh the page. |
| Claude says Monzo isn't configured | Ask Claude to *"log in to Monzo"* (Step 3). |
| Claude says the token is invalid or "SCA required" | Monzo asks you to sign in again every 90 days. Repeat Step 3. |
| Only the last 90 days of history | You synced more than 5 minutes after approving. Repeat Step 3 and sync straight away. |
| "No open personal account found" | Your login only has a business or joint account. Ask for the *business* (or *joint*) account. |
| The browser never opens, or sign-in doesn't finish | Check the redirect URL in Step 1 is exactly `http://localhost:6600/callback`, then ask Claude to log in again. |
| Something else | Take a screenshot of the error in **Settings → Extensions → Monzo** and send it to whoever shared this guide. |

## Updating to a new version

[Download the newest `monzo.mcpb`](https://github.com/ilyesBen/monzo-mcp/releases/latest/download/monzo.mcpb) and double-click it, just as you did the first time. Your settings, sign-in and transaction history are kept.

## Removing it later

- **To remove the extension:** go to **Settings → Extensions → Monzo** and click **Uninstall**.
- **To revoke access:** delete the OAuth client at [developers.monzo.com](https://developers.monzo.com).
- **To delete the saved data:** delete the `.config/monzo-mcp` folder in your home folder. It holds your sign-in and the transaction history Claude has downloaded.

## Good to know

- **The connector runs on your own computer.** It talks directly to Monzo. Your client secret, sign-in and transactions don't pass through any other company's servers.
- **What Claude can see:** only what it fetches to answer your questions. Those results are sent to Anthropic, the same as anything else you show Claude. For bank transfers, Claude sees the payee's name but not their sort code or account number.
- **Syncing happens when you ask.** There is no background job. The first transaction question each day fetches anything new; say *"sync Monzo"* for the very latest.
- **Claude Code and Claude Desktop can share one sign-in** if both use the default `~/.config/monzo-mcp` folder.
