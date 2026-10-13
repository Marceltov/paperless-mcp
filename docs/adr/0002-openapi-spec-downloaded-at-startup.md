---
status: accepted
date: 2026-10-13
---

# The OpenAPI spec is downloaded from Paperless at startup

## Context and Problem Statement

The tools are generated from an OpenAPI spec. trilium-mcp bundles Trilium's spec in its image, because Trilium doesn't serve one and its ETAPI changes rarely. Paperless-ngx generates its spec from its own code and serves it at `/api/schema/`, and its API moves with every release: the spec of the instance this project was developed against has 163 operations and API version 10. A bundled spec would describe whichever Paperless the image was built against, not the one a user runs.

## Considered Options

* Download the spec from the Paperless instance at startup, with a bundled snapshot as the fallback.
* Bundle the spec only, and release a new image for every Paperless release.
* Download only, and fail when Paperless can't be reached.

## Decision Outcome

Chosen option: "download at startup, bundled snapshot as fallback". The server requests `PAPERLESS_URL/api/schema/?format=json`, retrying connection errors and `5xx` answers for `PAPERLESS_SPEC_WAIT` seconds (default 60) because in a compose file both containers start together and Paperless boots slowly. Any other answer fails at once. If the download fails, the bundled snapshot is used and the log says so. `PAPERLESS_API_SPEC` pins the spec to a file or URL, with no fallback.

The API version sent to Paperless (`Accept: application/json; version=N`) is read from the same spec's `info.version`, so the request shapes and the tools always agree.

### Consequences

* Good, because the tools match the running Paperless without a new image, including endpoints added after the image was built.
* Good, because a Paperless that is briefly down at startup doesn't leave the sidecar without tools.
* Bad, because the tool surface is no longer fixed per image version: two users of the same image can see different tools.
* Bad, because the fallback can silently describe a different version; the only signal is the log line naming the spec source.
* Bad, because the spec is read once, so a Paperless update needs a sidecar restart.
* Bad, because the spec is trusted as served. Its repairs (`normalize_operation`) are written against known quirks and can go stale when Paperless fixes or changes them.

### Confirmation

`app/tests/test_spec.py` covers the download, the retry, the fallback, the pinned override and the version parsing. The dev stack downloads the spec from its own Paperless on every start, so the live tests run against a freshly downloaded spec; the unit tests run against the bundled one.

## More Information

Refresh the bundled snapshot from any Paperless with `curl -s '<url>/api/schema/?format=json' -o app/paperless-api.openapi.json`. Implementation: `resolve_spec`, `download_spec` and `api_version` in `app/server.py`.
