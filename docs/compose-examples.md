# Compose examples

paperless-mcp runs next to a Paperless-ngx server you already have. Pick the example that matches how Paperless is deployed: in the same compose file, or as its own compose project. Both are in the repo's [`examples/`](https://github.com/Marceltov/paperless-mcp/tree/main/examples) directory.

## Don't have Paperless-ngx yet?

paperless-mcp connects to an existing Paperless-ngx server. To set one up, follow Paperless's own [setup guide](https://docs.paperless-ngx.com/setup/), then come back here.

## In Paperless's compose file

Add the `paperless-mcp` service and the `mcp-oauth` volume to the `docker-compose.yaml` that runs Paperless. Its settings go in a separate `paperless-mcp.env`, so they don't mix with the env files Paperless already uses. Copy `paperless-mcp.env.example` to `paperless-mcp.env` next to the compose file, adjust it, and run `docker compose up -d paperless-mcp`.

=== "docker-compose.yaml"

    ```yaml
    --8<-- "examples/same-project/docker-compose.yaml"
    ```

=== "paperless-mcp.env"

    ```ini
    --8<-- "examples/same-project/paperless-mcp.env.example"
    ```

Both services share the compose network, so `webserver` resolves to your Paperless container.

## As a separate compose project

Use this when you'd rather keep paperless-mcp out of Paperless's compose file. It joins the Docker network Paperless is already on. Put the files in their own folder, copy `.env.example` to `.env`, adjust it, and run `docker compose up -d`.

=== "docker-compose.yaml"

    ```yaml
    --8<-- "examples/separate-project/docker-compose.yaml"
    ```

=== ".env"

    ```ini
    --8<-- "examples/separate-project/.env.example"
    ```

To find `PAPERLESS_NETWORK`, run `docker network ls`, or `docker inspect <paperless container>` to see which network Paperless is on. `PAPERLESS_URL` uses Paperless's service or container name on that network.

## Turning on OAuth

In either example, fill in `MCP_BASE_URL` and `MCP_OAUTH_SECRET` in the env file and recreate the container with `docker compose up -d`. Once the file holds the secret, keep it private (`chmod 600`) and out of version control. Every setting is described under [Configuration](configuration.md).
