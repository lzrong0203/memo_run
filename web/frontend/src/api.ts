import type { ReportData } from './types'

const API_BASE = '/api'

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

function validateRunId(runId: string): void {
  if (!UUID_REGEX.test(runId)) {
    throw new Error('Invalid run ID format')
  }
}

export async function startMonitor(keywords: string[]): Promise<{ run_id: string }> {
  const res = await fetch(`${API_BASE}/monitor/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ keywords }),
  })
  if (!res.ok) throw new Error(`Failed to start monitor: ${res.statusText}`)
  return res.json()
}

export async function getReport(runId: string): Promise<ReportData> {
  validateRunId(runId)
  const res = await fetch(`${API_BASE}/reports/${encodeURIComponent(runId)}`)
  if (!res.ok) throw new Error(`Failed to get report: ${res.statusText}`)
  return res.json()
}

export async function getHistory(page = 1, limit = 20): Promise<{
  runs: Array<{
    id: string
    status: string
    keywords: string[]
    created_at: string
    completed_at: string | null
    stats: { valid_count: number } | null
  }>
  total: number
  page: number
  limit: number
}> {
  const safePage = Math.max(1, Math.floor(page))
  const safeLimit = Math.min(100, Math.max(1, Math.floor(limit)))
  const res = await fetch(`${API_BASE}/history?page=${safePage}&limit=${safeLimit}`)
  if (!res.ok) throw new Error(`Failed to get history: ${res.statusText}`)
  return res.json()
}

export function connectWebSocket(runId: string): WebSocket {
  validateRunId(runId)
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  return new WebSocket(`${protocol}//${host}/api/monitor/ws/${encodeURIComponent(runId)}`)
}
