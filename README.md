# AI Service

REST API phân tích cảm xúc văn bản (sentiment analysis) xây dựng bằng **FastAPI**, model **DistilBERT**, database **PostgreSQL**, triển khai bằng **Docker Compose**.

---

## Tính năng

- Phân tích cảm xúc văn bản (POSITIVE / NEGATIVE) kèm confidence score
- Lưu lịch sử kết quả dự đoán vào PostgreSQL
- Tra cứu kết quả theo ID
- Health check endpoint kiểm tra trạng thái service và database
- Validate input tự động bằng Pydantic (HTTP 422 khi sai)
- CORS configurable qua biến môi trường

---

## Yêu cầu

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (bao gồm Docker Compose v2)

Không cần cài Python, PostgreSQL hay bất cứ thứ gì khác trên máy host.

---

## Cấu trúc project

```
ai-service/
├── app/
│   ├── main.py              # Khởi tạo FastAPI app, middleware, health check
│   ├── routers/
│   │   └── api.py           # Định nghĩa endpoints /predict, /result/{id}
│   ├── models/
│   │   ├── db.py            # ORM model (bảng predictions)
│   │   └── schemas.py       # Pydantic schemas cho request / response
│   └── services/
│       ├── core.py          # Load model DistilBERT, hàm predict
│       └── database.py      # SQLAlchemy engine và session
├── .env                     # Biến môi trường (không commit lên git)
├── .dockerignore
├── Dockerfile               # Multi-stage build, non-root user
├── docker-compose.yml       # Orchestration: db + api với healthcheck
└── requirements.txt
```

---

## Cài đặt và chạy

### 1. Tạo file `.env`

File `.env` không được commit lên git — sau khi clone về bạn phải tự tạo tay ở thư mục gốc:

```bash
cp .env.example .env   # hoặc tạo thủ công
```

Nội dung mặc định:

```env
POSTGRES_USER=aiuser
POSTGRES_PASSWORD=aipassword
POSTGRES_DB=aidb
DATABASE_URL=postgresql://aiuser:aipassword@db:5432/aidb
ALLOWED_ORIGINS=http://localhost:3000
```

> Đổi `POSTGRES_PASSWORD` và `ALLOWED_ORIGINS` phù hợp với môi trường của bạn trước khi chạy production.

### 2. Khởi động

```bash
docker compose up
```

Không cần chạy `docker compose build` riêng — Compose tự build image `api` từ `Dockerfile` nếu chưa có.

> **Lưu ý:** Lần đầu chạy sẽ mất vài phút vì Docker cần tải model DistilBERT (~250 MB) từ Hugging Face. Các lần sau nhanh hơn nhờ layer cache.

### 3. Dừng service

```bash
docker compose down
```

---

## API Endpoints

Base URL: `http://localhost:8000`

### `GET /health`

Kiểm tra trạng thái service và kết nối database.

**Response**
```json
{
  "status": "ok",
  "database": "connected"
}
```

---

### `POST /predict`

Phân tích cảm xúc một đoạn văn bản.

**Request body**
```json
{
  "text": "I love this product!"
}
```

| Field | Type   | Ràng buộc      |
|-------|--------|----------------|
| text  | string | bắt buộc, tối đa 500 ký tự |

**Response**
```json
{
  "id": 1,
  "label": "POSITIVE",
  "score": 0.9998
}
```

---

### `GET /result/{prediction_id}`

Lấy lại kết quả dự đoán đã lưu theo ID.

**Response**
```json
{
  "id": 1,
  "input_text": "I love this product!",
  "label": "POSITIVE",
  "score": 0.9998
}
```

Trả về `404` nếu không tìm thấy ID.

---

## Biến môi trường

| Biến               | Mô tả                                         | Ví dụ                                              |
|--------------------|-----------------------------------------------|----------------------------------------------------|
| `POSTGRES_USER`    | Username PostgreSQL                           | `aiuser`                                           |
| `POSTGRES_PASSWORD`| Password PostgreSQL                           | `aipassword`                                       |
| `POSTGRES_DB`      | Tên database                                  | `aidb`                                             |
| `DATABASE_URL`     | Connection string SQLAlchemy                  | `postgresql://aiuser:aipassword@db:5432/aidb`      |
| `ALLOWED_ORIGINS`  | Danh sách CORS origins, phân cách bằng dấu phẩy | `http://localhost:3000,https://yourdomain.com`  |

---

## Model AI

- **Model:** [`distilbert-base-uncased-finetuned-sst-2-english`](https://huggingface.co/distilbert-base-uncased-finetuned-sst-2-english)
- **Task:** Sentiment Analysis (POSITIVE / NEGATIVE)
- **Framework:** Hugging Face Transformers + PyTorch

Model được load vào memory khi container khởi động (startup event). Mọi request `/predict` sau đó đều dùng lại instance đã load, không load lại mỗi lần gọi.

---

## Stack công nghệ

| Thành phần   | Công nghệ                              |
|--------------|----------------------------------------|
| API framework | FastAPI 0.135                         |
| ASGI server  | Uvicorn 0.41                           |
| AI model     | DistilBERT via Hugging Face Transformers 5.2 |
| ORM          | SQLAlchemy 2.0                         |
| Database     | PostgreSQL 16                          |
| Container    | Docker (python:3.11-slim, multi-stage) |
| Orchestration | Docker Compose v2                     |
