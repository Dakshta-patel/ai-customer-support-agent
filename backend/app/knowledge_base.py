"""Load and section-chunk the NovaCart Markdown knowledge base."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


_HEADING_PATTERN = re.compile(r"^(#{1,6}\s+.+?)\s*$", re.MULTILINE)
_DEFAULT_MAX_CHUNK_CHARACTERS = 1600


@dataclass(frozen=True)
class KnowledgeChunk:
    """A retrievable piece of a knowledge-base document."""

    chunk_id: str
    text: str
    source: str
    index: int


def get_knowledge_base_directory() -> Path:
    """Return the repository's data/knowledge_base directory."""

    project_root = Path(__file__).resolve().parents[2]
    knowledge_base_directory = project_root / "data" / "knowledge_base"
    if not knowledge_base_directory.is_dir():
        raise FileNotFoundError(
            f"Knowledge-base directory not found: {knowledge_base_directory}"
        )
    return knowledge_base_directory


def load_documents(directory: Path | None = None) -> dict[str, str]:
    """Load all Markdown documents, keyed by their source filename."""

    knowledge_base_directory = directory or get_knowledge_base_directory()
    documents: dict[str, str] = {}

    for path in sorted(knowledge_base_directory.glob("*.md")):
        if path.name == ".gitkeep":
            continue
        documents[path.name] = path.read_text(encoding="utf-8")

    return documents


def _split_long_section(section: str, max_characters: int) -> list[str]:
    """Split a long section at paragraph boundaries while retaining its heading."""

    if len(section) <= max_characters:
        return [section]

    lines = section.splitlines()
    heading = lines[0] if lines and lines[0].lstrip().startswith("#") else ""
    body = "\n".join(lines[1:] if heading else lines).strip()
    paragraphs = [paragraph.strip() for paragraph in body.split("\n\n") if paragraph.strip()]

    chunks: list[str] = []
    current_parts: list[str] = [heading] if heading else []
    current_length = len(heading)

    for paragraph in paragraphs:
        separator_length = 2 if len(current_parts) > (1 if heading else 0) else 1
        proposed_length = current_length + separator_length + len(paragraph)
        if current_parts and proposed_length > max_characters and len(current_parts) > (1 if heading else 0):
            chunks.append("\n\n".join(current_parts).strip())
            current_parts = [heading, paragraph] if heading else [paragraph]
            current_length = len(heading) + (2 if heading else 0) + len(paragraph)
        else:
            current_parts.append(paragraph)
            current_length = proposed_length

    if current_parts and any(part.strip() for part in current_parts):
        chunks.append("\n\n".join(current_parts).strip())

    return chunks or [section]


def chunk_document(
    source: str, text: str, max_characters: int = _DEFAULT_MAX_CHUNK_CHARACTERS
) -> list[KnowledgeChunk]:
    """Split one Markdown document into heading-aware chunks."""

    sections: list[str] = []
    heading_matches = list(_HEADING_PATTERN.finditer(text))

    if heading_matches and heading_matches[0].start() > 0:
        sections.append(text[: heading_matches[0].start()].strip())

    for position, match in enumerate(heading_matches):
        end = heading_matches[position + 1].start() if position + 1 < len(heading_matches) else len(text)
        section = text[match.start() : end].strip()
        if section:
            sections.append(section)

    if not heading_matches and text.strip():
        sections.append(text.strip())

    chunks: list[KnowledgeChunk] = []
    for section in sections:
        for section_chunk in _split_long_section(section, max_characters):
            if section_chunk.strip():
                index = len(chunks)
                chunks.append(
                    KnowledgeChunk(
                        chunk_id=f"{source}:{index}",
                        text=section_chunk,
                        source=source,
                        index=index,
                    )
                )

    return chunks


def load_knowledge_base(
    directory: Path | None = None,
    max_characters: int = _DEFAULT_MAX_CHUNK_CHARACTERS,
) -> list[KnowledgeChunk]:
    """Load and chunk every Markdown document in the knowledge base."""

    chunks: list[KnowledgeChunk] = []
    for source, text in load_documents(directory).items():
        chunks.extend(chunk_document(source, text, max_characters))
    return chunks
