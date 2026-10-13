# Contributing

The repository has a ready-to-run development stack: a throwaway Paperless-ngx seeded with sample documents, plus the MCP server built from local source.

```bash
git clone https://github.com/Marceltov/paperless-mcp.git
cd paperless-mcp
docker compose up -d --build
curl http://localhost:9191/health   # -> ok
```

- Paperless: <http://localhost:9190>, user `admin`, password `paperless-mcp`
- MCP: `http://localhost:9191/mcp`, with OAuth on

Both are dev-only fixtures. The instance lives in Docker volumes; `docker compose down -v` throws it away, and the next `up` seeds a fresh one.

Run the tests against a clean stack with:

```bash
./run-tests.sh
```

To try a change on real data, there is a second stack that runs only the MCP server against a Paperless you already have. See [CONTRIBUTING.md](https://github.com/Marceltov/paperless-mcp/blob/main/CONTRIBUTING.md) for that, the seed data and the test layout.

This documentation is built from [`docs/`](https://github.com/Marceltov/paperless-mcp/tree/main/docs) with Material for MkDocs. Preview it locally with:

```bash
uvx --with mkdocs-material --with 'mkdocs<2' mkdocs serve
```
