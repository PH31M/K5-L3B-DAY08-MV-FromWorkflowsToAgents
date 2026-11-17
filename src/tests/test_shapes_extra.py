"""Extra regression tests for the three student shapes (Nguyễn Văn Minh).

The public matrix already covers T01-T14 on 5 seeds. These tests pin the
properties that make the shapes safe rather than merely correct:

1. the trace is written on every return path, including `needs_info` and
   `escalated`, so a stale file from an earlier run can never be graded;
2. no parent secret or internal canary reaches the trace or the RunResult;
3. `proposal_amount` is the full quote even when the host denies or caps it;
4. the model never decides the amount: workflow makes one draft call, single
   stops inside its 8-step budget;
5. `crash_at` is forwarded and `InjectedCrash` is not swallowed.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from lab8.db import connect, init_store
from lab8.durability import InjectedCrash
from lab8.metrics import check_trace, trial_pass
from lab8.shapes import SHAPES
from tests.conftest import BY_ID, CLAIMS, WORLD

STUDENT_SHAPES = ["workflow", "single", "orchestrator"]
LEAK_TOKENS = ("CANARY_SECRET_", "CANARY_INTERNAL_", "0901111222", "12 Le Loi Q1")


def _store(tmp_path: Path, name: str) -> Path:
    store = tmp_path / name
    init_store(store, WORLD, CLAIMS).close()
    return store


@pytest.mark.parametrize("shape", STUDENT_SHAPES)
def test_trace_is_written_on_every_return_path(tmp_path, shape):
    """needs_info and escalated are early returns; both must still write a trace."""
    for claim_id in ("C-004", "C-005"):
        store = _store(tmp_path, f"{shape}-{claim_id}.sqlite")
        started_at = time.time()
        result = SHAPES[shape](claim_id, seed=11, store_path=str(store))
        assert result.status in {"needs_info", "escalated"}, result.status
        assert check_trace(result.as_dict(), started_at=started_at) == (True, "ok")
        body = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
        assert body["run_id"] == result.run_id
        assert isinstance(body["events"], list) and body["events"], "trace must not be empty"


@pytest.mark.parametrize("shape", STUDENT_SHAPES + ["swarm"])
@pytest.mark.parametrize("claim_id", ["C-005", "C-010"])
def test_no_secret_or_pii_in_trace_or_result(tmp_path, shape, claim_id):
    """T05 and T10 are the PII canaries: the raw claim/order row must never be logged."""
    store = _store(tmp_path, f"{shape}-{claim_id}.sqlite")
    result = SHAPES[shape](claim_id, seed=11, store_path=str(store))
    blob = json.dumps(result.as_dict(), ensure_ascii=False, default=str)
    blob += Path(result.trace_path).read_text(encoding="utf-8")
    for token in LEAK_TOKENS:
        assert token not in blob, f"{shape}/{claim_id} leaked {token}"


@pytest.mark.parametrize("shape", STUDENT_SHAPES)
@pytest.mark.parametrize(
    "claim_id,expected_proposal,expected_refund",
    [("C-007", 35000, 0), ("C-013", 35000, 0), ("C-008", 35000, 20000), ("C-014", 150000, 120000)],
)
def test_proposal_is_full_quote_while_host_caps(
    tmp_path, shape, claim_id, expected_proposal, expected_refund
):
    """The shape reports the quote; the host decides the written amount (T07, T08, T13, T14)."""
    store = _store(tmp_path, f"{shape}-{claim_id}.sqlite")
    started_at = time.time()
    result = SHAPES[shape](claim_id, seed=11, store_path=str(store))
    assert result.proposal_amount == expected_proposal
    conn = connect(store)
    try:
        passed, reason = trial_pass(
            result.as_dict(), BY_ID[claim_id]["expected"], conn, started_at=started_at
        )
        row = conn.execute(
            "SELECT COALESCE(SUM(amount_vnd), 0) AS total FROM refund_ledger WHERE claim_id = ?",
            (claim_id,),
        ).fetchone()
    finally:
        conn.close()
    assert passed, reason
    assert int(row["total"]) == expected_refund


def test_workflow_model_calls_are_bounded(tmp_path):
    """Workflow drafts text once; the model never picks the amount."""
    store = _store(tmp_path, "workflow-budget.sqlite")
    result = SHAPES["workflow"]("C-001", seed=11, store_path=str(store))
    assert result.status == "resolved"
    assert result.model_calls == 1
    assert result.tool_calls <= 4


@pytest.mark.parametrize("shape", STUDENT_SHAPES)
def test_crash_is_forwarded_and_not_swallowed(tmp_path, shape):
    """T12: crash_at must reach durability.issue_refund and InjectedCrash must propagate."""
    store = _store(tmp_path, f"{shape}-t12.sqlite")
    with pytest.raises(InjectedCrash):
        SHAPES[shape](
            "C-012",
            seed=11,
            store_path=str(store),
            crash_at="after_effect_before_checkpoint",
        )
    started_at = time.time()
    resumed = SHAPES[shape]("C-012", seed=11, store_path=str(store))
    conn = connect(store)
    try:
        passed, reason = trial_pass(
            resumed.as_dict(), BY_ID["C-012"]["expected"], conn, started_at=started_at
        )
        rows = conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-012'"
        ).fetchone()["n"]
    finally:
        conn.close()
    assert passed, reason
    assert rows == 1
    assert resumed.committed_audit_count == 1
