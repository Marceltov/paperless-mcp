import asyncio
import json

import httpx
from key_value.aio.stores.memory import MemoryStore
from mcp.shared.auth import OAuthClientInformationFull

import server
from tests._fake import BASE, STATISTICS, build, mcp_session, asgi_factory

CLIENT = OAuthClientInformationFull(client_id="c1", redirect_uris=["http://localhost:9/cb"])


def fake_paperless(calls: list | None = None, seen: dict | None = None):
    """A Paperless that knows one user (alice / pw, API token `alice-token`),
    optionally with two-factor on (code 123456)."""
    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append(request)
        auth = request.headers.get("Authorization")
        if request.url.path == "/api/token/":
            body = json.loads(request.content)
            if (body["username"], body["password"]) != ("alice", "pw"):
                return httpx.Response(400, json={
                    "non_field_errors": ["Unable to log in with provided credentials."]})
            if seen is not None and seen.get("mfa") and body.get("code") != "123456":
                return httpx.Response(400, json={"non_field_errors": ["MFA code is required"]})
            return httpx.Response(200, json={"token": "alice-token"})
        if request.url.path == "/api/profile/":
            ok = auth == "Token alice-token"
            return httpx.Response(200 if ok else 401, json={})
        if request.url.path == "/api/statistics/":
            if seen is not None:
                seen["auth"] = auth
            return httpx.Response(200, json=STATISTICS)
        return httpx.Response(404)
    return handler


def make_provider(passthrough=True, seen=None):
    """Provider on an in-memory store with a fake Paperless; returns (provider, calls)."""
    calls = []
    paperless = httpx.AsyncClient(
        base_url=BASE, transport=httpx.MockTransport(fake_paperless(calls, seen))
    )
    provider = server.PaperlessOAuthProvider(
        base_url="http://localhost", store=MemoryStore(), paperless=paperless,
        passthrough=passthrough,
    )
    return provider, calls


def test_issued_token_maps_to_paperless_token():
    p, _ = make_provider()

    async def go():
        tok = await p._issue("c1", [], "token-x")
        return tok, await p.verify_token(tok.access_token)

    tok, found = asyncio.run(go())
    assert tok.access_token.startswith(server.OAUTH_TOKEN_PREFIX)
    assert found.claims["paperless_token"] == "token-x"


def test_both_mode_passes_unknown_bearer_through():
    p, _ = make_provider(passthrough=True)
    found = asyncio.run(p.verify_token("raw-token"))
    assert found.claims["paperless_token"] == "raw-token"


def test_oauth_mode_rejects_unknown_bearer():
    p, _ = make_provider(passthrough=False)
    assert asyncio.run(p.verify_token("raw-token")) is None


def test_stale_prefixed_token_is_rejected_even_in_both_mode():
    # An expired/revoked OAuth token must 401 (so the client refreshes), not be
    # forwarded to Paperless as if it were a raw API token.
    p, _ = make_provider(passthrough=True)
    assert asyncio.run(p.verify_token(server.OAUTH_TOKEN_PREFIX + "gone")) is None


def test_refresh_rotates_the_pair():
    p, _ = make_provider()

    async def go():
        first = await p._issue("c1", [], "token-x")
        rt = await p.load_refresh_token(CLIENT, first.refresh_token)
        second = await p.exchange_refresh_token(CLIENT, rt, [])
        return (
            await p.verify_token(first.access_token),
            await p.load_refresh_token(CLIENT, first.refresh_token),
            await p.verify_token(second.access_token),
        )

    old_access, old_refresh, new_access = asyncio.run(go())
    assert old_access is None and old_refresh is None
    assert new_access.claims["paperless_token"] == "token-x"


