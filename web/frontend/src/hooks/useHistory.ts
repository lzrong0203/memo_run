import { useState, useEffect, useCallback } from 'react'
import { getHistory } from '../api'

interface HistoryRun {
  id: string
  status: string
  keywords: string[]
  created_at: string
  completed_at: string | null
  stats: { valid_count: number } | null
}

interface UseHistoryReturn {
  runs: HistoryRun[]
  total: number
  page: number
  loading: boolean
  error: string | null
  fetchPage: (page: number) => Promise<void>
}

export function useHistory(): UseHistoryReturn {
  const [runs, setRuns] = useState<HistoryRun[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchPage = useCallback(async (targetPage: number) => {
    setLoading(true)
    setError(null)

    try {
      const data = await getHistory(targetPage)
      setRuns(data.runs)
      setTotal(data.total)
      setPage(data.page)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch history')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchPage(1)
  }, [fetchPage])

  return { runs, total, page, loading, error, fetchPage }
}
