# Web UI

The main way to use Godot RAG: a local chat app with streaming answers, history, and code copy.

![Chat UI with example prompts](../assets/screenshots/hero-empty-state.png)

## Start the app

From the **repository root** (after [installation](../getting-started/installation.md)):

```powershell
godot-web
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Settings bar

![API key and model in the top bar](../assets/screenshots/top-bar-settings.png)

Enter your **OpenAI API key** and **model** here. Keys stay in browser `localStorage` — see [API keys](../getting-started/api-keys.md).

## Chat history

![Sidebar with chat sessions](../assets/screenshots/sidebar-sessions.png)

Sessions are stored locally in your browser. Create, select, or delete chats from the left sidebar.

## Example prompts

On a new chat, click a suggested prompt (PackedScene, signals, movement, UI, animations, project structure) to send it immediately.

## Agent activity

![Loading / retrieving status with timer](../assets/screenshots/agent-activity.png)

While the agent works, the UI shows the current phase (loading embeddings, retrieving docs, thinking, writing) and elapsed time.

## Code in answers

![Syntax-highlighted code block with copy button](../assets/screenshots/chat-code-block.png)

Replies render as Markdown. Fenced code blocks include syntax highlighting and a **Copy** button.

## Development mode

Hot reload for UI work (single terminal):

```powershell
cd web/ui && npm install && cd ../..
godot-web --dev
```

Open [http://localhost:5173](http://localhost:5173). Vite proxies `/api` to port 8000.

| Flag | Description |
|------|-------------|
| `--dev` | API (reload) + Vite together |
| `--host` | API bind address (default `127.0.0.1`) |
| `--port` | API port (default `8000`) |

## First prompt

The first request downloads the local embedding model (`all-MiniLM-L6-v2`, ~90 MB). Later prompts skip this step.

## Security

For **local use only** (`127.0.0.1`). Do not expose `godot-web` to the public internet without authentication.
