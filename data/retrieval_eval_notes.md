# Retrieval evaluation notes

Smoke tests and A/B results for the Chroma `godot_rag` collection (29,426 chunks).

```powershell
.\.venv\Scripts\python scripts/chunk_pipeline.py eval-retrieval -n 5
.\.venv\Scripts\python scripts/chunk_pipeline.py retrieve "<query>" --prompt
.\.venv\Scripts\python scripts/chunk_pipeline.py query "<query>" -n 5 --text-only
```

## Coarse vs fine A/B (Phase 7)

Eval run: `data/retrieval_eval.json` (7 queries x 3 modes, top-1 match against expected tokens).

| Category | Winner (top-1) | Notes |
|----------|----------------|-------|
| api_method | unfiltered / fine tie | All modes hit; fine gives `class_characterbody2d#*_fine` method chunks |
| api_explain | unfiltered | Tutorial `using_character_body_2d` ranks first |
| api_overview | unfiltered | Coarse also hits; fine misses top-1 for "What is CharacterBody2D" |
| demo_code | unfiltered only | Use agent `retrieve` with `--source-type demo` fallback |
| scene | unfiltered | Improved with `scene` role bias for `.tscn` / signal queries |
| demo_project | unfiltered | Include project name in query (`compute heightmap`) |
| resource_doc | unfiltered | OpenXR action map docs rank well |

**Defaults kept:** `granularity_bias` applies `fine` for snake_case methods, `coarse` for "How does ClassName work?" — but unfiltered search is robust enough that hard filtering is optional.

## Agent retrieval

`retrieve` assembles separate prompt slots:

- **Documentation** — `explanation` + `api_ref` doc chunks
- **Example code** — demo `.gd` / `.cs` / shaders
- **Scenes and resources** — full `.tscn` / `.tres` when query mentions scenes or `--include-scenes`
- **Linked context** — `related_ids` expansion from cross-linking pass

```powershell
.\.venv\Scripts\python scripts/chunk_pipeline.py retrieve "dodge the creeps player movement" --prompt
.\.venv\Scripts\python scripts/chunk_pipeline.py retrieve "signal connection player.tscn" --include-scenes --prompt
```

Programmatic use:

```python
from scripts.ingest.retriever import retrieve_for_agent, format_context_for_prompt

context = retrieve_for_agent("How does move_and_slide work?")
prompt_block = format_context_for_prompt(context)
```

## Tuning knobs (`scripts/chunk/config.py`)

| Setting | Default | Re-ingest needed? |
|---------|---------|-----------------|
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Chroma rebuild only |
| `SEMANTIC_CHUNK_MIN_CHARS` | 500 | Re-chunk docs |
| `MAX_CHUNK_CHARS` | 4000 | Re-chunk docs |
| `SEMANTIC_BREAKPOINT_THRESHOLD_AMOUNT` | 95 | Re-chunk docs |

Swap embedding model: edit `EMBEDDING_MODEL`, then `load-chroma --rebuild`.

## Manual smoke queries

| Query | Expected | Result |
|-------|----------|--------|
| How does CharacterBody2D move_and_slide work? | Physics tutorial + demo | Good via `retrieve --prompt` |
| dodge the creeps player.gd movement | `player.gd` demo | Use `retrieve` (fills code slot) |
| fix signal connection in tscn | `.tscn` with `[connection` | Improved with scene role bias |
| compute shader heightmap | `compute/heightmap` | Add project name to query |
| OpenXR action map | XR doc + class ref | Good doc coverage |
