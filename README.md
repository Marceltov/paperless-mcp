<h1 align="center"><a href="https://github.com/Marceltov/paperless-ngx-mcp">Paperless-ngx MCP server</a></h1>

<p align="center">
  <a href="https://paperless-ngx-mcp.marceltov.de/">
    <img alt="Documentation" src="https://img.shields.io/badge/docs-paperless--mcp.marceltov.de-2f7a27">
  </a>
  <a href="https://github.com/Marceltov/paperless-ngx-mcp/pkgs/container/paperless-ngx-mcp">
    <img alt="GHCR image" src="https://img.shields.io/github/v/release/Marceltov/paperless-ngx-mcp?logo=docker&logoColor=white&label=ghcr.io%2Fmarceltov%2Fpaperless-ngx-mcp&color=2496ED">
  </a>
  <a href="LICENSE">
    <img alt="License: AGPL v3" src="https://img.shields.io/badge/License-AGPL_v3-blue.svg">
  </a>
</p>

A standalone [MCP](https://modelcontextprotocol.io) server that exposes the
[Paperless-ngx](https://docs.paperless-ngx.com) REST API as MCP tools. It runs as a
**container sidecar** next to your Paperless instance. At startup it downloads the
OpenAPI spec your Paperless serves at `/api/schema/` and turns it into tools with
`FastMCP.from_openapi`, so they match the version you run: by default the **80 tools**
for documents and their metadata (`documents_list`, `documents_retrieve`,
`documents_partial_update`, `tags_create`, `search_retrieve`, …), or all ~140 with
`MCP_TOOLSETS=all`. It is served over streamable **HTTP**, so any MCP client connects
to it by URL, with an API token or an OAuth login.

It is the Paperless counterpart of [trilium-mcp](https://github.com/Marceltov/trilium-mcp)
and shares its design.

## Documentation

**Full documentation: [paperless-ngx-mcp.marceltov.de](https://paperless-ngx-mcp.marceltov.de/)**

- [Quick start](https://paperless-ngx-mcp.marceltov.de/getting-started/): add the container, connect a client
- [Connect a client](https://paperless-ngx-mcp.marceltov.de/connecting/): OAuth or API token, Claude Code, Claude.ai
- [Tools](https://paperless-ngx-mcp.marceltov.de/tools/): the default toolsets and how to change them
- [Configuration](https://paperless-ngx-mcp.marceltov.de/configuration/), [reverse proxy and TLS](https://paperless-ngx-mcp.marceltov.de/reverse-proxy/) and [security](https://paperless-ngx-mcp.marceltov.de/security/)
- [How it works](https://paperless-ngx-mcp.marceltov.de/how-it-works/): architecture and request flows

## Quick start

Add the service next to your Paperless in `docker-compose.yaml`:

```yaml
  paperless-ngx-mcp:
    image: ghcr.io/marceltov/paperless-ngx-mcp:latest
    restart: unless-stopped
    environment:
      PAPERLESS_URL: http://webserver:8000
    ports:
      - "8081:8081"
```

Then copy your API token from Paperless (*My Profile → API Auth Token*) and connect your client:

```bash
docker compose up -d paperless-ngx-mcp
claude mcp add paperless-ngx --scope user --transport http \
  https://paperless-ngx-mcp.example.com/mcp \
  --header "Authorization: YOUR_PAPERLESS_API_TOKEN"
```

To log in with your Paperless username and password instead, set `MCP_BASE_URL` and
`MCP_OAUTH_SECRET` and leave the header out. See the
[quick start](https://paperless-ngx-mcp.marceltov.de/getting-started/).

## Contributing

For local development there's a ready-to-run stack: a throwaway Paperless-ngx seeded with sample documents plus the MCP server built from local source (`docker compose up -d --build`), and a second one that runs the server against a real Paperless. See [CONTRIBUTING.md](CONTRIBUTING.md) for the dev setup, seed-instance credentials, and how to run the tests. The documentation site is built from [`docs/`](docs/) with Material for MkDocs.

## License

Copyright © 2026 Marcel Bruckner.

Licensed under the [GNU Affero General Public License v3.0 or later](LICENSE) (AGPL-3.0-or-later). You may use, modify, and redistribute it, but any modified version — **including one you run as a network service** — must be released under the same license with its source made available to its users, and the original copyright notice preserved. See [LICENSE](LICENSE) for the full terms.
