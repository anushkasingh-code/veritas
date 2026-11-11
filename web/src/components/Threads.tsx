import { useLayoutEffect, useRef, useState } from 'react'
import type { Contradiction } from '../state'
import './Threads.css'

type ThreadsProps = {
  contradictions: Contradiction[]
}

type ThreadPath = {
  id: string
  path: string
  description: string
  midpoint: { x: number; y: number }
}

type LayerSize = { width: number; height: number }

function center(rect: DOMRect, origin: DOMRect) {
  return {
    x: rect.left - origin.left + rect.width / 2,
    y: rect.top - origin.top + rect.height / 2,
  }
}

function edgePoint(rect: DOMRect, origin: DOMRect, target: { x: number; y: number }) {
  const point = center(rect, origin)
  const dx = target.x - point.x
  const dy = target.y - point.y
  const halfWidth = Math.max(rect.width / 2, 1)
  const halfHeight = Math.max(rect.height / 2, 1)
  const scale = 1 / Math.max(Math.abs(dx) / halfWidth, Math.abs(dy) / halfHeight, 1)
  return { x: point.x + dx * scale, y: point.y + dy * scale }
}

function makePath(start: { x: number; y: number }, end: { x: number; y: number }) {
  const dx = end.x - start.x
  const dy = end.y - start.y
  const distance = Math.hypot(dx, dy) || 1
  const curve = Math.min(80, Math.max(24, distance * 0.18))
  const perpendicular = { x: -dy / distance, y: dx / distance }
  const controlOne = {
    x: start.x + dx * 0.35 + perpendicular.x * curve,
    y: start.y + dy * 0.35 + perpendicular.y * curve,
  }
  const controlTwo = {
    x: start.x + dx * 0.65 + perpendicular.x * curve,
    y: start.y + dy * 0.65 + perpendicular.y * curve,
  }
  const midpoint = {
    x: (start.x + 3 * controlOne.x + 3 * controlTwo.x + end.x) / 8,
    y: (start.y + 3 * controlOne.y + 3 * controlTwo.y + end.y) / 8,
  }
  return {
    path: `M ${start.x} ${start.y} C ${controlOne.x} ${controlOne.y}, ${controlTwo.x} ${controlTwo.y}, ${end.x} ${end.y}`,
    midpoint,
  }
}

export default function Threads({ contradictions }: ThreadsProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const activeIdRef = useRef<string | null>(null)
  const [paths, setPaths] = useState<ThreadPath[]>([])
  const [activeThread, setActiveThread] = useState<ThreadPath | null>(null)
  const [size, setSize] = useState<LayerSize>({ width: 0, height: 0 })

  useLayoutEffect(() => {
    const svg = svgRef.current
    const board = svg?.parentElement
    if (!svg || !board) return

    let frame = 0
    const recompute = () => {
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(() => {
        const boardRect = board.getBoundingClientRect()
        const nextSize = {
          width: Math.max(board.scrollWidth, boardRect.width),
          height: Math.max(board.scrollHeight, boardRect.height),
        }
        setSize(nextSize)

        const sourceElements = Array.from(board.querySelectorAll<HTMLElement>('[data-source-id]'))
        const findSource = (sourceId: string) =>
          sourceElements.find((element) => element.dataset.sourceId === sourceId)

        const nextPaths: ThreadPath[] = []
        contradictions.forEach((contradiction, index) => {
          const sourceA = findSource(contradiction.source_a_id)
          const sourceB = findSource(contradiction.source_b_id)
          if (!sourceA || !sourceB) return

          const rectA = sourceA.getBoundingClientRect()
          const rectB = sourceB.getBoundingClientRect()
          const centerA = center(rectA, boardRect)
          const centerB = center(rectB, boardRect)
          const start = edgePoint(rectA, boardRect, centerB)
          const end = edgePoint(rectB, boardRect, centerA)
          const curve = makePath(start, end)
          nextPaths.push({
            id: `${contradiction.claim_id}-${contradiction.source_a_id}-${contradiction.source_b_id}-${index}`,
            path: curve.path,
            description: contradiction.conflict_description,
            midpoint: curve.midpoint,
          })
        })

        setPaths(nextPaths)
        setActiveThread((current) => {
          if (!current) return null
          const updated = nextPaths.find((path) => path.id === current.id) ?? null
          activeIdRef.current = updated?.id ?? null
          return updated
        })
      })
    }

    recompute()
    const resizeObserver = new ResizeObserver(recompute)
    resizeObserver.observe(board)
    board.querySelectorAll<HTMLElement>('[data-source-id]').forEach((element) => resizeObserver.observe(element))

    const wall = board.closest('.wall-layout__main')
    wall?.addEventListener('scroll', recompute, { passive: true })
    window.addEventListener('resize', recompute)

    return () => {
      cancelAnimationFrame(frame)
      resizeObserver.disconnect()
      wall?.removeEventListener('scroll', recompute)
      window.removeEventListener('resize', recompute)
    }
  }, [contradictions])

  function showThread(thread: ThreadPath) {
    activeIdRef.current = thread.id
    setActiveThread(thread)
  }

  function hideThread(thread: ThreadPath) {
    if (activeIdRef.current !== thread.id) return
    activeIdRef.current = null
    setActiveThread(null)
  }

  return (
    <>
      <svg
        className="threads-layer"
        ref={svgRef}
        width={size.width}
        height={size.height}
        viewBox={`0 0 ${size.width} ${size.height}`}
        role="group"
        aria-label="Contradiction threads"
      >
        {paths.map((thread) => (
          <path
            className="thread-path"
            key={thread.id}
            d={thread.path}
            pathLength="1"
            onPointerEnter={() => showThread(thread)}
            onPointerLeave={() => hideThread(thread)}
            onFocus={() => showThread(thread)}
            onBlur={() => hideThread(thread)}
            tabIndex={0}
            role="img"
            aria-label={`Source conflict: ${thread.description}`}
          />
        ))}
      </svg>
      {activeThread && (
        <div
          className="thread-tooltip"
          role="tooltip"
          style={{ left: activeThread.midpoint.x, top: activeThread.midpoint.y }}
        >
          {activeThread.description}
        </div>
      )}
    </>
  )
}
