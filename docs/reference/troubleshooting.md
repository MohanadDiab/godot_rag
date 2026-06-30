# Troubleshooting

## Common issues

| Issue | Fix |
|-------|-----|
| `OPENAI_API_KEY is not set` | See [API keys](../getting-started/api-keys.md) |
| Model not found / 404 | Set `OPENAI_MODEL` in `.env` to a model your account supports |
| Empty or weak answers | Try rephrasing; use `godot-ask --search-only "..."` to inspect retrieved context |
| `git lfs` / missing index files | Run `git lfs install` then `git lfs pull` after cloning |
| Chroma errors on first run | Ensure `data/chroma/` exists (from LFS pull) |

## Git LFS

Large files (`data/chunks.jsonl`, `data/chroma/`) require Git LFS:

```powershell
git lfs install
git lfs pull
```

If files show as small pointer files instead of real data, LFS was not installed before clone.

## Embedding model download

The first retrieval or chat request downloads `all-MiniLM-L6-v2` from HuggingFace (~90 MB). This is cached locally. The web UI shows a progress bar on the first prompt.

If download is slow or blocked, ensure your network allows HuggingFace Hub access.

## Web UI

| Issue | Fix |
|-------|-----|
| `Web UI not built` message | Run `cd web/ui && npm run build`, or use `godot-web --dev` |
| Blank page in dev mode | Use `godot-web --dev` (starts API + Vite); open `http://localhost:5173` |
| Blank page in production | Run `npm run build` in `web/ui`, then `godot-web`; open `http://127.0.0.1:8000` |
| API key popup on send | Add your key in the top bar, or set `OPENAI_API_KEY` in `.env` for CLI |
| CORS errors in dev | Use `http://localhost:5173`, not the API port directly |

## Python environment

Use `python -m pip install -e .` if `pip` points to the wrong environment.

Ensure the venv is active before `godot-web` or `godot-ask`.
