import type { CSSProperties } from 'react'
import './Wordmark.css'

type WordmarkProps = {
  placement?: 'intake' | 'rail'
}

function randomForLetter(index: number, salt: number): number {
  let value = Math.imul(index + 1, 0x9e3779b1) ^ salt
  value = Math.imul(value ^ (value >>> 16), 0x85ebca6b)
  value = Math.imul(value ^ (value >>> 13), 0xc2b2ae35)
  value ^= value >>> 16
  return (value >>> 0) / 4294967296
}

export default function Wordmark({ placement = 'intake' }: WordmarkProps) {
  const letters = Array.from('research')

  return (
    <div className={`wordmark wordmark--${placement}`} role="img" aria-label="veritas research, verified">
      <span className="wordmark__name" aria-hidden="true">veritas</span>
      <span className="wordmark__tagline" aria-hidden="true">
        <span className="wordmark__research">
          <span className="wordmark__letters">
            {letters.map((letter, index) => {
              const rotation = -4 + randomForLetter(index, 0x517cc1b7) * 8
              const offsetY = -2 + randomForLetter(index, 0x6d2b79f5) * 4
              const style = {
                transform: `rotate(${rotation.toFixed(2)}deg) translateY(${offsetY.toFixed(2)}px)`,
              } satisfies CSSProperties
              return <span className="wordmark__letter" key={`${letter}-${index}`} style={style}>{letter}</span>
            })}
          </span>
          <svg className="wordmark__scribble" viewBox="0 0 150 10" aria-hidden="true" focusable="false">
            <path d="M2 6 C18 1 26 9 42 5 S66 2 78 6 S101 9 115 4 S136 2 148 5" />
          </svg>
        </span>
        <span className="wordmark__verified">, verified</span>
        <svg className="wordmark__tick" viewBox="0 0 18 18" aria-hidden="true" focusable="false">
          <path d="M2 9.5 7 14l9-10" />
        </svg>
      </span>
    </div>
  )
}
