import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from pydantic import BaseModel
from rag.embedder import embed_chunks
from rag.loader import load_document_pages
from rag.splitter import split_pages

UPLOAD_DIR=Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
load_dotenv()
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client= genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class ChatReq(BaseModel):
    message: str


class ChatRes(BaseModel):
    reply: str


@app.get("/")
def home():
    return {"message": "Backend is running"}


@app.post("/chat", response_model=ChatRes)
def chat(req: ChatReq):
    msg = req.message.strip()

    if not msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=msg,
        )

        return {"reply": res.text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
async def upload_file(file: UploadFile=File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code= 400,
            detail="only .pdf, .doc and .txt are allowed"

        )
    file_path=UPLOAD_DIR/file.filename
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "content_type": file.content_type,
            "path": str(file_path),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
def ingest(filename: str, content_type: str):
    safe_name = Path(filename).name
    file_path = UPLOAD_DIR / safe_name

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {file_path}",
        )

    try:
        pages = load_document_pages(file_path, content_type)
        tot_len=sum((len(p.text)for p in pages))

        if tot_len==0:
            raise HTTPException(
                status_code=400,
                detail="No text extracted. This may be a scanned PDF.",
            )

        chunks = split_pages(pages, chunk_size=1000, overlap=200)

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No chunks created from text.",
            )

        vectors = embed_chunks([c.text for c in chunks])

        return {
            "message": "Document ingested successfully",
            "filename": safe_name,
            "text_length": len(text),
            "chunks": len(chunks),
            "vectors": len(vectors),
            "embedding_dimension": len(vectors[0]) if vectors else 0,
            "sample_chunk": chunks[0].text[:300],
        }

    except HTTPException:
        raise

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/debug/chunks")
def debug_chunks(filename: str, content_type: str):
    safe_name = Path(filename).name
    file_path = UPLOAD_DIR / safe_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    pages = load_document_pages(file_path, content_type)
    chunks = split_pages(pages, chunk_size=1000, overlap=200)
    embedded_chunks = embed_chunks(chunks)

    return {
        "filename": safe_name,
        "page_count": len(pages),
        "total_text_length": sum(len(p.text) for p in pages),
        "chunk_count": len(chunks),
        "chunks": [
            {
                "id":c.id,
                "index": c.index,
                "page": c.metadata.get("page"),
                "metadata": c.metadata,
                "length": len(c.text),
                "time": ec.metadata["embedded_at"],
                "preview": c.text[:300],
                "full_text": c.text,
                
                
            }
            for c,ec in zip(chunks,embedded_chunks)
        ],
    }