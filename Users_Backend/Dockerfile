FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --user -r requirements.txt 

FROM python:3.12-slim AS final

WORKDIR /app

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH

ARG CHUNK_URL
ENV CHUNK_URL=${CHUNK_URL}

ARG VECTOR_DB_ENDPOINT
ENV VECTOR_DB_ENDPOINT=${VECTOR_DB_ENDPOINT}

ARG MEMORY_STORE_HOST
ENV MEMORY_STORE_HOST=${MEMORY_STORE_HOST}

ARG MEMORY_STORE_PORT
ENV MEMORY_STORE_PORT=${MEMORY_STORE_PORT}

COPY main.py .

EXPOSE 8080

ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]