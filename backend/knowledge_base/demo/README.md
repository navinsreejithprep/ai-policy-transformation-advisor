# Demo knowledge base

**DEMO DATA — NOT REAL POLICY EVIDENCE.**

Every file in this folder is synthetic content written for this project, describing
a fictional programme ("Digital Service Access Improvement Programme") and a
fictional country ("Estlandia") where a benchmark comparison is needed. None of it
describes a real government, agency, survey or programme. It exists so the
application is usable immediately without requiring you to source real documents
first.

| File | Fictional role |
|---|---|
| `demo_policy.txt` | The policy/programme document itself — paste its contents into the analysis input |
| `evidence_digital_literacy_survey.txt` | Evidence source: digital literacy / connectivity data |
| `benchmark_international_case_estlandia.txt` | Evidence source: comparable international programme |
| `risk_case_study_prior_rollout.txt` | Evidence source: a prior programme's implementation risks |
| `stakeholder_consultation_summary.txt` | Evidence source: stakeholder positions and concerns |
| `budget_and_funding_note.txt` | Evidence source: illustrative funding/governance model |
| `annual_report_2025_excerpt.txt` | Evidence source: reproduces a realistic paginated citation, e.g. `[Source: annual_report_2025_excerpt.txt, p. 43]` |
| `evaluation_pilot_program_outcomes.txt` | Evidence source: a prior pilot's KPIs and evaluation caveats |

These files are ingested automatically on first backend startup (see
`seed_demo_knowledge_base_if_empty` in `app/rag/ingest.py`) and are tagged
`is_demo_data: true` in the vector store, which the frontend uses to visually
mark demo-sourced citations as "DEMO" rather than as a real uploaded source.

## Replacing this with real documents

1. Upload real PDFs via `POST /documents/upload`, or drop `.pdf`/`.txt`/`.md`
   files anywhere under `knowledge_base/` and call `POST /documents/index` to
   rebuild the vector store from disk.
2. Real, uploaded documents are stored with `is_demo_data: false` automatically —
   no code changes needed to distinguish them.
3. Consider deleting the files in this folder (`DELETE /documents/{name}`) once
   you have real evidence, so the demo content doesn't dilute retrieval results.
