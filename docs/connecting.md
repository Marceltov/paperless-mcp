# Connect a client

## Choosing an auth method

| Method | Best for | How the client authenticates |
| ------ | -------- | ---------------------------- |
| **OAuth** | Remote access and app clients (Claude desktop, web and mobile, IDEs, anything that can open a browser) | Only the URL is configured. On first connect a browser page asks for your Paperless username and password once, and the server fetches your API token from Paperless, creating it if you have none. Nothing secret is pasted into client config. |
| **API token** | Headless clients (scripts, CI, servers, agents with no browser) and the local network | The token from *My Profile → API Auth Token* goes in the `Authorization` header on every request. |

Both work side by side in the default `both` mode once OAuth is configured (`MCP_BASE_URL` and `MCP_OAUTH_SECRET`, see [OAuth details](configuration.md#oauth-details)). Without those variables the server accepts API tokens only. OAuth needs an **HTTPS** public URL (plain `http` only for `localhost`), so it goes with a [reverse proxy](reverse-proxy.md). An API token over plain HTTP is for networks you trust.

Either way the client acts as **your Paperless user**: it sees and can change exactly what you can in the web UI, and Paperless's own permissions apply.

!!! note "Signing in to Paperless through single sign-on?"

    If your Paperless account comes from an identity provider (Authentik, Keycloak, …) and has no password of its own, there is nothing to type into the login page. Open *Signed in through single sign-on* on that page and paste your API token instead, or give the account a password in Paperless.

## Pick your client

- [Claude Code](claude-code.md): one `claude mcp add` command, with OAuth or an API token.
- [Claude.ai](claude-ai.md): a custom connector on the web, which the desktop and mobile apps then use too. OAuth only.

Any other MCP client that speaks streamable HTTP works the same way: give it the `/mcp` URL, and either let it run the OAuth login or set the `Authorization` header.
