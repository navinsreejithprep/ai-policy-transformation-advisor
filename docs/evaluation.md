# Evaluation

## What is measured, and how

`python -m app.evaluation.run` (from `backend/`) runs the 15 hand-written test cases in
`app/evaluation/testset.json` against whatever is currently in the vector store and computes:

- **Hit rate @ K** (K=5): did a chunk from an expected document appear in the top K results?
- **Mean reciprocal rank**: how highly was the first correct hit ranked, averaged over the positive
  cases (1.0 = always rank 1)
- **Negative-control accuracy**: for a query with no relevant document in the corpus at all
  ("quantum computing supply chain logistics" — not a topic in this KB), did retrieval correctly return
  nothing above the relevance threshold, rather than forcing an irrelevant top-k result?
- **Mean latency**: wall-clock time per `retrieve_evidence()` call

This deliberately only measures **retrieval**, not generation. See "Why not an automated groundedness
score" below.

## Actual results (this demo corpus, this test set, run 2026-09-27)

```json
{
  "top_k": 5,
  "num_positive_cases": 14,
  "num_negative_cases": 1,
  "hit_rate_at_k": 1.0,
  "mean_reciprocal_rank": 0.929,
  "negative_control_accuracy": 1.0,
  "mean_latency_ms": 748.3
}
```

**Read this correctly**: this is retrieval performance on **8 documents, 27 chunks, and 15 questions I
wrote myself knowing exactly what was in the corpus**. A hit-rate of 1.0 here says the retrieval pipeline
works correctly and the relevance threshold isn't so aggressive that it drops real matches — it says
nothing about retrieval quality on a real, larger, messier knowledge base with adversarial or ambiguous
queries. The negative-control case shows the relevance threshold does its job (no forced irrelevant
result), which matters more than the hit-rate number at this corpus size.

The `mean_latency_ms` figure includes local sentence-transformers embedding + ChromaDB query on a single
developer machine — not representative of a production deployment's latency under load.

Re-run it yourself after changing the corpus, the embedding model, or the relevance threshold:

```bash
cd backend && source .venv/bin/activate && python -m app.evaluation.run
```

## Why not an automated "groundedness" or "hallucination rate" score

A common pattern is to have a second LLM call grade the first LLM's output for groundedness and report a
percentage. This project deliberately does not ship that, for two reasons: (1) it would be a fabricated-
feeling precision on a demo corpus this small — a single-digit sample size dressed up as a percentage —
and the brief for this project is explicit about not overclaiming metrics; (2) it doubles LLM cost for a
metric whose main value (catching an ungrounded claim) is already partially covered by the Independent
Challenge Reviewer agent, whose `ReviewResult.issues` are logged and shown in the UI as a real signal of
which analyses needed correction.

**Manual protocol actually used during development**: for each full pipeline run, read the Evidence tab
and check that every citation's document/page actually appears in `backend/knowledge_base/`, and that
`evidence_gaps` is non-empty when a claim genuinely has no support in the corpus (verified during
development — see the real revision-loop trigger observed in a live run, logged in
`backend/logs/app.log`). This is "not yet measured" as an automated metric — described here as a design
choice and a manual process, not glossed over.

## What would a production evaluation add

- A larger, held-out test set not authored with knowledge of the corpus
- Automated citation-validity checking against the *agents'* actual output (not just raw retrieval),
  i.e. verifying every `SourceCitation` in a generated `FinalReport` really matches a chunk in the store
- Separate retrieval-quality and generation-quality dashboards tracked over time as the corpus grows
- Cost and token-usage tracking per analysis run (currently only latency is logged)
