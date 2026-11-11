<p align="center">
  <img src="docs/veritas-social-preview.png" alt="veritas: research, verified" width="720">
</p>

<p align="center">
  <b>Paste a claim. Watch five AI agents check it against the live web.</b>
</p>
---

## What is veritas?

veritas is a multi-agent fact-checking system. You give it a claim or a question; it breaks that into individual statements, searches the live web for evidence on each one, judges every statement against what it found, and flags places where sources disagree with each other. You get a verdict, a confidence score and the supporting sources for each claim, plus a written report.

A single LLM prompt can't do this reliably: it has no live evidence, and it can't show its reasoning. veritas separates the job into specialised agents, grounds every verdict in retrieved sources, and shows you each step as it happens instead of making you wait for a final answer.

## Features

- **Claim decomposition.** Complex input becomes atomic, independently checkable claims.
- **Live evidence.** Each claim is checked against fresh web results (Tavily), not model memory.
- **Semantic retrieval.** Results are embedded and indexed in FAISS so the verifier works from the most relevant passages.
- **Three-way verdicts.** `SUPPORTED`, `REFUTED` or `INCONCLUSIVE`, each with a 0 to 1 confidence score and written reasoning.
- **Contradiction detection.** Conflicts between sources are surfaced instead of averaged away.
- **Report generation.** A structured Markdown report with sources.
- **Provider-agnostic.** Switch between Groq, OpenAI, Anthropic and Google Gemini per request.
- **Live streaming.** The API emits a Server-Sent Event as each agent starts and finishes, and the interface renders them in real time.
- **Parallel verification.** Claims are verified concurrently (capped to respect rate limits).
- **Persistence.** Completed analyses are stored in MongoDB Atlas.

## The interface

The web app is built around the idea that a fact-check should look like evidence, not a chat window.

- Claims appear as columns on a light-table drafting surface and "develop" as the agents work.
- Each verdict lands as a rubber stamp: solid for supported, struck-through for refuted, dashed for inconclusive. Color is never the only signal.
- Sources sit under each claim as paper slips; contradictions are drawn as red thread between the conflicting slips.
- A pipeline rail shows which of the five agents is running.
- The full report opens in a side drawer.

The UI has no component library. It is React, TypeScript and hand-written CSS.

## How it works

```
        query
          |
          v
  +-----------------+     +------------------+     +----------------+
  | claim_extractor | --> | search_retriever | --> |  fact_verifier |
  |  atomic claims  |     | Tavily + FAISS   |     | verdict + conf |
  +-----------------+     +------------------+     +----------------+
                                                           |
                       +-----------------------+           v
   report + sources <--| report_generator      | <-- contradiction_detector
                       +-----------------------+
```

1. **Claim extractor** turns the input into atomic claims.
2. **Search retriever** runs web searches through Tavily and embeds the results with SentenceTransformers (`all-MiniLM-L6-v2` by default) into an in-memory FAISS index.
3. **Fact verifier** compares each claim with the retrieved evidence and returns a verdict, confidence and reasoning, plus which sources support or contradict it.
4. **Contradiction detector** finds pairs of sources that conflict on a claim.
5. **Report generator** writes the final Markdown report.

The agents are nodes in a LangGraph `StateGraph` that passes a shared state between steps. The graph is streamed with `astream`, which is what powers the live event feed.

## Tech stack

| Layer | Technology |
|---|---|
| API | FastAPI, Pydantic v2, Uvicorn |
| Agent orchestration | LangGraph, LangChain |
| LLM providers | Groq (default), OpenAI, Anthropic Claude, Google Gemini |
| Web search | Tavily |
| Vector search | FAISS (CPU), SentenceTransformers |
| Database | MongoDB Atlas via Motor (async) |
| Web client | React 18, TypeScript, Vite, plain CSS |
| Streaming | Server-Sent Events |

## API

