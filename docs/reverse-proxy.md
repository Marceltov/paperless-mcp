# Reverse proxy and TLS

The container serves plain HTTP on `:8081`. Terminate TLS at your reverse proxy, so the token never crosses an untrusted network in cleartext. OAuth requires this: its public URL must be HTTPS.

A minimal Caddyfile:

```
paperless-ngx-mcp.example.com {
    reverse_proxy paperless-ngx-mcp:8081
}
```

Then set `MCP_BASE_URL=https://paperless-ngx-mcp.example.com` if you use OAuth, and consider restricting accepted hosts with [`MCP_ALLOWED_HOSTS`](security.md#host-allowlist).

Give the Paperless-ngx MCP server its own host name rather than a path under Paperless's: OAuth discovery uses `/.well-known/…` paths at the root of the host.

!!! warning "Don't put a login wall in front of it"

    If your proxy protects sites with forward auth (Authentik, Authelia, an access gateway), exempt this host. MCP clients can't complete a browser login at the proxy; they authenticate to the Paperless-ngx MCP server itself, with OAuth or a token.

Direct `http://<lan-ip>:8081` access without a proxy is fine on a network you trust, with an API token.
