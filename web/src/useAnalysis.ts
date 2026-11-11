import { useCallback, useEffect, useRef } from 'react'
import { playMockStream, type AnalysisStreamEvent } from './mockStream'
import { useAppStore, type AgentName, type AnalyzeResponse } from './state'

const agentNames = new Set<AgentName>([
  'claim_extractor',
  'search_retriever',
  'fact_verifier',
  'contradiction_detector',
  'report_generator',
])

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isAnalyzeResponse(value: unknown): value is AnalyzeResponse {
  return isRecord(value)
    && typeof value.job_id === 'string'
    && typeof value.status === 'string'
    && typeof value.query === 'string'
    && Array.isArray(value.claims)
    && Array.isArray(value.sources)
    && Array.isArray(value.contradictions)
    && Array.isArray(value.errors)
}

export function useAnalysis() {
  const [store, dispatch] = useAppStore()
  const sourceRef = useRef<EventSource | null>(null)
  const cancelMockRef = useRef<(() => void) | null>(null)
  const completedRef = useRef(false)
  const lastQueryRef = useRef('')

  const stopActiveStream = useCallback(() => {
    sourceRef.current?.close()
    sourceRef.current = null
    cancelMockRef.current?.()
    cancelMockRef.current = null
  }, [])

  const handleEvent = useCallback((event: AnalysisStreamEvent) => {
    if (event.agent === 'complete') {
      if (!isAnalyzeResponse(event.data)) {
        stopActiveStream()
        dispatch({ type: 'stream-error', message: 'The completed analysis response was incomplete. Try again.' })
        return
      }
      completedRef.current = true
      stopActiveStream()
      dispatch({ type: 'complete', analysis: event.data })
      if (event.data.errors.length > 0) {
        dispatch({ type: 'stream-error', message: event.data.errors.join(' ') })
      }
      return
    }

    if (!agentNames.has(event.agent) || (event.status !== 'started' && event.status !== 'done')) return
    dispatch({ type: 'agent-event', agent: event.agent, status: event.status, data: event.data })
    const errors = event.data.errors
    if (Array.isArray(errors) && errors.some((item) => typeof item === 'string')) {
      dispatch({
        type: 'stream-error',
        message: errors.filter((item): item is string => typeof item === 'string').join(' '),
      })
    }
  }, [dispatch, stopActiveStream])

  const receiveMessage = useCallback((message: MessageEvent<string>) => {
    try {
      const parsed: unknown = JSON.parse(message.data)
      if (!isRecord(parsed) || typeof parsed.agent !== 'string') return
      if (parsed.agent === 'complete') {
        handleEvent({ agent: 'complete', data: parsed.data as AnalyzeResponse })
        return
      }
      if (!agentNames.has(parsed.agent as AgentName)) return
      if (parsed.status !== 'started' && parsed.status !== 'done') return
      handleEvent({
        agent: parsed.agent as AgentName,
        status: parsed.status,
        data: isRecord(parsed.data) ? parsed.data : {},
      })
    } catch {
      stopActiveStream()
      dispatch({ type: 'stream-error', message: 'An analysis update could not be read. Try again.' })
    }
  }, [dispatch, handleEvent, stopActiveStream])

  const startAnalysis = useCallback((query: string) => {
    stopActiveStream()
    lastQueryRef.current = query
    completedRef.current = false
    dispatch({ type: 'begin', query })

    const mockMode = new URLSearchParams(window.location.search).get('mock') === '1'
    if (mockMode) {
      cancelMockRef.current = playMockStream(query, handleEvent)
      return
    }

    const baseUrl = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
    const params = new URLSearchParams({ query })
    const source = new EventSource(`${baseUrl}/api/v1/analyze/stream?${params.toString()}`)
    sourceRef.current = source
    source.onmessage = receiveMessage
    source.onerror = () => {
      source.close()
      if (sourceRef.current === source) sourceRef.current = null
      if (!completedRef.current) {
        dispatch({
          type: 'stream-error',
          message: 'The analysis connection closed before completion. Try again.',
        })
      }
    }
  }, [dispatch, handleEvent, receiveMessage, stopActiveStream])

  const retry = useCallback(() => {
    if (lastQueryRef.current) startAnalysis(lastQueryRef.current)
  }, [startAnalysis])

  const backToIntake = useCallback(() => {
    stopActiveStream()
    dispatch({ type: 'back-to-intake' })
  }, [dispatch, stopActiveStream])

  useEffect(() => stopActiveStream, [stopActiveStream])

  return { store, startAnalysis, retry, backToIntake }
}
