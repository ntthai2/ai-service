# AVOIDANCE_TABLE.md

Tài liệu này chứng minh project đã tránh các lỗi phổ biến khi triển khai FastAPI + Docker Compose trong môi trường production.

Mỗi mục bao gồm:
- Problem — Vấn đề thường gặp
- Solution — Cách xử lý trong project
- Proof — Minh chứng trong repository

---

## Mistake #1 — Using python:latest Base Image

Problem:
`python:latest` kéo theo toàn bộ dev tools không cần thiết, khiến image nặng, build chậm và không ghim được runtime version — dẫn đến hành vi khác nhau giữa các lần build.

Solution:
Dùng `python:3.11-slim` để ghim version và giảm kích thước base image.
Áp dụng multi-stage build: stage `builder` cài dependencies vào `/install`, stage runtime chỉ copy kết quả đã build — không mang theo pip, build tools hay cache vào image cuối.

Proof:
- `Dockerfile`
```
FROM python:3.11-slim AS builder
...
FROM python:3.11-slim
COPY --from=builder /install /usr/local
```

---

## Mistake #2 — Missing .dockerignore

Problem:
Không có `.dockerignore` khiến Docker gửi toàn bộ thư mục vào build context, bao gồm `.git`, `__pycache__`, virtual environment và file `.env` — làm tăng thời gian build và rủi ro lộ secrets.

Solution:
Tạo file `.dockerignore` liệt kê tường minh các đường dẫn cần loại trừ khỏi build context.

Proof:
- `.dockerignore`
```
__pycache__/
*.pyc
.git
.env
venv/
.venv/
node_modules/
data/
```

---

## Mistake #3 — Hardcoded Secrets

Problem:
Hardcode database credentials trong source code gây rủi ro bảo mật khi repository public.

Solution:
Tách toàn bộ secrets ra file `.env` (không commit lên repository).
`docker-compose.yml` đọc biến qua `env_file: .env` và truyền vào container dưới dạng `${VAR}`.
Code đọc bằng `os.getenv()`, không có giá trị nào được hardcode trong source.
File `.env` đã được liệt kê trong `.dockerignore` để không bị copy vào image.

Proof:
- `.env` — chứa tất cả secrets (không commit)
- `docker-compose.yml` — dùng `env_file: .env` và `${POSTGRES_USER}`, `${DATABASE_URL}`...
- `app/services/database.py` và `app/main.py` — `DATABASE_URL = os.getenv("DATABASE_URL")`
- `.dockerignore` — `.env` đã được loại trừ

---

## Mistake #4 — Database Not Ready When API Starts

Problem:
Docker Compose khởi động các service gần như đồng thời. API có thể connect tới DB trước khi PostgreSQL hoàn tất init, gây lỗi `connection refused` và crash container.

Solution:
Cấu hình `healthcheck` trên service `db` dùng `pg_isready` để kiểm tra DB thực sự sẵn sàng nhận connection.
Service `api` dùng `depends_on: condition: service_healthy` để chỉ start sau khi healthcheck pass.

Proof:
- `docker-compose.yml`
```yaml
db:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
    interval: 5s
    timeout: 5s
    retries: 5

api:
  depends_on:
    db:
      condition: service_healthy
```

---

## Mistake #5 — Monolithic main.py

Problem:
Nhét toàn bộ route handler, business logic, database session và schema vào một file `main.py` duy nhất khiến code khó đọc, khó test và không thể mở rộng theo team.

Solution:
Tách project theo chuẩn FastAPI layered architecture — mỗi layer có trách nhiệm riêng biệt:
- `routers/` — định nghĩa endpoints, inject dependencies
- `models/` — schema Pydantic (`schemas.py`) và ORM model (`db.py`)
- `services/` — business logic (`core.py`) và database session (`database.py`)
- `main.py` — chỉ khởi tạo app, đăng ký router và middleware

Proof:
- Cấu trúc repository
```
app/
  main.py
  routers/api.py
  models/schemas.py
  models/db.py
  services/core.py
  services/database.py
```

---

## Mistake #6 — Missing Request Validation

Problem:
Không validate input khiến data sai kiểu hoặc thiếu field đi thẳng vào business logic, gây ra runtime errors và trả về HTTP 500 không rõ nguyên nhân cho client.

Solution:
Dùng Pydantic `BaseModel` để khai báo schema cho cả request lẫn response.
FastAPI tự động parse, validate và trả về HTTP 422 với chi tiết lỗi khi input không hợp lệ — không cần viết thêm logic validate thủ công.
Field `text` được giới hạn `max_length=500` để tránh payload quá lớn.

Proof:
- `app/models/schemas.py`
```python
class PredictRequest(BaseModel):
    text: str = Field(..., max_length=500)

class PredictResponse(BaseModel):
    id: int
    label: str
    score: float
```
- `app/routers/api.py` — `def predict(req: PredictRequest, ...)` khai báo type hint để FastAPI tự apply validation

---

## Mistake #7 — Unsafe CORS Configuration

Problem:
Cấu hình `allow_origins="*"` gây rủi ro bảo mật trong production, cho phép bất kỳ domain nào gọi API.

Solution:
Thêm `CORSMiddleware` vào FastAPI app với danh sách origin cụ thể.
Origin được đọc từ biến môi trường `ALLOWED_ORIGINS` (khai báo trong `.env`), không hardcode.
Chỉ cho phép method `GET` và `POST`, tránh expose các method nguy hiểm.

Proof:
- `app/main.py` — `app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, ...)`
- `.env` — `ALLOWED_ORIGINS=http://localhost:3000`

---

## Mistake #8 — Running Container as Root User

Problem:
Container chạy với quyền root làm tăng bề mặt tấn công và có thể fail security scan (ví dụ Trivy, Snyk).

Solution:
Tạo system group `appuser` và system user `appuser` trong Dockerfile.
Chuyển ownership thư mục `/app` sang user đó rồi dùng `USER appuser` để container không chạy bằng root.

Proof:
- `Dockerfile`
```
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser
```

---

## Summary

Project đã tránh đủ 8 lỗi deployment phổ biến thông qua:
- Docker best practices (slim image, multi-stage build, non-root user)
- Secret management với `.env` file và environment variables
- Healthcheck orchestration đảm bảo DB sẵn sàng trước API
- Structured FastAPI architecture (routers / models / services)
- Input validation với Pydantic models
- CORS configuration giới hạn origin cụ thể