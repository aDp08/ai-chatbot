import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from google import genai
from rag.splitter import Chunk

load_dotenv()

EMBED_MODEL = "gemini-embedding-001"

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


@dataclass
class EmbeddedChunk:
    id: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any]


def embed_text(text: str) -> list[float]:
    res = client.models.embed_content(
        model=EMBED_MODEL,
        contents=text,
    )

    return res.embeddings[0].values


def embed_chunks(chunks: list[Chunk]) -> list[EmbeddedChunk]:
    embedded_at = datetime.now(timezone.utc).isoformat()
    embedded: list[EmbeddedChunk] = []

    for chunk in chunks:
        vec = embed_text(chunk.text)

        embedded.append(
            EmbeddedChunk(
                id=chunk.id,
                text=chunk.text,
                embedding=vec,
                metadata={
                    **chunk.metadata,
                    "embedding_model": EMBED_MODEL,
                    "embedding_dimension": len(vec),
                    "embedded_at": embedded_at,
                },
            )
        )

    return embedded