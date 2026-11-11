import { useState, type FormEvent } from 'react'
import Wordmark from './Wordmark'
import './Intake.css'

type IntakeProps = {
  onSubmit: (query: string) => void
}

const exampleClaims = [
  'Global renewable electricity share exceeded 30% in 2024.',
  'India became the world’s most populous country in 2023.',
  'The James Webb Space Telescope launched in 2021.',
]

export default function Intake({ onSubmit }: IntakeProps) {
  const [query, setQuery] = useState('')
  const [error, setError] = useState('')

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const cleanQuery = query.trim()
    if (cleanQuery.length < 5) {
      setError('Add a little more detail, then try again.')
      return
    }
    setError('')
    onSubmit(cleanQuery)
  }

  function chooseExample(event: React.MouseEvent<HTMLAnchorElement>, claim: string) {
    event.preventDefault()
    setQuery(claim)
    setError('')
  }

  return (
    <main className="intake" data-state="intake">
      <section className="intake__content" aria-label="Start a fact check">
        <Wordmark placement="intake" />
        <form className="intake__form" onSubmit={submit}>
          <div className="intake__frame">
            <span className="intake__registration intake__registration--top-left" aria-hidden="true" />
            <span className="intake__registration intake__registration--top-right" aria-hidden="true" />
            <span className="intake__registration intake__registration--bottom-left" aria-hidden="true" />
            <span className="intake__registration intake__registration--bottom-right" aria-hidden="true" />
            <label className="intake__visually-hidden" htmlFor="claim-query">Paste a claim or a question</label>
            <textarea
              id="claim-query"
              className="intake__textarea"
              name="query"
              minLength={5}
              maxLength={1000}
              placeholder="Paste a claim or a question."
              value={query}
              onChange={(event) => {
                setQuery(event.currentTarget.value)
                if (error) setError('')
              }}
              aria-invalid={Boolean(error)}
              aria-describedby={error ? 'intake-error' : undefined}
              required
            />
          </div>
          {error && <p className="intake__error" id="intake-error" role="alert">{error}</p>}
          <button className="intake__submit" type="submit">Check this</button>
        </form>

        <nav className="intake__examples" aria-label="Example claims">
          {exampleClaims.map((claim, index) => (
            <a
              href={`#example-${index + 1}`}
              key={claim}
              onClick={(event) => chooseExample(event, claim)}
            >
              {claim}
            </a>
          ))}
        </nav>
      </section>
    </main>
  )
}
