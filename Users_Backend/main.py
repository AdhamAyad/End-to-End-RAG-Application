# main.py
"""
FastAPI app: /health, /ask
Flow:
 - /ask receives text
 - try Redis cache
 - if miss -> call chunk service (CHUNK_URL)
 - get embeddings from EMBEDDING_ENDPOINT
 - search vector DB (VECTOR_DB_ENDPOINT)
 - call LLM (Vertex AI generateContent) with contexts + question
 - cache (Redis) and return answer
Error handling: collects/errors per stage in response and logs full trace.
Designed to run inside Cloud Run.
"""

import os
import json
import time
import logging
import unicodedata
from functools import wraps
from typing import Optional, List, Any

import requests
import redis
import google.auth
from google.auth.transport.requests import AuthorizedSession
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("user-backend")

# ---------- Config (env vars) ----------
CHUNK_ENDPOINT = os.environ.get("CHUNK_URL")
VECTOR_ENDPOINT = os.environ.get("VECTOR_DB_ENDPOINT")
DEPLOYED_INDEX_ID = os.environ.get("DEPLOYED_INDEX_ID")
REDIS_HOST = os.environ.get("MEMORY_STORE_HOST")
REDIS_PORT = int(os.environ.get("MEMORY_STORE_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))
REDIS_PASSWORD = os.environ.get("MEMORY_STORE_PASSWORD")  # optional
REDIS_CONNECT_TIMEOUT = float(os.environ.get("REDIS_CONNECT_TIMEOUT", 5.0))
REDIS_TTL = int(os.environ.get("REDIS_TTL", 3600))  # seconds to cache answers

EMBEDDING_ENDPOINT = os.environ.get("EMBEDDING_ENDPOINT")

PROJECT_ID = os.environ.get("PROJECT_ID")
REGION = os.environ.get("REGION")
LLM_MODEL_ID = os.environ.get("LLM_MODEL_ID", "gemini-2.0-flash")
# Optionally pass full endpoint directly
LLM_ENDPOINT = os.environ.get("LLM_ENDPOINT") or (
    f"https://{REGION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{REGION}/publishers/google/models/{LLM_MODEL_ID}:generateContent"
)

LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", 0.2))
LLM_MAX_OUTPUT_TOKENS = int(os.environ.get("LLM_MAX_OUTPUT_TOKENS", 1024))

VECTOR_NEIGHBOR_COUNT = int(os.environ.get("VECTOR_NEIGHBOR_COUNT", 10))

MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))
BACKOFF_BASE = float(os.environ.get("BACKOFF_BASE", 0.2))
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", 30))

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
                    wait = backoff_base * (2 ** (attempt - 1))
                    logger.warning("Retry %s/%s for %s after error: %s (sleep %.2fs)", attempt, max_retries, fn._name_, e, wait)
                    time.sleep(wait)
            logger.exception("Function %s failed after %s attempts", fn._name_, max_retries)
            raise last_exc
        return wrapper
    return decorator

# ---------- Google Authorized session ----------
authed_session = None
try:
    credentials, _ = google.auth.default()
    authed_session = AuthorizedSession(credentials)
    logger.info("Authorized session initialized.")
except Exception as e:
    logger.warning("Google auth init failed: %s. Calls to Google endpoints will fail until auth is available.", e)
    authed_session = None

# ---------- Redis client ----------
def create_redis_client():
    if not REDIS_HOST:
        raise ValueError("Missing MEMORY_STORE_HOST")
    pool = redis.ConnectionPool(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD or None,
        socket_connect_timeout=REDIS_CONNECT_TIMEOUT,
        decode_responses=True,
    )
    return redis.Redis(connection_pool=pool)

redis_client = None
try:
    redis_client = create_redis_client()
    # quick ping to detect config problems early
    redis_client.ping()
    logger.info("Connected to Redis at %s:%s db=%s", REDIS_HOST, REDIS_PORT, REDIS_DB)
except Exception as e:
    logger.warning("Redis init failed (will surface on /health and ops): %s", e)
    redis_client = None

@retry_on_exception(MAX_RETRIES, BACKOFF_BASE)
def redis_get(key: str) -> Optional[str]:
    if not redis_client:
        raise RuntimeError("Redis client not initialized")
    return redis_client.get(key)

@retry_on_exception(MAX_RETRIES, BACKOFF_BASE)
def redis_set(key: str, value: str, ttl: int = REDIS_TTL):
    if not redis_client:
        raise RuntimeError("Redis client not initialized")
    if ttl > 0:
        return redis_client.setex(key, ttl, value)
    else:
        return redis_client.set(key, value)

