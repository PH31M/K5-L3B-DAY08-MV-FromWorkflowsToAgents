# Team

## Thông tin nhóm

- Tên nhóm: MV
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY08-MV-FromWorkflowsToAgents`
- URL repo: https://github.com/PH31M/K5-L3B-DAY08-MV-FromWorkflowsToAgents
- Nhánh nộp: `main` (feature gộp qua PR từ nhánh thành viên)
- Commit chốt: `fe4b2b2` (xem `report/team/decision_adr.md`)

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Phạm Hoàng Đức Minh | 2A202604114 | ducminh03102005@gmail.com | PH31M | Nhóm trưởng — shape A `workflow.py`, `decision_adr.md`, merge PR |
|   2 | Trần Đình Nhật Minh | 2A202604083 | trandinhnhatminh1112@gmail.com | trandinhnhatminh1452 | Shape B `single.py` (ReAct ≤ 8 bước), test step-cap/budget |
|   3 | Nguyễn Văn Minh | 2A202604117 | vm140205@gmail.com | vm140205-collab | Shape C `orchestrator.py` + handoff, benchmark/crash, group report |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Phạm Hoàng Đức Minh (2A202604114) | Shape A `workflow.py`, `decision_adr.md`, review + merge PR | `1864b2b` | `tests/test_workflow_extra.py` |
| Trần Đình Nhật Minh (2A202604083) | Shape B `single.py`, kiểm step cap 8 và budget model calls | `c425b34` | `tests/test_single_extra.py` |
| Nguyễn Văn Minh (2A202604117) | Shape C `orchestrator.py` + handoff allowlist, `reports/benchmark.json` + `reports/crash.json`, `group_report.md` | `710d8bc` | `tests/test_orchestrator_extra.py` |

Ghi chú: mỗi thành viên commit phần của mình bằng tài khoản GitHub của mình trên nhánh riêng, rồi mở PR vào `main`.

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/team/` theo dạng `report/team/MSSV_HoTen.md`.

## 2A202604114 — Phạm Hoàng Đức Minh

### Phần việc phụ trách

- Nhóm trưởng; thiết kế và triển khai Shape A (`workflow.py`); đối soát số liệu kiến trúc `decision_adr.md`; xây dựng bộ test hồi quy `tests/test_workflow_extra.py`.

### Đóng góp cụ thể

- Triển khai toàn bộ quy trình pipeline tuần tự của Shape A: tiền tính 100% bằng code qua `compute_compensation`, model chỉ đóng vai trò soạn thảo phản hồi.
- Xử lý Full quote (T14): truyền nguyên quote vào `issue_refund`, để Host tự trừ bồi thường trước đó nhằm tránh lỗi trừ 2 lần.
- Crash durability (T12): forward nguyên vẹn `crash_at` xuống Host, bắt `InjectedCrash` ghi trace và cập nhật mtime rồi re-raise ngoại lệ.
- Khắc phục triệt để lỗi `stale_trace` trên hệ thống file mount thông qua `_touch_trace`.
- Xây dựng 13 test case kiểm thử hồi quy bảo mật và toàn vẹn dữ liệu trong `tests/test_workflow_extra.py`.

### Bằng chứng

- Commit: `2a85a42` (PR merge: `1864b2b`).
- Báo cáo chi tiết: `report/team/2A202604114_PhamHoangDucMinh.md`.

## 2A202604083 — Trần Đình Nhật Minh

### Phần việc phụ trách

- Shape B: `src/lab8/shapes/single.py`, vòng ReAct tối đa 8 lượt quyết định.
- Test giới hạn bước, ngân sách model/tool và điều kiện an toàn trong `src/tests/test_single_extra.py`.

### Đóng góp cụ thể

- Cài đặt `run_react(max_steps=8)`: giới hạn nghiêm ngặt 8 bước decide, ánh xạ observation sang hành động đọc, chỉ định Host là writer duy nhất.
- Kiểm soát ngân sách model/tool qua `Budget`, đảm bảo chi phí và bước lặp tương đương giữa các shape.
- Xử lý crash/resume an toàn, truyền quote đầy đủ để Host áp trần.

### Bằng chứng

- Commit: `c425b34`.
- Báo cáo chi tiết: `report/team/2A202604083_TranDinhNhatMinh.md`.

## 2A202604117 — Nguyễn Văn Minh

### Phần việc phụ trách

- Shape C: `src/lab8/shapes/orchestrator.py`, cơ chế handoff allowlist với investigator chỉ đọc.
- Bằng chứng đo lường: `src/reports/benchmark.json` (280 trial) và `src/reports/crash.json` (20/20).
- Báo cáo nhóm `group_report.md` và test riêng `src/tests/test_orchestrator_extra.py`.

### Đóng góp cụ thể

- Dựng handoff qua `make_handoff` chặn toàn bộ write tool, lọc facts theo allowlist, investigator chỉ chạy tool đọc qua `run_readonly_investigators`.
- Phát hiện và đưa ra giải pháp sửa lỗi `stale_trace` trên filesystem mount bằng `os.utime`.
- Tạo 9 test case an toàn cho Shape C và tổng hợp đối sánh benchmark 4 shape trong `group_report.md`.

### Bằng chứng

- Commit: `710d8bc`.
- Báo cáo chi tiết: `report/team/2A202604117_NguyenVanMinh.md`.