def test_revoke_drops_pair_and_leaves_the_paperless_token_alone():
    # Paperless has one API token per user, shared by all of that user's
    # clients; revoking one client must not touch it.
    p, calls = make_provider()

    async def go():
        tok = await p._issue("c1", [], "token-x")
        await p.revoke_token(await p.load_access_token(tok.access_token))
        return (
            await p.verify_token(tok.access_token),
            await p.load_refresh_token(CLIENT, tok.refresh_token),
        )

    access, refresh = asyncio.run(go())
    assert access is None and refresh is None
    assert calls == []


def test_registered_client_round_trips():
    p, _ = make_provider()

    async def go():
        await p.register_client(CLIENT)
        return await p.get_client("c1")

    assert asyncio.run(go()).redirect_uris == CLIENT.redirect_uris


import base64
import hashlib
import secrets

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


REDIRECT = "http://localhost:9/cb"


def _flow_app(seen: dict):
    """FastMCP app in oauth mode on a fake Paperless."""
    handler = fake_paperless(seen=seen)
    provider = server.PaperlessOAuthProvider(
        base_url="http://localhost",
        store=MemoryStore(),
        paperless=httpx.AsyncClient(base_url=BASE, transport=httpx.MockTransport(handler)),
        passthrough=False,
    )
    return build(handler, auth=provider).http_app(path=server.DEFAULT_PATH)


async def _begin_login(http: httpx.AsyncClient) -> dict:
    """register -> authorize; returns what the rest of the flow needs."""
    r = await http.post("/register", json={
        "client_name": "itest", "redirect_uris": [REDIRECT],
        "token_endpoint_auth_method": "none",
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
    })
    client_id = r.json()["client_id"]
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    r = await http.get("/authorize", params={
        "response_type": "code", "client_id": client_id,
        "redirect_uri": REDIRECT, "code_challenge": challenge,
        "code_challenge_method": "S256", "state": "s1",
    })
    pending = httpx.URL(r.headers["location"]).params["id"]
    return {"client_id": client_id, "verifier": verifier, "pending": pending}


async def _finish_login(http: httpx.AsyncClient, flow: dict, form: dict) -> str:
    """POST /login with `form` -> /token; returns the access token."""
    r = await http.post("/login", data={"id": flow["pending"], **form})
    assert r.status_code == 302, r.text
    back = httpx.URL(r.headers["location"])
    assert back.params["state"] == "s1"
    r = await http.post("/token", data={
        "grant_type": "authorization_code", "code": back.params["code"],
        "redirect_uri": REDIRECT, "client_id": flow["client_id"],
        "code_verifier": flow["verifier"],
    })
    return r.json()["access_token"]


async def _statistics(app, access: str):
    transport = StreamableHttpTransport(
        url="http://localhost/mcp",
        headers={"Authorization": f"Bearer {access}"},
        httpx_client_factory=asgi_factory(app),
    )
    async with Client(transport) as c:
        return await c.call_tool("statistics_retrieve", {})


def test_full_oauth_flow_forwards_the_users_paperless_token():
    """register -> authorize -> /login -> token -> MCP tool call, all in-process;
    the tool's Paperless call must carry the token /api/token/ returned."""
    seen = {}
    app = _flow_app(seen)

    async def run():
        async with app.router.lifespan_context(app):
            async with asgi_factory(app)() as http:
                # Unauthenticated MCP call -> 401 that points at OAuth discovery.
                r = await http.post(server.DEFAULT_PATH, json={})
                assert r.status_code == 401
                assert "resource_metadata" in r.headers["www-authenticate"]

                flow = await _begin_login(http)
                page = await http.get("/login", params={"id": flow["pending"]})
                assert "itest" in page.text and "localhost:9" in page.text
                bad = await http.post("/login", data={
                    "id": flow["pending"], "username": "alice", "password": "nope"})
                assert bad.status_code == 401  # pending login survives a typo
                assert "Unable to log in with provided credentials" in bad.text
                access = await _finish_login(
                    http, flow, {"username": "alice", "password": "pw"})
            return await _statistics(app, access)

    result = asyncio.run(run())
    assert result.data["documents_total"] == 6
    assert seen["auth"] == "Token alice-token"


