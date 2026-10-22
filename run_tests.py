import csv
import json
import statistics
import time
from pathlib import Path
from app import classify

rows = list(csv.DictReader(open(Path(__file__).parent / "test_queries.csv", encoding="utf-8")))
results=[]
for row in rows:
    start=time.perf_counter(); out=classify(row["query"]); elapsed=(time.perf_counter()-start)*1000
    results.append({**row, **out, "elapsed_ms": round(elapsed,3), "correct": out["intent"]==row["expected_intent"]})
correct=sum(r["correct"] for r in results)
summary={"test_queries":len(results),"correct":correct,"accuracy":round(correct/len(results),3),"average_response_ms":round(statistics.mean(r["elapsed_ms"] for r in results),3),"results":results}
(Path(__file__).parent/"test_results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps({k:summary[k] for k in ["test_queries","correct","accuracy","average_response_ms"]}, indent=2))
