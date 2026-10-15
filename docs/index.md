---
hide:
  - toc
---

<div class="tm-hero" markdown>

# Your Paperless-ngx archive, as tools for Claude

<p class="tm-hero__lead">The Paperless-ngx MCP server runs next to your Paperless-ngx server and turns your AI assistant into a front end for your documents: ask Claude on your phone, desktop or claude.ai, or any other MCP client, to find, read, tag and file them, through the Paperless REST API.</p>

[Set it up](getting-started.md){ .md-button .md-button--primary } [Connect a client](connecting.md){ .md-button }

</div>

Once the container is reachable, connecting Claude Code from any machine takes one command, then `/mcp` to log in with your Paperless username and password:

```bash
claude mcp add paperless-ngx --scope user --transport http \
  https://paperless-ngx-mcp.example.com/mcp
```

## What it does

- **Your assistant becomes the front end.** Instead of opening Paperless, you ask: "what did the electricity cost last quarter?", "tag everything from the tax office as taxes", "which invoices are still in the inbox?". Claude searches, reads and edits the documents for you.
- **Works from any device.** The Paperless-ngx MCP server is served over HTTP, so Claude on your laptop, phone or the web can reach it through a reverse proxy, and app clients sign in with OAuth.
- **Always matches your Paperless version.** The tools are generated at startup from the OpenAPI spec your own Paperless serves at `/api/schema/`, not from a list frozen into the image. Update Paperless, restart the sidecar, and new endpoints are there.
- **A toolset sized for an assistant.** Paperless has about 160 API operations. By default the 80 that deal with documents and their metadata become tools; administration (users, mail, workflows) stays off until you [turn it on](tools.md).
- **Runs as a sidecar.** One small container on the same Docker network as Paperless.
- **Two ways to sign in.** Log in once in the browser with your Paperless username and password (OAuth, for remote and app clients), or send an API token with each request (for scripts and the local network). See [Choosing an auth method](connecting.md#choosing-an-auth-method).
- **Stores nothing in token mode.** Each client's token is forwarded to Paperless per request, so one sidecar serves many users, each with their own permissions.

```mermaid
--8<-- "docs/diagrams/architecture.mmd"
```