Interactive docs are served at `/docs`.

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/analyze` | Runs the pipeline and returns the complete result as JSON |
| `GET` | `/api/v1/analyze/stream?query=...` | Runs the pipeline and streams one event per agent start and finish, ending with a `complete` event |
| `GET` | `/api/v1/health` | Health check |

**Request**

```json
{
  "query": "Global renewable electricity share exceeded 30% in 2024.",
  "model_provider": "groq"
}
```

`query` is required (5 to 1000 characters). `model_provider` is optional: `groq`, `openai`, `claude` or `gemini`.

**Response (abridged)**

```json
{
  "job_id": "job_4fa5b7ed9f",
  "status": "completed",
  "summary": {
    "total_claims": 5,
    "supported_claims": 3,
    "refuted_claims": 0,
    "inconclusive_claims": 2,
    "total_sources": 15,
    "contradictions_detected": 1
  },
  "claims": [
    {
      "id": "claim_01",
      "text": "...",
      "category": "statistical",
      "verdict": "SUPPORTED",
      "confidence": 0.95,
      "reasoning": "...",
      "supporting_sources": ["src_01"],
      "contradicting_sources": []
    }
  ],
  "sources": [
    { "id": "src_01", "url": "...", "title": "...", "snippet": "...", "domain": "...", "score": 0.91 }
  ],
  "contradictions": [
    { "claim_id": "claim_03", "source_a_id": "src_02", "source_b_id": "src_07", "conflict_description": "..." }
  ],
  "report_markdown": "# ...",
  "errors": []
}
```

**Stream events**

```json
{ "agent": "claim_extractor", "status": "done", "data": { "claims": [ ... ] } }
```

Agents are reported in pipeline order, followed by `{ "agent": "complete", "data": <full response> }`.

## Run it locally

Requirements: Python 3.10+, Node.js 18+, a [Tavily](https://tavily.com) key, a key for at least one LLM provider ([Groq](https://console.groq.com) has a free tier), and a MongoDB Atlas connection string.

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
```

Fill in `.env`. Minimum for the default setup:

```
LLM_PROVIDER=groq
DEFAULT_LLM_PROVIDER=groq
GROQ_API_KEY=...
TAVILY_API_KEY=...
MONGODB_URI=...
```

Start the server:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The first request takes longer while the embedding model downloads. A smoke test is available with `python test_query.py` while the server is running.

### 2. Web client

```bash
cd web
npm install
npm run dev -- --host 127.0.0.1
```

Open the printed URL. To explore the interface without a backend, add `?mock=1` to the URL for a built-in sample run.

The client reads the API address from `VITE_API_URL` (default `http://127.0.0.1:8000`).

## Configuration

All settings live in `backend/.env`; see `backend/.env.example` for the full list.

| Variable | Purpose |
|---|---|
| `DEFAULT_LLM_PROVIDER` | `groq`, `openai`, `claude` or `gemini` |
| `GROQ_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY` | Provider keys (only the one you use is required) |
| `*_MODEL_NAME` | Model identifier per provider |
| `TAVILY_API_KEY` | Web search |
| `EMBEDDING_MODEL_NAME` | SentenceTransformers model |
| `MONGODB_URI`, `MONGODB_DB_NAME`, `MONGODB_COLLECTION_NAME` | Persistence |

## Deploying

- **Backend:** any host that runs a Python web service (for example Render). Set the environment variables above, install `requirements.txt`, and start with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. The embedding model and PyTorch need a reasonable amount of memory, so check your plan's limit. Add your frontend's URL to the backend's allowed CORS origins.
- **Web client:** any static host (for example Vercel or Netlify). Build with `npm run build` from `web/` and set `VITE_API_URL` to your backend URL at build time.

## Project structure

```
veritas/
├── backend/
│   ├── app/
│   │   ├── agents/        claim extractor, retriever, verifier, contradiction detector, report generator (+ prompts)
│   │   ├── api/v1/        analyze (JSON and SSE), health
│   │   ├── core/          settings, database connection
│   │   ├── graph/         LangGraph state and workflow
│   │   ├── llm/           provider wiring
│   │   ├── schemas/       request and response models
│   │   └── services/      LLM factory, Tavily, embeddings, FAISS, MongoDB
│   └── test_query.py
└── web/
    └── src/
        ├── components/    Intake, Rail, ClaimColumn, Stamp, Threads, ReportDrawer, Wordmark
        ├── useAnalysis.ts event stream hook and state merging
        └── mockStream.ts  sample run for development
```

## Limitations

- A full analysis takes roughly one to one and a half minutes, because it makes several LLM calls and live searches. The streaming interface exists to make that wait visible.
- Verdicts are only as good as the sources the search returns and the model that reads them. veritas shows its evidence so you can check it, but it is an aid to verification, not an authority.
- The claim extractor can occasionally add a claim that the input did not state.
- There is no automated test suite yet.

## Roadmap

- Tighter claim extraction that stays strictly within the user's input
- Saved analysis history in the interface
- Source credibility weighting
- Automated tests and evaluation against a labelled claim set

## License

MIT. See [LICENSE](LICENSE).
