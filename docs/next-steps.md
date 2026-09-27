# Recommended next steps

Superseded by [README.md §14-15](../README.md) (Limitations / Future improvements), which reflects the
current implementation. Kept here only as a pointer so old links don't 404.

Short version of what's still open:

1. Persist job state (Redis/Postgres) instead of in-memory.
2. Add hybrid (BM25 + vector) retrieval and reranking.
3. Independently re-verify agent-generated citations against the vector store (currently prompt-constrained
   only, not code-verified — see docs/interview-guide.md Q9).
4. Add authentication and document-level access controls before using sensitive data.
5. Automated generation-quality (groundedness) scoring — see docs/evaluation.md for why this wasn't
   added yet and what a real version would need.
