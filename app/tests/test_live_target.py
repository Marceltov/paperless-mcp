"""Guard: live tests must only ever target the in-repo throwaway stack.

A developer's shell may carry PAPERLESS_URL / PAPERLESS_TOKEN for a *real*
instance (docker-compose.live.yaml reads exactly those); if the live tests
honored them they would create and delete documents in someone's actual archive.
"""

import importlib

from tests.live import _client


def test_live_tests_ignore_real_instance_env(monkeypatch):
    monkeypatch.setenv("PAPERLESS_URL", "https://real.example")
    monkeypatch.setenv("PAPERLESS_TOKEN", "real-token")
    monkeypatch.setenv("PAPERLESS_MCP_URL", "https://real.example/mcp")
    try:
        client = importlib.reload(_client)
        assert client.MCP_URL == "http://localhost:9191/mcp"
        assert client.PAPERLESS_URL == "http://localhost:9190"
    finally:
        monkeypatch.undo()
        importlib.reload(_client)
