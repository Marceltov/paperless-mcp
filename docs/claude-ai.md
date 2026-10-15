# Claude.ai

Claude.ai connects through a custom connector that signs in with [OAuth](connecting.md#choosing-an-auth-method), so the server needs `MCP_BASE_URL` and `MCP_OAUTH_SECRET` set and an HTTPS public URL. A connector you add on the web is also available in the Claude desktop and mobile apps.

!!! warning "Log in to claude.ai first"

    Make sure you are already logged in to claude.ai before adding the connector. If claude.ai asks you to log in partway through, it can drop the finished OAuth login, and the connector stays unauthenticated with no tools. Remove that connector and add it again; the second attempt goes straight through.

1. In a new chat, open the **+** menu below the message box and choose *Connectors → Add connector → Add custom connector*. *Settings → Connectors* has the same button.
2. Enter a name (for example `Paperless`, shown in the connectors list) and the URL `https://paperless-ngx-mcp.example.com/mcp`, then click **Continue**.
3. Claude.ai detects the server's OAuth support. Keep the detected choices, **Sign in now** and **Register automatically**, and click **Add**. No request headers are needed.
4. The Paperless-ngx MCP server's login page opens. Enter your Paperless username and password and click **Authorize**; you are sent back to claude.ai. If you added the connector in Claude Desktop, your browser first asks *Finish connecting a connector?*; click **Continue connecting**.
5. In a chat, open **+ → Connectors** and switch the connector on to use its tools.
6. Check that the tools arrived: open the connector under *Settings → Connectors*. **Tool permissions** should list them (80 with the default [toolsets](tools.md)). If the list is empty, the login didn't finish; see the warning above.

    The same list lets you choose per tool whether Claude may always use it, must ask first, or may never use it, for example asking first for the `…_destroy` and `bulk_edit` tools.

Removing the connector in claude.ai disconnects it. Your Paperless API token is left as it is, because [other clients share it](security.md#one-api-token-per-user).
