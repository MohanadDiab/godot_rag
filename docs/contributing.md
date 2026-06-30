# Contributing

Thank you for improving Godot RAG!

## Focus areas

- **Web UI** — `web/ui/` (primary product)
- **Agent & retrieval** — `scripts/agent/`, `scripts/ingest/`
- **Documentation** — `docs/` (MkDocs)

## Setup

```powershell
git clone https://github.com/MohanadDiab/godot_rag.git
cd godot_rag
git lfs pull
python -m venv .venv
.\.venv\Scripts\pip install -e .
cd web/ui && npm install && cd ../..
```

**Run the app:** `godot-web` (after `npm run build` in `web/ui`)

**UI development:** `godot-web --dev`

## Documentation

```powershell
pip install -r docs/requirements.txt
mkdocs serve
```

Add screenshots to `docs/assets/screenshots/` per `docs/assets/screenshots/MANIFEST.txt`.

## Pull requests

1. Fork the repository
2. Create a feature branch
3. Open a PR with a clear description

Never commit `.env` or API keys. See [API keys](getting-started/api-keys.md).

## License

Contributions are licensed under the [MIT License](https://github.com/MohanadDiab/godot_rag/blob/main/LICENSE).
