# API keys and environment variables

The Godot RAG agent uses **OpenAI** for answering questions. Vector search runs locally (ChromaDB + sentence-transformers) and does not need a cloud API key.

## Quick setup

1. Copy the template in the project root:

   ```powershell
   copy .env.example .env
   ```

2. Edit `.env` and set your OpenAI API key:

   ```
   OPENAI_API_KEY=sk-your-key-here
   OPENAI_MODEL=gpt-5-nano
   ```

3. **Never commit `.env`** — it is listed in `.gitignore`. Only `.env.example` (with placeholders) belongs in git.

## Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes (for `ask` / agent) | Your [OpenAI API key](https://platform.openai.com/api-keys). Starts with `sk-`. |
| `OPENAI_MODEL` | No | Chat model name. Default: `gpt-5-nano`. Use any model your account supports (e.g. `gpt-4o-mini`, `gpt-5.4-nano`). |

## What needs a key?

| Feature | OpenAI key needed? |
|---------|-------------------|
| `godot-ask` / `ask()` | **Yes** |
| `godot-ask --search-only` / `search()` | **No** — local retrieval only |
| `godot-rag query` / `retrieve` | **No** |
| `godot-rag load-chroma` | **No** — uses local embeddings |

## Getting an OpenAI API key

1. Sign in at [platform.openai.com](https://platform.openai.com).
2. Go to **API keys** and create a new secret key.
3. Paste it into `.env` as `OPENAI_API_KEY=sk-...`.
4. Ensure your account has credits or billing enabled for the model you choose.

## Security checklist

- Do **not** put keys in source code, notebooks, or commit messages.
- Do **not** share `.env` in screenshots or issue attachments.
- Rotate the key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys) if it is ever exposed.
- For CI, use repository **secrets** (GitHub Actions: `OPENAI_API_KEY`), not committed files.

## Alternative: environment variables without `.env`

You can export variables in your shell instead of using a file:

```powershell
$env:OPENAI_API_KEY = "sk-your-key-here"
$env:OPENAI_MODEL = "gpt-5-nano"
godot-ask "How does move_and_slide work?"
```

```bash
export OPENAI_API_KEY=sk-your-key-here
export OPENAI_MODEL=gpt-5-nano
godot-ask "How does move_and_slide work?"
```

`python-dotenv` loads `.env` from the project root automatically when you use the agent.

## Troubleshooting

| Error | Fix |
|-------|-----|
| `OPENAI_API_KEY is not set` | Create `.env` from `.env.example` or set the env var |
| Model not found / 404 | Set `OPENAI_MODEL` to a model your account can access |
| Rate limit / quota | Check billing and usage on the OpenAI dashboard |
| Key works in shell but not in IDE | Ensure the IDE terminal cwd is the project root, or set env in IDE run config |
