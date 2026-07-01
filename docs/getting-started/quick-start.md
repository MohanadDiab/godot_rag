# Quick start

Get the Godot RAG chat UI running in a few minutes.

![Empty chat with example prompts](../assets/screenshots/hero-empty-state.png)

## 1. Clone with Git LFS

The vector index is stored via [Git LFS](https://git-lfs.com/):

```powershell
git lfs install
git clone https://github.com/MohanadDiab/godot_rag.git
cd godot_rag
git lfs pull
```

## 2. Install Python dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

On Linux/macOS: `source .venv/bin/activate` instead of `Activate.ps1`.

## 3. Build the web UI (one time)

Requires [Node.js](https://nodejs.org/) (LTS):

```powershell
cd web/ui
npm install
npm run build
cd ../..
```

## 4. Start the app

From the **repository root**:

```powershell
godot-web
```

Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.

## 5. Add your OpenAI API key

![OpenAI API key field in the top bar](../assets/screenshots/key_location.png)

Enter your key and model in the **top bar**. The key is stored in browser `localStorage` only — see [API keys](api-keys.md).

A `.env` file is optional for the web UI (useful if you also run `godot-ask` from the terminal).

## Try it

Click an **example prompt** on the empty chat screen, or type your own Godot 4.x question.

On the first message, the local embedding model downloads once (~90 MB). A progress bar appears in the UI.

## Next steps

- [Web UI guide](../user-guide/web-ui.md) — features, dev mode, screenshots
- [API keys](api-keys.md) — security and troubleshooting
- [Advanced — CLI](../user-guide/cli.md) — terminal usage without the browser
