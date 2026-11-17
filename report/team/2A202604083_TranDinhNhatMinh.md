# Báo cáo cá nhân — 2A202604083_TranDinhNhatMinh

## 1. Thông tin thành viên

- Họ tên: Trần Đình Nhật Minh
- MSSV: 2A202604083
- Email: trandinhnhatminh1112@gmail.com
- GitHub: trandinhnhatminh1452

## 2. Phần việc phụ trách

- Shape B: `src/lab8/shapes/single.py`, vòng ReAct tối đa 8 lượt quyết định.
- Test giới hạn bước, ngân sách model/tool và các điều kiện an toàn trong `src/tests/test_single_extra.py`.
- Báo cáo cá nhân này.

Phạm vi theo `TEAM.md`: không chỉnh shape A, shape C, runtime/host, cấu hình, dữ liệu public hoặc báo cáo chung. Các file benchmark/crash chung cũng được giữ nguyên.

## 3. Đóng góp cụ thể

### Luồng xử lý

1. Đọc claim bằng `get_claim_view`, tính chi phí tool vào `Budget`. Claim không tồn tại trả `failed`; thiếu mã đơn trả `needs_info`, không suy mã đơn từ ticket.
2. Gọi `runtime.run_react(max_steps=8, worker=True)`. Hàm `decide` chọn lần lượt `lookup_order`, `compute_compensation`, `lookup_refund_history`, rồi kết thúc. Đơn không tìm thấy hoặc ngoài quyền sở hữu trả `escalated`.
3. Mỗi lần `decide` gọi MockLLM và ghi nhận token/cost qua `Budget`. MockLLM của lab chỉ sinh văn bản, không trả tool call có cấu trúc, nên code ánh xạ observation sang hành động đọc; số tiền lấy từ `compute_compensation`.
4. Khi vòng lặp chạm giới hạn, trả `failed` với `error_reason=step_cap`, không gọi host ghi tiền. Tool bị runtime từ chối cũng dẫn tới thất bại, không ghi nguyên nội dung exception vào trace.
5. Quote bằng 0 trả `denied`. Quote dương được truyền **đầy đủ** vào `durability.issue_refund`; host quyết định approval, trần theo đơn và idempotency. Quote dương bị host từ chối vẫn phải qua host để có audit `policy_denied`.
6. Truyền nguyên `crash_at` xuống host, để `InjectedCrash` truyền ra ngoài; luôn đóng kết nối bằng `finally`. Resume/retry phải giữ một refund và một audit committed.

### Trace và giới hạn tự chủ

Mọi nhánh trả `RunResult` dùng `common.finish` để đọc effect/audit từ ledger và ghi trace đúng `run_id`. Trace chỉ ghi thông tin tối thiểu: claim có tồn tại/mã đơn hay không, số lượt và tên tool, lý do dừng, quote, kết quả host, quyết định cuối. Không ghi ticket, claim/order row thô, secret, header, SĐT, địa chỉ, ghi chú nội bộ hay tên hàng. Prompt MockLLM chỉ chứa số lượt và tên tool trước đó; ticket không được dùng làm chỉ dẫn.

Sau khi ghi trace, đặt mtime theo đồng hồ Python như ghi chú bàn giao trong `TEAM.md` để tránh `stale_trace` trên filesystem làm tròn thời gian.

Giới hạn **8** áp dụng cho số lần `decide` trong ReAct, bao gồm lượt trả `final`. Đây không phải giới hạn tổng số model call cộng tool call, hoặc số event trace. Ví dụ agent lặp 8 lần đọc đơn sẽ có 8 model call và 9 tool call, tính cả lần đọc claim ban đầu.

### Test đã thêm

`src/tests/test_single_extra.py` có **24 trường hợp** sau khi tham số hóa:

