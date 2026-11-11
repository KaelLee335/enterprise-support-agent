"""Read-only adapters for saved evaluation JSON and CSV."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_evaluation(results_path: Path | None = None, errors_path: Path | None = None) -> dict[str, Any]:
    results_path = results_path or PROJECT_ROOT / "reports/evaluation_results.json"
    errors_path = errors_path or PROJECT_ROOT / "reports/eval_errors.csv"
    if not results_path.exists():
        raise FileNotFoundError(f"评估 JSON 不存在：{results_path}")
    if not errors_path.exists():
        raise FileNotFoundError(f"错误案例 CSV 不存在：{errors_path}")
    data = json.loads(results_path.read_text(encoding="utf-8"))
    with errors_path.open(encoding="utf-8-sig", newline="") as handle:
        errors = list(csv.DictReader(handle))
    return {"data": data, "errors": errors}


def format_rate(metric: dict[str, Any] | None) -> str:
    if not isinstance(metric, dict) or metric.get("rate") is None:
        return "未测量"
    return f"{metric['rate']:.1%} ({metric.get('passed', 0)}/{metric.get('measured', 0)})"


def metric_summary(version_data: dict[str, Any]) -> dict[str, str]:
    latency = version_data.get("latency_ms") or {}
    p50, p95 = latency.get("p50"), latency.get("p95")
    latency_text = f"P50 {p50:g} ms · P95 {p95:g} ms" if p50 is not None and p95 is not None else "未测量"
    unauthorized = version_data.get("unauthorized_action_count")
    return {
        "task_success": format_rate(version_data.get("task_success_rate")),
        "evidence_hit": format_rate(version_data.get("evidence_hit_at_3")),
        "tool_accuracy": format_rate(version_data.get("tool_accuracy")),
        "grounded_answer": format_rate(version_data.get("grounded_answer_rate")),
        "latency": latency_text,
        "unauthorized_actions": str(unauthorized) if unauthorized is not None else "未测量",
    }
