# Pipedrive for Claude

Talk to your Pipedrive CRM directly from Claude. Ask things like:

> "Show me all open deals"  
> "Create a deal called 'Acme website' worth 12,000 DKK"  
> "Find the contact John Smith and add a note that we spoke today"  
> "Create a follow-up call for deal #5 due tomorrow at 10:00"  
> "Search Pipedrive for Carlsberg"

---

## Quick install (Windows)

### Step 1 — Install Python

If you don't have Python, download it from **https://www.python.org/downloads/**

> During install, check the box **"Add Python to PATH"** — this is important!

### Step 2 — Download this project

Click the green **Code** button on GitHub → **Download ZIP** → unzip it anywhere on your computer.

### Step 3 — Run the setup script

Open the `pipedrive-mcp` folder and double-click **`setup.bat`**

It will:
- Install everything automatically
- Ask for your Pipedrive API token (see below)
- Connect itself to Claude Code

### Step 4 — Get your Pipedrive API token

1. Log in to [Pipedrive](https://app.pipedrive.com)
2. Click your **avatar** in the top-right corner
3. Go to **Personal preferences → API**
4. Copy your **Personal API token**

Paste it into the setup window when asked.

### Step 5 — Open VS Code and reload

1. Open the project folder in VS Code
2. Press `Ctrl+Shift+P` and type **Developer: Reload Window**
3. Claude should now have access to your Pipedrive

---

## What you can ask Claude

| What you want | What to say |
|---|---|
| See your deals | "Show me all open deals" |
| Find something | "Search Pipedrive for Acme" |
| Create a deal | "Create a deal called 'X' worth 5000 DKK" |
| Add a contact | "Create a contact: Jane Doe, jane@example.com" |
| Log a note | "Add a note to deal #3: spoke with client today" |
| Schedule a task | "Create a follow-up call for deal #3 due Friday at 2pm" |
| See your tasks | "Show me all pending activities" |
| Mark task done | "Mark activity #7 as done" |
| Create a lead | "Create a lead called 'Potential client - Carlsberg'" |
| See pipelines | "List all pipelines and stages" |

---

## Troubleshooting

**"MCP server failed to connect"**  
→ Re-run `setup.bat` and make sure you pasted the correct token.

**"Python not found"**  
→ Reinstall Python from python.org and check **"Add Python to PATH"** during install.

**The server connects but returns errors**  
→ Check that your Pipedrive token is correct: Settings → Personal preferences → API.

---

## For developers

The server is built with:
- [FastMCP](https://github.com/modelcontextprotocol/python-sdk) — MCP server framework
- [httpx](https://www.python-httpx.org/) — async HTTP client
- [Pipedrive API v1](https://developers.pipedrive.com/docs/api/v1)

To add new tools, edit `server.py` and add a `@mcp.tool()` function.  
The API client is in `pipedrive.py`.

```
pipedrive-mcp/
├── server.py       # MCP tools (what Claude can do)
├── pipedrive.py    # Pipedrive API client
├── setup.bat       # One-click installer (Windows)
└── .env            # Your API token (never commit this)
```
