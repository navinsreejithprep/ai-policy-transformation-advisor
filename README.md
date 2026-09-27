# AI Policy & Transformation Advisor

A portfolio proof-of-concept combining **RAG + CrewAI + multi-agent analysis** for policy/programme
implementation — built as a demonstration of applied GenAI + consulting-style problem solving, not a
production system.

> **This is a portfolio POC.** Numbers quoted anywhere in this repo (retrieval hit-rate, latency, etc.)
> come from a real run against the small synthetic demo knowledge base described below. They are not
> a claim about performance on real documents, at scale, or in production. See
> [docs/evaluation.md](docs/evaluation.md) for exactly how they were computed.

## 1. Project overview

Given a policy/programme document and a knowledge base of supporting evidence, the system:

1. Extracts the policy's objectives, mechanisms, target groups and assumptions
2. Retrieves supporting/contradictory evidence with RAG, citing document + page
3. Maps stakeholders on an influence/interest basis
4. Builds a risk register across strategic/operational/financial/regulatory/technology/data/adoption/execution categories
5. Benchmarks comparable programmes found in the knowledge base
6. Produces a 90-day plan and 12-month roadmap linked back to the evidence, risks and stakeholders
7. Independently challenges the whole analysis and triggers a bounded revision loop
8. Synthesizes everything into a structured executive report with source citations

## 2. Business problem

A government department, enterprise or consulting team receiving a new policy/programme document needs
a structured, evidence-grounded first-pass analysis before committing resources: what is this trying to
achieve, what does the evidence actually support, who needs to be engaged, what could go wrong, and what
should happen in the first 90 days. Doing this manually is slow and inconsistent; asking a single LLM
prompt to do all of it at once produces plausible-sounding but ungrounded and unstructured output. This
project demonstrates a middle path: specialized agents, each grounded in retrieved evidence, producing
structured output that a human can verify claim-by-claim.

## 3. Why multi-agent?

The analysis has genuinely distinct responsibilities — interpreting a policy, retrieving evidence,
reading stakeholder dynamics, assessing risk, benchmarking, planning, and *critiquing* — each requiring
different instructions, different grounding, and different failure modes to guard against. Splitting
these into separate agents with `output_pydantic` contracts (see `app/models/schemas.py`) means every
hand-off between agents is validated structured data, not a hopeful re-parse of free text, and each
agent's output is independently inspectable. Critically, the **Challenge Agent** is a genuinely separate
agent whose only job is to find fault with the other six — see [docs/agent-design.md](docs/agent-design.md)
for why this isn't "one prompt in seven trenchcoats."

## 4. Why CrewAI?

CrewAI gives structured `Agent`/`Task` primitives, an LLM-provider-agnostic model string
(`openai/gpt-4o-mini`, or swap to `anthropic/...` via one config flag — see §10), and `output_pydantic`
support that does the JSON-schema-constrained generation and validation for us. This project deliberately
does **not** use CrewAI's own `Crew.kickoff()` sequential orchestration for the main pipeline — see
"Why manual orchestration" in [docs/architecture.md](docs/architecture.md) for why the revision loop
needed more control than CrewAI's built-in sequential process gives.

## 5. Why RAG?

The agents need grounded access to policy and programme evidence — a general-purpose LLM has no
knowledge of *this* programme's specific evidence base, and asking it to "just know" comparable
programmes or risk precedents invites fabrication. RAG (chunk → embed → ChromaDB → semantic retrieval)
supplies real, citable passages, and every agent is explicitly instructed to say
`"Insufficient evidence in the available knowledge base."` rather than invent a citation.

## 6. Architecture

```text
Policy text
    |
    v
Policy Analyst  --------------------------------------------------+
    |  (objectives, assumptions -> retrieval queries)              |
    v                                                               |
Evidence Analyst <---- retrieve_evidence() <---- ChromaDB <---- ingest (PDF/TXT/MD)
    |                                                               |
    v                                                               |
Stakeholder Analyst -> Risk Analyst -> Benchmark Analyst -> Implementation Strategist
    |                                                               |
    v                                                               |
Independent Challenge Reviewer  --(NEEDS_REVISION, up to 2 cycles)--+
    |  (PASS)
    v
Synthesis Advisor (executive summary only — everything else assembled
    |               deterministically in code from the structured outputs above)
    v
FinalReport (Pydantic) -> FastAPI job store -> Next.js dashboard
```

Full write-up: [docs/architecture.md](docs/architecture.md). Agent-by-agent detail:
[docs/agent-design.md](docs/agent-design.md). RAG pipeline detail: [docs/rag-design.md](docs/rag-design.md).

## 7. Agents

| # | Agent | Job |
|---|---|---|
| 1 | Policy Analyst | Extract objectives, mechanisms, target groups, assumptions from the raw text only |
| 2 | Evidence Analyst | Find supporting/contradictory evidence via RAG; cite or say evidence is missing |
| 3 | Stakeholder Analyst | Build an influence/interest stakeholder matrix; mark inferred positions |
| 4 | Risk Analyst | Build a qualitative risk register across 8 categories with mitigations |
| 5 | Benchmark Analyst | Find comparable programmes in the KB; don't overclaim comparability |
| 6 | Implementation Strategist | 90-day plan + 12-month roadmap, every item linked to prior analysis |
| 7 | Independent Challenge Reviewer | Attacks the other six agents' output; triggers revision |
| — | Synthesis Advisor | Writes only the executive summary — everything else is code-assembled |

