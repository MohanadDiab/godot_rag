"""Cross-linking models and graph construction."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProjectLink:
    """Bidirectional association between doc tutorial prefix and demo project(s)."""

    doc_prefixes: list[str]
    demo_paths: list[str]  # e.g. 2d/dodge_the_creeps
    link_type: str = "tutorial_to_demo"
    source: str = "unknown"


@dataclass
class LinkGraph:
    """Collection of project-level doc ↔ demo links."""

    links: list[ProjectLink] = field(default_factory=list)

    def add(self, link: ProjectLink) -> None:
        for existing in self.links:
            if (
                set(existing.doc_prefixes) == set(link.doc_prefixes)
                and set(existing.demo_paths) == set(link.demo_paths)
            ):
                return
        self.links.append(link)

    def merge(self, other: LinkGraph) -> None:
        for link in other.links:
            self.add(link)