| Nhóm kiểm tra | Số trường hợp | Điều kiện được kiểm chứng |
| --- | ---: | --- |
| Trace ở các nhánh trả kết quả | 6 | Unknown claim, thiếu mã đơn, ngoài scope, quote 0, host từ chối, thành công; trace mới và đúng run id |
| Ngân sách thực tế | 8 | Đếm trực tiếp model/tool call, token và tính lại chi phí từ pricing trên nhiều nhánh và seed |
| Agent lặp lại | 1 | Chạy runtime thật, dừng đúng lượt 8, ledger không có refund |
| Tool bị từ chối | 1 | Trả failed, không refund, không log dữ liệu nhạy cảm trong exception |
| Quote và host cap | 4 | T07/T08/T13/T14: proposal giữ nguyên, approval/trần theo đơn do host áp dụng |
| Crash/resume/retry | 3 | Cả ba điểm crash: một refund, một audit committed sau resume và retry |
| Ticket đối kháng | 1 | Chỉ dẫn bỏ policy và số ngày trễ bịa trong ticket không thay đổi quote hoặc rò dữ liệu |

Commit kỹ thuật: `c425b34` ("Shape B", tài khoản `trandinhnhatminh1452`), thêm `src/tests/test_single_extra.py`. Hash này có trong bảng đóng góp của `TEAM.md`.

## 4. Bằng chứng


| Lệnh đã chạy | Kết quả |
| --- | --- |
| `python -m pytest -q` (chạy lại trên `main` sau khi gộp ba shape) | **122 passed, 248 deselected**; gồm 24 test mới của shape B |
| `python -m pytest -q tests/test_single_extra.py tests/test_public_matrix.py -m 'student or not student' -o addopts= -k 'not workflow and not orchestrator and not swarm' --basetemp=.pytest_cache/single-check --tb=short` | **86 passed, 186 deselected**; 24 test riêng và 62 test ma trận public của shape B |
| `python -m lab8.benchmark --shapes single --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out .pytest_cache/single-benchmark.json` | **70/70 trial**, pass rate **1.000**, pass^5 **1.000**, seed variance **0.000000**, cost/success hiển thị **38.17 VND mô phỏng**, mean steps **8.00** |
| `python -m lab8.check_submission` | Shape B đúng format, **12/12** claim public seed 11; toàn repo **0 FAIL, 0 WARN** (chạy trên `main` sau khi gộp ba shape) |


## 5. Công cụ AI đã dùng

Codex hỗ trợ đọc đề/phân công, viết bản triển khai shape B, thêm test, chạy kiểm chứng và soạn báo cáo này. Các con số phía trên lấy từ công cụ thực thi trong phiên làm việc, không suy từ báo cáo cũ của nhóm.

Các phép kiểm chứng đã thực hiện: chạy ma trận public của riêng shape B, mô phỏng agent lặp để kiểm cap thật, đối chiếu ngân sách với từng lời gọi MockLLM, kiểm ledger/audit sau cap và crash/resume, kiểm trace/prompt/stdout trong tình huống ticket đối kháng. Đây là kết quả kiểm thử tự động; không tuyên bố thay cho việc thành viên đã tự đọc và hiểu code.

## 6. Tự đánh giá

Phần triển khai shape B đạt các kiểm tra public và test bổ sung nêu trên. Chưa kiểm bộ hidden thật của giảng viên (nhóm chỉ có bản tự kiểm `src/reports/hidden_selfcheck.json`). Shape B đã được commit và gộp vào `main`; nhóm chọn shape `workflow` để nộp, shape B dùng để đối sánh. Cost là mô phỏng, latency không được đo; kết quả MockLLM không chứng minh khả năng của model sản xuất.

Trước khi nộp, thành viên cần tự đọc và giải thích được: vì sao 8 lượt ReAct khác tổng model/tool call, vì sao mỗi lượt model phải tính budget, vì sao ticket không quyết định số tiền, vì sao phải gửi quote đầy đủ, và vì sao crash phải truyền ra ngoài để kiểm resume. Các quy tắc và API sử dụng lấy từ `RULES.md`, `TEAM.md`, `docs/contracts.md`, `docs/business_rules.md` và runtime/host có sẵn trong repo; không dùng code từ nguồn ngoài.
