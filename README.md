# AppleSupport AI Support Agent

A demo support copilot for AppleSupport-style conversations. It combines LLM intent classification, FAISS retrieval over historical support examples, grounded reply generation, and escalation safeguards behind a FastAPI service and a Next.js triage dashboard.

## How it works

Each customer message passes through one pipeline:

1. `LLMClassifier` assigns one intent from `src/intent/taxonomy.json` using Groq.
2. `ReplyGenerator` retrieves similar examples from `models/embedding_index` and asks Groq for a grounded draft.
3. `EscalationDecider` applies confidence, safety/legal keyword, frustration, thread-length, and optional LLM checks.
4. Escalated cases suppress the draft from the customer-facing reply and are shown for human review.

The dashboard supports free-form messages, preset scenarios, a triage queue, retrieved-example inspection, and approve/edit/route-to-human override logging.

## Stack

- Backend: Python 3.10+, FastAPI, Uvicorn, Pydantic
- AI: Groq API with `openai/gpt-oss-20b`
- Retrieval: Sentence Transformers embeddings and FAISS CPU index
- Data and evaluation: pandas, NumPy, scikit-learn, custom metrics, LLM judge
- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS, Framer Motion, Lucide
- Deployment: Docker Compose with separate backend and frontend containers

## Repository layout

```text
hiver support agent/
api.py                         FastAPI application and REST endpoints
src/agent.py                   End-to-end SupportAgent orchestration
src/intent/                    Taxonomy, LLM classifier, and baselines
src/reply/                     Embeddings, FAISS retrieval, generation, baselines
src/escalation/                Hybrid escalation rules and baselines
data/golden_eval/              Golden evaluation set
data/processed/                Prepared AppleSupport conversation data
models/embedding_index/        FAISS index and retrieved-example metadata
eval/                          Evaluation harness, metrics, and LLM judge
frontend/                      Next.js triage dashboard
Dockerfile.backend             Backend image
docker-compose.yml             Full-stack local deployment
```

## Prerequisites

- Python 3.10 or newer
- Node.js 20 or newer and npm
- A Groq API key
- The embedding files `models/embedding_index/faiss.index` and `examples.json`

The embedding index is local/generated data and is ignored by Git. Make sure it exists before starting the backend. The raw dataset under `data/raw` is also ignored; the processed data and golden set included in the repository are enough to run the documented application and evaluation paths.

## Local setup

### 1. Backend

From the repository root, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a root `.env` file:

```dotenv
GROQ_API_KEY=your_groq_api_key
```

Start the API:

```powershell
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

The API is available at `http://localhost:8000`. Interactive OpenAPI documentation is at `http://localhost:8000/docs`.

### 2. Frontend

In a second terminal:

```powershell
cd frontend
npm ci
```

Create `frontend/.env.local` if the API is not running at the default address:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start the dashboard:

```powershell
npm run dev
```

Open `http://localhost:3000` and confirm the status bar reports a healthy backend. The frontend expects the backend to allow requests from `localhost:3000` or `127.0.0.1:3000`.

## Docker Compose

With `GROQ_API_KEY` in the root `.env`, start both services with:

```powershell
docker compose up --build
```

Then open `http://localhost:3000`. The backend listens on port `8000` and the frontend on port `3000`.

The Docker backend build excludes `models/embedding_index/*.index` through `.dockerignore`. Therefore, a production-ready image still needs an explicit index-volume or artifact step; otherwise the agent may start in a degraded state when the FAISS index is unavailable.

## API summary

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Report backend and agent load status |
| `GET` | `/api/presets` | Return demo scenarios |
| `POST` | `/api/process` | Classify, retrieve, draft, and decide escalation |
| `POST` | `/api/override` | Log an approve, edit, or human-routing action |

Example request:

```json
{
  "message": "My iPhone battery is swelling. What should I do?",
  "conversation_history": [],
  "ticket_id": null
}
```

`/api/process` returns a ticket ID, intent and confidence, generated/released reply, retrieved examples, escalation reasons, auto-handled status, and processing latency.

## Evaluation

Run the full benchmark from the repository root:

```powershell
python -m eval.harness
```

The harness reads `data/golden_eval/golden_set.json`, compares the main agent with random, TF-IDF, nearest-neighbor, keyword, and always-escalate baselines, and writes `eval/results/evaluation_results.json`. It reports intent accuracy and F1, BLEU-1-style word overlap, escalation precision/recall/F1, and an LLM-judge sample over 30 items. The LLM judge also requires `GROQ_API_KEY`.

For a lightweight syntax check:

```powershell
python -m compileall -q api.py src eval
```

For the frontend:

```powershell
cd frontend
npm run lint
npm run build
```

## Important limitations

- This is a local demo, not a production ticketing system. Tickets and override logs are held in process memory and disappear when the API restarts.
- Groq is required for classification, generation, and the nuanced escalation check. Model/API failures fall back to conservative local responses in some components, but should still be monitored.
- The system uses historical AppleSupport-style data from 2017; generated guidance should be reviewed before real customer use.
- The evaluation harness makes live LLM calls and can incur provider latency or cost.
- The current CORS policy only allows the two local frontend origins.

## Supporting documents

- [EVALUATION_REPORT.md](EVALUATION_REPORT.md) contains the recorded evaluation summary.
- [decision_log.md](decision_log.md) records project decisions and trade-offs.
- [frontend/README.md](frontend/README.md) contains the generated Next.js starter notes.
