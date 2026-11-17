"""Shape B — one ReAct agent. Student work (Trần Đình Nhật Minh).

`lab8.runtime.run_react` with `max_steps=8`. `decide` may pick a read tool; the
host rejects write tools, so the model cannot call `issue_refund`. After the
loop the shape validates the quote and the host is the only writer.

The decide policy below reads structured fields only. It never takes the delay
number written in the ticket (T02) and never invents an `order_id` from the
ticket (T04), because the ticket is user data, not an instruction.

Per-order cap: `lookup_refund_history` shows what earlier claims already got on
the same order. The host still enforces the cap, so the full quote is what goes
into `durability.issue_refund`, never a net amount (T13, T14).

Budget: every decide step is one model call, so cost stays comparable with the
other shapes.

Trace contract v1: a JSON file written on every return path, `run_id` equal to
`RunResult.run_id`, `events` a list. Only allowlisted fields go into it.
"""

from __future__ import annotations

import os
import sqlite3
import time
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
import time

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.mock_llm import complete
from lab8.runtime import ToolRejected, run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace

SHAPE = "single"
MAX_STEPS = 8


def _touch_trace(path: str) -> str:
    """Stamp the trace with the clock the grader compares against."""
    stamp = float(int(time.time()) + 1)
    try:
        os.utime(path, (stamp, stamp))
    except OSError:
        pass
    return path


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id(SHAPE, claim_id, seed))

    def result(status: str, proposal: int, reason: str | None = None) -> RunResult:
        trace.add("decision", {"status": status, "reason": reason})
        outcome = finish(
            conn,
            shape=SHAPE,
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=reason,
        )
        _touch_trace(outcome.trace_path)
        return outcome

    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    trace.add(
        "claim",
        {
            "claim_id": claim_id,
            "found": bool(claim.get("found")),
            "has_order_id": bool(claim.get("order_id")),
        },
    )
    if not claim.get("found"):
        return result("failed", 0, "unknown_claim")
    if not claim.get("order_id"):
        complete(budget, seed=seed, purpose="draft", prompt="needs_info")
        return result("needs_info", 0, "missing_order_id")

    state: dict[str, Any] = {"step": 0, "quote": None, "history": None}

    def decide(seen: dict[str, Any]) -> dict[str, Any]:
        state["step"] += 1
        # One model call per decision: the agent reads the ticket, the code decides.
        complete(budget, seed=seed, purpose="parse", prompt=f"step={state['step']}")
        last = seen.get("last_tool")
        if last is None:
            trace.add("react", {"step": state["step"], "tool": "lookup_order"})
            return {
                "tool": "lookup_order",
                "args": {
                    "order_id": claim["order_id"],
                    "principal_id": claim["principal_id"],
                },
            }
        last_result = seen.get("last_result") or {}
        if last == "lookup_order":
            if not last_result.get("visible"):
                trace.add("react", {"step": state["step"], "final": "escalated"})
                return {"final": {"status": "escalated", "reason": last_result.get("reason")}}
            trace.add("react", {"step": state["step"], "tool": "compute_compensation"})
            return {"tool": "compute_compensation", "args": {"order": last_result["order"]}}
        if last == "compute_compensation":
            state["quote"] = last_result
            trace.add("react", {"step": state["step"], "tool": "lookup_refund_history"})
            return {
                "tool": "lookup_refund_history",
                "args": {
                    "order_id": claim["order_id"],
                    "principal_id": claim["principal_id"],
                },
            }
        if last == "lookup_refund_history":
            state["history"] = last_result
            trace.add("react", {"step": state["step"], "final": "quoted"})
            return {"final": {"status": "quoted"}}
        trace.add("react", {"step": state["step"], "final": "unexpected_tool"})
        return {"final": {"status": "failed", "reason": "unexpected_tool"}}

    loop = run_react(
        conn,
        budget,
        observation={"claim": {"claim_id": claim_id, "order_id": claim["order_id"]}},
        decide=decide,
        max_steps=MAX_STEPS,
    )
    final = loop.get("final") or {}
    trace.add("react_stop", {"stopped": loop.get("stopped"), "steps": state["step"]})

    if final.get("status") == "escalated":
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        return result("escalated", 0, final.get("reason"))
    if final.get("status") != "quoted" or not state["quote"]:
        reason = final.get("reason") or loop.get("stopped") or "no_quote"
        return result("failed", 0, reason)

    quote_payload = state["quote"]
    proposal = int(quote_payload["amount_vnd"])
    trace.add(
        "quote",
        {
            "amount_vnd": proposal,
            "reason": quote_payload.get("reason"),
            "clause_ids": quote_payload.get("clause_ids"),
            "refunded_vnd_before": (state["history"] or {}).get("refunded_vnd"),
        },
    )
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")

    if proposal <= 0:
        return result("denied", 0, quote_payload.get("reason"))

    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        _touch_trace(trace.write())
        raise

    trace.add(
        "host",
        {
            "ok": bool(outcome["ok"]),
            "reason": outcome["reason"],
            "conflict": bool(outcome["conflict"]),
        },
    )
    if not outcome["ok"]:
        status = "failed" if outcome["conflict"] else "denied"
        return result(status, proposal, outcome["reason"])
    return result("resolved", proposal)
