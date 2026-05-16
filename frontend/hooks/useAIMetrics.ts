'use client'

import { useEffect, useRef } from 'react'
import { useAIMetricsStore } from '@/store/ai_metrics'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function useAIMetrics() {
  const { setData, setLoading } = useAIMetricsStore()
  const pollRef = useRef<ReturnType<typeof setInterval>>()

  async function fetchMetrics() {
    setLoading(true)
    try {
      const res = await fetch(`${BASE}/ai-metrics/`)
      if (!res.ok) return
      const json = await res.json()
      if (json.data) setData(json.data)
    } catch {
      // silent — backend may not be running
    } finally {
      setLoading(false)
    }
  }

  async function resetMetrics() {
    try {
      await fetch(`${BASE}/ai-metrics/reset`, { method: 'POST' })
      await fetchMetrics()
    } catch {}
  }

  useEffect(() => {
    fetchMetrics()
    pollRef.current = setInterval(fetchMetrics, 10_000)
    return () => clearInterval(pollRef.current)
  }, [])

  return { fetchMetrics, resetMetrics }
}
