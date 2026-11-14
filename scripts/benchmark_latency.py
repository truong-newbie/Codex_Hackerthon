"""
ShiftLens Latency Benchmark Script (NFR-10 Verification)
Executes N (default=10) full E2E runs (Compiler -> Simulator -> Evaluator)
and computes Min, Mean, P50 (Median), P95, and Max latency in milliseconds.
"""
import os
import sys
import time
import statistics
import argparse
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Benchmark data must never be written into an operator's configured database.
_isolated_dir = tempfile.TemporaryDirectory(prefix="shiftlens-benchmark-")
_db_path = (Path(_isolated_dir.name) / "benchmark.db").resolve()
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path.as_posix()}"
os.environ["ENVIRONMENT"] = "test"
os.environ["AI_MODE"] = "stub"

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
from app.seed import seed_database

def percentile(data, p):
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_data) - 1)
    if f == c:
        return float(sorted_data[int(k)])
    return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)

def run_benchmark(runs: int = 10):
    Base.metadata.create_all(bind=engine)
    seed_database()
    client = TestClient(app)

    health = client.get("/v1/health").json()
    ai_mode = health.get("ai_mode", "stub")
    live_ready = health.get("live_ready", False)

    print(f"=== ShiftLens NFR-10 Latency Benchmark ({runs} Runs) ===")
    print(f"AI_MODE: {ai_mode.upper()} | LIVE_READY: {live_ready}\n")

    login_res = client.post("/v1/auth/login", json={
        "username_or_email": "emp_a",
        "password": "ShiftLens@2026"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    compiler_latencies = []
    simulator_latencies = []
    evaluator_latencies = []

    for i in range(1, runs + 1):
        # 1. Start (Compiler)
        t0 = time.perf_counter()
        s_res = client.post("/v1/training/start", headers=headers, json={"sop_id": "sop-complaint-a"})
        c_ms = (time.perf_counter() - t0) * 1000
        assert s_res.status_code == 200, f"Start failed on run {i}: {s_res.text}"
        session_id = s_res.json()["session_id"]
        compiler_latencies.append(c_ms)

        # 2. Turn (Simulator)
        t0 = time.perf_counter()
        t_res = client.post(
            f"/v1/training/{session_id}/turn",
            headers=headers,
            json={"message": "Dạ em rất xin lỗi anh về ly cà phê này ạ. Em kiểm tra hóa đơn rồi đổi ly mới hoặc báo quản lý hỗ trợ anh ngay ạ."}
        )
        s_ms = (time.perf_counter() - t0) * 1000
        assert t_res.status_code == 200, f"Turn failed on run {i}: {t_res.text}"
        simulator_latencies.append(s_ms)

        # 3. Evaluate (Evaluator + Deterministic Scoring)
        t0 = time.perf_counter()
        e_res = client.post(f"/v1/training/{session_id}/evaluate", headers=headers)
        e_ms = (time.perf_counter() - t0) * 1000
        assert e_res.status_code == 200, f"Evaluate failed on run {i}: {e_res.text}"
        evaluator_latencies.append(e_ms)

        print(f"Run #{i:02d}/{runs}: Compiler={c_ms:.1f}ms | Simulator={s_ms:.1f}ms | Evaluator={e_ms:.1f}ms | Score={e_res.json()['score']}/100")

    print("\n### Bảng Tổng Hợp Độ Trễ (NFR-10 Benchmark Summary)")
    print("| Module | Số lượt (Runs) | Mean (ms) | P50 / Median (ms) | P95 (ms) | Max (ms) |")
    print("| :--- | :---: | :---: | :---: | :---: | :---: |")
    for name, arr in [
        ("1. AI Compiler (`/start`)", compiler_latencies),
        ("2. Customer Simulator (`/turn`)", simulator_latencies),
        ("3. Evidence Evaluator (`/evaluate`)", evaluator_latencies),
    ]:
        mean_v = statistics.mean(arr)
        p50_v = percentile(arr, 50)
        p95_v = percentile(arr, 95)
        max_v = max(arr)
        print(f"| {name} | {runs} | {mean_v:.1f} | {p50_v:.1f} | **{p95_v:.1f}** | {max_v:.1f} |")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark isolated ShiftLens flows using stub AI")
    parser.add_argument("--runs", type=int, default=10)
    args = parser.parse_args()
    if not 1 <= args.runs <= 100:
        parser.error("--runs must be between 1 and 100")
    try:
        run_benchmark(args.runs)
    finally:
        _isolated_dir.cleanup()
