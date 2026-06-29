"""Chunk tutorial and getting_started RST documents."""

from __future__ import annotations

from scripts.chunk.config import GODOT_VERSION
from scripts.chunk.docs.rst_utils import (
    TabContent,
    dedupe_tab_prose,
    file_hierarchy_parts,
    iter_content_blocks,
    parse_sections,
    preprocess_rst,
)
from scripts.chunk.schema import Chunk, make_doc_chunk_id, slugify


def chunk_tutorial_file(rel_path: str, raw_content: str) -> list[Chunk]:
    """Produce chunks from a tutorial/getting_started RST file."""
    cleaned = preprocess_rst(raw_content)
    if not cleaned.strip():
        return []

    path_parts = file_hierarchy_parts(rel_path)
    chunks: list[Chunk] = []

    sections = parse_sections(cleaned)
    if not sections:
        return []

    # File-level parent chunk
    first = sections[0]
    file_title = first.title or path_parts[-1].replace("_", " ")
    file_id = make_doc_chunk_id(rel_path)
    overview_text = _build_file_overview(file_title, sections)
    if overview_text.strip():
        chunks.append(
            Chunk(
                chunk_id=file_id,
                text=overview_text,
                source_type="doc",
                role="explanation",
                godot_version=GODOT_VERSION,
                hierarchy=path_parts,
                file_path=rel_path,
                title=file_title,
            )
        )

    for section in sections:
        if not section.content.strip() and not section.title:
            continue
        section_title = section.title or file_title
        hierarchy = path_parts + ([section_title] if section.title else [])
        section_id = make_doc_chunk_id(rel_path, section_title)

        section_chunks = _chunk_section_content(
            rel_path=rel_path,
            section_id=section_id,
            section_title=section_title,
            hierarchy=hierarchy,
            content=section.content,
            parent_id=file_id if overview_text.strip() else None,
        )
        chunks.extend(section_chunks)

    return chunks


def _build_file_overview(title: str, sections: list) -> str:
    parts = [f"# {title}" if title else ""]
    if sections and sections[0].content:
        intro = sections[0].content.split("\n\n")[0][:800]
        if intro and sections[0].title:
            parts.append(intro)
    return "\n\n".join(p for p in parts if p).strip()


def _chunk_section_content(
    *,
    rel_path: str,
    section_id: str,
    section_title: str,
    hierarchy: list[str],
    content: str,
    parent_id: str | None,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    prose_parts: list[str] = []
    tab_groups: list[list[TabContent]] = []

    for block_type, data in iter_content_blocks(content):
        if block_type == "prose":
            prose_parts.append(data)  # type: ignore[arg-type]
        else:
            tab_groups.append(dedupe_tab_prose(data))  # type: ignore[arg-type]

    prose_text = "\n\n".join(prose_parts).strip()
    if prose_text:
        chunks.append(
            Chunk(
                chunk_id=section_id,
                text=f"## {section_title}\n\n{prose_text}" if section_title else prose_text,
                source_type="doc",
                role="explanation",
                godot_version=GODOT_VERSION,
                hierarchy=hierarchy,
                parent_id=parent_id,
                file_path=rel_path,
                title=section_title,
            )
        )

    section_parent = section_id if prose_text else parent_id

    for tab_group in tab_groups:
        for tab in tab_group:
            if tab.is_stub or not tab.content.strip():
                continue
            lang = tab.language
            suffix = lang or slugify(tab.label)
            tab_id = make_doc_chunk_id(rel_path, section_title, suffix=suffix)
            header = f"## {section_title} ({tab.label})\n\n" if section_title else ""
            chunks.append(
                Chunk(
                    chunk_id=tab_id,
                    text=f"{header}{tab.content}",
                    source_type="doc",
                    role="explanation",
                    godot_version=GODOT_VERSION,
                    hierarchy=hierarchy + [tab.label],
                    parent_id=section_parent,
                    file_path=rel_path,
                    title=f"{section_title} — {tab.label}",
                    language=lang,  # type: ignore[arg-type]
                )
            )

    # Section with only tabs and no prose — create a minimal parent anchor
    if not prose_text and tab_groups and section_title:
        anchor = Chunk(
            chunk_id=section_id,
            text=f"## {section_title}",
            source_type="doc",
            role="explanation",
            godot_version=GODOT_VERSION,
            hierarchy=hierarchy,
            parent_id=parent_id,
            file_path=rel_path,
            title=section_title,
        )
        chunks.insert(0, anchor)
        for c in chunks[1:]:
            if c.parent_id == section_parent:
                c.parent_id = section_id

    return chunks
