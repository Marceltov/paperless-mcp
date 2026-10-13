"""Upload a document, then follow it through the trash and the task list."""

from tests.live._client import client, payload, rows, run_async, upload_text


def test_upload_delete_restore_and_empty_trash():
    async def go():
        async with client() as c:
            first = await upload_text(c, "itest upload one", "first uploaded document, zebra")
            second = await upload_text(c, "itest upload two", "second uploaded document, okapi")
            assert "zebra" in payload(await c.call_tool("documents_retrieve", {"id": first}))["content"]

            # Single delete and bulk delete both move documents to the trash.
            await c.call_tool("documents_destroy", {"id": first})
            await c.call_tool("documents_delete", {"documents": [second]})
            trashed = {row["id"] for row in rows(await c.call_tool("trash_list"))}
            assert {first, second} <= trashed

            await c.call_tool("trash_create", {"action": "restore", "documents": [first]})
            assert payload(await c.call_tool("documents_retrieve", {"id": first}))["id"] == first

            await c.call_tool("documents_destroy", {"id": first})
            await c.call_tool("trash_create", {"action": "empty", "documents": [first, second]})
            return {row["id"] for row in rows(await c.call_tool("trash_list"))}

    assert run_async(go()) == set()


def test_tasks_report_the_consumption():
    async def go():
        async with client() as c:
            tasks = rows(await c.call_tool("tasks_list", {"task_type": ["consume_file"]}))
            task = payload(await c.call_tool("tasks_retrieve", {"id": tasks[0]["id"]}))
            acknowledged = payload(await c.call_tool("acknowledge_tasks", {"tasks": [task["id"]]}))
            return {
                "tasks": tasks, "task": task, "acknowledged": acknowledged,
                "active": payload(await c.call_tool("tasks_active_list")),
                "counts": payload(await c.call_tool("tasks_status_counts_retrieve")),
                "summary": payload(await c.call_tool("tasks_summary_list")),
            }

    seen = run_async(go())
    # The seed alone consumed six files.
    assert len(seen["tasks"]) >= 6
    assert seen["task"]["task_type"] == "consume_file"
    assert seen["acknowledged"] == 1
    assert isinstance(seen["active"], list)
    assert seen["counts"]["completed"] >= 6
    assert "consume_file" in [row["task_type"] for row in seen["summary"]]