# ---------- Core service calls ----------
@retry_on_exception(MAX_RETRIES, BACKOFF_BASE)
def call_chunk_service(text: str) -> List[str]:
    if not CHUNK_ENDPOINT:
        raise RuntimeError("CHUNK_ENDPOINT not configured")
    url = CHUNK_ENDPOINT.rstrip("/") + "/chunk"
    logger.info("Calling chunk service %s", url)
    resp = requests.post(url, data={"text": text, "chunk_size": 500}, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    # normalize to list[str]
    if isinstance(data, dict) and "chunks" in data and isinstance(data["chunks"], list):
        # each chunk might be dict or str
        out = []
        for c in data["chunks"]:
            if isinstance(c, str):
                out.append(c)
            elif isinstance(c, dict):
                # common key: text or content
                out.append(c.get("text") or c.get("content") or json.dumps(c, ensure_ascii=False))
            else:
                out.append(str(c))
        return out
    elif isinstance(data, list):
        return [c if isinstance(c, str) else (c.get("text") if isinstance(c, dict) and "text" in c else json.dumps(c, ensure_ascii=False)) for c in data]
    elif isinstance(data, dict) and "result" in data:
        return [data["result"]]
    else:
        # fallback: return whole response as single chunk string
        return [json.dumps(data, ensure_ascii=False)]

@retry_on_exception(MAX_RETRIES, BACKOFF_BASE)
def get_embeddings(chunks: List[str]) -> List[List[float]]:
    if not EMBEDDING_ENDPOINT:
        raise RuntimeError("EMBEDDING_ENDPOINT not configured")
    if not authed_session:
        raise RuntimeError("Google auth not available for embeddings call")
    payload = {
        "instances": [
            {"task_type": "RETRIEVAL_DOCUMENT", "title": "document title", "content": c}
            for c in chunks
        ]
    }
    headers = {"Content-Type": "application/json"}
    logger.info("Requesting embeddings for %d chunks", len(chunks))
    resp = authed_session.post(EMBEDDING_ENDPOINT, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    try:
        return [pred["embeddings"]["values"] for pred in data["predictions"]]
    except Exception:
        logger.error("Unexpected embedding response: %s", json.dumps(data, indent=2, ensure_ascii=False))
        raise RuntimeError("Unexpected embedding response format")

@retry_on_exception(MAX_RETRIES, BACKOFF_BASE)
def search_vector_db(embedding: List[float]) -> Any:
    if not VECTOR_ENDPOINT:
        raise RuntimeError("VECTOR_DB_ENDPOINT not configured")
    if not authed_session:
        raise RuntimeError("Google auth not available for vector DB call")
    payload = {
        "deployedIndexId": DEPLOYED_INDEX_ID,
        "queries": [{"datapoint": {"featureVector": embedding}, "neighborCount": VECTOR_NEIGHBOR_COUNT}]
    }
    logger.info("Calling vector DB endpoint")
    resp = authed_session.post(VECTOR_ENDPOINT, json=payload, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()

@retry_on_exception(MAX_RETRIES, BACKOFF_BASE)
def call_llm(prompt: str, contexts: Optional[List[str]] = None) -> Any:
    if not LLM_ENDPOINT:
        raise RuntimeError("LLM_ENDPOINT not configured")
    if not authed_session:
        raise RuntimeError("Google auth not available for LLM call")
    text_input = prompt
    if contexts:
        context_str = "\n\n".join(contexts)
        text_input = f"Context:\n{context_str}\n\nQuestion:\n{prompt}"

    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": text_input}]}
        ],
        "generationConfig": {"temperature": LLM_TEMPERATURE, "maxOutputTokens": LLM_MAX_OUTPUT_TOKENS}
    }
    headers = {"Content-Type": "application/json"}
    logger.info("Calling LLM endpoint: %s", LLM_ENDPOINT)
    resp = authed_session.post(LLM_ENDPOINT, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def parse_llm_response(resp: Any) -> str:
    # try common patterns used by Vertex generateContent
    try:
        if isinstance(resp, dict):
            # pattern: candidates -> content -> parts -> text
            candidates = resp.get("candidates") or resp.get("predictions")
            if candidates and isinstance(candidates, list) and len(candidates) > 0:
                c0 = candidates[0]
                # try content.parts
                content = c0.get("content") if isinstance(c0, dict) else None
                if isinstance(content, dict):
                    parts = content.get("parts")
                    if parts and isinstance(parts, list):
                        texts = []
                        for p in parts:
                            if isinstance(p, str):
                                texts.append(p)
                            elif isinstance(p, dict) and "text" in p:
                                texts.append(p["text"])
                            else:
                                texts.append(json.dumps(p, ensure_ascii=False))
                        return "\n".join(texts)
                # fallback: try candidate fields
                if isinstance(c0, dict):
                    # try nested keys
                    for key in ("output", "message", "text"):
                        if key in c0:
                            val = c0[key]
                            return val if isinstance(val, str) else json.dumps(val, ensure_ascii=False)
                return json.dumps(c0, ensure_ascii=False)
        # fallback: stringify
        return str(resp)
    except Exception as e:
        logger.exception("Failed to parse LLM response: %s", e)
        return json.dumps(resp, ensure_ascii=False)

# ---------- FastAPI app & models ----------
app = FastAPI(title="Redis+Vector+LLM RAG service")

class QuestionRequest(BaseModel):
    question: str

@app.get("/health")
async def health():
    problems = []
    # Redis check
    try:
        if redis_client:
            redis_client.ping()
        else:
            problems.append("redis_client_not_initialized")
    except Exception as e:
        problems.append(f"redis_error: {str(e)}")
    # Google auth check
    if not authed_session:
        problems.append("google_auth_not_initialized")
    status = "ok" if not problems else "degraded"
    return {"status": status, "problems": problems}

@app.post("/ask")
async def ask(req: QuestionRequest):
    q = normalize_text(req.question)
    if not q:
        raise HTTPException(status_code=400, detail="Empty question")

    errors = []
    # 1) Redis read
    cached = None
    try:
        cached = redis_get(q)
    except Exception as e:
        logger.warning("Redis GET error for key=%s: %s", q, e)
        errors.append({"stage": "redis_get", "error": str(e)})

    if cached:
        return {"found": True, "question": q, "answer": cached, "errors": errors}

    # 2) Chunk service
    try:
        chunk_texts = call_chunk_service(q)
        if not chunk_texts:
            raise RuntimeError("Chunk service returned empty")
    except Exception as e:
        logger.exception("Chunking failed")
        errors.append({"stage": "chunk", "error": str(e)})
        raise HTTPException(status_code=503, detail=f"Chunk stage failed: {str(e)}")

    # 3) Embeddings
    try:
        embeddings = get_embeddings(chunk_texts)
        if not embeddings or len(embeddings) == 0:
            raise RuntimeError("No embeddings returned")
    except Exception as e:
        logger.exception("Embeddings failed")
        errors.append({"stage": "embeddings", "error": str(e)})
        raise HTTPException(status_code=503, detail=f"Embeddings stage failed: {str(e)}")

    # 4) Vector search (use first embedding)
    search_resp = None
    try:
        search_resp = search_vector_db(embeddings[0])
    except Exception as e:
        logger.exception("Vector search failed")
        errors.append({"stage": "vector_search", "error": str(e)})
        # We continue without contexts (still can call LLM), but note the error.

    # 5) build contexts list from search response (best-effort)
    contexts: List[str] = []
    try:
        if search_resp:
            # try common response shapes
            nn = search_resp.get("nearestNeighbors") or search_resp.get("nearest_neighbors") or search_resp.get("nearestNeighborsResult") or search_resp.get("results") or search_resp
            # if dict with list under index 0 -> neighbors
            if isinstance(nn, dict) and "neighbors" in nn:
                neighbors = nn.get("neighbors", [])
            elif isinstance(nn, list) and len(nn) > 0 and isinstance(nn[0], dict) and "neighbors" in nn[0]:
                neighbors = nn[0].get("neighbors", [])
            elif isinstance(search_resp, dict):
                # fallback: look for neighbors inside nested fields
                neighbors = []
                # try common nested keys
                for k in ("neighbors", "matches", "results"):
                    v = search_resp.get(k)
                    if v:
                        neighbors = v
                        break
            else:
                neighbors = []

            for n in neighbors:
                # neighbor may be dict with datapoint or datapointId or payload
                if isinstance(n, dict):
                    dp = n.get("datapoint") or n.get("datapointId") or n.get("payload") or n.get("data")
                    if isinstance(dp, dict):
                        text = dp.get("text") or dp.get("content") or dp.get("data") or dp.get("displayName") or json.dumps(dp, ensure_ascii=False)
                        contexts.append(text)
                    elif isinstance(dp, str):
                        contexts.append(dp)
                    else:
                        # maybe neighbor has 'datapointId'
                        contexts.append(str(n.get("datapointId") or n.get("id") or n))
                else:
                    contexts.append(str(n))
    except Exception as e:
        logger.exception("Parsing vector search response failed")
        errors.append({"stage": "parse_vector", "error": str(e)})
        # contexts may be empty

    # 6) Call LLM
    try:
        llm_resp = call_llm(q, contexts if contexts else None)
        answer = parse_llm_response(llm_resp)
    except Exception as e:
        logger.exception("LLM call failed")
        errors.append({"stage": "llm", "error": str(e)})
        raise HTTPException(status_code=503, detail=f"LLM call failed: {str(e)}")

    # 7) Cache the Q/A (best-effort)
    try:
        redis_set(q, answer)
    except Exception as e:
        logger.warning("Redis SET failed for key=%s: %s", q, e)
        errors.append({"stage": "redis_set", "error": str(e)})

    return {"found": False, "question": q, "answer": answer, "contexts_count": len(contexts), "errors": errors}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))