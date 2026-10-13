# Quick start

Three steps: add one service to your compose file, make it reachable, and point your client at it. You need a running Paperless-ngx 2.15 or newer (the first version that serves its OpenAPI spec).

## 1. Add paperless-mcp to your compose file

Add one service to the `docker-compose.yaml` that runs Paperless. It pulls the prebuilt image, so there's nothing to clone or build:

```yaml
services:
  webserver:
    # ... your existing Paperless-ngx service ...

  paperless-mcp:
    image: ghcr.io/marceltov/paperless-mcp:latest
    container_name: paperless-mcp
    restart: unless-stopped
    environment:
      # Paperless's service name on this compose network, port 8000.
      PAPERLESS_URL: http://webserver:8000
    ports:
      - "8081:8081"
```

Both services share the compose network, so `webserver` (the service name in Paperless's own compose files) resolves to your Paperless container. Is Paperless in its own compose project? Use the [separate compose project](compose-examples.md#as-a-separate-compose-project) example instead.

Start it and check that it's up:

```bash
docker compose up -d paperless-mcp
curl http://localhost:8081/health   # -> ok
docker compose logs paperless-mcp   # -> OpenAPI spec: http://webserver:8000/api/schema/
```

On startup paperless-mcp downloads the OpenAPI spec from your Paperless and generates the tools from it. If Paperless is still booting it waits up to a minute; see [the spec download](configuration.md#the-openapi-spec).

## 2. Make it reachable

The MCP endpoint is served on port 8081 at `/mcp`. How your clients reach it depends on where they run:

=== "Trusted local network"

    Clients on the same network connect directly by IP or hostname, over plain HTTP:

    ```
    http://192.168.1.50:8081/mcp
    ```

    The API token travels in cleartext, so only do this on a network you trust.

=== "Reverse proxy (HTTPS)"

    For access from anywhere, put paperless-mcp behind a reverse proxy that terminates TLS. With [Caddy](https://caddyserver.com), which fetches certificates automatically:

    ```
    paperless-mcp.example.com {
        reverse_proxy paperless-mcp:8081
    }
    ```

    Clients then connect to `https://paperless-mcp.example.com/mcp`. HTTPS is also required for [OAuth](claude-code.md#oauth). More in [Reverse proxy and TLS](reverse-proxy.md).

## 3. Connect your MCP client

Copy your API token from Paperless (*My Profile → API Auth Token*; click the refresh icon if the field is empty), then register the server's address with it on the machine running your client:

```bash
claude mcp add paperless --scope user --transport http \
  https://paperless-mcp.example.com/mcp \
  --header "Authorization: YOUR_PAPERLESS_API_TOKEN"
```

Your client now has the Paperless tools. Ask it to search your documents to try it out.

## Next steps

- **Log in with your Paperless username and password instead of a token.** Turn on [OAuth](claude-code.md#oauth) for app clients like Claude on desktop, web and mobile; the [compose examples](compose-examples.md) show the settings.
- **Choose what the assistant may touch.** See [Tools](tools.md) for the default toolsets and how to add administration or narrow it down.
- **Lock it down.** Read [Security](security.md), and restrict accepted host names with `MCP_ALLOWED_HOSTS`.