## 8. Tech stack

- **Backend**: Python, FastAPI, Pydantic v2, CrewAI, OpenAI API (Anthropic swappable via config)
- **RAG**: sentence-transformers embeddings, ChromaDB, PyMuPDF (PDF), plain-text/Markdown ingestion
- **Frontend**: Next.js 15, TypeScript, Tailwind CSS (no chart library — visualizations are hand-built
  SVG/CSS so the stack stays small; see `frontend/components/report/`)
- **Tests**: pytest (backend), `tsc --noEmit` + `next build` (frontend)

## 9. Installation

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt   # requirements.txt + pytest
cp .env.example .env
```

Add your `OPENAI_API_KEY` to `backend/.env`.

```bash
cd ../frontend
npm install
cp .env.local.example .env.local   # only needed if the backend isn't on localhost:8000
```

## 10. Environment variables

See `backend/.env.example` for the full list. The important ones:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | LLM credentials |
| `LLM_PROVIDER` | `openai` (default) or `anthropic` — see `app/agents/definitions.py` |
| `KNOWLEDGE_BASE_PATH` | Where PDFs/TXT/MD are read from and uploads are saved (default `./knowledge_base`, relative to the backend process's working directory) |
| `TOP_K_DEFAULT`, `RETRIEVAL_RELEVANCE_THRESHOLD` | Retrieval tuning |
| `REVISION_MAX_CYCLES` | Hard cap on the challenge/revision loop (default 2) |
| `MAX_UPLOAD_MB` | Upload size limit |

## 11. Running locally

```bash
# Terminal 1
cd backend && source .venv/bin/activate && python -m app.main
# Terminal 2
cd frontend && npm run dev
```

Backend: `http://localhost:8000` (docs at `/docs`). Frontend: `http://localhost:3000`.

On first startup, if the vector store is empty, the backend automatically ingests everything in
`backend/knowledge_base/` (including the 8-document synthetic demo corpus) — no manual setup required.
Click "Load demo policy" in the UI, then "Run Advisory Analysis."

## 12. Example workflow

1. Open `http://localhost:3000`. The Knowledge Base panel shows the auto-seeded demo documents.
2. Click **Load demo policy**, then **Run Advisory Analysis**.
3. Watch the 8-stage progress indicator (the pipeline runs asynchronously — `POST /analysis/start`
   returns a job id immediately; the UI polls `GET /analysis/{id}` every 2s).
4. When complete, browse the report tabs: Executive Summary, Evidence, Stakeholders (with an
   influence/interest matrix), Risks (with a heatmap), Benchmarks, Roadmap, KPIs, Sources (click a
   citation to see the retrieved passage).
5. Upload a real PDF via the Knowledge Base panel, or delete the demo documents once you have real
   evidence — see `backend/knowledge_base/demo/README.md`.

## 13. Evaluation

`python -m app.evaluation.run` runs 15 hand-written retrieval queries against whatever is currently in
the vector store and reports hit-rate@k, mean reciprocal rank, a negative-control check, and latency —
see [docs/evaluation.md](docs/evaluation.md) for the actual numbers from the demo corpus and why
*generation*-quality (groundedness, hallucination) is evaluated manually rather than with a fabricated
automated score.

## 14. Limitations

- **Design choice, not a framework limitation**: the revision loop is orchestrated in application code
  (`app/crew/runner.py`), not via CrewAI's `Process.hierarchical` — see docs/architecture.md for why.
- Retrieval is pure dense/cosine search — no hybrid BM25+vector, no reranking.
- The vector store is a single local ChromaDB instance; there's no multi-tenant or access-control layer,
  which matters a great deal before this could touch real confidential government data.
- Job state lives in an in-memory dict (`app/services/jobs.py`) — it does not survive a backend restart
  and doesn't work across multiple backend workers. **Design choice**, acceptable for a POC.
- Evaluation numbers are for a 7-document synthetic corpus and 15 questions — **not yet measured** on
  real, larger, or messier documents.
- No authentication on any endpoint. Not yet measured against adversarial prompt injection beyond the
  basic instruction included in each agent's prompt (see `PROMPT_INJECTION_GUARD` in `app/crew/tasks.py`).

## 15. Future improvements

- Hybrid retrieval + reranking; document-level access control
- Persist job state (Redis/Postgres) so it survives restarts and works across workers
- Real automated groundedness scoring for generation quality, not just retrieval metrics
- Authentication and per-document access control before using confidential data
- Streaming progress (SSE/WebSocket) instead of polling

## Demo data

`backend/knowledge_base/demo/` contains 8 clearly labelled **DEMO DATA — NOT REAL POLICY EVIDENCE**
synthetic documents describing a fictional programme. See its own README for what each file is for and
how to replace it with real evidence.

## AI-generated analysis

The UI displays this on every report: **"AI-generated analysis — verify critical decisions against
primary sources."** Treat every output as a first-pass draft, not a final answer.
