"""Chunk class reference RST files (coarse + fine granularity)."""

from __future__ import annotations

import re

from scripts.chunk.config import GODOT_VERSION
from scripts.chunk.docs.rst_utils import (
    TabContent,
    dedupe_tab_prose,
    file_hierarchy_parts,
    iter_content_blocks,
    preprocess_rst,
    simplify_rst_markup,
)
from scripts.chunk.schema import Chunk, make_doc_chunk_id, slugify

_CLASS_TITLE_RE = re.compile(r"^([A-Z][A-Za-z0-9_]+)\s*$", re.MULTILINE)
_ANCHOR_RE = re.compile(r"^\.\.\s+_(class_\w+_(?:method|property|signal|constant)_[^:]+):")

_MAJOR_SECTIONS = (
    "Description",
    "Tutorials",
    "Properties",
    "Methods",
    "Signals",
    "Enumerations",
    "Theme Properties",
    "Property Descriptions",
    "Method Descriptions",
    "Signal Descriptions",
    "Constants",
    "Constructors",
    "Operators",
)


def chunk_class_ref_file(rel_path: str, raw_content: str) -> list[Chunk]:
    """Produce coarse and fine chunks from a class_*.rst file."""
    cleaned = preprocess_rst(raw_content)
    if not cleaned.strip():
        return []

    class_name = _extract_class_name(cleaned, rel_path)
    path_parts = file_hierarchy_parts(rel_path)
    hierarchy = path_parts + [class_name]
    class_parent_id = make_doc_chunk_id(rel_path)

    chunks: list[Chunk] = []

    intro = _extract_intro(cleaned, class_name)
    if intro.strip():
        chunks.append(
            Chunk(
                chunk_id=class_parent_id,
                text=intro,
                source_type="doc",
                role="api_ref",
                granularity="coarse",
                godot_version=GODOT_VERSION,
                hierarchy=hierarchy,
                file_path=rel_path,
                title=class_name,
            )
        )

    sections = _split_major_sections(cleaned)

    for section_name, section_body in sections.items():
        if not section_body.strip():
            continue
        if section_name in ("Property Descriptions", "Method Descriptions", "Signal Descriptions"):
            chunks.extend(
                _chunk_fine_items(
                    rel_path=rel_path,
                    class_name=class_name,
                    hierarchy=hierarchy,
                    parent_id=class_parent_id,
                    section_name=section_name,
                    body=section_body,
                )
            )
            continue

        if section_name in ("Properties", "Methods", "Signals", "Enumerations", "Theme Properties"):
            coarse_id = make_doc_chunk_id(rel_path, section_name, suffix="coarse")
            chunks.append(
                Chunk(
                    chunk_id=coarse_id,
                    text=f"## {class_name} — {section_name}\n\n{section_body.strip()}",
                    source_type="doc",
                    role="api_ref",
                    granularity="coarse",
                    godot_version=GODOT_VERSION,
                    hierarchy=hierarchy + [section_name],
                    parent_id=class_parent_id,
                    file_path=rel_path,
                    title=f"{class_name} — {section_name}",
                )
            )
            continue

        if section_name == "Description":
            continue  # already in intro

        if section_name == "Tutorials":
            coarse_id = make_doc_chunk_id(rel_path, "Tutorials", suffix="coarse")
            chunks.append(
                Chunk(
                    chunk_id=coarse_id,
                    text=f"## {class_name} — Tutorials\n\n{section_body.strip()}",
                    source_type="doc",
                    role="api_ref",
                    granularity="coarse",
                    godot_version=GODOT_VERSION,
                    hierarchy=hierarchy + ["Tutorials"],
                    parent_id=class_parent_id,
                    file_path=rel_path,
                    title=f"{class_name} — Tutorials",
                )
            )

    return chunks


def _extract_class_name(cleaned: str, rel_path: str) -> str:
    match = re.search(r"^\.\.\s+_class_(\w+):", cleaned, re.MULTILINE)
    if match:
        return match.group(1)
    stem = rel_path.split("/")[-1].replace(".rst", "")
    if stem.startswith("class_"):
        return stem[6:]
    return stem


def _extract_intro(cleaned: str, class_name: str) -> str:
    lines = cleaned.splitlines()
    intro_lines: list[str] = []
    in_desc = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "Description" and i + 1 < len(lines) and lines[i + 1].strip() == "-----------":
            in_desc = True
            continue
        if in_desc:
            if stripped in _MAJOR_SECTIONS and i + 1 < len(lines):
                next_u = lines[i + 1].strip()
                if next_u and all(c == "-" for c in next_u):
                    break
            intro_lines.append(line)
        elif stripped == class_name or "**Inherits:**" in stripped:
            intro_lines.append(line)
    text = simplify_rst_markup("\n".join(intro_lines)).strip()
    if not text.startswith(class_name):
        text = f"# {class_name}\n\n{text}"
    return text


