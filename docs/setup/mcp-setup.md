# MCP Server Setup (Optional but Recommended)

**MCP** = Model Context Protocol. MCP servers let Claude Code read your Zotero library, your Google Drive files, or live PubMed results directly. Each server is a separate install + one `claude mcp add` command.

You can use MedSci Skills without any MCP servers — they fall back to local files and public APIs. MCPs just make integration smoother (e.g., `lit-sync` skill is much faster with the Zotero MCP).

---

## Zotero MCP (highest value for paper writing)

**Why**: `lit-sync`, `verify-refs`, and `write-paper` all benefit from direct Zotero access (read your library, add new items by DOI, sync references to manuscripts).

**Install** (Mac/Linux/Windows):

```bash
# Make sure Zotero desktop is running and you have an API key
# Get API key: https://www.zotero.org/settings/keys → Create new private key
# Save your library ID: visible in https://www.zotero.org/settings/keys

claude mcp add zotero --scope user \
  -e ZOTERO_LOCAL=true \
  -e ZOTERO_API_KEY=<your-api-key> \
  -e ZOTERO_LIBRARY_ID=<your-library-id> \
  -- npx zotero-mcp
```

**Verify**:
```bash
claude mcp list | grep zotero
```
Expected: `zotero ✓ Connected`

---

## Google Drive / Workspace MCP

**Why**: Read/write Google Docs, Sheets, Drive files. Useful if your data lives in Google Sheets or your manuscripts are shared via Google Docs.

```bash
claude mcp add gdrive --scope user -- npx @modelcontextprotocol/server-gdrive
```

First run will prompt you to authenticate via browser (OAuth).

---

## PubMed MCP (alternative to built-in `search-lit`)

**Why**: Slightly faster and richer than the E-utilities fallback in `search-lit`.

```bash
claude mcp add pubmed --scope user -- npx pubmed-mcp
```

No API key required for basic searches. For higher rate limits, add `-e NCBI_API_KEY=<your-key>` (get one at <https://www.ncbi.nlm.nih.gov/account/settings/>).

---

## Filesystem MCP (built-in, usually pre-configured)

Claude Code ships with filesystem access by default. If you've disabled it, re-enable per project:

```bash
claude mcp add filesystem --scope project -- npx @modelcontextprotocol/server-filesystem ~/Documents
```

---

## Verifying All MCP Servers

```bash
claude mcp list
```

Expected output:
```
filesystem ✓ Connected
zotero     ✓ Connected
gdrive     ✓ Connected (or paused for auth)
pubmed     ✓ Connected
```

The `/setup-medsci` skill includes this check automatically.

---

## Common MCP Issues

| Symptom | Cause | Fix |
|---|---|---|
| `claude mcp list` shows nothing | MCP servers added at project scope but you're in a different directory | Use `--scope user` so they persist across projects |
| `zotero ✗ Disconnected` | Zotero desktop not running, or API key wrong | Start Zotero, verify key at <https://www.zotero.org/settings/keys> |
| `npx command not found` | Node.js not installed | See [`mac.md`](mac.md) Step 4 or [`windows.md`](windows.md) Step 5 |
| Authentication popup keeps reopening | Browser blocking pop-ups | Allow pop-ups for `localhost` |

---

## Removing an MCP Server

```bash
claude mcp remove zotero --scope user
```
