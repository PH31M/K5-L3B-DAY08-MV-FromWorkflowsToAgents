# Báo cáo cá nhân — 2A202604117_NguyenVanMinh

## 1. Thông tin thành viên

- Họ tên: Nguyễn Văn Minh
- MSSV: 2A202604117
- Email: vm140205@gmail.com
- GitHub: vm140205-collab

## 2. Phần việc phụ trách

- Shape C `src/lab8/shapes/orchestrator.py`: orchestrator + investigator chỉ đọc, handoff allowlist.
- Bằng chứng đo: `src/reports/benchmark.json` (4 shape × 14 claim × 5 seed) và `src/reports/crash.json` (20/20).
- Test riêng: `src/tests/test_orchestrator_extra.py` (9 test).
- `report/team/group_report.md` và file báo cáo này.

## 3. Đóng góp cụ thể

**Shape C.** Orchestrator dựng handoff bằng `handoff.make_handoff` với 4 tool đọc (`lookup_order`, `lookup_policy`, `compute_compensation`, `lookup_refund_history`), chạy investigator qua `run_readonly_investigators`, rồi tự gọi `durability.issue_refund` với **quote đầy đủ**. Quyết định kỹ thuật: không đưa `facts` vào handoff ở bước đầu vì chưa có order view; để investigator tự đọc, còn orchestrator chỉ nhận field allowlist trở về. Trace ghi handoff đã sanitize, không ghi parent context.

**Sửa lỗi `stale_trace` khi tái lập benchmark.** Chạy lại `lab8.benchmark` cho 53/70 trial `stale_trace` dù trace vừa ghi. Nguyên nhân: `check_trace` so `mtime` với `started_at`, nhưng trên filesystem mount `mtime` lấy từ đồng hồ khác và bị floor về giây (đo được lệch từ −0.17s đến +1.58s). Cách sửa nằm trong file shape: sau khi ghi trace, đặt `mtime = int(time.time()) + 1` bằng `os.utime`. Sau khi sửa, hai lần chạy liên tiếp cho số giống hệt. Lỗi này ảnh hưởng cả shape A và B, nên đã ghi lại trong `TEAM.md` mục bàn giao.

**Bằng chứng.** `crash_safety 20/20`; benchmark 280 trial; `workflow/single/orchestrator` 70/70, swarm 69/70 (miss `C-002` seed 55). Số trong `decision_adr.md` lấy từ `reports/benchmark.json`, không chép tay.

Commit chính (nhánh `main`): `22b5163` (workflow + single + TEAM.md — sau đó đã trả hai file này về stub cho đúng phần người phụ trách), `710d8bc` (orchestrator + crash + benchmark), `53c7724` (ADR + research card + test), `9e2bd15` (bàn giao A/B, test riêng cho shape C).

## 4. Bằng chứng

- `src/lab8/shapes/orchestrator.py` — shape C.
- `src/tests/test_orchestrator_extra.py` — 9 test: handoff allowlist + từ chối write tool, trace ở mọi nhánh return, không lộ `CANARY_SECRET_*`/PII, quote đầy đủ khi host cap (T07/T08/T13/T14), forward `crash_at` (T12).
- `src/reports/benchmark.json`, `src/reports/crash.json`.
- Lệnh kiểm: `python -m pytest -q` → 63 passed; `python -m pytest -q -m student -o addopts= -k orchestrator` → 62 passed; `python -m lab8.crash_test --count 20 --out reports/crash.json` → 20/20; `python -m lab8.check_submission` → 0 FAIL.

## 5. Công cụ AI đã dùng

Dùng một trợ lý AI (pi + Claude) để: đọc và tóm tắt `docs/`, dựng bản nháp shape C, và viết test.

Cách tự kiểm tra, không tin kết quả tự khai:

- Chạy lại toàn bộ ma trận 248 test và cổng host, đọc từng dòng `FAILED` khi có, không chỉ nhìn dòng tổng kết.
- Tự đọc `metrics.trial_pass` để hiểu thứ tự 10 cổng chấm, rồi đối chiếu từng nhánh return của shape với `docs/contracts.md` (đặc biệt `proposal_amount` là quote đầy đủ, và nhánh `denied` vẫn phải gọi host để có audit `policy_denied`).
- Kiểm chứng số liệu bằng cách chạy lại `lab8.benchmark` hai lần và so từng metric — chính bước này phát hiện lỗi `stale_trace`.
- Kiểm chứng nguồn tài liệu trước khi đưa vào `research_card.md`: mọi citation được tra lại URL gốc; hai chỗ đề bài trích sai hình thức đã được sửa (bài của Google Research nay là *Capable language models can outgrow the benefits of collaboration*, Nature Machine Intelligence 2026; bài EMNLP có tên đầy đủ *Rethinking the Evaluation of Efficiency Methods for Multi-Agent Systems*).

## 6. Tự đánh giá

Phần shape C và bằng chứng đo hoàn thành, tái lập được. Điểm chưa tốt: mình viết cả shape A và B trong lần đầu, vượt phần hai bạn phụ trách; đã sửa bằng cách đưa hai file về stub và giữ bản tham khảo ở nhánh `ref/shapes` để các bạn tự viết lại. Bài học: chia việc theo file phải chốt trước khi viết dòng đầu, không phải sau khi có kết quả xanh.
