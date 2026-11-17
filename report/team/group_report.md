# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: MV
- Thành viên: 3 người, xem `TEAM.md` (Phạm Hoàng Đức Minh — shape A; Trần Đình Nhật Minh — shape B; Nguyễn Văn Minh — shape C + benchmark)
- Commit chốt (trùng `report/team/decision_adr.md`): `96a395c`
- Shape chọn: `workflow`

## 2. Mục tiêu và cách tiếp cận

Bài toán là một claim hoàn phí vận chuyển: đọc ticket, tra đơn, tính entitlement, rồi ghi refund. Nhóm đọc `docs/business_rules.md` và `docs/contracts.md` trước khi viết dòng code nào, và rút ra ba ranh giới quyết định toàn bộ cách làm:

1. **Tiền do code tính**, không do model: `compensation.quote` lấy **max** của các clause đủ điều kiện, không cộng ship với damage.
2. **Chỉ host ghi tiền**: `durability.issue_refund` kiểm approval → trần theo đơn → idempotency, rồi ghi ledger và audit `refund_committed` trong một transaction.
3. **Trace là ranh giới bảo mật**, không phải log debug: grader quét cả `RunResult` lẫn mọi file `<run_id>*`, nên claim row và order row thô không được xuất hiện ở đâu cả.

Cách chia việc: mỗi người một shape, tự viết và tự commit phần của mình; Nguyễn Văn Minh phụ trách shape C kiêm benchmark/crash và báo cáo nhóm. Thứ tự làm: A (workflow) trước vì nó là baseline rẻ nhất và dễ đối chiếu nhất, rồi B (single) để thấy chi phí của vòng ReAct, rồi C (orchestrator) để thấy chi phí của việc tách investigator. Swarm có sẵn, chỉ dùng làm đối chứng.

## 3. Giải pháp

Cả ba shape dùng chung một khung: `get_claim_view` → kiểm `order_id` → `lookup_order` → quote → `durability.issue_refund`. Khác nhau ở chỗ **ai** quyết định và **bao nhiêu bước**.

| Shape | Đọc gì | Ai quyết định dừng/đi tiếp | Ai gọi `issue_refund` |
|---|---|---|---|
| A `workflow` | claim view, order, quote | code, thứ tự cố định | code của shape |
| B `single` | claim view, rồi `run_react` ≤ 8 bước: `lookup_order` → `compute_compensation` → `lookup_refund_history` | model chọn tool, code chặn tool ghi | code của shape sau vòng lặp |
| C `orchestrator` | claim view, handoff, investigator chạy 4 tool đọc | orchestrator lập kế hoạch, investigator chỉ đọc | orchestrator |

**Ranh giới code / model.** Số tiền, approval, idempotency, trần theo đơn đều nằm trong code của host. Model chỉ được: soạn câu trả lời (A, C), chọn tool **đọc** trong bound 8 bước (B), và đọc ticket để quyết định có cần hỏi thêm hay không. Ticket là dữ liệu: shape B không lấy số ngày trễ trong ticket (T02) và không lấy `order_id` từ câu chữ (T04) — cả hai đều là bẫy có sẵn trong bộ public.

**Handoff.** Shape C dựng handoff bằng `handoff.make_handoff` với `allowed_tools` toàn tool đọc. `sanitize` lọc theo `ALLOWED_FIELDS`, ném `HandoffError` nếu còn secret/header, và từ chối mọi write tool. Investigator chạy trong `run_readonly_investigators`, nơi `dispatch(worker=True)` chặn tool ngoài danh sách đọc — nên kể cả handoff có bị sửa thì investigator cũng không ghi được tiền. Trace ghi **handoff đã sanitize**, không ghi parent context.

**Trace event.** `claim` (chỉ `claim_id`, `found`, `has_order_id`), `order`/`investigator` (field allowlist + `reason`), `handoff`, `quote` (`amount_vnd`, `reason`, `clause_ids`), `host` (`ok`, `reason`, `conflict`), `decision` (`status`, `reason`). Shape B thêm `react` (step + tên tool) và `react_stop`. Không ghi: `parent_secret`, `raw_headers_json`, `phone`, `address`, `internal_note`, `item_name`, và toàn bộ text ticket.

## 4. Kết quả

Từ `src/reports/benchmark.json` — 4 shape × 14 claim public × seed `11,22,33,44,55` = 280 trial, mỗi trial một SQLite mới, cùng MockLLM, cùng `config/pricing.yaml`, cùng evaluator:

| Shape | Pass | Pass^5 | Seed min–max | Variance | Cost/success (VND) | Mean / p95 steps |
|---|---:|---:|---|---:|---:|---|
| **workflow** | **1.000** | **1.000** | 1.000–1.000 | **0.000000** | **28.79** | 4.43 / 5 |
| single | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 38.17 | 8.00 / 9 |
| orchestrator | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 57.33 | 5.36 / 6 |
| swarm | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 / 3 |

Crash safety: **20/20** (`src/reports/crash.json`), gồm 5 điểm `before_effect`, 7 điểm `after_effect_before_checkpoint`, 5 điểm `after_checkpoint`, cộng ba kịch bản conflict / missing-approval / swarm-resume.

