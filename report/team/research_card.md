# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R2 |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Cemri et al., *Why Do Multi-Agent LLM Systems Fail?* (MAST), NeurIPS 2025 Datasets & Benchmarks Track (Spotlight), arXiv:2503.13657, https://arxiv.org/abs/2503.13657 — benchmark + human annotation trên 150 trace, không phải production report |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Lỗi của hệ multi-agent gom vào 14 failure mode thuộc 3 nhóm — system design, inter-agent misalignment, task verification — với κ = 0,88 giữa người gán nhãn; nghĩa là phần lớn lỗi không phải "model kém" mà là lỗi thiết kế/kiểm chứng của hệ |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Taxonomy dựng từ 150 trace của 5 framework (MetaGPT, ChatDev, AG2, HyperAgent, AppWorld), model GPT-4 / Claude 3 / Qwen2.5 / CodeLlama, task coding-math-agent. κ = 0,88 là đồng thuận **giữa người với người**, không phải trần cho một tagger bằng luật. Không có claim nào về chi phí token hay latency |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Nếu lỗi của swarm là **task verification** (tin số ngày trong ticket thay vì cột `delay_days`), thì bỏ đúng một biến đó — nguồn của `delay_days` — phải làm pass rate từ 0,986 lên 1,000 và variance từ 0,000816 về 0, trong khi cost/success gần như không đổi |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Giữ cố định MockLLM (cùng seed 11/22/33/44/55), cùng bộ tool đọc, cùng `data/public_claims.jsonl` (14 claim), cùng `config/pricing.yaml`, cùng `metrics.trial_pass`, mỗi trial một SQLite mới. Biến duy nhất: **nguồn của `delay_days` khi quote** — swarm lấy số trong ticket ở seed chia hết cho 5 (`REFERENCE_WEAKNESS`), workflow/single/orchestrator luôn lấy cột `orders.delay_days` |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến: trial C-002 ở seed 55 bị `status resolved != denied` (trả 20.000 cho đơn trễ 2 ngày). Đo bằng pass rate, pass^5, seed variance, cost/success từ `src/reports/benchmark.json`, cộng `secret_leak_count`/`approval_bypass_count` phải bằng 0 |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn):

```bash
cd src
python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
```

- Run id / file report: `R-workflow-C-001-s11` … (280 trial trong `src/reports/benchmark.json`), commit `96a395c`
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu:

**Đúng một phần, và đúng ở đúng chỗ dự đoán.** Shape lấy `delay_days` từ cột order (workflow, single, orchestrator): pass rate 1,000, pass^5 1,000, variance 0,000000. Shape lấy từ ticket ở seed 55 (swarm): pass rate 0,9857, pass^5 0,9286, seed min–max 0,929–1,000, variance 0,000816. Trial fail duy nhất là `C-002` seed 55, lý do `status resolved != denied` — đúng trial mà hypothesis chỉ ra.

Phần **không** đúng như dự đoán: cost/success không "gần như không đổi". Swarm rẻ hơn orchestrator nhưng **đắt hơn workflow** (49,57 so với 28,79 VND mỗi lần thành công) vì nó gọi 3 model call và 4,66 tool call mỗi trial. Vậy bỏ biến gây lỗi không chỉ sửa accuracy mà còn rẻ đi 42% — nghĩa là kiến trúc multi-agent ở đây vừa kém chính xác hơn vừa đắt hơn.

Theo taxonomy MAST, lỗi này thuộc nhóm **task verification** (nhóm 3): agent không kiểm chứng dữ kiện trước khi dùng nó để tính tiền, chứ không phải lỗi giao việc (nhóm 1) hay lệch mục tiêu giữa các agent (nhóm 2). Điều này khớp với thiết kế của lab: mọi shape đều có chung host gate, nên lỗi giao việc bị chặn ở code; chỉ còn đường "dữ kiện sai lọt vào quote" là lọt được.

- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`. Chỉ 1 trial fail trên 70 trial của swarm nên không thể suy ra tỉ lệ failure mode cho cả taxonomy — đây là một quan sát đơn lẻ, không phải phân bố. κ = 0,88 của paper là đồng thuận giữa người, không phải ngưỡng nhóm phải đạt.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
