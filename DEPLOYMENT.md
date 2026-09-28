# Thông tin deploy — Checkpoint 5

| Mục | Nội dung |
|---|---|
| Họ và tên | Trần Nhật Minh |
| Mã học viên | 2A202602483 |
| Repo | https://github.com/minh-tran-2611/K4-L3A-TranNhatMinh-2A202602483-Cloud-Service-And-Deployment |
| Local URL | http://localhost:8000 |
| Public URL | Chưa có; dùng LOCAL_FALLBACK=true |
| Platform | Docker Desktop + Docker Compose tại máy; chưa triển khai Railway / Render |
| Ngày thực hiện | 2026-09-28 |

## Lý do dùng phương án dự phòng

Người dùng chưa có tài khoản cloud và chọn chạy local trước. Không có URL HTTPS công khai. CP5 bị giới hạn tối đa 9/15 điểm theo quy định lab.

## Biến môi trường

| Biến | Nguồn |
|---|---|
| `PORT` | Compose đặt cổng nội bộ 8000 |
| `AGENT_API_KEY` | Khóa ngẫu nhiên trong `.env` được Git bỏ qua; Compose truyền lúc chạy |
| `REDIS_URL` | Compose trỏ tới service redis; script trên host dùng localhost |
| `RATE_LIMIT_PER_MINUTE` | `.env`, 10 request/phút |
| `MONTHLY_BUDGET_USD` | `.env`, 10 USD/user/tháng |
| `LOG_LEVEL` | `.env`, INFO |
| `LOCAL_FALLBACK` | `.env`, true |
| `DEPLOY_API_KEY` | `.env`, cùng key của service local |

## Kiểm tra

```powershell
docker compose up -d --build
docker compose ps
curl.exe -i http://localhost:8000/health
curl.exe -i http://localhost:8000/ready
.venv\Scripts\python scripts/verify_local.py
.venv\Scripts\python -m pytest tests/test_cp5.py -v
```

Script kiểm tra không in key và lưu kết quả tại `evidence/local-verification.json` sau khi chạy thành công. Kết quả chạy thật:

- `/health`: 200, status ok; `/ready`: 200, Redis true.
- `/ask` thiếu key: 401; user đã vượt budget: 402.
- 15 lượt liên tiếp: 10 lần 200, sau đó 5 lần 429.
- `history_length`: 0, 2, 4, 6, 8, 10, 12, 14, 16, 18.
- 3 replica qua Nginx: cùng kết quả; log chứng minh cả ba cùng phục vụ.
- Khi dừng Redis: health 200, ready 503; khởi động lại: ready 200.
- Docker runtime user: uid=999(agent), gid=999(agent).
- `docker images`: multi-stage 271 MB; single-stage 1.7 GB.
- CP1–CP5: 77 passed, 1 failed (thiếu screenshot), 5 skipped (cloud).
- `grade.py --no-bonus`: 94/100; CP5 bị giới hạn 9/15. Ảnh vẫn bắt buộc, điểm tự động không chứng minh đã đủ hồ sơ.
- Shutdown thật: 1,42 giây, exit code 0, có log service_stopped.

Hiện để lại một agent và một Redis đang chạy local. Bộ test và grade.py giữ nguyên. Điểm tự động chưa thay thế việc giảng viên kiểm tra ảnh và nội dung phản ánh.

## Minh chứng

Ảnh cần bổ sung: `screenshots/health.png` từ trình duyệt mở `/health`, và `screenshots/dashboard.png` từ Docker Desktop hiển thị stack đang chạy. Công cụ điều khiển trình duyệt báo `Unable to load browser request-header policy`; công cụ desktop báo `Computer Use native pipe is unavailable`. Không tạo ảnh giả để thay bằng chứng chạy thật.
