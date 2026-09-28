# Các bước thực hiện lab Day 12

Sinh viên: Trần Nhật Minh — mã học viên 2A202602483 (theo tên repository).

Phạm vi hiện tại: đã triển khai app và Redis trên Railway, đồng thời có Docker Compose để kiểm tra local. Public URL: https://app-production-b8e1.up.railway.app.

Kiểm tra ngày 2026-09-28: CP1–CP5 đạt 79 test, gồm build Docker thật và `/ask` với API key trên cloud. Bốn test local fallback được bỏ qua đúng điều kiện vì đang dùng cloud. Kết quả chấm mới nhất nằm trong `evidence/grade.txt`; điểm tự động không thay thế đánh giá nội dung phản ánh của giảng viên.

Đã kiểm chứng ba replica, mất kết nối Redis, và shutdown sạch trong 1,42 giây (exit code 0). Image theo `docker images`: 271 MB multi-stage và 1.7 GB single-stage.

## 1. Chuẩn bị

- Kiểm tra Docker Desktop, Docker Compose và Python.
- Tạo `.venv`, cài `requirements.txt`.
- Sinh API key ngẫu nhiên trong `.env`; sau khi deploy cloud, đặt `LOCAL_FALLBACK=false` và cấu hình `DEPLOY_API_KEY` cục bộ.
- Kiểm tra `.env` được Git bỏ qua. Không đưa secret vào tài liệu hoặc image.

## 2. Hoàn thiện CP1–CP4

- `app/config.py`: đọc 6 biến môi trường; key bắt buộc; kiểm tra cổng và hạn mức hợp lệ.
- `app/logging_utils.py`: log JSON một dòng với thời gian UTC.
- `app/auth.py`: kiểm tra key bằng `secrets.compare_digest`, trả 401 nếu thiếu/sai.
- `app/rate_limiter.py`: cửa sổ trượt 60 giây, member UUID, TTL; dùng WATCH/MULTI để tránh vượt quota khi nhiều replica nhận request đồng thời.
- `app/cost_guard.py`: cộng chi phí theo user/tháng UTC, đặt TTL, trả 402 khi vượt budget.
- `app/store.py`: Redis List giữ 20 message mới nhất, TTL 7 ngày, timeout kết nối.
- `app/lifecycle.py`: xử lý SIGTERM/SIGINT và chuyển tiếp handler cũ.
- `app/main.py`: `/health`, `/ready`, `/ask`; kiểm tra auth, rate limit và budget trước mock LLM.

Cost guard làm theo giao diện đề bài: kiểm tra số đã tiêu rồi ghi chi phí sau lượt gọi. Đây chưa phải cơ chế đặt trước ngân sách cho các request đồng thời. `X-User-Id` cũng do client khai báo; hệ thống thực tế cần gắn user với danh tính đã xác thực.

## 3. Docker

- Dockerfile hai stage trên `python:3.11-slim`, cài dependency trước khi copy code.
- Runtime chạy user `agent`, có healthcheck, đọc `$PORT`, dùng `exec` để chuyển signal tới Uvicorn.
- Compose chờ Redis healthy; Redis có volume; các cổng chỉ bind localhost.
- `.dockerignore` loại `.env`, Git, môi trường ảo và cache.
- `Dockerfile.single` giữ cấu hình một stage để thực nghiệm dung lượng.

## 4. Chạy và kiểm tra

```powershell
docker compose up -d --build
docker compose ps
.venv\Scripts\python scripts/verify_local.py
.venv\Scripts\python -m pytest tests/test_cp1.py tests/test_cp2.py tests/test_cp3.py tests/test_cp4.py tests/test_cp5.py -v
.venv\Scripts\python grade.py --no-bonus
```

`scripts/verify_local.py` kiểm tra 200/401/402/429 và lịch sử tăng 0, 2, …, 18; lưu kết quả thật vào `evidence/local-verification.json`. Script mặc định kiểm tra cấu hình lab 10 request/phút, budget 10 USD.

## 5. Thử scale

```powershell
docker compose -f docker-compose.yml -f compose.scale.yml up -d --scale agent=3
.venv\Scripts\python scripts/verify_local.py
docker compose -f docker-compose.yml -f compose.scale.yml logs agent
```

File override bỏ cổng cố định của agent để tránh trùng cổng; Nginx nhận cổng 8000 và chia request cho các replica. Cần Compose hỗ trợ `!override` (bản đã kiểm tra là v5.5.1).

Trở lại một agent:

```powershell
docker compose -f docker-compose.yml -f compose.scale.yml stop nginx
docker compose up -d --scale agent=1 --remove-orphans
```

## 6. Cloud, CI và hồ sơ nộp

- Railway project `perfect-passion`, environment `production`: app và Redis đều Online. Ảnh thật: `screenshots/dashboard.png`.
- Repo GitHub đã được đổi đúng mẫu: `K4-L3A-DAY12-TranNhatMinh-2A202602483-CloudServicesAndDeployment`, chế độ public. `origin` dùng URL mới.
- `DEPLOYMENT.md` và Câu 10 trong `exercises.md` đã cập nhật kết quả cloud. Bản ghi HTTP thật từ curl: `evidence/health.txt`.
- Workflow `.github/workflows/ci.yml` kiểm tra code, build image và chỉ chạy job deploy sau khi hai job đó thành công.
- Chưa tạo được project token: Railway yêu cầu xác minh tài khoản tại Project Settings → Tokens. Khi được phép tạo, lưu token vào GitHub Actions secret `RAILWAY_TOKEN`; không ghi vào repo hoặc chat. Khi chưa có secret, workflow bỏ qua deploy, nên badge xanh chỉ chứng minh test/build, chưa chứng minh CD hoàn chỉnh.
- Đọc và diễn đạt phần phản ánh theo hiểu biết bản thân; bài có sử dụng AI hỗ trợ. Không sửa `tests/` hay `grade.py`.
- Bước nộp link repository trên Codelab chưa được xác nhận.

Khi Docker Hub tải quá chậm, đã tải base image từ Docker Official Images trên ECR Public rồi dùng cache Docker để build; tham khảo [hướng dẫn pull của AWS](https://docs.aws.amazon.com/AmazonECR/latest/public/docker-pull-ecr-image.html). Không thay đổi thiết lập Docker Desktop toàn cục.

Tắt stack nhưng giữ dữ liệu: `docker compose down`. Khởi động lại: `docker compose up -d`.
