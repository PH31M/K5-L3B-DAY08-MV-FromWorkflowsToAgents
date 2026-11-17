# Bonus report: B3

- Topic + nguồn (tên, năm, slide): B3 — verifier/aggregator chống khuếch đại lỗi. Nguồn: *Capable language models can outgrow the benefits of collaboration*, Nature Machine Intelligence 8:1157–1172 (2026), doi:10.1038/s42256-026-01268-y — bản preprint cùng tác giả là *Towards a Science of Scaling Agent Systems* (arXiv:2512.08296), slide 17, 22, 42.
- CLAIM của nguồn (1 câu): Trong phân tích trace-level, bốn biến thể multi-agent xếp đúng theo thứ tự từ independent (error amplification **17,2×**) tới centralized (**4,4×**), nghĩa là **validation bottleneck** chặn lỗi trước khi chúng được tổng hợp vào kết quả cuối.
- BOUNDARY (model / dataset / setup): 6 benchmark (BrowseComp-Plus, Finance Agent, PlanCraft, WorkBench, SWE-bench Verified, Terminal-Bench), 3 họ model (GPT-5, Gemini 2.5, Claude 4.x), n = 20–100 mỗi cell. Paper đo **accuracy và token cost**, không đo latency. Quan trọng: 17,2× và 4,4× là **tỉ lệ khuếch đại lỗi trên trace**, không phải chênh lệch pass rate — nhóm không tuyên bố "tái lập 17,2×".
- HYPOTHESIS trên LogiX: thêm một validation bottleneck **bằng code** ngay trước `issue_refund` sẽ đưa swarm từ 0,986 lên 1,000 trên bộ public và từ 0,875 lên 1,000 trên bộ đối kháng, trong khi cost/success không tăng.
- Biến cố định / biến thay đổi: cố định MockLLM (seed 11/22/33/44/55), bộ tool đọc, corpus, `config/pricing.yaml`, evaluator `metrics.trial_pass`, mỗi trial một SQLite mới. Biến duy nhất: **có hay không bước verifier** giữa bước quote và bước ghi tiền (`bonus/swarm_verified.py`).
- Lệnh tái lập (copy-paste được):

```bash
cd src
python -m bonus.benchmark_b3
python -m pytest -q tests/test_bonus_verifier.py
```

- File report + run id: `src/reports/bonus_b3.json` (sinh bởi lệnh trên, không sửa tay). Run id dạng `R-swarm_verified-<claim>-s<seed>`, ví dụ `R-swarm_verified-C-B01-s55`.

## Kết quả

Bảng lấy từ `reports/bonus_b3.json`. Bộ **public** là 14 claim của đề; bộ **adversarial** là 8 claim nhóm tự viết trong `bonus/cases.jsonl` (nhãn viết tay theo `docs/business_rules.md`), trong đó 5 claim cài bẫy "ticket nói khác order".

| Bộ | Shape | Pass | Pass^5 | Variance | Cost/success (VND) | Mean steps |
|---|---|---:|---:|---:|---:|---:|
| public | workflow | 1,000 | 1,000 | 0,000000 | 28,79 | 4,43 |
| public | swarm | 0,986 | 0,929 | 0,000816 | 49,57 | 2,80 |
| public | **swarm_verified** | **1,000** | **1,000** | **0,000000** | 49,00 | 5,40 |
| adversarial | workflow | 1,000 | 1,000 | 0,000000 | 30,93 | 4,38 |
| adversarial | swarm | 0,875 | 0,375 | 0,062500 | 61,02 | 3,12 |
| adversarial | **swarm_verified** | **1,000** | **1,000** | **0,000000** | 54,64 | 5,75 |

Verifier can thiệp **1/70** trial trên public và **5/40** trial trên bộ đối kháng — đúng 5 claim bẫy, chỉ ở seed 55 (seed chia hết cho 5, nơi swarm tin ticket). Mỗi lần can thiệp ghi một event `verifier_override` với `fields`, `before_vnd`, `after_vnd`, `source: structured_order`.

## Kết luận

Hypothesis **đúng về accuracy, sai về chi phí**. Verifier đưa swarm về đúng bằng workflow: 1,000 trên cả hai bộ, variance về 0, pass^5 từ 0,929 lên 1,000 (public) và từ 0,375 lên 1,000 (adversarial). Nó sửa được cả hai chiều: chặn trả tiền khi ticket nói quá (`C-B01`: 35.000 → 0) và trả đủ khi ticket nói thiếu (`C-B06`: 0 → 30.000).

Nhưng cost/success **không** giữ nguyên: trên bộ đối kháng, swarm_verified tốn 54,64 VND mỗi lần thành công so với 30,93 của workflow — **đắt 1,77 lần** để đạt cùng accuracy. Trên public là 49,00 so với 28,79, đắt 1,70 lần. Trả lời câu hỏi của topic: sau khi verifier đã thay phần kiểm chứng, swarm **không còn giữ giá trị nào trên task này** — phần còn lại của nó là ba model call (peer, parse, draft) và một vòng investigator, tức đúng phần bị verifier vô hiệu hoá. Giá trị của swarm chỉ xuất hiện khi các nhánh thật sự song song được, mà claims flow ở đây là tuần tự: phải có order mới quote được, phải có quote mới ghi được.

Điều kiện đảo kết luận: nếu verifier phải kiểm nhiều nguồn dữ kiện hơn (thêm kho vận, lịch sử approval) thì chi phí kiểm chứng tăng và có thể vượt phần tiết kiệm; nếu luật nghiệp vụ cho phép ticket thắng khi có bằng chứng kèm ảnh, verifier không còn quyền override và swarm lấy lại phần tự chủ.

## Giới hạn

Bộ đối kháng chỉ có 8 claim nhãn tay do nhóm viết, nên 0,875 → 1,000 là quan sát trên 40 trial, không phải ước lượng cho phân bố lỗi thật. Verifier chỉ kiểm được ba field (`delay_days`, `status`, `damage_verified`) — lỗi nằm ngoài ba field đó (ví dụ approval bị thu hồi) vẫn do host chặn, không do verifier. MockLLM không phải model sản xuất nên "model call" chỉ là chi phí mô phỏng; latency là `unavailable`. Nguồn cũng có giới hạn riêng: 17,2×/4,4× là tỉ lệ trên trace, không phải delta pass rate, nên nhóm chỉ dùng nó để biện luận hướng, không dùng để so số.

## Phụ lục: một topic đã làm nhưng không nộp

Nhóm làm thêm topic B7 (kiểm toán grader): code `bonus/grader_audit_report.py`, test `tests/test_bonus_grader_audit.py` (13 test), report `reports/bonus_grader_audit.json`. Kết quả: chỉ bản `grader_b` thoả mọi quan hệ metamorphic; `grader_a` cộng cost hai lần (31,50 so với 21,06 trên fixture infra) và `grader_c` tính trial hạ tầng là sai (pass rate 0,750 → 0,5625). Topic này không được nộp vì `lab8.check_submission` chỉ nhận tiêu đề `Bonus report: B1`…`B6` (dòng 243), trong khi `docs/bonus_topics.md` có B7 — nhóm chọn B3 để bài nộp không có FAIL về format. Mã và bằng chứng của B7 vẫn để nguyên trong repo để chạy lại được.
