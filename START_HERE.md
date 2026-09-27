# START HERE

## 1. Open this folder in VS Code

Open `ai-policy-transformation-advisor`.

## 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt   # requirements.txt + pytest
cp .env.example .env
```

Put your API key in `.env`.

Then:

```bash
python -m app.main
```

## 3. Frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

## 4. Run the tests and evaluation

```bash
cd backend && source .venv/bin/activate
python -m pytest -q
python -m app.evaluation.run
```

## 5. Before your interview

Read:
- docs/architecture.md
- docs/agent-design.md
- docs/rag-design.md
- docs/evaluation.md
- docs/interview-guide.md

Then replace the demo knowledge base with real public documents and actually test the system.
