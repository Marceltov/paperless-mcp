---
status: accepted
date: 2026-10-13
---

# OAuth 2.1 login via the Paperless login, alongside raw API tokens

## Context and Problem Statement

App and remote MCP clients (Claude desktop, web and mobile, IDEs) expect the MCP authorization spec: OAuth 2.1 with discovery, dynamic client registration and PKCE. Paperless-ngx's REST API has no OAuth of its own. It accepts a per-user API token (`Authorization: Token …`), so whatever OAuth flow a client completes, the server must end up holding that user's API token to forward. [trilium-mcp](https://github.com/Marceltov/trilium-mcp) solved the same problem for Trilium, and this project follows its design where Paperless allows.

## Decision Drivers

* Keep one sidecar per Paperless, with no external identity provider to run or register with.
* Token clients (scripts, the local network) must work with no OAuth configuration at all.
* Paperless is multi-user: a client must act as the user who logged in, with that user's permissions.
* Accounts that sign in to Paperless through single sign-on must not be locked out.

## Considered Options

* The MCP server is its own authorization server; login is the Paperless username and password, exchanged via `POST /api/token/` for the user's API token.
* An external identity provider via FastMCP's OAuth proxy, with a configured identity → API token mapping.
* Stay token-only.

## Decision Outcome

Chosen option: "the MCP server is its own authorization server", because it needs no external service, works for every Paperless user without per-user configuration, and builds on FastMCP's `OAuthProvider`, so we write only the login page and storage.

`MCP_AUTH_MODE=token|oauth|both` selects the gate. Unset means `both` when `MCP_BASE_URL` and `MCP_OAUTH_SECRET` are set, otherwise `token`. In `both`, bearers the server didn't issue (no `pmcp_` prefix) are forwarded to Paperless as raw API tokens.

Three things differ from trilium-mcp, all because of how Paperless works:

* **The login asks for a username**, and for a two-factor code when the account has one. `/api/token/` takes all three.
* **Revoking does not delete anything in Paperless.** Trilium mints a fresh ETAPI token per login, so revoking a client can delete its token. Paperless keeps one token per user (`/api/token/` returns the existing one, creating it only if there is none), shared with every other client and the web UI. Revoke therefore drops only the OAuth pair.
* **The login page also accepts a pasted API token.** A single-sign-on account has no password for `/api/token/` to check. The token is validated against `GET /api/profile/` before anything is issued. This keeps the claude.ai connector, which is OAuth-only, usable for such accounts.

### Consequences

* Good, because app clients connect with just a URL, and each user gets their own permissions.
* Good, because token clients are unaffected.
* Bad, because the server is no longer stateless in OAuth modes: it stores client registrations and users' API tokens (Fernet-encrypted, `/data/oauth`), which needs a volume and a secret to protect.
* Bad, because the issuer must be HTTPS (localhost excepted, an MCP SDK rule), so OAuth needs a TLS reverse proxy.
* Bad, because there is no per-client credential in Paperless: cutting one client off happens on this server, and cutting off a leaked API token means regenerating it for all of that user's clients.
* Bad, because every login reaches Paperless from the sidecar's address, so Paperless's login throttle (five a minute) is shared by all users of one sidecar.
* Bad, because dynamic client registration lets anyone send a user a genuine login link; the login page shows the client name and redirect host as the mitigation, with no redirect allowlist yet.

### Confirmation

`app/tests/test_oauth.py` drives the full flow in-process (register → authorize → login → token → tool call carries the user's API token) and covers the two-factor code, the pasted token, mode selection, rotation, revoke and the raw-header passthrough; `app/tests/live/test_oauth_flow.py` repeats the flow against the dev stack.

## More Information

Flow diagrams: the OAuth section of [How it works](../how-it-works.md#oauth). Implementation: `PaperlessOAuthProvider`, `resolve_auth_mode` and `wrap_app` in `app/server.py`.
