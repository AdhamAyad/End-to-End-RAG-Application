import os, redis, unicodedata, logging, time, json, requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from functools import wraps
from typing import Optional
import google.auth
from google.auth.transport.requests import AuthorizedSession, Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag-backend")

# ---------- Config ----------
REDIS_HOST = os.environ.get("MEMORY_STORE_HOST")
REDIS_PORT = int(os.environ.get("MEMORY_STORE_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))
REDIS_CONNECT_TIMEOUT = float(os.environ.get("REDIS_CONNECT_TIMEOUT", 5.0))

CHUNK_ENDPOINT = os.environ.get("CHUNK_URL")
VECTOR_ENDPOINT = os.environ.get("VECTOR_DB_ENDPOINT")
EMBEDDING_ENDPOINT = os.environ.get("EMBEDDING_ENDPOINT")

PROJECT_ID = os.environ.get("PROJECT_ID")
REGION = os.environ.get("REGION", "us-east1")
LLM_MODEL_ID = os.environ.get("LLM_MODEL_ID", "gemini-2.0-flash")

MAX_RETRIES = 3
BACKOFF_BASE = 0.2

# Initialize credentials
creds, _ = google.auth.default()
authed_session = AuthorizedSession(creds)

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
                    logger.warning(f"Attempt {attempt} failed: {e}")
                    time.sleep(backoff_base * (2 ** (attempt - 1)))
            logger.error(f"All {max_retries} attempts failed: {last_exc}")
            raise last_exc
        return wrapper
    return decorator

def create_redis_client():
    if not REDIS_HOST:
        raise ValueError("Missing REDIS_HOST")
    pool = redis.ConnectionPool(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        socket_connect_timeout=REDIS_CONNECT_TIMEOUT,
        decode_responses=True
    )
    return redis.Redis(connection_pool=pool)

redis_client = create_redis_client()

@retry_on_exception(MAX_RETRIES, BACKOFF_BASE)
def redis_get(key: str):
    return redis_client.get(key)

def redis_set(key: str, value: str, expire: int = 86400):
    redis_client.set(key, value, ex=expire)

@retry_on_exception(MAX_RETRIES, BACKOFF_BASE)
def get_embeddings(chunks):
    if not EMBEDDING_ENDPOINT:
        raise RuntimeError("EMBEDDING_ENDPOINT not configured")
    
    payload = {
        "instances": [
            {"task_type": "RETRIEVAL_DOCUMENT", "title": "document title", "content": c}
            for c in chunks
        ]
    }
    headers = {"Content-Type": "application/json"}
    resp = authed_session.post(EMBEDDING_ENDPOINT, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    
    try:
        return [pred["embeddings"]["values"] for pred in data["predictions"]]
    except KeyError:
        logger.error(f"Unexpected embedding response: {json.dumps(data, indent=2)}")
        raise RuntimeError("Unexpected embedding response format")

@retry_on_exception(MAX_RETRIES, BACKOFF_BASE)
def search_vector_db(embedding):
    if not VECTOR_ENDPOINT:
        raise RuntimeError("VECTOR_DB_ENDPOINT not configured")
    
    payload = {
        "deployedIndexId": os.environ.get("DEPLOYED_INDEX_ID"),
        "queries": [{"datapoint": {"featureVector": embedding}, "neighborCount": 10}]
    }
    resp = authed_session.post(VECTOR_ENDPOINT, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()

# ---------- LLM (المشكلة الاساسية) ----------
@retry_on_exception(MAX_RETRIES, BACKOFF_BASE)
def generate_llm_response(prompt: str):
    """
    LLM function - تم التصحيح لمطابقة الكوماند تماماً
    """
    try:
        # تأكد من صحة التوكن
        if not creds.valid:
            creds.refresh(Request())
        
        access_token = creds.token
        logger.info(f"Using access token for LLM request")

        # بناء endpoint بنفس طريقة الكوماند
        endpoint = f"https://{REGION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{REGION}/publishers/google/models/{LLM_MODEL_ID}:generateContent"
        logger.info(f"LLM endpoint: {endpoint}")

        # payload مطابق للكوماند تماماً
        payload = {
            "contents": [{
                "role": "user",
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024
            }
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        logger.info(f"Sending LLM request with prompt: {prompt[:100]}...")
        
        # إرسال الطلب بنفس طريقة الكوماند
        response = requests.post(
            endpoint, 
            headers=headers, 
            json=payload, 
            timeout=60  # زيادة timeout
        )
        
        logger.info(f"LLM response status: {response.status_code}")
        
        if response.status_code != 200:
            error_msg = f"LLM API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # معالجة الresponse بنفس طريقة الكوماند
        response_data = response.json()
        logger.info("LLM response received successfully")
        
        # استخراج النص بنفس الهيكل
        return response_data["candidates"][0]["content"]["parts"][0]["text"]
        
    except Exception as e:
        logger.error(f"LLM failed: {str(e)}")
        raise RuntimeError(f"LLM generation failed: {str(e)}")

# ---------- FastAPI ----------
app = FastAPI(title="RAG Backend")

class QuestionRequest(BaseModel):
    question: str

@app.get("/health")
async def health():
    try:
        redis_client.ping()
        # اختبار بسيط للLLM
        test_result = generate_llm_response("test")
        return {"status": "ok", "redis": "connected", "llm": "connected"}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}

@app.get("/test-llm")
async def test_llm():
    """Endpoint لاختبار الLLM فقط"""
    try:
        result = generate_llm_response("Hello, are you working?")
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/ask-simple")
async def ask_simple(req: QuestionRequest):
    try:
        logger.info(f"ask-simple request: {req.question}")
        answer = generate_llm_response(req.question)
        return {
            "source": "llm", 
            "question": req.question, 
            "answer": answer
        }
    except Exception as e:
        logger.error(f"ask-simple error: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))

@app.post("/ask")
async def ask(req: QuestionRequest):
    try:
        q = normalize_text(req.question)
        logger.info(f"ask request: {q}")
        
        # 1. Check cache
        cached = redis_get(q)
        if cached:
            logger.info("Cache hit")
            return {"source": "cache", "answer": cached}

        # 2. Chunking
        logger.info("Starting chunking")
        r = authed_session.post(
            f"{CHUNK_ENDPOINT}/chunk", 
            data={"text": q, "chunk_size": 500}, 
            timeout=30
        )
        r.raise_for_status()
        chunks = r.json().get("chunks", [])
        logger.info(f"Got {len(chunks)} chunks")

        # 3. Embeddings
        logger.info("Getting embeddings")
        embed_resp = get_embeddings(chunks)
        embeddings_flat = [val for sublist in embed_resp for val in sublist]
        logger.info(f"Got embeddings of length {len(embeddings_flat)}")

        # 4. Vector search
        logger.info("Searching vector DB")
        results = search_vector_db(embeddings_flat)
        context = " ".join([doc.get("text", "") for doc in results.get("matches", [])])
        logger.info(f"Got context: {context[:100]}...")

        # 5. LLM generation
        logger.info("Generating LLM response")
        prompt = f"Question: {q}\nContext: {context}\nAnswer:"
        answer = generate_llm_response(prompt)
        logger.info("LLM response generated successfully")

        # 6. Cache result
        redis_set(q, answer)
        return {
            "source": "llm", 
            "question": q, 
            "answer": answer
        }
        
    except Exception as e:
        logger.error(f"Ask error: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))