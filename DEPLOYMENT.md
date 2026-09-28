# Thông tin deploy — Checkpoint 5

| Mục | Nội dung |
|---|---|
| Họ và tên | Trần Nhật Minh |
| Mã học viên | 2A202602483 |
| Repo | https://github.com/minh-tran-2611/K4-L3A-DAY12-TranNhatMinh-2A202602483-CloudServicesAndDeployment |
| Public URL | https://app-production-b8e1.up.railway.app |
| Platform | Railway (project `perfect-passion`, environment `production`, service `app` + `Redis`) |
| Build | Dockerfile multi-stage, cấu hình trong `railway.toml`; healthcheck `/ready` |
| Local URL | http://localhost:8000 (Docker Compose, dùng khi phát triển) |
| Ngày thực hiện | 2026-09-28 |

## Cách deploy

1. Tạo project Railway và thêm Redis từ database template (service tên `Redis`).
2. `railway link` thư mục repo vào project, `railway add --service app` tạo service ứng dụng.
3. Khai báo biến môi trường cho service `app` (bảng dưới), không đưa giá trị vào Git.
4. `railway up --ci --service app`: Railway build `Dockerfile`, chạy CMD của image và chỉ chuyển traffic khi `/ready` trả 200.
5. `railway domain --service app` sinh domain HTTPS công khai.
6. GitHub Actions (`.github/workflows/ci.yml`) đã có job test, build và deploy phụ thuộc hai job trước. Hiện Railway yêu cầu xác minh tài khoản trước khi tạo project token, nên chưa có secret `RAILWAY_TOKEN`; deploy tự động đang bị bỏ qua. Cần hoàn tất bước này trước khi coi bonus CI/CD đã hoàn chỉnh.

## Biến môi trường trên Railway

| Biến | Nguồn |
|---|---|
| `PORT` | Railway tự cấp (log: Uvicorn chạy trên 8080); app đọc `$PORT`, không cố định |
| `AGENT_API_KEY` | Khóa ngẫu nhiên sinh bằng `secrets.token_urlsafe`, chỉ lưu trong Railway Variables và `.env` local |
| `REDIS_URL` | Reference `${{Redis.REDIS_URL}}` → `redis.railway.internal:6379` (mạng private) |
| `RATE_LIMIT_PER_MINUTE` | `10` |
| `MONTHLY_BUDGET_USD` | `10.0` |
| `LOG_LEVEL` | `INFO` |
| `RAILWAY_DEPLOYMENT_DRAINING_SECONDS` | `30`, cho request đang chạy hoàn tất trước SIGKILL |

Ở máy local, `.env` đặt `LOCAL_FALLBACK=false` và `DEPLOY_API_KEY` bằng khóa của bản cloud để `tests/test_cp5.py` gọi thử `/ask`.

## Kiểm tra bản cloud

```powershell
curl.exe -i https://app-production-b8e1.up.railway.app/health
curl.exe -i https://app-production-b8e1.up.railway.app/ready
curl.exe -i -X POST https://app-production-b8e1.up.railway.app/ask -H "Content-Type: application/json" -d '{\"question\":\"hi\"}'
curl.exe -i -X POST https://app-production-b8e1.up.railway.app/ask -H "Content-Type: application/json" -H "X-API-Key: $env:DEPLOY_API_KEY" -H "X-User-Id: demo" -d '{\"question\":\"Deploy la gi?\"}'
.venv\Scripts\python -m pytest tests/test_cp5.py -v
```

Kết quả chạy thật ngày 2026-09-28:

- `/health`: 200 `{"status":"ok"}`; `/ready`: 200 `{"status":"ready","redis":true}`.
- `/ask` không có key: 401; có key đúng: 200, trả `answer`, `cost_usd`, `tokens`.
- 12 request liên tiếp cùng user: 10 lần 200, sau đó 429 (rate limit dùng Redis trên cloud).
- Runtime log: `event="service_started"`, Uvicorn lắng nghe `0.0.0.0:8080` theo `PORT` của Railway.

## Kiểm tra bản local (trước khi deploy)

- `/health` 200, `/ready` 200; `/ask` thiếu key 401; vượt budget 402; 15 lượt: 10 lần 200 rồi 5 lần 429.
- `history_length` tăng 0, 2, 4, … 18 qua các lượt hỏi.
- 3 replica qua Nginx cùng phục vụ; dừng Redis: health 200, ready 503; bật lại: ready 200.
- Container chạy uid 999 (non-root); image multi-stage 271 MB so với single-stage 1,7 GB.
- Shutdown: 1,42 giây, exit code 0, có log `service_stopped`.

## Minh chứng

- `screenshots/dashboard.png`: dashboard Railway, service `app` và `Redis` đang Active.
- `evidence/health.txt`: nguyên output `curl.exe -i` gọi HTTPS `/health`, có thời gian thu thập. Chrome hiện báo `ERR_BLOCKED_BY_CLIENT` khi mở endpoint trực tiếp; curl và test cloud vẫn thành công.

## Output curl được lưu lại

Xem [bản ghi HTTP đầy đủ](evidence/health.txt). Body trả về:

```json
{"status":"ok","service":"day12-agent","version":"1.0.0"}
```

Kiểm tra bắt buộc mới nhất: 79 passed, 4 skipped (chỉ các test local fallback); không có test bắt buộc thất bại.
