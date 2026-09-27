"""Retrieval evaluation.

Run with: python -m app.evaluation.run

What this measures (and only this — see docs/evaluation.md for why generation
quality is evaluated manually instead of with an automated LLM-graded metric):

- Hit rate @ K: did a chunk from an expected document appear in the top K results?
- Mean reciprocal rank: how highly was the first correct hit ranked?
- Negative-control accuracy: for queries with no relevant document in the corpus,
  did retrieval correctly return nothing above the relevance threshold?
- Latency: wall-clock time per query.

These numbers are specific to the 7-document synthetic demo corpus and this
15-question test set — they say nothing about retrieval quality on a different,
larger or real-world knowledge base. Do not quote them as general system accuracy.
"""
import json
import statistics
import time
from pathlib import Path

from ..rag.retrieve import retrieve_evidence

TESTSET_PATH = Path(__file__).parent / "testset.json"


def load_testset() -> list[dict]:
    return json.loads(TESTSET_PATH.read_text())


def evaluate(top_k: int = 5) -> dict:
    cases = load_testset()
    positive_cases = [c for c in cases if c["expected_documents"]]
    negative_cases = [c for c in cases if not c["expected_documents"]]

    hits_at_k = 0
    reciprocal_ranks = []
    latencies = []
    per_case_results = []

    for case in positive_cases:
        start = time.monotonic()
        rows = retrieve_evidence(case["query"], top_k=top_k)
        latencies.append(time.monotonic() - start)

        retrieved_docs = [r["document"] for r in rows]
        rank = next(
            (i + 1 for i, doc in enumerate(retrieved_docs) if doc in case["expected_documents"]),
            None,
        )
        hit = rank is not None
        hits_at_k += int(hit)
        reciprocal_ranks.append(1 / rank if hit else 0)
        per_case_results.append(
            {"query": case["query"], "expected": case["expected_documents"], "retrieved": retrieved_docs, "hit": hit, "rank": rank}
        )

    correct_rejections = 0
    for case in negative_cases:
        start = time.monotonic()
        rows = retrieve_evidence(case["query"], top_k=top_k)
        latencies.append(time.monotonic() - start)
        correctly_empty = len(rows) == 0
        correct_rejections += int(correctly_empty)
        per_case_results.append(
            {"query": case["query"], "expected": [], "retrieved": [r["document"] for r in rows], "hit": correctly_empty, "rank": None}
        )

    n_pos = len(positive_cases)
    n_neg = len(negative_cases)

    return {
        "top_k": top_k,
        "num_positive_cases": n_pos,
        "num_negative_cases": n_neg,
        "hit_rate_at_k": round(hits_at_k / n_pos, 3) if n_pos else None,
        "mean_reciprocal_rank": round(statistics.mean(reciprocal_ranks), 3) if reciprocal_ranks else None,
        "negative_control_accuracy": round(correct_rejections / n_neg, 3) if n_neg else None,
        "mean_latency_ms": round(statistics.mean(latencies) * 1000, 1) if latencies else None,
        "per_case_results": per_case_results,
    }


if __name__ == "__main__":
    results = evaluate()
    print(json.dumps(results, indent=2))
