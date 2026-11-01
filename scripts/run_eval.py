"""Call the Dify Chatflow API for selected cases and save only observed fields."""
import argparse
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_env_file():
    path = ROOT / ".env"
    if not path.exists(): return
    for line in path.read_text(encoding="utf-8").splitlines():
        line=line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        key,value=line.split("=",1)
        os.environ.setdefault(key.strip(),value.strip().strip("\"'"))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case-id",action="append",default=[],help="Case ID; repeat to choose a small batch")
    ap.add_argument("--limit",type=int,default=3,help="Maximum cases when --case-id is omitted (default: 3)")
    ap.add_argument("--timeout",type=int,default=120)
    args=ap.parse_args(); load_env_file()
    base=os.getenv("DIFY_BASE_URL", "http://localhost/v1").rstrip("/")
    key=os.getenv("DIFY_API_KEY", "").strip()
    user=os.getenv("DIFY_USER_ID", "enterprise-support-demo")
    if not key or key.startswith("replace-"):
        raise SystemExit("Missing DIFY_API_KEY. Copy .env.example to .env and set a local app key.")
    cases=json.loads((ROOT/"data/eval_cases.json").read_text(encoding="utf-8"))["cases"]
    by_id={c["id"]:c for c in cases}
    unknown=[cid for cid in args.case_id if cid not in by_id]
    if unknown: raise SystemExit("Unknown case ID(s): "+", ".join(unknown))
    selected=[by_id[cid] for cid in args.case_id] if args.case_id else cases[:max(0,args.limit)]
    endpoint=base+"/chat-messages"; records=[]
    for case in selected:
        body=json.dumps({"inputs":{},"query":case["query"],"response_mode":"blocking","conversation_id":"","user":user},ensure_ascii=False).encode("utf-8")
        req=urllib.request.Request(endpoint,data=body,headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
        start=time.perf_counter(); status="error"; answer=""; evidence=None; error_type=None
        try:
            with urllib.request.urlopen(req,timeout=args.timeout) as resp:
                payload=json.loads(resp.read().decode("utf-8")); status="success"
            answer=payload.get("answer", "")
            meta=payload.get("metadata") or {}
            raw=meta.get("retriever_resources")
            if isinstance(raw,list):
                evidence=[{"rank":i+1,"source_id":x.get("document_id") or x.get("document_name"),"content":x.get("content"),"score":x.get("score")} for i,x in enumerate(raw)]
        except urllib.error.HTTPError as exc:
            status="error"; error_type=f"http_{exc.code}"
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            status="error"; error_type=type(exc).__name__
        elapsed=round((time.perf_counter()-start)*1000,2)
        records.append({"run_id":"dify-api-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"),"app_version":"api-current","case_id":case["id"],"input":case["query"],"output":answer or None,"workflow_status":status,"retrieved_evidence":evidence,"route":None,"tool_calls":None,"executed_actions":None,"unauthorized_action_count":None,"latency_ms":elapsed,"node_latencies_ms":[],"judgments":{"task_success":"unmeasured","grounded_answer":"unmeasured","no_answer_correct":"unmeasured","judgment_source":"Dify API response captured; no automatic semantic judge applied."},"error_types":[error_type] if error_type else [],"capture_note":"Only fields returned by the Dify API were recorded. Missing route/tool/action telemetry stays unmeasured."})
        print(f"{case['id']}: {status}, {elapsed} ms")
    out=ROOT/"reports/live_runs.json"
    existing=json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"is_demo":True,"runs":[]}
    existing["runs"].extend(records); existing["count"]=len(existing["runs"])
    out.write_text(json.dumps(existing,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Saved {len(records)} run(s) to {out}")

if __name__=="__main__": main()