Ba shape nhóm viết đều pass 70/70. Chênh lệch duy nhất giữa chúng là chi phí: orchestrator đắt gấp 1.99 lần workflow mà không thêm trial pass nào, vì nó chạy 5.57 tool call mỗi trial so với 2.79. Swarm rẻ hơn orchestrator nhưng mất đúng một trial — `C-002` ở seed 55, nơi nó tin "trễ 5 ngày" trong ticket thay vì cột `delay_days = 2`, nên trả 20.000 cho một claim phải `denied`. Đó là variance 0.000816 mà ba shape kia không có.

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

**a) `proposal_amount` không phải số tiền đã ghi.** Lần đầu nhóm trả số đã cap, nên T08 và T14 đỏ với `proposal_mismatch` / `refund_mismatch`. Đọc lại `docs/contracts.md` mới rõ: `proposal_amount` là **quote đầy đủ**, còn số ghi ledger do host quyết. Sửa: luôn truyền quote đầy đủ vào `issue_refund`, không tự trừ phần đã hoàn — tự trừ thì host trừ lần thứ hai và T14 chỉ còn 90.000 thay vì 120.000.

**b) Nhánh `denied` vẫn phải gọi host.** T07 và T13 đỏ với `missing_policy_denied` vì shape tự kết luận "denied" rồi bỏ qua `issue_refund`. Audit `policy_denied` chỉ có khi host từ chối, nên shape phải đẩy quote > 0 qua cửa host rồi mới báo denied.

**c) `stale_trace` khi chạy lại benchmark — lỗi thật, tìm ra bằng cách chạy lại.** Chạy `lab8.benchmark` lần hai cho 53/70 trial `stale_trace` dù trace vừa được ghi. Nguyên nhân: `check_trace` so `mtime` với `started_at` (đồng hồ Python), nhưng `traces/` nằm trên filesystem mount nên `mtime` lấy từ đồng hồ khác và bị floor về giây; lệch quá 1 giây là mọi trace bị coi là cũ. Đo được độ lệch dao động từ −0.17s tới +1.58s giữa hai lần đo. Cách xử lý: sau khi ghi trace, đặt `mtime = int(time.time()) + 1` bằng `os.utime`, để mốc thời gian không bao giờ cũ hơn lần chạy đã ghi ra nó. Sau khi sửa, hai lần chạy benchmark liên tiếp cho số giống hệt nhau. Đây cũng là lý do `reports/benchmark.json` phải sinh lại sau khi shape A và B được viết lại.

**d) Crash phải để nó nổ.** T12 đỏ khi shape bắt `InjectedCrash` để "chạy tiếp cho an toàn". Test kiểm `crashed` là true, nên shape phải forward `crash_at` xuống `issue_refund` và để exception đi ra; resume sau đó mới là việc của ledger.

## 6. Tổng hợp đóng góp

Mỗi thành viên viết và commit phần của mình trên tài khoản GitHub riêng, kèm test riêng:

| Thành viên | Phần việc | Commit | Test thêm |
|---|---|---|---|
| Phạm Hoàng Đức Minh (2A202604114) | Nhóm trưởng; shape A `workflow.py`; ADR; review và merge PR | `2a85a42` | `test_workflow_extra.py` (13 test) |
| Trần Đình Nhật Minh (2A202604083) | Shape B `single.py` (ReAct ≤ 8 bước), kiểm step cap và budget | `c425b34` | `test_single_extra.py` (24 test) |
| Nguyễn Văn Minh (2A202604117) | Shape C `orchestrator.py` + handoff; benchmark, crash; group report; bonus B3 | `710d8bc`, `9e2bd15` | `test_orchestrator_extra.py` (9 test) |

Chi tiết nằm trong bảng đóng góp của `TEAM.md` và báo cáo cá nhân `report/team/2A202604114_PhamHoangDucMinh.md`, `2A202604083_TranDinhNhatMinh.md`, `2A202604117_NguyenVanMinh.md`.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất: nó deterministic theo seed và không đọc hiểu thật, nên "model call" ở đây chỉ là chi phí mô phỏng, không chứng minh năng lực. Latency là `unavailable` — nhóm không suy ra latency từ file replay. Corpus public chỉ 14 claim (280 trial), đủ thấy khác biệt về chi phí và variance nhưng chưa đủ cho kết luận thống kê mạnh; một trial fail trên 70 không cho phép suy ra phân bố failure mode.

Hướng cải thiện: (1) thêm claim đối kháng tự viết cho các nhánh chưa có trong public — approval của claim khác, đơn đã hoàn một phần rồi hỏng hàng, ticket nói thiếu ngày; (2) chạy bootstrap CI cho pass rate thay vì so sánh điểm; (3) nếu có model thật, đo lại cost/success với giá thật và kiểm tra xem ưu thế của workflow còn giữ khi bước "hiểu ticket" trở nên khó hơn.

## 8. Tài liệu tham khảo

- `docs/business_rules.md`, `docs/contracts.md`, `docs/metrics.md`, `docs/architecture.md` — luật nghiệp vụ, contract `RunResult` và trace v1, định nghĩa metric, ranh giới code/model.
- Cemri et al., *Why Do Multi-Agent LLM Systems Fail?* (MAST), NeurIPS 2025 Datasets & Benchmarks Track, https://arxiv.org/abs/2503.13657 — dùng cho phiếu nghiên cứu R2.
- `src/reports/benchmark.json`, `src/reports/crash.json` — bằng chứng do `lab8.benchmark` và `lab8.crash_test` sinh, không sửa tay.
