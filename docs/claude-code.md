# Claude Code

Register paperless-mcp with `claude mcp add`. Pick the [auth method](connecting.md#choosing-an-auth-method) per connection.

## OAuth

Register the URL with no header. The client opens the login page on first use:

```bash
claude mcp add paperless --scope user --transport http \
  https://paperless-mcp.example.com/mcp
```

In Claude Code, run `/mcp` and pick the server to authenticate. Enter your Paperless username and password (and the two-factor code, if your account has one).

## API token

The API token is the credential: pass it in the `Authorization` header. Point the URL at wherever paperless-mcp is reachable.

=== "Behind a reverse proxy (TLS)"

    ```bash
    claude mcp add paperless --scope user --transport http \
      https://paperless-mcp.example.com/mcp \
      --header "Authorization: YOUR_PAPERLESS_API_TOKEN"
    ```

=== "On a trusted local network"

    ```bash
    claude mcp add paperless --scope user --transport http \
      http://192.168.1.50:8081/mcp \
      --header "Authorization: YOUR_PAPERLESS_API_TOKEN"
    ```

=== "`.mcp.json`"

    Commit a project-level config instead, filling in your host and token (a copy is in the repo as [`.mcp.json`](https://github.com/Marceltov/paperless-mcp/blob/main/.mcp.json)):

    ```json
    {
      "mcpServers": {
        "paperless": {
          "type": "http",
          "url": "https://paperless-mcp.example.com/mcp",
          "headers": {
            "Authorization": "YOUR_PAPERLESS_API_TOKEN"
          }
        }
      }
    }
    ```

The header may hold the bare token, `Bearer YOUR_TOKEN`, or Paperless's own form `Token YOUR_TOKEN`; all three are forwarded to Paperless as `Token YOUR_TOKEN`.

## User or project scope

`--scope user` registers the server across all your projects, which is usually what you want for a personal archive. Drop it to fall back to the default local scope, available only to you in the current project. This works the same with either auth method.
