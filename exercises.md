# Phiếu phản ánh — Day 12

Họ tên: Trần Nhật Minh — Mã học viên: 2A202602483.

Bản giải thích được soạn với hỗ trợ AI. Người học cần đọc code, chạy lại các lệnh và diễn đạt theo hiểu biết của mình. Những thí nghiệm chưa chạy xong được ghi rõ, không coi là đã quan sát.

### Câu 1 — Fail fast

Khi tạo một service mới trên cloud, có thể quên khai báo AGENT_API_KEY. Nếu mặc định là changeme thì service vẫn public và người khác dùng khóa dễ đoán để gọi API. Trường bắt buộc khiến Pydantic báo lỗi cấu hình khi khởi động; lifespan gọi get_settings() ngay nên không phải đợi request đầu tiên mới phát hiện. Key rỗng cũng bị từ chối.

### Câu 2 — Log cho máy đọc

Hàm log_event tạo JSON một dòng có event, level, timestamp và trường bổ sung. Với ask_completed, có thể lọc các lượt của một user_id và cộng cost_usd hoặc tokens_in/tokens_out theo thời gian. Chuỗi cố định “đã trả lời xong” không chứa các trường để thực hiện hai thao tác này. Dòng thực tế (trích từ evidence/scale-agent-logs.txt):

```json
{"user_id":"verify-299b166e5408","tokens_in":3,"tokens_out":41,"cost_usd":0.00002505,"event":"ask_completed","level":"info","timestamp":"2026-09-28T07:48:02.484247+00:00"}
```

### Câu 3 — Kích thước image

| Bản | Dung lượng đo được |
|---|---|
| Một stage với python:3.11 | 1.7 GB (khoảng 1700 MB, theo docker images) |
| Multi-stage với python:3.11-slim | 271 MB (theo docker images) |

Dockerfile.single dùng base đầy đủ và COPY toàn bộ context; Dockerfile chính dùng slim và chỉ copy app/utils cùng dependency đã cài. Base đầy đủ chứa nhiều công cụ và thư viện hệ điều hành hơn. Multi-stage không tự bảo đảm nhỏ nếu vẫn copy mọi thứ; phần giảm dung lượng còn đến từ slim và giới hạn nội dung runtime. Không dùng số ước lượng thay số đo thật.

### Câu 4 — Thứ tự lệnh trong Dockerfile

Theo thứ tự lệnh hiện tại, sửa app/main.py chỉ làm mất cache từ COPY app trở đi. Layer COPY requirements.txt và RUN pip install trong builder vẫn có thể dùng lại nếu dependency không đổi; COPY utils cũng có thể được BuildKit tái sử dụng tùy đồ thị build. Nếu COPY . . đứng trước pip install, thay đổi source làm mất cache của layer cài dependency phía sau. Đã thêm một comment vào app/main.py, build rồi khôi phục source. evidence/cache-build.txt xác nhận COPY requirements.txt, RUN pip install và COPY --from=builder đều CACHED; COPY app và COPY utils chạy lại.

### Câu 5 — Không chạy bằng root

Lỗ hổng thực thi lệnh trong Python cho kẻ tấn công quyền của tiến trình app. Nếu tiến trình là root trong container, họ có nhiều quyền trên filesystem container hơn; nếu có thêm lỗ hổng kernel/container escape, mount nhạy cảm hoặc cấu hình đặc quyền sai thì có thể ảnh hưởng host. Root trong container không tự động đồng nghĩa root trên host. USER agent giảm quyền ngay ở tiến trình bị khai thác, nhưng không thay thế việc vá lỗi, giới hạn mount/capability và không gắn Docker socket vào app.

### Câu 6 — Cửa sổ trượt

Có thể gửi 20 request trong hai giây qua ranh giới phút: 10 ở 10:00:59 và 10 ở 10:01:00. Fixed window reset bộ đếm lúc đổi phút nên cho qua cả hai nhóm. Sliding window đếm 60 giây gần nhất nên nhóm thứ hai bị chặn. UUID trong member tránh ghi đè các lượt cùng timestamp; WATCH/MULTI tránh hai replica cùng đọc quota còn một và cùng nhận lượt cuối.

### Câu 7 — Rate limit và cost guard

Rate limit giới hạn số lượt trong 60 giây; cost guard kiểm tra USD tích lũy theo user/tháng UTC. Một user chỉ gửi một lượt trong phút nhưng đã tiêu 10.01 USD trên ngân sách 10 USD: rate limit cho qua, cost guard trả 402. Một user mới tiêu 0.01 USD nhưng gửi lượt thứ 11 trong một phút: rate limiter trả 429 dù vẫn còn budget. Bản lab kiểm tra số đã tiêu trước lượt gọi, chưa đặt trước chi phí nên vẫn có thể vượt một lượt hoặc vượt do request đồng thời; hệ thống tính tiền thật cần cơ chế reserve/refund nguyên tử.

### Câu 8 — Health khác readiness

Redis mất kết nối → probe chung báo lỗi ở cả ba container → load balancer có thể ngừng gửi traffic; nếu cùng probe đó được dùng làm liveness bởi orchestrator, sau ngưỡng lỗi các container bị restart → Redis chưa phục hồi nên restart không sửa được gốc lỗi → khi Redis trở lại còn phải đợi app khởi động và probe xanh. Tách riêng giúp /health vẫn 200 và /ready trả 503 trong thời gian Redis lỗi. Đã dừng Redis local và quan sát đúng 200/503; sau khởi động Redis, /ready trở lại 200 (evidence/redis-outage.json). Docker Compose thuần chỉ đánh dấu unhealthy; HEALTHCHECK không tự restart container nếu không có cơ chế giám sát khác.

### Câu 9 — Stateless

Đã bổ sung compose.scale.yml để bỏ publish port trên agent và dùng Nginx ở cổng 8000. Lệnh chạy là docker compose -f docker-compose.yml -f compose.scale.yml up -d --scale agent=3. Với các request tuần tự cùng user, lịch sử quan sát được là 0, 2, 4, 6, 8, 10, 12, 14, 16, 18 cho 10 lượt được nhận; các lượt 11–15 trả 429. Store giới hạn 20 message. Dict riêng ở mỗi process tạo ba lịch sử tách biệt, nên có thể thấy 0, 0, 0, 2, 2… và mất dữ liệu khi restart. Đã chạy ba container thật: evidence/scale-agent-logs.txt có cùng user ở agent-1, agent-2 và agent-3; evidence/scale-verification.json ghi kết quả. Sau thí nghiệm đã trở về một agent.

### Câu 10 — Deploy thực tế

Chưa triển khai Railway/Render vì chưa có tài khoản cloud, người dùng đã chọn local fallback. Vì vậy chưa có lỗi cloud thực tế để mô tả. Vấn đề quan sát được khi triển khai local là tải image Docker Hub rất chậm: nhiều dòng Downloading lặp lại, Docker daemon vẫn trả lời nhưng compose ps chưa có service. Đã kiểm tra log build, tạm dừng image một stage lớn và tải các base image từ public.ecr.aws/docker/library; sau đó cả hai image đã build thành công. Đây là vấn đề tải image local, không phải một lỗi cloud đã được tái hiện.