# Security

The MCP endpoint grants **read and write access to your documents**, with the permissions of the Paperless user whose token is used. Every request must carry either a Paperless API token or an OAuth access token issued by this server in the `Authorization` header. Requests with no `Authorization` header are rejected with `401` before reaching any tool.

The server never validates an API token itself: Paperless enforces validity and permissions when the forwarded request arrives. In token-only mode the server holds no secret of its own. The `/health` endpoint is always unauthenticated, for the container healthcheck.

## Tokens in transit

The token is sent in the `Authorization` header on every call. Over plain HTTP it travels in cleartext, so either keep traffic on a **trusted network** (a LAN or the Docker network) or put TLS in front with a [reverse proxy](reverse-proxy.md).

## One API token per user

Paperless keeps a single API token per user. The web UI shows it under *My Profile*, and every client of that user, through this server or not, uses the same one. That has consequences worth knowing:

- An OAuth login doesn't create a separate credential per client. It fetches that one token, and creates it only if the user had none.
- Revoking a client's OAuth token (or removing the connector in the app) cuts that client off at this server and leaves the Paperless token untouched, so other clients keep working.
- To cut off **everything** at once, regenerate the token in *My Profile*. Clients using the raw token must be given the new one; OAuth clients log in again.
- With `MCP_AUTH_MODE=oauth`, a client never holds the Paperless token, only opaque `pmcp_` tokens that this server can revoke one by one.

## Host allowlist

By default the server accepts requests for **any** `Host` (FastMCP's DNS-rebinding protection is off), so it can be reached by LAN IP or by the domain your reverse proxy forwards. To lock this down, set `MCP_ALLOWED_HOSTS` to a comma-separated list of the `host[:port]` values you actually use, for example `192.168.1.50:8081,paperless-mcp.example.com`. `localhost` is always allowed; anything else gets a `421`.

## OAuth secrets

With [OAuth](configuration.md#oauth-details) enabled the server does hold secrets: the API tokens of the users who logged in, stored Fernet-encrypted under `/data/oauth` with the key from `MCP_OAUTH_SECRET`. Protect that volume and that variable like the tokens themselves.

The login page shows which client is asking and where the authorization code will be sent. Only approve logins you started yourself, because any client can register and send you a login link.

The login page forwards username and password attempts to Paperless, so Paperless's own login throttle (five a minute by default) is what limits guessing.

## What the tools can't do

Whatever toolsets are enabled, no tool can mint or replace an API token, change two-factor settings or disconnect a social login. See [what is left out](tools.md#what-is-left-out-in-every-toolset). Administration (users, groups, mail accounts, workflows, application config) is off unless you add those [toolsets](tools.md#toolsets).

## Startup errors

If the OpenAPI spec can't be loaded or the auth configuration is invalid, the server still starts and completes the MCP handshake, but exposes only a single `startup_error` tool describing how to fix it, rather than failing with an opaque connection error.
