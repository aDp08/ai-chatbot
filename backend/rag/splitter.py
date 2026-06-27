import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag.loader import LoadedPage


@dataclass
class Chunk:
    id: str
    text: str
    index: int
    metadata: dict[str, Any]


def make_chunk_id(source_id: str, filename: str, page: int | None, index: int, text: str) -> str:
    #source_id = page.metadata.get("source_id", page.metadata["filename"])
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    page_part = f"p{page}" if page is not None else "pnone"
    return f"{source_id}:{page_part}:c{index}:{h}"


def split_pages(
    pages: list[LoadedPage],
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[Chunk]:
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[Chunk] = []
    idx = 0

    for page in pages:
        parts = splitter.split_text(page.text)

        for local_idx, part in enumerate(parts):
            part = part.strip()

            if len(part) < 50:
                continue
            source_id = hashlib.sha256(page.metadata["source"].encode()).hexdigest()[:12]
            cid = make_chunk_id(
                source_id=source_id,
                filename=page.metadata["filename"],
                page=page.page_number,
                index=idx,
                text=part,
                
            )

            chunks.append(
                Chunk(
                    id=cid,
                    text=part,
                    index=idx,
                    metadata={
                        **page.metadata,
                        "chunk_index": idx,
                        "page_chunk_index": local_idx,
                        "chunk_size": chunk_size,
                        "chunk_overlap": overlap,
                        "splitter": "recursive_character",
                        "char_length": len(part),
                        "created_at": datetime.now(timezone.utc).isoformat()
                    },
                )
            )

            idx += 1

    return chunks
