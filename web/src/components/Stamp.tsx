import { useEffect, useRef, useState, type CSSProperties } from 'react'
import type { Verdict } from '../state'
import './Stamp.css'

type StampProps = {
  claimId: string
  verdict: Verdict | null
  confidence: number | null
}

function seededRotation(claimId: string): string {
  let seed = 2166136261
  for (let index = 0; index < claimId.length; index += 1) {
    seed = Math.imul(seed ^ claimId.charCodeAt(index), 16777619)
  }

  let value = seed + 0x6d2b79f5
  value = Math.imul(value ^ (value >>> 15), value | 1)
  value ^= value + Math.imul(value ^ (value >>> 7), value | 61)
  const randomValue = ((value ^ (value >>> 14)) >>> 0) / 4294967296
  return `${(-4 + randomValue * 7).toFixed(2)}deg`
}

export default function Stamp({ claimId, verdict, confidence }: StampProps) {
  const [landing, setLanding] = useState(false)
  const hasLanded = useRef(false)

  useEffect(() => {
    if (verdict === null || hasLanded.current) return
    hasLanded.current = true
    setLanding(true)
    const timer = window.setTimeout(() => setLanding(false), 140)
    return () => window.clearTimeout(timer)
  }, [verdict])

  const rotationStyle = { '--stamp-rotation': seededRotation(claimId) } as CSSProperties
  if (verdict === null) {
    return (
      <span className="stamp stamp--pending" style={rotationStyle} aria-label="Verdict pending">
        Developing
      </span>
    )
  }

  const confidenceText = confidence === null ? 'not available' : confidence.toFixed(2)
  return (
    <span
      className={`stamp stamp--${verdict.toLowerCase()}${landing ? ' stamp--landing' : ''}`}
      style={rotationStyle}
      role="img"
      aria-label={`${verdict} verdict, confidence ${confidenceText}`}
    >
      {verdict}
    </span>
  )
}
