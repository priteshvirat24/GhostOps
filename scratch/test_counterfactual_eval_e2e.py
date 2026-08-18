import sys
import os
import json

# Ensure python path includes apps/api
sys.path.insert(0, os.path.abspath("apps/api"))

from app.db.session import SessionLocal
from app.services.evaluation.harness import AgentEvaluationHarness
from app.services.evaluation.golden_dataset import GoldenDatasetRegistry
from app.db.models.evaluation import EvaluationRun, EvaluationCaseResult
from sqlalchemy import select

def main():
    print("=" * 80)
    print("GhostOps Stage 10 Counterfactual Replay & Regression Evaluation Engine E2E Test")
    print("=" * 80)

    db = SessionLocal()
    try:
        # 1. Dataset Verification
        print("\n--- 1. GOLDEN DATASET VERIFICATION ---")
        dataset = GoldenDatasetRegistry.get_dataset()
        print(f"Dataset Version: {GoldenDatasetRegistry.DATASET_VERSION}")
        print(f"Total Benchmark Cases: {len(dataset)}")
        case_1847 = next((c for c in dataset if c.benchmark_id == "INC-1847"), None)
        assert case_1847 is not None, "Flagship Incident #1847 missing from dataset!"
        print(f"Flagship Incident #1847 Verified: {case_1847.incident_title}")

        # 2. Run Full Counterfactual Replay Benchmark
        print("\n--- 2. RUNNING COUNTERFACTUAL REPLAY BENCHMARK ---")
        result = AgentEvaluationHarness.run_benchmark(db)
        print(f"Evaluation Run ID: {result['evaluation_run_id']}")
        print(f"Execution Duration: {result['execution_duration_ms']} ms")
        print(f"Total Cases Evaluated: {result['total_benchmark_cases']}")

        # 3. Report Real Metrics
        print("\n--- 3. EMPIRICAL BENCHMARK METRICS ---")
        print(f"  Precision@1:             {result['precision_at_1']:.2%}")
        print(f"  Precision@3:             {result['precision_at_3']:.2%}")
        print(f"  Mean Reciprocal Rank:    {result['mrr']:.4f}")
        print(f"  Temporal Verdict Acc:    {result['temporal_verdict_accuracy']:.2%}")
        print(f"  Evidence Grounding:      {result['evidence_grounding_score']:.2%}")
        print(f"  Unsafe Replay Rate:      {result['unsafe_replay_rate']:.2%}")
        print(f"  False Execution Rate:    {result['false_execution_rate']:.2%}")

        # 4. Regression Gate Check
        print("\n--- 4. DETERMINISTIC REGRESSION GATE ---")
        print(f"Status: {result['status']}")
        print(f"Regression Gate Passed: {result['regression_gate_passed']}")
        for k, v in result['gate_details'].items():
            status_str = "PASS" if v['passed'] else "FAIL"
            print(f"  - {k}: value={v['value']}, threshold={v['threshold']} -> [{status_str}]")

        assert result['unsafe_replay_rate'] == 0.0, "Unsafe replays detected!"
        assert result['false_execution_rate'] == 0.0, "False execution detected!"
        assert result['regression_gate_passed'] is True, "Regression gate failed!"

        # 5. Flagship Incident #1847 Counterfactual Outcome
        print("\n--- 5. INCIDENT #1847 COUNTERFACTUAL VERIFICATION ---")
        c1847 = next((c for c in result['cases'] if c['benchmark_id'] == "INC-1847"), None)
        assert c1847 is not None
        print(f"  Actual Temporal Verdict: {c1847['actual_temporal_verdict']}")
        print(f"  Would Execute Today:     {c1847['would_execute']}")
        print(f"  Unsafe Execution:        {c1847['unsafe_execution']}")
        print(f"  Counterfactual Status:   {c1847['counterfactual_status']}")
        assert c1847['actual_temporal_verdict'] == "DO_NOT_EXECUTE", "Incident #1847 should be DO_NOT_EXECUTE!"
        assert c1847['would_execute'] is False, "Incident #1847 must not execute!"

        # 6. Database Persistence Verification
        print("\n--- 6. COCKROACHDB PERSISTENCE CHECK ---")
        run_in_db = db.get(EvaluationRun, result['evaluation_run_id'])
        assert run_in_db is not None, "Evaluation run not persisted in CockroachDB!"
        cases_in_db = db.scalars(
            select(EvaluationCaseResult).where(EvaluationCaseResult.evaluation_run_id == result['evaluation_run_id'])
        ).all()
        print(f"  Persisted EvaluationRun in CockroachDB: {run_in_db.id} (status: {run_in_db.status})")
        print(f"  Persisted Case Results in CockroachDB:  {len(cases_in_db)} records")
        assert len(cases_in_db) == len(dataset), "Case record count mismatch in CockroachDB!"

        print("\n" + "=" * 80)
        print("Stage 10 Counterfactual Replay & Regression Evaluation Engine: ALL CHECKS PASSED")
        print("=" * 80)

    finally:
        db.close()

if __name__ == "__main__":
    main()