def _split_major_sections(cleaned: str) -> dict[str, str]:
    lines = cleaned.splitlines()
    sections: dict[str, list[str]] = {}
    current: str | None = None
    i = 0
    while i < len(lines):
        line = lines[i]
        if i + 1 < len(lines):
            title = line.strip()
            underline = lines[i + 1].strip()
            if title in _MAJOR_SECTIONS and underline and all(c == "-" for c in underline):
                current = title
                sections[current] = []
                i += 2
                continue
        if current:
            sections[current].append(line)
        i += 1
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def _chunk_fine_items(
    *,
    rel_path: str,
    class_name: str,
    hierarchy: list[str],
    parent_id: str,
    section_name: str,
    body: str,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    items = _split_on_item_anchors(body)

    item_type = "method"
    if "Property" in section_name:
        item_type = "property"
    elif "Signal" in section_name:
        item_type = "signal"

    for anchor, item_body in items:
        if not item_body.strip():
            continue
        item_name = _anchor_item_name(anchor, item_type)
        item_id = make_doc_chunk_id(rel_path, anchor, suffix="fine")

        text_parts = [f"## {class_name}.{item_name}"]
        processed = _process_fine_item_body(item_body)
        text_parts.append(processed)
        text = "\n\n".join(text_parts)

        lang_chunks = _split_fine_tabs(
            rel_path=rel_path,
            class_name=class_name,
            item_name=item_name,
            anchor=anchor,
            hierarchy=hierarchy + [section_name, item_name],
            parent_id=item_id,
            body=processed,
            base_text_header=f"## {class_name}.{item_name}",
        )
        if lang_chunks:
            chunks.append(
                Chunk(
                    chunk_id=item_id,
                    text=text,
                    source_type="doc",
                    role="api_ref",
                    granularity="fine",
                    godot_version=GODOT_VERSION,
                    hierarchy=hierarchy + [section_name, item_name],
                    parent_id=parent_id,
                    file_path=rel_path,
                    title=f"{class_name}.{item_name}",
                )
            )
            chunks.extend(lang_chunks)
        else:
            chunks.append(
                Chunk(
                    chunk_id=item_id,
                    text=text,
                    source_type="doc",
                    role="api_ref",
                    granularity="fine",
                    godot_version=GODOT_VERSION,
                    hierarchy=hierarchy + [section_name, item_name],
                    parent_id=parent_id,
                    file_path=rel_path,
                    title=f"{class_name}.{item_name}",
                )
            )

    return chunks


def _split_on_item_anchors(body: str) -> list[tuple[str, str]]:
    lines = body.splitlines()
    items: list[tuple[str, str]] = []
    current_anchor = ""
    current_lines: list[str] = []
    i = 0

    while i < len(lines):
        anchor_match = _ANCHOR_RE.match(lines[i].strip())
        if anchor_match:
            if current_anchor or current_lines:
                items.append((current_anchor, "\n".join(current_lines)))
            current_anchor = anchor_match.group(1)
            current_lines = []
            i += 1
            continue
        if current_anchor:
            if lines[i].strip() == ".." and i + 1 < len(lines) and "classref-item-separator" in lines[i + 1]:
                i += 2
                while i < len(lines) and lines[i].strip() in ("", "----"):
                    i += 1
                continue
            current_lines.append(lines[i])
        i += 1

    if current_anchor:
        items.append((current_anchor, "\n".join(current_lines)))

    return items


def _anchor_item_name(anchor: str, item_type: str) -> str:
    for prefix in (f"_private_{item_type}_", f"_{item_type}_"):
        idx = anchor.rfind(prefix)
        if idx >= 0:
            return anchor[idx + len(prefix) :]
    return anchor.split("_")[-1]


def _process_fine_item_body(body: str) -> str:
    return preprocess_rst(body) if ".. tabs::" in body else simplify_rst_markup(body).strip()


def _split_fine_tabs(
    *,
    rel_path: str,
    class_name: str,
    item_name: str,
    anchor: str,
    hierarchy: list[str],
    parent_id: str,
    body: str,
    base_text_header: str,
) -> list[Chunk]:
    """Add per-language tab children for fine method chunks."""
    extra: list[Chunk] = []
    seen_tab_ids: set[str] = set()
    for block_type, data in iter_content_blocks(body):
        if block_type != "tabs":
            continue
        for tab in dedupe_tab_prose(data):  # type: ignore[arg-type]
            if tab.is_stub or not tab.content.strip() or not tab.language:
                continue
            tab_id = make_doc_chunk_id(
                rel_path,
                anchor,
                suffix=f"fine_{tab.language}",
            )
            if tab_id in seen_tab_ids:
                continue
            seen_tab_ids.add(tab_id)
            extra.append(
                Chunk(
                    chunk_id=tab_id,
                    text=f"{base_text_header} ({tab.label})\n\n{tab.content}",
                    source_type="doc",
                    role="api_ref",
                    granularity="fine",
                    godot_version=GODOT_VERSION,
                    hierarchy=hierarchy + [tab.label],
                    parent_id=parent_id,
                    file_path=rel_path,
                    title=f"{class_name}.{item_name} — {tab.label}",
                    language=tab.language,  # type: ignore[arg-type]
                )
            )
    return extra
