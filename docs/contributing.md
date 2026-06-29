# Contributing

Thank you for your interest in improving Godot RAG!

## Ways to contribute

- **Bug reports** — open a GitHub issue with steps to reproduce
- **Documentation** — edit pages under `docs/` and preview with `mkdocs serve`
- **Web UI** — React app in `web/ui/`
- **Agent & retrieval** — `scripts/agent/` and `scripts/ingest/`

## Development setup

```powershell
git clone https://github.com/MohanadDiab/godot_rag.git
cd godot_rag
git lfs pull
python -m venv .venv
.\.venv\Scripts\pip install -e ".[web]"
cd web/ui && npm install && cd ../..
```

**Web UI development:** `godot-web --dev` (API + Vite in one terminal).

## Documentation preview

```powershell
pip install -r docs/requirements.txt
mkdocs serve
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) to preview the docs site locally.

## Pull requests

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Open a pull request with a clear description

## Security

- **Never commit `.env` or API keys**
- See [API keys](getting-started/api-keys.md) for safe key handling

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](https://github.com/MohanadDiab/godot_rag/blob/main/LICENSE).
