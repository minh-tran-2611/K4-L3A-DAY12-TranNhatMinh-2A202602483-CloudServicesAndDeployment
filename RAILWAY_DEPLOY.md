# Deploy lab lên Railway

Trạng thái: đã chọn Railway, chưa tạo deployment cloud. Bản local vẫn hoạt động.

1. Đăng ký/đăng nhập Railway bằng tài khoản GitHub của bạn.
2. Push các commit của bài lab lên repository GitHub.
3. Tạo một project Railway, thêm Redis bằng database template, đặt tên service `Redis`.
4. Thêm service ứng dụng từ GitHub repository của bài lab. Railway build bằng Dockerfile; để trống Start Command để dùng CMD đã kiểm tra trong image.
5. Trong Variables của ứng dụng, khai báo:

| Biến | Giá trị hoặc nguồn |
|---|---|
| `AGENT_API_KEY` | Khóa riêng, nhập trực tiếp trong dashboard; không đưa vào Git |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` — chọn reference tới service Redis |
| `RATE_LIMIT_PER_MINUTE` | `10` |
| `MONTHLY_BUDGET_USD` | `10.0` |
| `LOG_LEVEL` | `INFO` |
| `RAILWAY_DEPLOYMENT_DRAINING_SECONDS` | `30` để request có thời gian hoàn tất trước SIGKILL |

Không dùng địa chỉ Redis localhost trên cloud. PORT do Railway cung cấp.

6. Deploy các thay đổi. `railway.toml` dùng `/ready` để chỉ nhận bản deploy đã kết nối được Redis.
7. Tạo public domain trong phần Networking của service ứng dụng.
8. Kiểm tra `/health`, `/ready`, `/ask` với và không có key.
9. Khi service hoạt động thật: cập nhật URL vào DEPLOYMENT.md; đặt LOCAL_FALLBACK=false và DEPLOY_API_KEY đúng với cloud trong `.env` local; chạy lại CP5.
10. Lưu ảnh dashboard và health trong screenshots/, ghi kết quả thật và commit CP5.

Kiểm tra credit/quota trong tài khoản trước khi deploy; ngân sách MONTHLY_BUDGET_USD chỉ là cơ chế của bài lab, không giới hạn hóa đơn Railway.

Tài liệu: [Docker Compose sang Railway](https://docs.railway.com/guides/docker-compose), [healthcheck](https://docs.railway.com/deployments/healthchecks), [biến môi trường](https://docs.railway.com/variables/reference).
