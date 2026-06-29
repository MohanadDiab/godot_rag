"""Summarize project.godot for chunking."""

from __future__ import annotations

import re


def summarize_project_godot(raw: str, category: str, project_name: str) -> str:
    """Extract high-value fields from project.godot."""
    lines = raw.splitlines()
    sections: dict[str, list[str]] = {}
    current = "_top"
    sections[current] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith(";") or not stripped:
            continue
        section_match = re.match(r"^\[([^\]]+)\]", stripped)
        if section_match:
            current = section_match.group(1)
            sections.setdefault(current, [])
            continue
        if current == "input" and stripped.endswith("={"):
            sections.setdefault("input", []).append(stripped[:-1])
            continue
        if current == "input" and '"events"' in stripped:
            continue
        if current == "input" and stripped.startswith("Object("):
            continue
        if current == "input" and stripped in ("}", "]", "],"):
            continue
        sections.setdefault(current, []).append(stripped)

    parts = [f"Project: {category}/{project_name}", "File: project.godot", ""]

    for key in ("application", "display", "rendering", "input"):
        if key not in sections:
            continue
        parts.append(f"[{key}]")
        for entry in sections[key][:30]:
            if key == "input" and entry.endswith("="):
                parts.append(entry)
            elif not entry.startswith("Object("):
                parts.append(entry)
        parts.append("")

    return "\n".join(parts).strip()
