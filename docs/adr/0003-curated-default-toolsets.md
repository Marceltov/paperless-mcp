---
status: accepted
date: 2026-10-13
---

# A curated default toolset instead of every operation

## Context and Problem Statement

trilium-mcp exposes every ETAPI operation, 38 tools. Paperless's spec has 163 operations. Generated as they are, their tool definitions come to about 200,000 characters, which a client loads into the model's context before the first question. Much of that is administration (users, groups, mail accounts, workflows, application config) that a document assistant has no use for, and some of it should never be a tool at all.

## Decision Outcome

Operations are grouped into toolsets by their first path segment after `/api/`. `MCP_TOOLSETS` selects them; the default is the document-centred set (documents, search, correspondents, document types, tags, storage paths, custom fields, saved views, share links, tasks, trash, statistics, bulk edit of objects), and `all` turns everything on. On API version 10 that is 80 tools and about 68,000 characters by default, 139 tools with `all`.

Independently of the selection:

* Operations that mint or replace the user's API token or change how the account logs in are never tools (`NEVER_EXPOSED`).
* `PUT` is dropped wherever the same path has `PATCH`.
* Generated output schemas are cleared, and each description is prefixed with its method and path, because many Paperless operations carry an unrelated mixin docstring as their description.

### Consequences

* Good, because the default fits in a client's context and covers everyday document work.
* Good, because an administrator can still reach everything with one variable.
* Bad, because the default is a judgement call, and a new Paperless path prefix is off until someone adds it to the default or to their own list.
* Bad, because toolsets are coarse: one can't enable reading documents without also enabling deleting them. Per-tool permissions in the client, and Paperless's own user permissions, are the finer controls.

### Confirmation

`app/tests/test_spec.py` checks the default, narrowed and `all` selections and that the credential operations are absent from every one. `app/tests/test_coverage.py` fails when a default tool has no live test.
