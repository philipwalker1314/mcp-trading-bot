'use client'

import { useEffect, useRef } from 'react'
import { useAnalyticsStore } from '@/store/analytics'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function fetchJSON<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${BASE}${path}`)
    if (!res.ok) return null
    const json = await res.json()
    return json.data ?? null
  } catch {
    return null
  }
}

export function useAnalytics() {
  const {
    setEquityCurve,
    setSharpe,
    setDrawdown,
    setTradeStats,
    setAiPerformance,
    setLoading,
  } = useAnalyticsStore()

  const pollRef = useRef<ReturnType<typeof setInterval>>()

  async function fetchAll() {
    setLoading(true)
    try {
      const [curve, sharpe, drawdown, tradeStats, aiPerf] = await Promise.all([
        fetchJSON<any[]>('/analytics/equity-curve?days=30'),
        fetchJSON<any>('/analytics/sharpe?days=30'),
        fetchJSON<any>('/analytics/drawdown?days=30'),
        fetchJSON<any>('/analytics/trade-stats'),
        fetchJSON<any>('/analytics/ai-performance'),
      ])

      if (curve)      setEquityCurve(curve)
      if (sharpe)     setSharpe(sharpe)
      if (drawdown)   setDrawdown(drawdown)
      if (tradeStats) setTradeStats(tradeStats)
      if (aiPerf)     setAiPerformance(aiPerf)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAll()
    pollRef.current = setInterval(fetchAll, 60_000)
    return () => clearInterval(pollRef.current)
  }, [])
}
