import type { Claim, Source } from '../state'
import Stamp from './Stamp'
import './ClaimColumn.css'

type ClaimColumnProps = {
  claim: Claim
  sources: Source[]
  index: number
  develop: boolean
}

function ConfidenceTicks({ confidence }: { confidence: number | null }) {
  const filledCount = confidence === null ? 0 : Math.round(Math.max(0, Math.min(1, confidence)) * 10)
  const accessibleValue = confidence === null ? 'not available' : confidence.toFixed(2)
  return (
    <div className="confidence" role="img" aria-label={`Confidence ${accessibleValue}; ${filledCount} of 10` }>
      <span className="confidence__ticks" aria-hidden="true">
        {Array.from({ length: 10 }, (_, tick) => (
          <span className={`confidence__tick${tick < filledCount ? ' confidence__tick--filled' : ''}`} key={tick} />
        ))}
      </span>
      <span className="confidence__value">{accessibleValue}</span>
    </div>
  )
}

function SourceSlip({ source }: { source: Source }) {
  return (
    <a
      className="source-slip"
      data-source-id={source.id}
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`Open source: ${source.title} (${source.domain}) in a new tab`}
    >
      <span className="source-slip__domain">{source.domain}</span>
      <span className="source-slip__title">{source.title}</span>
      <span className="source-slip__snippet">{source.snippet}</span>
    </a>
  )
}

export default function ClaimColumn({ claim, sources, index, develop }: ClaimColumnProps) {
  const hasVerdict = claim.verdict !== null

  const referencedIds = new Set([...claim.supporting_sources, ...claim.contradicting_sources])
  const claimSources = sources.filter((source) => referencedIds.has(source.id))

  return (
    <article
      className={`claim-column${!hasVerdict ? ' claim-column--underexposed' : ''}${develop ? ' claim-column--develop' : ''}`}
      style={{ animationDelay: `${index * 150}ms` }}
      aria-labelledby={`claim-${claim.id}`}
    >
      <h2 className="claim-column__text" id={`claim-${claim.id}`}>{claim.text}</h2>
      <div className="claim-column__verdict">
        <Stamp claimId={claim.id} verdict={claim.verdict} confidence={claim.confidence} />
        <ConfidenceTicks confidence={claim.confidence} />
      </div>
      <p className="claim-column__reasoning">
        {claim.reasoning || 'Waiting for evidence to be checked.'}
      </p>
      {claimSources.length > 0 && (
        <div className="claim-column__sources" aria-label="Sources for this claim">
          {claimSources.map((source) => <SourceSlip source={source} key={source.id} />)}
        </div>
      )}
    </article>
  )
}
