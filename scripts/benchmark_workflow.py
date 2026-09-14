import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import json
import platform
import statistics
import time
from pathlib import Path

from starlette.testclient import TestClient

from src.api.main import app

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EMPLOYEE_HEADERS = {"Authorization": "Bearer token-employee-dev"}
MANAGER_HEADERS = {"Authorization": "Bearer token-manager-ops"}


def run_benchmark(iterations: int = 100) -> dict:
    print(f"=== Enterprise Workforce Agents: Benchmark Harness ({iterations} iterations) ===")
    client = TestClient(app)

    latencies_query = []
    latencies_hitl = []

    # 1. Benchmark Query Workflow (Single Agent - Data)
    for _ in range(iterations):
        t0 = time.perf_counter()
        res = client.post(
            "/api/v1/tasks",
            json={"user_goal": "Analyze budget status for Engineering department"},
            headers=EMPLOYEE_HEADERS
        )
        dur = (time.perf_counter() - t0) * 1000.0
        assert res.status_code == 201
        latencies_query.append(dur)

    # 2. Benchmark Full Multi-Agent Workflow with HITL Gateway Pause & Resume
    for _ in range(min(50, iterations)):
        t0 = time.perf_counter()
        res = client.post(
            "/api/v1/tasks",
            json={"user_goal": "Purchase $12,000 server racks for Operations from RackCorp"},
            headers=EMPLOYEE_HEADERS
        )
        wf_id = res.json()["workflow_id"]
        # Human approval step
        appr_res = client.post(
            f"/api/v1/tasks/{wf_id}/approve",
            json={"decision": "APPROVE", "reason": "Benchmark run"},
            headers=MANAGER_HEADERS
        )
        dur = (time.perf_counter() - t0) * 1000.0
        assert appr_res.status_code == 200
        latencies_hitl.append(dur)

    latencies_query.sort()
    latencies_hitl.sort()

    def calc_stats(lats):
        return {
            "iterations": len(lats),
            "p50_ms": round(statistics.median(lats), 2),
            "p95_ms": round(lats[int(len(lats) * 0.95)], 2),
            "p99_ms": round(lats[int(len(lats) * 0.99)], 2),
            "mean_ms": round(statistics.mean(lats), 2),
            "min_ms": round(min(lats), 2),
            "max_ms": round(max(lats), 2),
            "std_ms": round(statistics.stdev(lats) if len(lats) > 1 else 0.0, 2)
        }

    report = {
        "metadata": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "query_workflow": calc_stats(latencies_query),
        "full_hitl_multiagent_workflow": calc_stats(latencies_hitl)
    }

    out_file = PROJECT_ROOT / "results" / "benchmark_report.json"
    out_file.parent.mkdir(exist_ok=True)
    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n" + "-" * 70)
    print(f"{'Workflow Type':<35} | {'p50 (Median)':<15} | {'p95':<12}")
    print("-" * 70)
    print(f"{'Single Agent Query Workflow':<35} | {report['query_workflow']['p50_ms']:<12} ms | {report['query_workflow']['p95_ms']:<9} ms")
    print(f"{'Full HITL Multi-Agent Requisition':<35} | {report['full_hitl_multiagent_workflow']['p50_ms']:<12} ms | {report['full_hitl_multiagent_workflow']['p95_ms']:<9} ms")
    print("-" * 70)
    print(f"[+] Benchmark report exported to: {out_file.relative_to(PROJECT_ROOT)}\n")
    return report


if __name__ == "__main__":
    run_benchmark()
