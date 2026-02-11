import { useState, useRef, useCallback, useEffect } from 'react'
import { startMonitor, connectWebSocket } from '../api'
import type { ProgressMessage } from '../types'

type MonitorStatus = 'idle' | 'connecting' | 'running' | 'completed' | 'failed'

interface UseMonitorReturn {
  status: MonitorStatus
  runId: string | null
  progress: ProgressMessage[]
  error: string | null
  start: (keywords: string[]) => Promise<void>
  reset: () => void
}

export function useMonitor(): UseMonitorReturn {
  const [status, setStatus] = useState<MonitorStatus>('idle')
  const [runId, setRunId] = useState<string | null>(null)
  const [progress, setProgress] = useState<ProgressMessage[]>([])
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const statusRef = useRef<MonitorStatus>('idle')

  // Keep the ref in sync with state
  useEffect(() => {
    statusRef.current = status
  }, [status])

  const cleanup = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  useEffect(() => {
    return cleanup
  }, [cleanup])

  const reset = useCallback(() => {
    cleanup()
    setStatus('idle')
    setRunId(null)
    setProgress([])
    setError(null)
  }, [cleanup])

  const start = useCallback(async (keywords: string[]) => {
    cleanup()
    setStatus('connecting')
    setProgress([])
    setError(null)

    try {
      const { run_id } = await startMonitor(keywords)
      setRunId(run_id)

      const ws = connectWebSocket(run_id)
      wsRef.current = ws

      ws.onopen = () => {
        setStatus('running')
      }

      ws.onmessage = (event) => {
        try {
          const msg: ProgressMessage = JSON.parse(event.data)
          setProgress((prev) => [...prev, msg])

          if (msg.type === 'completed') {
            setStatus('completed')
          } else if (msg.type === 'error') {
            setStatus('failed')
            setError(String(msg.data.message ?? 'Unknown error'))
          }
        } catch {
          // Ignore non-JSON messages
        }
      }

      ws.onerror = () => {
        setStatus('failed')
        setError('WebSocket connection error')
      }

      ws.onclose = (event) => {
        if (statusRef.current !== 'completed' && statusRef.current !== 'failed') {
          if (!event.wasClean) {
            setStatus('failed')
            setError('WebSocket connection closed unexpectedly')
          }
        }
      }
    } catch (err) {
      setStatus('failed')
      setError(err instanceof Error ? err.message : 'Failed to start monitor')
    }
  }, [cleanup])

  return { status, runId, progress, error, start, reset }
}