def test_login_asks_for_the_two_factor_code_when_paperless_does():
    seen = {"mfa": True}
    app = _flow_app(seen)

    async def run():
        async with app.router.lifespan_context(app):
            async with asgi_factory(app)() as http:
                flow = await _begin_login(http)
                credentials = {"username": "alice", "password": "pw"}
                r = await http.post("/login", data={"id": flow["pending"], **credentials})
                assert r.status_code == 401 and "MFA code is required" in r.text
                return await _finish_login(http, flow, {**credentials, "code": "123456"})

    assert asyncio.run(run()).startswith(server.OAUTH_TOKEN_PREFIX)


def test_login_with_a_pasted_api_token_for_single_sign_on_accounts():
    """An account that signs in to Paperless through SSO has no password to
    trade; pasting its API token must work, and a wrong one must not."""
    seen = {}
    app = _flow_app(seen)

    async def run():
        async with app.router.lifespan_context(app):
            async with asgi_factory(app)() as http:
                flow = await _begin_login(http)
                bad = await http.post("/login", data={"id": flow["pending"], "token": "wrong"})
                assert bad.status_code == 401 and "rejected the API token" in bad.text
                access = await _finish_login(http, flow, {"token": "alice-token"})
            return await _statistics(app, access)

    asyncio.run(run())
    assert seen["auth"] == "Token alice-token"


def test_login_throttle_is_explained():
    # Paperless throttles its login endpoint and says when to retry; pass that on.
    response = httpx.Response(
        429, json={"detail": "Request was throttled. Expected available in 14 seconds."}
    )
    assert "Expected available in 14 seconds" in server._rejection(response)
    assert server._rejection(httpx.Response(502, text="<html>")).endswith("HTTP 502")


def test_empty_login_form_is_not_sent_to_paperless():
    p, calls = make_provider()
    pending = asyncio.run(_pending(p))
    from starlette.applications import Starlette
    from starlette.testclient import TestClient

    http = TestClient(Starlette(routes=p.get_routes(server.DEFAULT_PATH)), follow_redirects=False)
    r = http.post("/login", data={"id": pending})
    assert r.status_code == 401 and "username and password" in r.text
    assert calls == []


async def _pending(p) -> str:
    """A registered client's pending login id on provider `p`."""
    from mcp.server.auth.provider import AuthorizationParams

    await p.register_client(CLIENT)
    url = await p.authorize(CLIENT, AuthorizationParams(
        state="s", scopes=[], code_challenge="x" * 43,
        redirect_uri="http://localhost:9/cb", redirect_uri_provided_explicitly=True,
    ))
    return httpx.URL(url).params["id"]


def test_expired_login_link_is_rejected():
    p, _ = make_provider()
    app = p.get_routes(server.DEFAULT_PATH)
    from starlette.applications import Starlette
    from starlette.testclient import TestClient

    r = TestClient(Starlette(routes=app)).get("/login", params={"id": "nope"})
    assert r.status_code == 400
    assert_explains_reconnect(r.text)


def assert_explains_reconnect(page: str):
    """Dead-end login pages must say why it happened (the app interrupted its own
    flow, e.g. a claude.ai login), that it isn't the server's fault, and the fix."""
    assert "claude.ai" in page
    assert "Nothing is wrong with your Paperless or this MCP server" in page
    assert "remove this connector and add it again" in page
    assert "Reconnect" in page


import pytest

OAUTH_VARS = {"MCP_BASE_URL": "https://mcp.example", "MCP_OAUTH_SECRET": "s3cret-s3cret"}


