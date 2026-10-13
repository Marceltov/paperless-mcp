"""Read-only smoke test of an MCP server pointed at a REAL Paperless-ngx.

For docker-compose.live.yaml: it checks that the tools generated from that
instance's own OpenAPI spec work on real data. It only ever calls tools that
read, so it is safe to run against an archive you care about.

    cd app && uv run --env-file ../.env.live python ../dev/live-smoke.py

Needs PAPERLESS_TOKEN (an API token of that instance); MCP_URL defaults to the
live stack on localhost:9192.
"""

import asyncio
import json
import os
import sys

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

MCP_URL = os.environ.get("MCP_URL", "http://localhost:9192/mcp")
TOKEN = os.environ.get("PAPERLESS_TOKEN", "").strip()

# Read-only calls; the document ID for the per-document ones is taken from the
# first result of documents_list.
LISTS = [
    ("statistics_retrieve", {}),
    ("documents_list", {"page_size": 3, "fields": ["id", "title", "created"]}),
    ("correspondents_list", {"page_size": 3}),
    ("document_types_list", {"page_size": 3}),
    ("tags_list", {"page_size": 3}),
    ("storage_paths_list", {"page_size": 3}),
    ("custom_fields_list", {"page_size": 3}),
    ("saved_views_list", {"page_size": 3}),
    ("tasks_status_counts_retrieve", {}),
    ("trash_list", {"page_size": 1}),
]
PER_DOCUMENT = [
    "documents_retrieve", "documents_metadata_retrieve", "documents_suggestions_retrieve",
    "documents_notes_list", "documents_thumb_retrieve", "documents_download_retrieve",
]


def summarize(result) -> str:
    first = result.content[0] if result.content else None
    if first is None:
        return "(empty)"
    if first.type != "text":
        return f"<{first.type} {getattr(first, 'mimeType', '')}>"
    try:
        data = json.loads(first.text)
    except ValueError:
        return f"{len(first.text)} chars of text"
    if isinstance(data, dict) and set(data) == {"result"}:
        data = data["result"]  # FastMCP's wrapper around a bare array or scalar
    if isinstance(data, dict) and "count" in data:
        return f"count={data['count']}"
    if isinstance(data, dict):
        return "keys: " + ", ".join(list(data)[:6])
    return f"{type(data).__name__} of {len(data)}" if hasattr(data, "__len__") else repr(data)


async def main() -> int:
    if not TOKEN:
        sys.exit("PAPERLESS_TOKEN is not set (see .env.live.example).")
    transport = StreamableHttpTransport(MCP_URL, headers={"Authorization": TOKEN})
    failures = 0
    async with Client(transport) as client:
        tools = await client.list_tools()
        print(f"{len(tools)} tools from {MCP_URL}")
        calls = list(LISTS)
        listing = await client.call_tool("documents_list", {"page_size": 1, "fields": ["id"]})
        documents = json.loads(listing.content[0].text)["results"]
        if documents:
            calls += [(name, {"id": documents[0]["id"]}) for name in PER_DOCUMENT]
        for name, args in calls:
            try:
                print(f"  ok    {name}: {summarize(await client.call_tool(name, args))}")
            except Exception as e:  # report every failing tool, then exit non-zero
                failures += 1
                print(f"  FAIL  {name}: {str(e).splitlines()[0][:200]}")
    return failures


if __name__ == "__main__":
    sys.exit(1 if asyncio.run(main()) else 0)
