FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --user -r requirements.txt 

FROM python:3.12-slim AS final

WORKDIR /app

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH

COPY main.py .

EXPOSE 8080

ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
