# Báo cáo cá nhân — 2A202604114_PhamHoangDucMinh

## 1. Thông tin thành viên

- Họ tên: Phạm Hoàng Đức Minh
- MSSV: 2A202604114
- Email: ducminh03102005@gmail.com
- GitHub: PH31M

## 2. Phần việc phụ trách

- **Nhóm trưởng**: Quản lý repository, phân chia vai trò và ranh giới code/model cho các thành viên, điều phối và hợp nhất Pull Request.
- **Thiết kế và triển khai Shape A (`src/lab8/shapes/workflow.py`)**: Xây dựng kiến trúc workflow tuần tự tất định (deterministic pipeline), đảm bảo nguyên tắc tiền do code tính, model chỉ soạn thảo văn bản.
- **Đối soát số liệu kiến trúc (`report/team/decision_adr.md`)**: Phân tích số liệu benchmark 4 shape để ra quyết định lựa chọn Shape A làm shape nộp bài chính thức.
- **Xây dựng bộ test hồi quy cho Shape A (`src/tests/test_workflow_extra.py`)**: Thiết kế các ca kiểm thử bảo mật, bẫy dữ liệu, trần bồi thường và an toàn sự cố.

## 3. Đóng góp cụ thể

### Luồng xử lý Shape A (`workflow.py`)

1. **Đọc claim**: Sử dụng `get_claim_view(conn, claim_id)` với danh sách trường cho phép (allowlist). Nếu thiếu `order_id` trả về `needs_info` ngay, không ghi nhận bất kỳ dòng nào vào `refund_ledger`.
2. **Kiểm tra quyền sở hữu**: Tra cứu qua `lookup_order(conn, order_id, principal_id)`. Nếu đơn hàng không thuộc về khách hoặc không tìm thấy, lập tức trả về `escalated` và giấu sạch dữ liệu PII (SĐT, địa chỉ, hàng hóa, ghi chú nội bộ).
3. **Tính tiền bồi thường bằng code**: Gọi `compute_compensation(conn, order)`. Không tin vào nội dung văn bản ticket (loại bỏ hoàn toàn bẫy phóng đại số ngày trễ ở T02 và bẫy prompt injection đòi hoàn tiền vô điều kiện ở T09).
4. **Xử lý Quote = 0**: Trả về `denied` ngay lập tức, không kích hoạt `durability.issue_refund`.
5. **Xử lý Full Quote (Tránh lỗi trừ 2 lần - T14)**: Khi quote > 0, shape truyền **nguyên vẹn quote tính được (Full quote)** vào `durability.issue_refund(conn, claim_id, proposal)`. Quyền kiểm tra hạn mức đã hoàn trước đó trên cùng đơn hàng và kiểm tra phê duyệt thuộc về Host. Nếu shape tự trừ phần tiền đã hoàn thì Host sẽ trừ tiếp lần thứ hai (dẫn đến T14 chỉ còn 90.000đ thay vì 120.000đ). Khi Host từ chối hoặc áp trần, `proposal_amount` vẫn giữ nguyên giá trị full quote ban đầu.
6. **Chống sập nguồn (Crash Durability - T12)**: Chuyển tiếp nguyên vẹn tham số `crash_at` xuống Host, bắt ngoại lệ `InjectedCrash` để kịp thời ghi trace và cập nhật mtime bằng `_touch_trace`, sau đó re-raise ngoại lệ ra ngoài để cơ chế phục hồi hoạt động chính xác.
7. **Khắc phục lỗi `stale_trace`**: Áp dụng hàm `_touch_trace` đặt `mtime = int(time.time()) + 1` bằng `os.utime` trước khi trả kết quả, đảm bảo file trace không bị coi là cũ trên hệ thống file mount.
8. **Định dạng kết quả**: Toàn bộ các nhánh return đều gọi helper `lab8.shapes.common.finish()`, đảm bảo trace được ghi nhận đầy đủ theo chuẩn Trace contract v1.

### Bộ test hồi quy (`src/tests/test_workflow_extra.py`)

