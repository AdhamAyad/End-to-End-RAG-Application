from fastapi import FastAPI, UploadFile, File, Form
from typing import Optional, List
import pandas as pd
import PyPDF2

app = FastAPI(title="Chunk Function API")

def file_to_text(file: UploadFile) -> str:
    ext = file.filename.split('.')[-1].lower()
    if ext == "txt":
        return file.file.read().decode('utf-8', errors='ignore')
    elif ext == "csv":
        df = pd.read_csv(file.file)
        return df.to_csv(index=False)
    elif ext == "pdf":
        reader = PyPDF2.PdfReader(file.file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    else:
        raise ValueError("Unsupported file type")

def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i+chunk_size]))
    return chunks

@app.post("/chunk")
async def chunk_endpoint(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    chunk_size: Optional[int] = Form(500)
):
    if not file and not text:
        return {"error": "Either file or text must be provided"}
    
    if file:
        try:
            content = file_to_text(file)
        except Exception as e:
            return {"error": str(e)}
    else:
        content = text

    chunks = chunk_text(content, chunk_size)
    return {
        "chunks_count": len(chunks),
        "chunks": chunks
    }