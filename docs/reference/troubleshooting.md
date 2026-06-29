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
| Blank page in dev mode | Ensure `godot-web` is running on port 8000 and Vite dev server on 5173 |
| API key popup on send | Add your key in the top bar, or set `OPENAI_API_KEY` in `.env` for CLI |
| CORS errors in dev | Use the Vite dev server URL (`localhost:5173`), not the API port directly |

## Python environment

Use `python -m pip` if `pip` points to a broken or wrong virtualenv:

```powershell
python -m pip install -e ".[web]"
```

Ensure you activate the project venv before running `godot-ask` or `godot-web`.