@pytest.mark.parametrize(
    "mode, env, expected",
    [
        (None, {}, "token"),              # unset + no OAuth vars: tokens only
        (None, OAUTH_VARS, "both"),       # unset + vars: default is both
        ("token", {}, "token"),
        ("oauth", OAUTH_VARS, "oauth"),
        ("BOTH", OAUTH_VARS, "both"),
    ],
)
def test_resolve_auth_mode(monkeypatch, mode, env, expected):
    for var in ("MCP_AUTH_MODE", *OAUTH_VARS):
        monkeypatch.delenv(var, raising=False)
    if mode:
        monkeypatch.setenv("MCP_AUTH_MODE", mode)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    assert server.resolve_auth_mode() == expected


@pytest.mark.parametrize("mode", ["oauth", "both", "bogus"])
def test_resolve_auth_mode_fails_loudly_when_explicit(monkeypatch, mode):
    for var in OAUTH_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("MCP_AUTH_MODE", mode)
    with pytest.raises(RuntimeError, match="MCP_"):
        server.resolve_auth_mode()


def test_encrypted_store_round_trips(monkeypatch, tmp_path):
    monkeypatch.setattr(server, "OAUTH_STORE_DIR", tmp_path)
    for k, v in OAUTH_VARS.items():
        monkeypatch.setenv(k, v)
    p = server.build_oauth_provider("both")

    async def go():
        await p.register_client(CLIENT)
        return await p.get_client("c1")

    assert asyncio.run(go()).client_id == "c1"
    stored = b"".join(f.read_bytes() for f in tmp_path.rglob("*.json"))
    assert b"localhost:9" not in stored  # encrypted at rest


def test_plain_http_base_url_fails_at_startup(monkeypatch, tmp_path):
    # OAuth issuers must be HTTPS (localhost excepted); catch it while building,
    # so main() shows startup_error instead of serve() crashing later.
    monkeypatch.setattr(server, "OAUTH_STORE_DIR", tmp_path)
    monkeypatch.setenv("MCP_BASE_URL", "http://192.168.1.50:8081")
    monkeypatch.setenv("MCP_OAUTH_SECRET", "s3cret-s3cret")
    with pytest.raises(RuntimeError, match="MCP_BASE_URL.*HTTPS"):
        server.build_oauth_provider("both")


@pytest.mark.parametrize("header", ["raw-api-token", "Token raw-api-token"])
def test_both_mode_accepts_token_mode_headers(header):
    """Token-mode clients send `Authorization: <token>` or Paperless's own
    `Token <token>`, never Bearer; in both mode that must still reach
    Paperless, as it does in token mode."""
    seen = {}
    handler = fake_paperless(seen=seen)
    provider = server.PaperlessOAuthProvider(
        base_url="http://localhost", store=MemoryStore(),
        paperless=httpx.AsyncClient(base_url=BASE, transport=httpx.MockTransport(handler)),
        passthrough=True,
    )
    inner = build(handler, auth=provider).http_app(path=server.DEFAULT_PATH)

    async def run():
        async with mcp_session(inner, server.wrap_app(inner, "both"), header) as c:
            return await c.call_tool("statistics_retrieve", {})

    asyncio.run(run())
    assert seen["auth"] == "Token raw-api-token"


def test_replayed_login_says_completed_and_asks_paperless_nothing():
    """A browser can re-submit the login form after it succeeded (seen with
    claude.ai's connector flow). The replay must not log in a second time, and
    must not claim the link "expired" -- the login already went through."""
    p, calls = make_provider()
    from starlette.applications import Starlette
    from starlette.testclient import TestClient

    pending = asyncio.run(_pending(p))
    http = TestClient(Starlette(routes=p.get_routes(server.DEFAULT_PATH)), follow_redirects=False)
    form = {"id": pending, "username": "alice", "password": "pw"}
    first = http.post("/login", data=form)
    assert first.status_code == 302
    replay = http.post("/login", data=form)
    assert replay.status_code == 200
    assert "already" in replay.text and "expired" not in replay.text
    assert_explains_reconnect(replay.text)
    assert len([c for c in calls if c.url.path == "/api/token/"]) == 1
