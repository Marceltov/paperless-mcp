# Contributing

Everything runs in Docker; `uv` is used for the Python side (`app/`). There are two development stacks.

## The seeded dev stack

A throwaway Paperless-ngx with sample data, plus the MCP server built from local source. Use it for anything that writes.

```bash
docker compose up -d --build     # rebuild after any change under app/
curl http://localhost:9191/health   # -> ok
```

| | URL | Credentials |
| - | --- | ----------- |
| Paperless-ngx | <http://localhost:9190> | `admin` / `paperless-ngx-mcp` |
| MCP server | `http://localhost:9191/mcp` | the admin's API token, or the OAuth login |

These are **committed dev fixtures** for the disposable instance. Never reuse them anywhere real.

Connect Claude Code to it with OAuth:

```bash
claude mcp add paperless-ngx-dev --transport http http://localhost:9191/mcp
```

### The seed

On first start the one-shot `seed` service runs [`dev/seed/seed.py`](dev/seed/seed.py). Through the REST API it creates four correspondents, four document types, five tags and a custom field, uploads the six text files in [`dev/seed/documents/`](dev/seed/documents/) with that metadata, and waits until Paperless has consumed them. The MCP container starts only after the seed has finished, so a healthy MCP means a seeded Paperless.

The seed skips an instance that already holds documents. To get back to the pristine state, throw the volumes away:

```bash
docker compose down -v && docker compose up -d --build
```

To change the seed, edit `seed.py` or the files next to it and reset as above. The documents are plain text on purpose: Paperless consumes them in a second, with no OCR.

## The live stack

Only the MCP server, built from local source, pointed at a **real** Paperless-ngx. Use it to see how a change behaves on real data: thousands of documents, your own tags and custom fields, whatever API version that instance runs.

```bash
cp .env.live.example .env.live   # set PAPERLESS_URL, and PAPERLESS_TOKEN for the smoke test
docker compose --env-file .env.live -f docker-compose.live.yaml up -d --build
```

The MCP endpoint is `http://localhost:9192/mcp`. On startup it downloads the OpenAPI spec from that instance, so this is also how you check the server against a Paperless version other than the dev stack's.

`.env.live` is gitignored and holds a real credential; keep it `chmod 600`.

A read-only smoke test calls the listing and reading tools through that stack and prints one line each:

```bash
cd app && uv run --env-file ../.env.live python ../dev/live-smoke.py
```

Tools called through the live stack change real documents. The test suite never targets it: the live tests are pinned to `localhost:9190` / `localhost:9191` and ignore the environment (`app/tests/test_live_target.py` guards this).

## Tests

```bash
./run-tests.sh                   # clean stack -> pytest -> teardown
./run-tests.sh tests/live -q     # extra args pass through to pytest
./run-tests.sh -k upload         # a single test by keyword
KEEP_STACK=1 ./run-tests.sh      # leave the stack running afterwards
```

`run-tests.sh` removes the dev stack with its volumes, starts a fresh one, waits for the MCP health check, runs pytest and tears everything down again, also when a test fails. Without `uv` on the machine it runs pytest in uv's container image.

Against a stack that is already up:

```bash
cd app && uv run pytest
cd app && uv run pytest -k test_strip_scheme   # single test
```

Two kinds of tests live under `app/tests/`:

- **Unit tests** (`test_*.py`) drive `server.py` with an httpx mock transport standing in for Paperless, and the bundled spec. No network.
- **Live tests** (`live/`) drive the real MCP server over HTTP against the dev stack. They skip themselves when `http://localhost:9191/health` doesn't answer. They create and delete objects but clean up after themselves; uploaded documents are emptied from the trash.

`test_coverage.py` is a guard: every tool in the default toolsets needs a live test, except the ones listed there with a reason (they need an AI backend, an SMTP server, or PDFs).

## The bundled spec

`app/paperless-api.openapi.json` is the fallback for when the download at startup fails, and what the unit tests run against. Refresh it from any current Paperless, for example the dev stack:

```bash
curl -s 'http://localhost:9190/api/schema/?format=json' -o app/paperless-api.openapi.json
```

Then run the tests: tool names and counts in the unit tests and the docs follow the spec.

## Documentation

User-facing docs live in `docs/` (navigation in `mkdocs.yml`); the README is a short intro that links to the site. Preview with:

```bash
uvx --with mkdocs-material --with 'mkdocs<2' mkdocs serve
```

The compose files under `examples/` are embedded in `docs/compose-examples.md`; after editing them, copy the `.env.example` files into place and check with `docker compose config`.

## Releases

Every branch push builds an image tagged `:<branch>`. A `v*` tag builds the versioned release (`:1.2.3`, `:1.2`, `:1`, `:latest`) and a GitHub release.
