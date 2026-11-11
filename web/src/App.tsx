import Intake from './components/Intake'
import ClaimColumn from './components/ClaimColumn'
import Rail from './components/Rail'
import ReportDrawer from './components/ReportDrawer'
import Threads from './components/Threads'
import './components/Wall.css'
import { useAnalysis } from './useAnalysis'
import { useCallback, useState } from 'react'

export default function App() {
  const { store, startAnalysis, retry } = useAnalysis()
  const [reportOpen, setReportOpen] = useState(false)
  const closeReport = useCallback(() => setReportOpen(false), [])

  if (store.screen === 'intake') {
    return <Intake onSubmit={startAnalysis} />
  }

  return (
    <main className="wall-layout" data-state={store.screen}>
      <Rail agentStatus={store.agentStatus} claimCount={store.analysis.claims.length} />
      <section className="wall-layout__main" aria-label="Claim verification wall">
        {store.streamError && (
          <div className="wall-layout__error" role="alert">
            <p>{store.streamError}</p>
            <button type="button" onClick={retry}>Try again</button>
          </div>
        )}
        {store.analysis.report_markdown && (
          <div className="wall-layout__actions">
            <button type="button" onClick={() => setReportOpen(true)}>Read the report</button>
          </div>
        )}
        <div className="wall-layout__board">
          <Threads contradictions={store.analysis.contradictions} />
          {store.analysis.claims.length > 0 ? (
            <div className="wall-layout__claims">
              {store.analysis.claims.map((claim, index) => (
                <ClaimColumn
                  key={claim.id}
                  claim={claim}
                  sources={store.analysis.sources}
                  index={index}
                  develop={store.agentStatus.claim_extractor === 'done'}
                />
              ))}
            </div>
          ) : (
            <p className="wall-layout__empty">Claims will appear here as the query is split into verifiable statements.</p>
          )}
        </div>
      </section>
      {reportOpen && (
        <ReportDrawer reportMarkdown={store.analysis.report_markdown} onClose={closeReport} />
      )}
    </main>
  )
}
