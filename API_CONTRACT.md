# API_CONTRACT.md

Backend base URL: `import.meta.env.VITE_API_URL` (default `http://127.0.0.1:8000`).

## Stream: GET /api/v1/analyze/stream?query=<urlencoded>

Server-Sent Events. Use `EventSource`. Each message is `data: <json>` with this shape:

```json
{ "agent": "<node name>", "status": "started" | "done", "data": { } }
```

Agent names in order:
`claim_extractor` -> `search_retriever` -> `fact_verifier` -> `contradiction_detector` -> `report_generator`, then a final `{ "agent": "complete", "data": <AnalyzeResponse> }`.

### Verified payload (observed)

`claim_extractor` / `done`:
```json
{ "claims": [ { "id": "claim_01", "text": "...", "category": "statistical",
  "verdict": null, "confidence": null, "reasoning": null,
  "supporting_sources": [], "contradicting_sources": [] } ] }
```
`started` events carry `"data": {}`.

### Assumed payloads (NOT yet observed, code defensively)

- `search_retriever` / `done`: `{ "sources": Source[] }`
- `fact_verifier` / `done`: `{ "claims": Claim[] }` with verdict, confidence, reasoning, supporting_sources, contradicting_sources filled in
- `contradiction_detector` / `done`: `{ "contradictions": Contradiction[] }`
- `report_generator` / `done`: `{ "report_markdown": string }`

Rules: merge each `done` payload into one state object by key. Ignore unknown keys. If a key is missing, keep the previous value. Never crash on a missing field. The `complete` event is the source of truth and overwrites all state.

### Errors

An event may carry `"errors": string[]` inside `data` or a final `complete` with a non-empty `errors`. If the connection closes before `complete`, show the error state with a "Try again" button. Do not auto-retry (each run costs API calls).

## Types

```ts
type Verdict = "SUPPORTED" | "REFUTED" | "INCONCLUSIVE";
interface Claim { id: string; text: string; category: string;
  verdict: Verdict | null; confidence: number | null; // 0..1
  reasoning: string | null; supporting_sources: string[]; contradicting_sources: string[]; }
interface Source { id: string; url: string; title: string; snippet: string; domain: string; score: number; }
interface Contradiction { claim_id: string; source_a_id: string; source_b_id: string; conflict_description: string; }
interface AnalyzeResponse { job_id: string; status: string; query: string; created_at: string; completed_at: string;
  summary: { total_claims: number; supported_claims: number; refuted_claims: number; inconclusive_claims: number;
             total_sources: number; contradictions_detected: number };
  claims: Claim[]; sources: Source[]; contradictions: Contradiction[]; report_markdown: string; errors: string[]; }
```

`supporting_sources` / `contradicting_sources` hold Source ids. A slip appears under every claim that references it.

## Other endpoints

- `POST /api/v1/analyze` body `{ "query": string, "model_provider"?: "groq"|"claude"|"openai"|"gemini" }` returns AnalyzeResponse. Not used by the UI; keep as fallback if EventSource fails.
- Typical run: 40-85 seconds. UI must be useful the whole time.

## Frontend must NOT

Call any endpoint not listed here. The old `frontend/src/api/auth.ts`, `reports.ts`, `analytics.ts` target endpoints that do not exist.
