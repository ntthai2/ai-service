FROM python:3.11-slim AS builder

WORKDIR /install
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt


FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY app ./app

RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]