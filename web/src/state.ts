import { useReducer } from 'react'

export type Verdict = 'SUPPORTED' | 'REFUTED' | 'INCONCLUSIVE'

export interface Claim {
  id: string
  text: string
  category: string
  verdict: Verdict | null
  confidence: number | null
  reasoning: string | null
  supporting_sources: string[]
  contradicting_sources: string[]
}

export interface Source {
  id: string
  url: string
  title: string
  snippet: string
  domain: string
  score: number
}

export interface Contradiction {
  claim_id: string
  source_a_id: string
  source_b_id: string
  conflict_description: string
}

export interface AnalyzeResponse {
  job_id: string
  status: string
  query: string
  created_at: string
  completed_at: string
  summary: {
    total_claims: number
    supported_claims: number
    refuted_claims: number
    inconclusive_claims: number
    total_sources: number
    contradictions_detected: number
  }
  claims: Claim[]
  sources: Source[]
  contradictions: Contradiction[]
  report_markdown: string
  errors: string[]
}

export type AgentName =
  | 'claim_extractor'
  | 'search_retriever'
  | 'fact_verifier'
  | 'contradiction_detector'
  | 'report_generator'

export type AgentStatus = 'idle' | 'started' | 'done'
export type ScreenState = 'intake' | 'wall' | 'report'

export type AppStore = {
  screen: ScreenState
  analysis: AnalyzeResponse
  agentStatus: Record<AgentName, AgentStatus>
  streamError: string | null
}

type AgentEventAction = {
  type: 'agent-event'
  agent: AgentName
  status: 'started' | 'done'
  data: Record<string, unknown>
}

export type AppAction =
  | { type: 'begin'; query: string }
  | AgentEventAction
  | { type: 'complete'; analysis: AnalyzeResponse }
  | { type: 'stream-error'; message: string }
  | { type: 'show-wall' }
  | { type: 'show-report' }
  | { type: 'back-to-intake' }

const emptySummary = {
  total_claims: 0,
  supported_claims: 0,
  refuted_claims: 0,
  inconclusive_claims: 0,
  total_sources: 0,
  contradictions_detected: 0,
}

export const emptyAnalysis: AnalyzeResponse = {
  job_id: '',
  status: '',
  query: '',
  created_at: '',
  completed_at: '',
  summary: emptySummary,
  claims: [],
  sources: [],
  contradictions: [],
  report_markdown: '',
  errors: [],
}

const initialAgentStatus: Record<AgentName, AgentStatus> = {
  claim_extractor: 'idle',
  search_retriever: 'idle',
  fact_verifier: 'idle',
  contradiction_detector: 'idle',
  report_generator: 'idle',
}

export const initialStore: AppStore = {
  screen: 'intake',
  analysis: emptyAnalysis,
  agentStatus: initialAgentStatus,
  streamError: null,
}

const responseKeys = new Set<keyof AnalyzeResponse>([
  'job_id',
  'status',
  'query',
  'created_at',
  'completed_at',
  'summary',
  'claims',
  'sources',
  'contradictions',
  'report_markdown',
  'errors',
])

function mergeKnownFields(current: AnalyzeResponse, data: Record<string, unknown>): AnalyzeResponse {
  const merged = { ...current }
  const writable = merged as unknown as Record<string, unknown>
  for (const [key, value] of Object.entries(data)) {
    if (responseKeys.has(key as keyof AnalyzeResponse)) writable[key] = value
  }
  return merged
}

export function appReducer(store: AppStore, action: AppAction): AppStore {
  switch (action.type) {
    case 'begin':
      return {
        screen: 'wall',
        analysis: { ...emptyAnalysis, query: action.query },
        agentStatus: initialAgentStatus,
        streamError: null,
      }
    case 'agent-event':
      return {
        ...store,
        analysis: action.status === 'done'
          ? mergeKnownFields(store.analysis, action.data)
          : store.analysis,
        agentStatus: { ...store.agentStatus, [action.agent]: action.status },
      }
    case 'complete':
      return { ...store, screen: 'report', analysis: action.analysis, streamError: null }
    case 'stream-error':
      return { ...store, streamError: action.message }
    case 'show-wall':
      return { ...store, screen: 'wall' }
    case 'show-report':
      return { ...store, screen: 'report' }
    case 'back-to-intake':
      return { ...store, screen: 'intake' }
    default:
      return store
  }
}

export function useAppStore() {
  return useReducer(appReducer, initialStore)
}
