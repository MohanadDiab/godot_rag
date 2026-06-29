"""RST preprocessing and parsing utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator

TAB_LANGUAGE_MAP: dict[str, str] = {
    "gdscript": "gdscript",
    "csharp": "csharp",
    "c++": "cpp",
    "cpp": "cpp",
}

STUB_TAB_PATTERNS = (
    "not rewritten",
    "wasn't rewritten",
    "was not rewritten",
    "not yet rewritten",
)

HEADING_CHARS = "=~-^"

_REF_INLINE_RE = re.compile(
    r":ref:`([^`<]+)(?:<[^>]+>)?`",
)
_DOC_INLINE_RE = re.compile(r":doc:`([^`]+)`")
_CLASS_LINK_RE = re.compile(r":ref:`(\w+)<class_\w+>`")
_IMAGE_DIRECTIVE_RE = re.compile(r"^\.\.\s+image::\s+(\S+)")
_METADATA_LINE_RE = re.compile(
    r"^:(?:github_url|allow_comments|generated):",
)
_EDITOR_WALKTHROUGH_RE = re.compile(
    r"^(?:Click|Open the|In the .+ window, click|Choose the path|Launch Godot)",
    re.IGNORECASE,
)


@dataclass
class RstSection:
    """A heading-delimited section of an RST document."""

    title: str
    level: int
    content: str
    anchor: str | None = None


@dataclass
class TabContent:
    """Content extracted from a single RST tab."""

    label: str
    language: str | None
    content: str
    is_stub: bool = False


def map_tab_language(tab_label: str, code_tab_lang: str | None = None) -> str | None:
    if code_tab_lang:
        key = code_tab_lang.strip().lower()
        return TAB_LANGUAGE_MAP.get(key, key if key in ("gdscript", "csharp", "cpp") else None)
    label = tab_label.strip().lower()
    if label in TAB_LANGUAGE_MAP:
        return TAB_LANGUAGE_MAP[label]
    if "c#" in label or label == "csharp":
        return "csharp"
    if "gdscript" in label:
        return "gdscript"
    if "c++" in label:
        return "cpp"
    return None


def is_stub_tab_content(content: str) -> bool:
    lowered = content.lower()
    return any(p in lowered for p in STUB_TAB_PATTERNS)


def simplify_rst_markup(text: str) -> str:
    """Reduce RST references to plain readable text."""

    def ref_repl(match: re.Match[str]) -> str:
        return match.group(1)

    text = _REF_INLINE_RE.sub(ref_repl, text)
    text = _DOC_INLINE_RE.sub(
        lambda m: m.group(1).split("/")[-1].replace("_", " "),
        text,
    )
    text = _CLASS_LINK_RE.sub(r"\1", text)
    text = text.replace("|void|", "void")
    text = text.replace(":ref:`🔗", "")
    return text


def _strip_directive_block(lines: list[str], start: int, base_indent: int) -> int:
    """Skip a directive body; return index after the block."""
    i = start + 1
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent <= base_indent and not line.startswith(" "):
            break
        i += 1
    return i


def preprocess_rst(raw: str) -> str:
    """Normalize RST: strip noise, simplify refs, filter low-value paragraphs."""
    lines = raw.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if _METADATA_LINE_RE.match(stripped):
            i += 1
            continue

        if stripped.startswith(".. DO NOT EDIT"):
            i += 1
            while i < len(lines) and lines[i].strip().startswith(".."):
                i += 1
            continue

        if stripped.startswith(".. toctree::"):
            i = _strip_directive_block(lines, i, len(line) - len(line.lstrip(" ")))
            continue

        if stripped.startswith(".. only:: i18n"):
            i = _strip_directive_block(lines, i, len(line) - len(line.lstrip(" ")))
            continue

        if stripped.startswith(".. only::"):
            # Keep body; drop the only:: line itself
            i += 1
            continue

        if stripped.startswith(".. raw:: html"):
            i = _strip_directive_block(lines, i, len(line) - len(line.lstrip(" ")))
            continue

        image_match = _IMAGE_DIRECTIVE_RE.match(stripped)
        if image_match:
            out.append(f"[image: {image_match.group(1)}]")
            i += 1
            continue

        if stripped.startswith(".. rst-class::"):
            i += 1
            continue

        if stripped in ("----", "===") or (
            stripped and all(c == stripped[0] for c in stripped) and stripped[0] in HEADING_CHARS
        ):
            # Standalone separator lines from class ref — skip
            if stripped == "----" and out and out[-1].strip():
                i += 1
                continue

        out.append(line)
        i += 1

    text = "\n".join(out)
    text = simplify_rst_markup(text)
    text = _filter_editor_walkthrough_paragraphs(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _filter_editor_walkthrough_paragraphs(text: str) -> str:
    """Drop paragraphs that are purely editor UI navigation."""
    paragraphs = re.split(r"\n\s*\n", text)
    kept: list[str] = []
    for para in paragraphs:
        if not para.strip():
            continue
        if _is_editor_only_paragraph(para.strip()):
            continue
        kept.append(para)
    return "\n\n".join(kept)


def _is_editor_only_paragraph(paragraph: str) -> bool:
    if "```" in paragraph or ".. code" in paragraph:
        return False
    if paragraph.count("``") >= 2:
        return False
    if _EDITOR_WALKTHROUGH_RE.match(paragraph) and "[image:" in paragraph:
        return True
    if _EDITOR_WALKTHROUGH_RE.match(paragraph):
        # Keep if it mentions technical values
        if re.search(r"`[a-z_]+`", paragraph, re.IGNORECASE):
            return False
        if re.search(r"\d+", paragraph):
            return False
        if "→" in paragraph or "->" in paragraph:
            if "``" not in paragraph:
                return True
    return False


def parse_sections(text: str) -> list[RstSection]:
    """Split RST into sections by underline/overline headings."""
    lines = text.splitlines()
    sections: list[RstSection] = []
    current_anchor: str | None = None
    i = 0
    preamble_lines: list[str] = []

    while i < len(lines):
        line = lines[i]
        anchor_match = re.match(r"^\.\.\s+_([^:]+):\s*$", line.strip())
        if anchor_match and i + 1 < len(lines):
            current_anchor = anchor_match.group(1)
            i += 1
            continue

        if i + 1 < len(lines):
            next_line = lines[i + 1]
            if (
                line.strip()
                and next_line.strip()
                and all(c == next_line.strip()[0] for c in next_line.strip())
                and next_line.strip()[0] in HEADING_CHARS
            ):
                title = line.strip()
                level = HEADING_CHARS.index(next_line.strip()[0]) + 1
                i += 2
                body_lines: list[str] = []
                while i < len(lines):
                    if i + 1 < len(lines):
                        nl = lines[i + 1]
                        if (
                            lines[i].strip()
                            and nl.strip()
                            and all(c == nl.strip()[0] for c in nl.strip())
                            and nl.strip()[0] in HEADING_CHARS
                        ):
                            break
                    body_lines.append(lines[i])
                    i += 1
                content = "\n".join(body_lines).strip()
                sections.append(
                    RstSection(
                        title=title,
                        level=level,
                        content=content,
                        anchor=current_anchor,
                    )
                )
                current_anchor = None
                continue

        if not sections:
            preamble_lines.append(line)
        i += 1

    preamble = "\n".join(preamble_lines).strip()
    if preamble and not sections:
        sections.append(RstSection(title="", level=0, content=preamble))
    elif preamble and sections:
        sections[0].content = f"{preamble}\n\n{sections[0].content}".strip()

    return sections


def iter_content_blocks(content: str) -> Iterator[tuple[str, str | list[TabContent]]]:
    """
    Yield (block_type, data) where block_type is 'prose' or 'tabs'.
    For prose, data is str. For tabs, data is list[TabContent].
    """
    lines = content.splitlines()
    i = 0
    prose_buf: list[str] = []

    def flush_prose() -> Iterator[tuple[str, str | list[TabContent]]]:
        nonlocal prose_buf
        if prose_buf:
            text = "\n".join(prose_buf).strip()
            prose_buf = []
            if text:
                yield ("prose", text)

    while i < len(lines):
        if lines[i].strip() == ".. tabs::":
            yield from flush_prose()
            tabs, i = _parse_tabs_block(lines, i)
            yield ("tabs", tabs)
            continue
        prose_buf.append(lines[i])
        i += 1

    yield from flush_prose()


def _parse_tabs_block(lines: list[str], start: int) -> tuple[list[TabContent], int]:
    tabs: list[TabContent] = []
    i = start + 1
    current_label = ""
    current_lang: str | None = None
    content_lines: list[str] = []

    def flush_tab() -> None:
        nonlocal content_lines, current_label, current_lang
        if not current_label and not content_lines:
            return
        body = "\n".join(content_lines).strip()
        lang = map_tab_language(current_label, current_lang)
        stub = is_stub_tab_content(body)
        tabs.append(
            TabContent(
                label=current_label or "tab",
                language=lang,
                content=body,
                is_stub=stub,
            )
        )
        content_lines = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        tab_match = re.match(r"\.\.\s+tab::\s+(.+)", stripped)
        code_tab_match = re.match(r"\.\.\s+code-tab::\s+(\S+)\s*(.*)", stripped)

        if tab_match or code_tab_match:
            flush_tab()
            if code_tab_match:
                current_lang = code_tab_match.group(1)
                current_label = code_tab_match.group(2).strip() or code_tab_match.group(1)
            else:
                current_label = tab_match.group(1)
                current_lang = None
            i += 1
            continue

        if current_label:
            if not stripped:
                i += 1
                continue
            # Unindented prose after tab content ends the tabs block
            if not line.startswith(" ") and not line.startswith("\t") and not stripped.startswith(".."):
                flush_tab()
                break
            content_lines.append(line.strip() if line.startswith("    ") else stripped)
            i += 1
            continue

        if stripped.startswith(".. ") and not stripped.startswith(".. tab") and not stripped.startswith(
            ".. code-tab"
        ):
            if not line.startswith(" ") and not line.startswith("\t"):
                break

        if not stripped:
            i += 1
            continue

        i += 1

    flush_tab()
    return tabs, i


def file_hierarchy_parts(rel_path: str) -> list[str]:
    parts = rel_path.replace("\\", "/").split("/")
    if parts[-1].endswith(".rst"):
        parts[-1] = parts[-1][:-4]
    return parts


def dedupe_tab_prose(tabs: list[TabContent]) -> list[TabContent]:
    """Mark duplicate identical tab bodies (keep first of each language)."""
    seen: dict[str, str] = {}
    result: list[TabContent] = []
    for tab in tabs:
        key = tab.content.strip()
        lang = tab.language or "unknown"
        if key in seen and seen[key] == lang:
            continue
        seen[key] = lang
        result.append(tab)
    return result
