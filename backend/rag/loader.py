from dataclasses import dataclass
from pathlib import Path
from typing import Any

from docx import Document
from pypdf import PdfReader


@dataclass
class LoadedPage:
    text: str
    page_number: int | None
    metadata: dict[str, Any]


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = []
    for line in text.split("\n"):
        line = " ".join(line.split())
        if line:
            lines.append(line)

    return "\n".join(lines).strip()


def load_txt_pages(path: Path, content_type: str) -> list[LoadedPage]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    text = clean_text(raw)

    return [
        LoadedPage(
            text=text,
            page_number=None,
            metadata={
                "filename": path.name,
                "source": str(path),
                "content_type": content_type,
                "page": None,
            },
        )
    ]


def load_pdf_pages(path: Path, content_type: str) -> list[LoadedPage]:
    reader = PdfReader(str(path))
    pages: list[LoadedPage] = []

    for i, page in enumerate(reader.pages):
        raw = page.extract_text() or ""
        text = clean_text(raw)

        if not text:
            continue

        pages.append(
            LoadedPage(
                text=text,
                page_number=i + 1,
                metadata={
                    "filename": path.name,
                    "source": str(path),
                    "content_type": content_type,
                    "page": i + 1,
                },
            )
        )

    return pages


def load_docx_pages(path: Path, content_type: str) -> list[LoadedPage]:
    doc = Document(str(path))

    paras = []
    for p in doc.paragraphs:
        t = clean_text(p.text)
        if t:
            paras.append(t)

    text = "\n".join(paras)

    return [
        LoadedPage(
            text=text,
            page_number=None,
            metadata={
                "filename": path.name,
                "source": str(path),
                "content_type": content_type,
                "page": None,
            },
        )
    ]


def load_document_pages(path: Path, content_type: str) -> list[LoadedPage]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if content_type == "application/pdf":
        return load_pdf_pages(path, content_type)

    if content_type == "text/plain":
        return load_txt_pages(path, content_type)

    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return load_docx_pages(path, content_type)

    raise ValueError(f"Unsupported file type: {content_type}")


def load_document(path: Path, content_type: str) -> str:
    pages = load_document_pages(path, content_type)
    return "\n\n".join(page.text for page in pages)