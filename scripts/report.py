"""Summarize saved Dify traces and compare versions without inferring missing data."""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def rate(values):
    scored = [v for v in values if v in ("pass", "fail", "partial")]
    return f"{sum(v == 'pass' for v in scored)}/{len(scored)}" if scored else "未测量"

def source_id(item):
    return str(item.get("source_id") or item.get("file") or item.get("document_name") or "").upper()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--compare", nargs=2, metavar=("LEFT", "RIGHT"), default=None)
    args = ap.parse_args()
    history = ROOT / "reports/evaluation_runs.json"
    payload = json.loads(history.read_text(encoding="utf-8")) if history.exists() else {"runs": []}
    rows = payload.get("runs", [])
    live = ROOT / "reports/live_runs.json"
    if live.exists(): rows += json.loads(live.read_text(encoding="utf-8")).get("runs", [])
    case_rows = json.loads((ROOT / "data/eval_cases.json").read_text(encoding="utf-8"))["cases"]
    cases = {c["id"]: c for c in case_rows}
    by_version = defaultdict(list); by_category = defaultdict(list); latest = {}
    def hit3(run):
        case = cases.get(run.get("case_id"), {})
        required = case.get("required_evidence") or []
        evidence = run.get("retrieved_evidence")
        if not required or not isinstance(evidence, list): return None
        sources = [source_id(e) for e in evidence if isinstance(e, dict) and int(e.get("rank", 999)) <= 3]
        return any(any(str(req).upper() in src for src in sources) for req in required)
    def route_judgment(run):
        actual = run.get("route")
        expected = cases.get(run.get("case_id"), {}).get("expected", {}).get("route")
        return ("pass" if actual == expected else "fail") if actual is not None and expected is not None else None
    def tool_judgment(run):
        actual = run.get("tool_calls")
        expected = cases.get(run.get("case_id"), {}).get("expected", {}).get("tool")
        if actual is None or expected is None: return None
        if isinstance(actual, list): actual = actual[0].get("name") if actual and isinstance(actual[0], dict) else actual
        return "pass" if actual == expected else "fail"
    for run in rows:
        version = run.get("app_version", "unknown"); case_id = run.get("case_id")
        run["_hit3"] = ("pass" if hit3(run) else "fail") if hit3(run) is not None else None
        run["_route"] = route_judgment(run); run["_tool"] = tool_judgment(run)
        by_version[version].append(run)
        by_category[(version, cases.get(case_id, {}).get("category", "unknown"))].append(run)
        latest[(version, case_id)] = run
    compare = args.compare or (("v7.10", "v7.11") if "v7.10" in by_version and "v7.11" in by_version else None)
    lines = ["# Evaluation Summary", "", f"- Test specifications: {len(case_rows)}", f"- Saved run records: {len(rows)}", "- Missing API telemetry remains unmeasured; final text is not used to infer tool execution.", "- Live Dify API runs are appended from reports/live_runs.json when present.", "", "## By version", "", "| Version | Runs | Task | Evidence Hit@3 | Grounded | No-answer | Route | Tool | Unauthorized actions | Client latency P50/P95 |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for version, runs in sorted(by_version.items()):
        task = [r.get("judgments", {}).get("task_success") for r in runs]
        evidence = [r.get("_hit3") for r in runs]
        grounded = [r.get("judgments", {}).get("grounded_answer") for r in runs]
        no_answer = [r.get("judgments", {}).get("no_answer_correct") for r in runs]
        routes = [r.get("_route") for r in runs]
        tools = [r.get("_tool") for r in runs]
        unauthorized = [r.get("unauthorized_action_count") for r in runs if isinstance(r.get("unauthorized_action_count"), int)]
        times = sorted(r["latency_ms"] for r in runs if isinstance(r.get("latency_ms"), (int, float)))
        latency = f"{times[math.ceil(.50*len(times))-1]}/{times[math.ceil(.95*len(times))-1]} ms" if times else "未测量"
        ua = str(sum(unauthorized)) if unauthorized else "未测量"
        lines.append(f"| {version} | {len(runs)} | {rate(task)} | {rate(evidence)} | {rate(grounded)} | {rate(no_answer)} | {rate(routes)} | {rate(tools)} | {ua} | {latency} |")
    lines += ["", "## By case category", "", "| Version | Category | Runs | Task success |", "|---|---|---:|---:|"]
    for (version, category), runs in sorted(by_category.items()):
        lines.append(f"| {version} | {category} | {len(runs)} | {rate([r.get('judgments', {}).get('task_success') for r in runs])} |")
    if compare:
        left, right = compare
        lines += ["", f"## Comparison: {left} vs {right}", "", f"| Case | Category | {left} | {right} |", "|---|---|---|---|"]
        shared = sorted(cid for ver, cid in latest if ver == left and (right, cid) in latest)
        for cid in shared:
            l = latest[(left, cid)].get("judgments", {}).get("task_success", "unmeasured")
            r = latest[(right, cid)].get("judgments", {}).get("task_success", "unmeasured")
            lines.append(f"| {cid} | {cases.get(cid, {}).get('category', 'unknown')} | {l} | {r} |")
        if not shared: lines.append("| — | — | 无共有案例 | 无共有案例 |")
    lines += ["", "## Errors and review", "", "| Version | Category | Case | Status | Error types | Review note |", "|---|---|---|---|---|---|"]
    found = False
    for run in rows:
        status = run.get("judgments", {}).get("task_success")
        if run.get("error_types") or status in ("fail", "partial"):
            found = True; note = (run.get("review_note") or "").replace("|", "/").replace("\n", " ")
            lines.append(f"| {run.get('app_version')} | {cases.get(run.get('case_id'), {}).get('category', 'unknown')} | {run.get('case_id')} | {status or 'unmeasured'} | {', '.join(run.get('error_types', [])) or '需人工分类'} | {note} |")
    if not found: lines.append("| — | — | — | — | — | 当前捕获运行没有显式失败/部分通过标签。 |")
    lines += ["", "## Metric limits", "", "- Evidence Hit@3 is scored only when ranked retrieved evidence and expected evidence are available.", "- Grounded Answer Rate requires a documented human or judge label.", "- Routing/tool accuracy and unauthorized writes require actual execution telemetry; final answers are not evidence.", "- Latency is client-observed API duration, not internal Dify node duration.", ""]
    target = ROOT / "reports/evaluation.md"; target.write_text("\n".join(lines), encoding="utf-8"); print(target)

if __name__ == "__main__": main()
