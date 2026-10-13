# Tools

Tools are generated from the OpenAPI spec of your Paperless, one per API operation, and named after the spec's operation IDs: `documents_list`, `documents_retrieve`, `tags_create`, `correspondents_partial_update`, and so on. Each tool's description starts with its HTTP method and path, so `PATCH /api/documents/{id}/` tells you (and the model) what it does.

## Toolsets

A toolset is the first path segment after `/api/`: everything under `/api/documents/` is the `documents` toolset. `MCP_TOOLSETS` picks which ones become tools.

On by default (80 tools on Paperless-ngx with API version 10):

| Toolset | What it covers |
| ------- | -------------- |
| `documents` | List, filter and full-text search; read content and metadata; edit; notes; history; suggestions; bulk edit; merge, rotate and other PDF operations; upload, download, preview and thumbnail |
| `search` | Global search and autocomplete |
| `correspondents`, `document_types`, `tags`, `storage_paths`, `custom_fields` | Create, list, read, update and delete each |
| `saved_views`, `share_links` | Saved views and public share links |
| `tasks` | Background tasks: what is being consumed, what failed |
| `trash` | List, restore and empty the trash |
| `statistics` | Counts for the whole archive |
| `bulk_edit_objects` | Bulk delete and permission changes for tags, correspondents and the like |

Off by default: `users`, `groups`, `profile`, `config`, `mail_accounts`, `mail_rules`, `processed_mail`, `workflows`, `workflow_actions`, `workflow_triggers`, `share_link_bundles`, `logs`, `status`, `remote_version`, `ui_settings`.

```ini
# Only what a read-mostly assistant needs
MCP_TOOLSETS=documents,search,tags,correspondents,document_types

# The defaults plus workflows
MCP_TOOLSETS=documents,search,correspondents,document_types,tags,storage_paths,custom_fields,saved_views,share_links,tasks,trash,statistics,bulk_edit_objects,workflows,workflow_actions,workflow_triggers

# Everything (139 tools)
MCP_TOOLSETS=all
```

Setting `MCP_TOOLSETS` replaces the default list, it doesn't add to it. Every tool takes up room in the model's context, so more is not better: turn on what you use.

Toolsets decide which tools exist. What a tool may do is still decided by Paperless: a user without permission to delete documents gets Paperless's `403` from `documents_destroy`.

## What is left out, in every toolset

- **Credential operations.** `/api/token/`, `/api/profile/generate_auth_token/`, the two-factor endpoints and `disconnect_social_account`. Regenerating the API token would disconnect every client of that user, including the one making the call.
- **`PUT` where `PATCH` exists.** A full update needs every field re-sent; the partial update (`…_partial_update`) does the same job without accidental resets.
- **`bulk_download`** (a ZIP of binaries) and **`update_version`** (a file upload the generated tool can't express).
- **`/api/oauth/callback/`**, a browser redirect target.

## Tools that are written by hand

Four operations can't work as generated and are replaced by tools of the same name:

| Tool | What it does |
| ---- | ------------ |
| `documents_post_document_create` | Uploads a document. Takes `filename` and either `content` (text) or `content_base64` (anything else), plus optional title, date, correspondent, document type, storage path, tags, serial number and custom fields. Returns the task ID; Paperless consumes the file in the background. |
| `documents_download_retrieve` | Returns the file: the archived PDF, or the original with `original=true`. |
| `documents_preview_retrieve` | Returns the inline preview. |
| `documents_thumb_retrieve` | Returns the thumbnail as an image. |

Files are returned inside the tool result, so they are capped at 10 MB. To read a document, the model doesn't need the file: `documents_retrieve` returns the extracted text in its `content` field.

## Hints and descriptions

Every tool tells the client how it behaves, through the standard MCP tool annotations. Clients use them to decide which calls need your confirmation.

| Kind of tool | Read-only | Destructive | Idempotent |
| ------------ | --------- | ----------- | ---------- |
| `GET` (`…_list`, `…_retrieve`), and the two `POST`s that only read (`documents_selection_data_create`, `storage_paths_test`) | yes | no | yes |
| `PATCH` (`…_partial_update`) | no | no | yes |
| `POST` that creates (`tags_create`, the upload, …) | no | no | no |
| `DELETE` (`…_destroy`) | no | yes | yes |
| `POST` that deletes or rewrites files: `bulk_edit`, `bulk_edit_objects`, `documents_delete`, `trash_create`, `documents_merge`, `documents_edit_pdf`, `documents_rotate`, `documents_remove_password` | no | yes | no |

The tools that send mail or contact a mailbox (`documents_email_document`, `email_documents`, `mail_account_test`, `mail_account_process`) are marked as reaching beyond Paperless (`openWorldHint`).

A `PATCH` overwrites the fields you send, but it is marked non-destructive: it changes one object and the old values can be set again. The hints are advice for the client, not access control; what a user may do is decided by their Paperless permissions.

Descriptions start with the method and path. The tools a model uses most, and the ones where a wrong call is costly, have a description written for this server: `documents_list`, `documents_retrieve`, `documents_partial_update`, `documents_destroy`, `documents_delete`, `bulk_edit`, `bulk_edit_objects`, `trash_list`, `trash_create`, `search_retrieve`, `search_autocomplete_list`, `statistics_retrieve`, `tasks_list`, `documents_selection_data_create` and the list tools for tags, correspondents, document types, storage paths and custom fields. They say what comes back, which filters narrow the result, and how to keep it small. The other tools keep the text from the Paperless spec, with a note on paging for lists and on permanence for deletes.

The server also sends short instructions when a client connects: look IDs up first, filter on the server and leave out `content` with `fields`, read full text one document at a time, and confirm before a destructive call.

## Tips for prompts

- `documents_list` returns the full text of every document on the page. Ask for `fields` (for example `id`, `title`, `created`, `correspondent`) and a small `page_size` when you only need an overview.
- Full-text search is the `query` parameter of `documents_list`; `title__icontains`, `correspondent__id`, `tags__id__all`, `created__date__gte` and the other filters narrow by metadata.
- Metadata is referenced by ID. To tag a document, look the tag up with `tags_list` first, then pass its ID to `documents_partial_update` or `bulk_edit`.
