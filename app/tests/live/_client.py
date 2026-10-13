"""Shared helpers for the live integration tests (see conftest.py for the skip)."""

import asyncio
import json
import time

import httpx
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

# Pinned to the in-repo throwaway stack (docker-compose.yaml, seeded by
# dev/seed/seed.py). Deliberately NOT overridable from the environment: these
# tests create and delete documents, and a developer's shell may well carry
# PAPERLESS_URL / PAPERLESS_TOKEN for a *real* instance (docker-compose.live.yaml
# reads exactly those).
MCP_URL = "http://localhost:9191/mcp"
PAPERLESS_URL = "http://localhost:9190"
HEALTH_URL = str(httpx.URL(MCP_URL).copy_with(path="/health", query=None))
# Committed dev fixture credentials (see docker-compose.yaml).
USERNAME = "admin"
PASSWORD = "paperless-mcp"

_reachable: bool | None = None
_token: str | None = None


def stack_reachable() -> bool:
    """True if the MCP /health endpoint answers 200. Cached so the network
    probe runs once per session."""
    global _reachable
    if _reachable is None:
        try:
            _reachable = httpx.get(HEALTH_URL, timeout=2.0).status_code == 200
        except httpx.HTTPError:
            _reachable = False
    return _reachable


def token() -> str:
    """The seeded admin's API token, fetched once from the dev Paperless."""
    global _token
    if _token is None:
        response = httpx.post(
            f"{PAPERLESS_URL}/api/token/",
            json={"username": USERNAME, "password": PASSWORD},
            timeout=30,
        )
        response.raise_for_status()
        _token = response.json()["token"]
    return _token


def client() -> Client:
    return Client(StreamableHttpTransport(MCP_URL, headers={"Authorization": token()}))


def run_async(coro):
    return asyncio.run(coro)


async def call(tool: str, args: dict | None = None):
    async with client() as c:
        return await c.call_tool(tool, args or {})


def payload(result):
    """The JSON a tool returned. FastMCP leaves `.data` as None for a top-level
    array and wraps scalars as {"result": ...}, so fall back to the text."""
    data = result.data
    if data is None and result.content:
        try:
            data = json.loads(result.content[0].text)
        except (json.JSONDecodeError, AttributeError, IndexError):
            data = None
    if isinstance(data, dict) and set(data) == {"result"}:
        return data["result"]
    return data


def rows(result) -> list:
    """The items of a list tool: Paperless paginates as {"results": [...]},
    a few endpoints return a bare array."""
    data = payload(result)
    if isinstance(data, dict):
        return data.get("results", [])
    return data or []


async def find_document(c, title: str) -> dict:
    """A seeded document by its exact title."""
    found = rows(await c.call_tool("documents_list", {"title__iexact": title}))
    assert found, f"seeded document {title!r} not found"
    return found[0]


async def upload_text(c, title: str, text: str) -> int:
    """Upload a text document and wait until Paperless has consumed it; returns
    the new document's ID."""
    await c.call_tool(
        "documents_post_document_create",
        {"filename": f"{title}.txt", "content": text, "title": title},
    )
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        found = rows(await c.call_tool("documents_list", {"title__iexact": title}))
        if found:
            return found[0]["id"]
        await asyncio.sleep(1)
    raise AssertionError(f"uploaded document {title!r} was not consumed in time")
