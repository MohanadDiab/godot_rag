# Web UI

Local chat interface with streaming responses, sidebar history, markdown code blocks with copy, and an in-browser API key field.

## Development (two terminals)

**Terminal 1 — API server:**

```powershell
pip install -e ".[web]"
godot-web
```

**Terminal 2 — frontend:**

```powershell
cd web/ui
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

Enter your OpenAI API key and model in the top bar. The key is stored in browser `localStorage` only — see [API keys](../getting-started/api-keys.md#web-ui).

## Production (single server)

Build the React UI and serve it from FastAPI:

```powershell
cd web/ui
npm install
npm run build
cd ../..
godot-web
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Features

- **Streaming answers** with live status (loading embeddings, retrieving docs, thinking, writing)
- **Chat history** stored in browser `localStorage` (new / select / delete sessions)
- **Example prompts** on empty chats to get started quickly
- **Syntax-highlighted code blocks** with a copy button
- **Response timer** showing elapsed seconds per reply

## First prompt

On the first request, the local embedding model (`all-MiniLM-L6-v2`) is downloaded and cached. A progress bar appears in the UI. Subsequent prompts skip this step.

## Security

`godot-web` is intended for **local use only**. Do not expose it to the public internet without authentication. See [API keys — Web UI](../getting-started/api-keys.md#web-ui).
