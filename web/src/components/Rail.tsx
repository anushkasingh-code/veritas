import type { AgentName, AgentStatus } from '../state'
import './Rail.css'

type RailProps = {
  agentStatus: Record<AgentName, AgentStatus>
  claimCount: number
}

const agents: Array<{ id: AgentName; label: string; activeText: (count: number) => string }> = [
  { id: 'claim_extractor', label: 'Claim extractor', activeText: () => 'Splitting the query into verifiable claims.' },
  { id: 'search_retriever', label: 'Search retriever', activeText: (count) => `Reading sources for ${count} ${count === 1 ? 'claim' : 'claims'}.` },
  { id: 'fact_verifier', label: 'Fact verifier', activeText: () => 'Checking claims against the sources.' },
  { id: 'contradiction_detector', label: 'Contradiction detector', activeText: () => 'Cross-checking sources for contradictions.' },
  { id: 'report_generator', label: 'Report generator', activeText: () => 'Writing the report.' },
]

export default function Rail({ agentStatus, claimCount }: RailProps) {
  const activeAgent = agents.find((agent) => agentStatus[agent.id] === 'started')
  const allDone = agents.every((agent) => agentStatus[agent.id] === 'done')
  const statusText = activeAgent
    ? activeAgent.activeText(claimCount)
    : allDone
      ? 'Analysis complete.'
      : 'Waiting for the next step.'

  return (
    <aside className="agent-rail" aria-label="Analysis pipeline">
      <ol className="agent-rail__steps">
        {agents.map((agent) => {
          const status = agentStatus[agent.id]
          return (
            <li
              className={`agent-rail__step agent-rail__step--${status}`}
              key={agent.id}
              aria-current={status === 'started' ? 'step' : undefined}
            >
              <span className="agent-rail__node" aria-hidden="true" />
              <span className="agent-rail__label">{agent.label}</span>
              <span className="agent-rail__status">{status === 'done' ? 'Done' : status === 'started' ? 'Active' : 'Waiting'}</span>
            </li>
          )
        })}
      </ol>
      <p className="agent-rail__message" aria-live="polite">{statusText}</p>
    </aside>
  )
}
