#!/usr/bin/env bash
# Clone Godot documentation and demo projects for rebuilding the RAG index.
# The pre-built vector index in data/chroma/ works without these repos.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

clone_if_missing() {
    local name="$1"
    local url="$2"
    local branch="${3:-}"
    if [[ -d "$name" ]]; then
        echo "  $name/ already exists — skipping"
        return
    fi
    echo "  Cloning $name ..."
    if [[ -n "$branch" ]]; then
        git clone --depth 1 --branch "$branch" "$url" "$name"
    else
        git clone --depth 1 "$url" "$name"
    fi
}

echo "Setting up Godot source corpora in $ROOT"
clone_if_missing "godot-docs" "https://github.com/godotengine/godot-docs.git" "master"
clone_if_missing "godot-demo-projects" "https://github.com/godotengine/godot-demo-projects.git"
echo "Done."
