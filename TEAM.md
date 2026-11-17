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
|   1 | Phạm Hoàng Đức Minh | 2A202604114 | ducminh03102005@gmail.com | PH31M | Nhóm trưởng — shape A `workflow.py`, merge PR, số liệu ADR |
|   2 | Trần Đình Nhật Minh | 2A202604083 |  | (điền handle) | Shape B `single.py` (ReAct ≤ 8 bước), test step-cap/budget |
|   3 | Nguyễn Văn Minh | 2A202604117 |  | vm140205-collab | Shape C `orchestrator.py` + handoff, benchmark/crash, báo cáo nhóm |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Phạm Hoàng Đức Minh (2A202604114) | Shape A `workflow.py`, review + merge PR, điền `decision_adr.md` | `feat/shapes`: workflow.py | `tests/test_workflow_extra.py` |
| Trần Đình Nhật Minh (2A202604083) | Shape B `single.py`, kiểm step cap 8 và budget model calls | `feat/shapes`: single.py | `tests/test_single_extra.py` |
| Nguyễn Văn Minh (2A202604117) | Shape C `orchestrator.py` + handoff allowlist, `reports/benchmark.json` + `reports/crash.json`, `group_report.md` | `feat/shapes`: orchestrator.py | `tests/test_handoff_extra.py` |

Ghi chú: mỗi thành viên tự commit phần test + mục báo cáo của mình bằng tài khoản GitHub của mình trên nhánh riêng, rồi mở PR vào `feat/shapes`. Cột Commit/Test ở trên là phần việc đã nhận; cập nhật hash thật khi PR được merge.

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
