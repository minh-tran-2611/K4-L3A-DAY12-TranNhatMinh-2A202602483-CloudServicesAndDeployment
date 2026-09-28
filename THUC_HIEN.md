# Các bước thực hiện lab Day 12

Sinh viên: Trần Nhật Minh — mã học viên 2A202602483 (theo tên repository).

Phạm vi: chạy local bằng Docker Compose theo lựa chọn của người dùng; chưa deploy cloud.

Kết quả: CP1–CP4 đạt đủ 70 test (gồm build Docker thật); CP5 đạt 7/8 test local/tài liệu, còn thiếu ảnh chụp, 5 test cloud bỏ qua. `grade.py --no-bonus` trả 94/100 do CP5 bị chặn ở 9/15; đây không phải xác nhận hồ sơ nộp đã đầy đủ. Xem `evidence/grade.txt`.

Đã kiểm chứng ba replica, mất kết nối Redis, và shutdown sạch trong 1,42 giây (exit code 0). Hiện để lại stack một agent + Redis. Image theo `docker images`: 271 MB multi-stage và 1.7 GB single-stage.

## 1. Chuẩn bị

- Kiểm tra Docker Desktop, Docker Compose và Python.
- Tạo `.venv`, cài `requirements.txt`.
- Sinh API key ngẫu nhiên trong `.env`, bật `LOCAL_FALLBACK=true`.
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

## 6. Trước khi nộp

- Đọc `DEPLOYMENT.md` và bằng chứng kiểm thử; bổ sung ảnh chụp thật nếu chưa có.
- Đọc và diễn đạt lại `exercises.md` theo hiểu biết của bản thân; nội dung được soạn với hỗ trợ AI.
- Repository hiện thiếu `DAY12` và chưa đúng phần tên bài. Tên yêu cầu theo mã hiện tại: `K4-L3A-DAY12-TranNhatMinh-2A202602483-CloudServicesAndDeployment`.
- Chưa đổi tên repo từ xa, chưa push và chưa nộp Codelab.
- Bonus CI/CD không nằm trong phạm vi bản local này.
- Không sửa `tests/` hay `grade.py`.

Ảnh còn cần bạn chụp vì công cụ browser/desktop của phiên làm việc không kết nối được: mở `http://localhost:8000/health`, lưu ảnh vào `screenshots/health.png`; chụp stack healthy trong Docker Desktop vào `screenshots/dashboard.png`. Sau đó chạy lại CP5 và commit ảnh bằng `git add screenshots` rồi `git commit -m "CP5: add local deployment screenshots"`.

Khi Docker Hub tải quá chậm, đã tải base image từ Docker Official Images trên ECR Public rồi dùng cache Docker để build; tham khảo [hướng dẫn pull của AWS](https://docs.aws.amazon.com/AmazonECR/latest/public/docker-pull-ecr-image.html). Không thay đổi thiết lập Docker Desktop toàn cục.

Tắt stack nhưng giữ dữ liệu: `docker compose down`. Khởi động lại: `docker compose up -d`.