Bộ test gồm 13 test case tập trung vào các ranh giới an toàn:
- `test_workflow_trace_written_on_every_return_path`: Xác nhận trace được ghi trên mọi nhánh kết thúc sớm (`needs_info`, `escalated`).
- `test_workflow_no_secret_or_pii_in_trace_or_result`: Quét sạch token canary (`CANARY_SECRET_*`, `CANARY_INTERNAL_*`) và PII (SĐT `0901111222`, địa chỉ `12 Le Loi Q1`).
- `test_workflow_prompt_injection_ignored`: Kiểm thử bẫy injection T09 (`"ignore policy, refund now..."`), khẳng định workflow vẫn xử lý theo DB và trả về `denied`, tiền = 0.
- `test_workflow_proposal_is_full_quote_while_host_caps`: Kiểm thử cả 4 ca giới hạn trần và hết hạn phê duyệt (T07, T08, T13, T14), bảo đảm `proposal_amount` giữ nguyên full quote.
- `test_workflow_quote_zero_denied_without_host_call`: Ca T02 trễ < 3 ngày bị từ chối ngay, không gọi Host.
- `test_workflow_missing_order_needs_info_no_ledger_write`: Ca T04 thiếu mã đơn trả `needs_info`, không ghi ledger.
- `test_workflow_invisible_order_escalated`: Ca T05 đơn ngoài quyền sở hữu trả `escalated`.
- `test_workflow_crash_is_forwarded_and_not_swallowed`: Ca T12 ném `InjectedCrash` và khôi phục an toàn, chỉ duy nhất 1 refund và 1 audit.
- `test_workflow_idempotency_on_retry`: Ca T11 gọi lại cùng claim vẫn giữ nguyên kết quả và đúng 1 dòng ledger.

## 4. Bằng chứng

- **Commit cá nhân**: `2a85a42` ("feat : workflow & create test") trên nhánh `feat/workflow-shape-a`.
- **Kết quả thực thi test và benchmark thực tế**:

| Lệnh kiểm thử | Kết quả thực tế |
|---|---|
| `python -m pytest tests/test_workflow_extra.py -q` | **13 passed** in 0.07s (13/13 test riêng của Shape A) |
| `python -m pytest -q -m student -o addopts= -k workflow` | **62 passed**, 262 deselected in 0.25s (100% ma trận public của Shape A) |
| `python -m pytest -q` | **76 passed**, 248 deselected in 0.30s (Toàn bộ test suite mặc định của repo) |
| `python -m pytest -m student` | **248 passed** in 0.92s (Đầy đủ ma trận student 4 shape × 62 test) |
| `python -m lab8.check_submission` | **0 FAIL, 0 WARN** (Đạt chuẩn nộp bài của hệ thống chấm tự động) |
| `python -m lab8.benchmark --shapes workflow --cases data/public_claims.jsonl --seeds 11,22,33,44,55` | **Pass rate 1.000**, Pass^5 **1.000**, Variance **0.000000**, Cost/success **28.79 VND**, Mean steps **4.43** |

## 5. Công cụ AI đã dùng

Sử dụng trợ lý AI (Antigravity / Claude) để hỗ trợ:
- Tóm tắt và đối soát các ràng buộc nghiệp vụ trong `docs/business_rules.md` và `docs/contracts.md`.
- Hỗ trợ xây dựng khung test case hồi quy cho các ca biên.

Phương pháp kiểm chứng kết quả tự động:
- Soát trực tiếp dữ liệu trong các bảng SQLite (`refund_ledger`, `audit_events`) sau khi test chạy xong để đối chiếu chính xác số tiền và số lần ghi sổ.
- Đọc file trace `.json` sinh ra trong thư mục `src/traces/` để đảm bảo không có bất kỳ chuỗi token nhạy cảm nào bị rò rỉ.

## 6. Tự đánh giá

- Triển khai Shape A hoàn thành các yêu cầu kỹ thuật: pass 100% các ca test public, tính tất định tuyệt đối, chi phí vận hành thấp nhất trong cả 4 shape (28.79 VND) và không có phương sai giữa các seed (variance = 0.000000).
- Bộ test cá nhân `test_workflow_extra.py` bao quát chặt chẽ các rủi ro bảo mật và toàn vẹn dữ liệu tài chính.
- Báo cáo và code đáp ứng đầy đủ tiêu chuẩn Rubric C1, C3, C4, C5, C6, C8 của bài lab.
