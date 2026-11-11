import { useEffect, useRef, type ReactNode } from 'react'
import './ReportDrawer.css'

type ReportDrawerProps = {
  reportMarkdown: string
  onClose: () => void
}

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const tokens = /\*\*([^*]+)\*\*|\[([^\]]+)\]\(([^)\s]+)\)/g
  const output: ReactNode[] = []
  let cursor = 0
  let match: RegExpExecArray | null
  let tokenIndex = 0

  while ((match = tokens.exec(text)) !== null) {
    if (match.index > cursor) output.push(text.slice(cursor, match.index))
    if (match[1] !== undefined) {
      output.push(<strong key={`${keyPrefix}-bold-${tokenIndex}`}>{match[1]}</strong>)
    } else {
      const label = match[2]
      const url = match[3]
      if (/^https?:\/\//i.test(url)) {
        output.push(
          <a href={url} key={`${keyPrefix}-link-${tokenIndex}`} target="_blank" rel="noopener noreferrer">
            {label}
          </a>,
        )
      } else {
        output.push(label)
      }
    }
    cursor = tokens.lastIndex
    tokenIndex += 1
  }

  if (cursor < text.length) output.push(text.slice(cursor))
  return output
}

function renderMarkdown(markdown: string): ReactNode[] {
  const blocks: ReactNode[] = []
  let paragraph: string[] = []
  let listItems: string[] = []
  let listKind: 'ordered' | 'unordered' | null = null
  let blockIndex = 0

  const flushParagraph = () => {
    if (paragraph.length === 0) return
    blocks.push(
      <p key={`paragraph-${blockIndex}`}>
        {renderInline(paragraph.join(' '), `paragraph-${blockIndex}`)}
      </p>,
    )
    blockIndex += 1
    paragraph = []
  }

  const flushList = () => {
    if (listKind === null || listItems.length === 0) return
    const ListTag = listKind === 'ordered' ? 'ol' : 'ul'
    blocks.push(
      <ListTag key={`list-${blockIndex}`}>
        {listItems.map((item, index) => (
          <li key={`list-${blockIndex}-item-${index}`}>
            {renderInline(item, `list-${blockIndex}-item-${index}`)}
          </li>
        ))}
      </ListTag>,
    )
    blockIndex += 1
    listItems = []
    listKind = null
  }

  for (const rawLine of markdown.split(/\r?\n/)) {
    const line = rawLine.trim()
    if (!line) {
      flushParagraph()
      flushList()
      continue
    }

    const heading = /^(#{1,6})\s+(.+)$/.exec(line)
    if (heading) {
      flushParagraph()
      flushList()
      const level = heading[1].length
      const HeadingTag = `h${level}` as keyof JSX.IntrinsicElements
      blocks.push(
        <HeadingTag key={`heading-${blockIndex}`}>
          {renderInline(heading[2], `heading-${blockIndex}`)}
        </HeadingTag>,
      )
      blockIndex += 1
      continue
    }

    const unorderedItem = /^[-*+]\s+(.+)$/.exec(line)
    const orderedItem = /^\d+\.\s+(.+)$/.exec(line)
    const nextListKind = unorderedItem ? 'unordered' : orderedItem ? 'ordered' : null
    if (nextListKind) {
      flushParagraph()
      if (listKind !== null && listKind !== nextListKind) flushList()
      listKind = nextListKind
      listItems.push((unorderedItem ?? orderedItem)![1])
      continue
    }

    flushList()
    paragraph.push(line)
  }

  flushParagraph()
  flushList()
  return blocks
}

export default function ReportDrawer({ reportMarkdown, onClose }: ReportDrawerProps) {
  const drawerRef = useRef<HTMLElement>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    const previouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null
    closeButtonRef.current?.focus()

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        event.preventDefault()
        onClose()
        return
      }
      if (event.key !== 'Tab' || !drawerRef.current) return

      const focusable = Array.from(
        drawerRef.current.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
      ).filter((element) => element.getAttribute('aria-hidden') !== 'true')
      if (focusable.length === 0) {
        event.preventDefault()
        drawerRef.current.focus()
        return
      }

      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && (document.activeElement === first || !drawerRef.current.contains(document.activeElement))) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && (document.activeElement === last || !drawerRef.current.contains(document.activeElement))) {
        event.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      previouslyFocused?.focus()
    }
  }, [onClose])

  return (
    <div className="report-overlay">
      <aside
        className="report-drawer"
        ref={drawerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="report-drawer-title"
        tabIndex={-1}
      >
        <header className="report-drawer__header">
          <h2 id="report-drawer-title">Research report</h2>
          <button className="report-drawer__close" type="button" onClick={onClose} ref={closeButtonRef}>
            Close report
          </button>
        </header>
        <div className="report-markdown">
          {reportMarkdown ? renderMarkdown(reportMarkdown) : <p>No report is available yet.</p>}
        </div>
      </aside>
    </div>
  )
}
