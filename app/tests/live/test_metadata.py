"""Correspondents, document types, tags, storage paths and custom fields:
the same create / list / retrieve / update / delete round trip for each."""

import pytest

from tests.live._client import call, client, find_document, payload, rows, run_async

# (create, list, retrieve, partial_update, destroy), fields for create, field to change
_RESOURCES = [
    (("correspondents_create", "correspondents_list", "correspondents_retrieve",
      "correspondents_partial_update", "correspondents_destroy"),
     {"name": "itest correspondent"}, {"name": "itest correspondent renamed"}),
    (("document_types_create", "document_types_list", "document_types_retrieve",
      "document_types_partial_update", "document_types_destroy"),
     {"name": "itest type"}, {"name": "itest type renamed"}),
    (("tags_create", "tags_list", "tags_retrieve", "tags_partial_update", "tags_destroy"),
     {"name": "itest tag", "color": "#ff0000"}, {"color": "#00ff00"}),
    (("storage_paths_create", "storage_paths_list", "storage_paths_retrieve",
      "storage_paths_partial_update", "storage_paths_destroy"),
     {"name": "itest path", "path": "{{ created_year }}/{{ title }}"},
     {"path": "{{ correspondent }}/{{ title }}"}),
    (("custom_fields_create", "custom_fields_list", "custom_fields_retrieve",
      "custom_fields_partial_update", "custom_fields_destroy"),
     {"name": "itest field", "data_type": "string"}, {"name": "itest field renamed"}),
]


@pytest.mark.parametrize("tools, fields, change", _RESOURCES, ids=lambda v: v[0] if isinstance(v, tuple) else None)
def test_crud_round_trip(tools, fields, change):
    create, list_, retrieve, update, destroy = tools

    async def go():
        async with client() as c:
            created = payload(await c.call_tool(create, fields))
            object_id = created["id"]
            try:
                listed = rows(await c.call_tool(list_, {"name__icontains": "itest"}))
                assert object_id in [row["id"] for row in listed]
                assert payload(await c.call_tool(retrieve, {"id": object_id}))["name"] == fields["name"]
                updated = payload(await c.call_tool(update, {"id": object_id, **change}))
                for key, value in change.items():
                    assert updated[key] == value
            finally:
                await c.call_tool(destroy, {"id": object_id})
            gone = rows(await c.call_tool(list_, {"name__icontains": "itest"}))
            assert object_id not in [row["id"] for row in gone]

    run_async(go())


def test_seeded_metadata_is_listed():
    names = {row["name"] for row in rows(run_async(call("correspondents_list")))}
    assert {"ACME Hardware", "Northwind Energy"} <= names


def test_storage_path_template_is_rendered_for_a_document():
    async def go():
        async with client() as c:
            document = await find_document(c, "ACME invoice AC-2026-0317")
            return payload(await c.call_tool(
                "storage_paths_test",
                {"document": document["id"], "path": "{{ correspondent }}/{{ title }}"},
            ))

    assert run_async(go()).startswith("ACME Hardware/ACME invoice AC-2026-0317")


def test_bulk_edit_objects_deletes_several_at_once():
    async def go():
        async with client() as c:
            ids = [
                payload(await c.call_tool("tags_create", {"name": f"itest bulk {n}"}))["id"]
                for n in (1, 2)
            ]
            await c.call_tool(
                "bulk_edit_objects",
                {"objects": ids, "object_type": "tags", "operation": "delete"},
            )
            return rows(await c.call_tool("tags_list", {"name__icontains": "itest bulk"}))

    assert run_async(go()) == []
