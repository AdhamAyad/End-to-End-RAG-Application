# app_minimal.py
import os, redis, unicodedata, logging, time
from fastapi import FastAPI, HTTPException, Form
from pydantic import BaseModel
from functools import wraps
from typing import Optional
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("redis-fastapi")

# ---------- Config ----------
REDIS_HOST = os.environ.get("MEMORY_STORE_HOST")
REDIS_PORT = int(os.environ.get("MEMORY_STORE_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))
REDIS_CONNECT_TIMEOUT = float(os.environ.get("REDIS_CONNECT_TIMEOUT", 5.0))
CHUNK_ENDPOINT = os.environ.get("CHUNK_URL")  # endpoint للـ chunk function

MAX_RETRIES = 3
BACKOFF_BASE = 0.2

# ---------- Helpers ----------
def normalize_text(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    return unicodedata.normalize("NFC", s).strip()

def retry_on_exception(max_retries=3, backoff_base=0.2):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    time.sleep(backoff_base * (2 ** (attempt - 1)))
            raise last_exc
        return wrapper
    return decorator

# ---------- Redis client ----------
def create_redis_client():
    if not REDIS_HOST:
        raise ValueError("Missing REDIS_HOST")
    pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,
                                socket_connect_timeout=REDIS_CONNECT_TIMEOUT,
                                decode_responses=True)
    return redis.Redis(connection_pool=pool)

redis_client = create_redis_client()

@retry_on_exception(MAX_RETRIES, BACKOFF_BASE)
def redis_get(key: str):
    return redis_client.get(key)

# ---------- FastAPI app ----------
app = FastAPI(title="Redis + Chunk Fallback")

class QuestionRequest(BaseModel):
    question: str

# ---------- Endpoints ----------
@app.get("/health")
async def health():
    try:
        redis_client.ping()
        return {"status": "ok", "message": "Redis reachable"}
    except:
        return {"status": "degraded", "message": "Cannot reach Redis"}

@app.post("/ask")
async def ask(req: QuestionRequest):
    q = normalize_text(req.question)
    # 1️⃣ جرب تجيب من Redis
    val = redis_get(q)
    if val:
        return {"found": True, "question": q, "answer": val}
    
    # 2️⃣ لو مش موجود، كلم الـ chunk function
    if not CHUNK_ENDPOINT:
        raise HTTPException(status_code=500, detail="CHUNK_ENDPOINT not configured")
    
    try:
        resp = requests.post(CHUNK_ENDPOINT, data={"text": q, "chunk_size": 500}, timeout=5)
        resp.raise_for_status()
        chunk_answer = resp.json()
        return {"found": False, "question": q, "chunk_answer": chunk_answer}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Chunk function call failed: {str(e)}")