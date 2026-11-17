# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: fe4b2b2
- Run id dẫn chứng: R-workflow-C-001-s11 (bộ trace của benchmark trong `src/reports/benchmark.json`, 280 trial)
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000–1.000 / 0.000000
- Cost per success (mô phỏng, VND): 28.79
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 0 / 0 (public: 0 trial lộ `CANARY_SECRET_*`, 0 refund khi thiếu approval hợp lệ; `hidden_grade.json` do giảng viên tạo)

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Số đo lấy từ `src/reports/benchmark.json` (4 shape × 14 claim public × seed `11,22,33,44,55` = 280 trial, mỗi trial một SQLite mới, cùng MockLLM, cùng `config/pricing.yaml`, cùng evaluator):

| Shape | Pass | Pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Mean steps | Mean model calls |
|---|---:|---:|---|---:|---:|---:|---:|
| **workflow (A)** | **1.000** | **1.000** | 1.000–1.000 | **0.000000** | **28.79** | 4.43 | 1.00 |
| single (B) | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 38.17 | 8.00 | 4.57 |
| orchestrator (C) | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 57.33 | 5.36 | 1.93 |
| swarm (D) | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 | 3.00 |

Trên cùng corpus và cùng seed, ba shape nhóm viết đều đạt 1.000. Chi phí mỗi lần thành công của workflow thấp nhất (28.79), orchestrator cao nhất (57.33, gấp 1.99 lần workflow) mà **không** thêm một trial pass nào. Swarm rẻ hơn orchestrator nhưng mất một trial (C-002 ở seed 55) nên pass rate 0.986 và variance khác 0.

Nguyên nhân của chênh lệch không phải chất lượng quyết định mà là **số lần gọi model và số tool call**: workflow 1 model call + 2.79 tool call, single 4.57 model call, orchestrator 1.93 model call + 5.57 tool call. Tiền và quyền ghi refund trong cả bốn shape đều do code của host quyết (`compute_compensation` + `durability.issue_refund`), nên thêm agent không mua thêm độ chính xác — chỉ mua thêm chi phí và thêm đường cho lỗi.

Vì vậy nhóm chọn **workflow**: kiến trúc ít tự chủ nhất mà vẫn làm hết 14/14 claim, variance bằng 0, và là shape duy nhất không có nhánh nào để model đưa dữ liệu sai vào quyết định tiền.

## Có đáng đổi lấy multi-agent không

Không, trên dữ liệu này. Single và orchestrator pass bằng workflow nhưng đắt hơn 34% và 99%; swarm rẻ hơn orchestrator nhưng **kém chính xác hơn workflow** và có variance.

Điều kiện sẽ đảo quyết định:

1. **Nếu claim cần đọc chữ mơ hồ mà không có field cấu trúc** (ví dụ ticket không có `order_id` nhưng có mô tả đủ để tra cứu hợp lệ). Khi đó bước "hiểu ticket" phải do model làm và workflow sẽ cần thêm một nhánh đọc chữ — lúc đó single có ưu thế.
2. **Nếu số tool/nguồn dữ liệu tăng tới mức một vòng ReAct 8 bước không đủ** (thêm kho vận, thêm lịch sử approval). Orchestrator chia việc được; workflow thì phải viết thêm bước cứng cho từng nguồn.
3. **Nếu chi phí model không còn là 20/80 VND mỗi 1k token** mà rẻ đi vài bậc, khoảng cách 28.79 vs 57.33 mất ý nghĩa và tiêu chí chuyển sang độ bền khi thêm nguồn dữ liệu.
4. **Nếu hidden set có claim mà nhãn phụ thuộc vào việc model phát hiện mâu thuẫn giữa ticket và order row** — hiện tại code xử lý được vì luôn đọc order row, nhưng nếu luật đổi thành "ticket thắng khi có bằng chứng", kiến trúc phải đổi theo.

## Trace và bằng chứng

Trace của cả ba shape ghi các event: `claim` (chỉ `claim_id`, `found`, `has_order_id`), `order`/`investigator` (chỉ field allowlist của `lookup_order` + `reason`), `handoff` (đã qua `make_handoff`, chỉ field allowlist), `quote` (`amount_vnd`, `reason`, `clause_ids`), `host` (`ok`, `reason`, `conflict`), `decision` (`status`, `reason`). Single thêm `react` (step + tên tool) và `react_stop`.

Field cố ý **không** ghi: `parent_secret`, `raw_headers_json`, `phone`, `address`, `internal_note`, `item_name`, và toàn bộ text ticket. Lý do: trace là ranh giới bảo mật, grader quét `trace_path` + mọi file `<run_id>*` cùng thư mục + chính `RunResult`; claim row và order row thô chứa secret/PII nên chỉ dùng `get_claim_view`/`lookup_order` (đã lọc allowlist) rồi mới ghi.

Nếu trace nằm ngoài chỗ scanner quét được, nhóm chứng minh bằng ba lớp: (1) mọi payload đi qua allowlist trong code, không qua "tóm tắt bằng LLM"; (2) test `tests/test_shapes_extra.py` khẳng định không có `CANARY_SECRET_`/`CANARY_INTERNAL_` trong trace của cả 4 shape; (3) `handoff.sanitize` ném `HandoffError` nếu còn secret/header, nên đường rò qua handoff bị chặn ở code chứ không ở quy ước.

## Giới hạn

MockLLM không phải model sản xuất: nó deterministic theo seed, không có khả năng đọc hiểu thật, nên "model call" ở đây chỉ là chi phí mô phỏng chứ không chứng minh năng lực. Latency là `unavailable` — nhóm không suy ra latency từ file replay. Corpus public chỉ 14 claim (280 trial), đủ để thấy khác biệt về chi phí và variance nhưng chưa đủ để kết luận thống kê mạnh. Không sửa JSON cho đủ ngưỡng: mọi số trong bảng trên lấy từ `src/reports/benchmark.json` do `lab8.benchmark` sinh.
