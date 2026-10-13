"""Saved views and share links."""

from tests.live._client import client, find_document, payload, rows, run_async


def test_saved_view_round_trip():
    async def go():
        async with client() as c:
            view = payload(await c.call_tool("saved_views_create", {
                "name": "itest view",
                # rule_type 0: title contains
                "filter_rules": [{"rule_type": 0, "value": "invoice"}],
            }))
            try:
                listed = [row["id"] for row in rows(await c.call_tool("saved_views_list"))]
                fetched = payload(await c.call_tool("saved_views_retrieve", {"id": view["id"]}))
                renamed = payload(await c.call_tool(
                    "saved_views_partial_update", {"id": view["id"], "name": "itest view renamed"}
                ))
            finally:
                await c.call_tool("saved_views_destroy", {"id": view["id"]})
            left = [row["id"] for row in rows(await c.call_tool("saved_views_list"))]
            return view, listed, fetched, renamed, left

    view, listed, fetched, renamed, left = run_async(go())
    assert view["id"] in listed and view["id"] not in left
    assert fetched["filter_rules"][0]["value"] == "invoice"
    assert renamed["name"] == "itest view renamed"


def test_share_link_round_trip():
    async def go():
        async with client() as c:
            document_id = (await find_document(c, "Electricity supply contract"))["id"]
            link = payload(await c.call_tool(
                "share_links_create", {"document": document_id, "file_version": "original"}
            ))
            try:
                listed = [row["id"] for row in rows(await c.call_tool("share_links_list"))]
                fetched = payload(await c.call_tool("share_links_retrieve", {"id": link["id"]}))
                of_document = payload(await c.call_tool(
                    "document_share_links", {"id": str(document_id)}
                ))
            finally:
                await c.call_tool("share_links_destroy", {"id": link["id"]})
            return link, listed, fetched, of_document

    link, listed, fetched, of_document = run_async(go())
    assert link["id"] in listed
    assert fetched["slug"] == link["slug"]
    assert link["id"] in [row["id"] for row in of_document]
