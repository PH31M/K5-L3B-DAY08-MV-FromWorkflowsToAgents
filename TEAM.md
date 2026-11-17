# Team

## Thông tin nhóm

- Tên nhóm: MV
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY08-MV-FromWorkflowsToAgents`
- URL repo: https://github.com/PH31M/K5-L3B-DAY08-MV-FromWorkflowsToAgents
- Nhánh nộp: `main` (feature gộp qua PR từ `feat/shapes`)
- Commit chốt: cập nhật sau khi merge (xem `report/team/decision_adr.md`)

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Phạm Hoàng Đức Minh | 2A202604114 | ducminh03102005@gmail.com | PH31M | Nhóm trưởng — shape A `workflow.py`, `decision_adr.md`, merge PR |
|   2 | Trần Đình Nhật Minh | 2A202604083 |  | (điền handle) | Shape B `single.py` (ReAct ≤ 8 bước), test step-cap/budget |
|   3 | Nguyễn Văn Minh | 2A202604117 |  | vm140205-collab | Shape C `orchestrator.py` + handoff, benchmark/crash, group report |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Phạm Hoàng Đức Minh (2A202604114) | Shape A `workflow.py`, `decision_adr.md`, review + merge PR | (điền hash) | `tests/test_workflow_extra.py` |
| Trần Đình Nhật Minh (2A202604083) | Shape B `single.py`, kiểm step cap 8 và budget model calls | (điền hash) | `tests/test_single_extra.py` |
| Nguyễn Văn Minh (2A202604117) | Shape C `orchestrator.py` + handoff allowlist, `reports/benchmark.json` + `reports/crash.json`, `group_report.md` | (điền hash) | `tests/test_orchestrator_extra.py` |

Ghi chú: mỗi thành viên commit phần của mình bằng tài khoản GitHub của mình trên nhánh riêng, rồi mở PR vào `main`. Cột Commit để trống cho tới khi PR được merge — không ghi hash trước.

### Bàn giao shape A và B

`workflow.py` và `single.py` trên `main` đang là stub gốc của đề. Nhánh `ref/shapes` giữ một bản tham khảo đã chạy 62/62 test mỗi shape, để đọc khi bí — **không copy nguyên**: người phụ trách phải tự viết và giải thích được từng bước (RULES.md cấm nhận bài làm thay, và người chấm có thể hỏi trực tiếp).

Hai điểm bắt buộc khi viết lại, cả hai đều đã trả giá bằng test đỏ:

1. **Trace phải được ghi ở mọi nhánh return**, kể cả `needs_info` và `escalated`, và `run_id` trong file phải trùng `RunResult.run_id`. Dùng `lab8.shapes.common.finish()` là cách ngắn nhất.
2. **mtime của file trace phải không cũ hơn `started_at`** mà grader đo. Trên filesystem mount (drvfs, mạng, FAT) mtime có thể lấy từ đồng hồ khác và bị floor về giây, nên một trace vừa ghi vẫn bị chấm `stale_trace`. Cách xử lý trong `ref/shapes`: sau khi ghi, đặt mtime về `int(time.time()) + 1` bằng `os.utime`. Không có bước này, chạy lại benchmark trên máy khác sẽ ra `stale_trace` hàng loạt và mất điểm C7.

Sau khi A và B land, phải sinh lại bằng chứng bằng đúng lệnh trong `src/reports/README.md` rồi cập nhật số trong `decision_adr.md` — `reports/benchmark.json` hiện tại là của lần chạy trên nhánh `ref/shapes`.

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## MSSV_HoTen

### Phần việc phụ trách

-

### Đóng góp cụ thể

-

### Bằng chứng

-
