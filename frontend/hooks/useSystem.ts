'use client'

import { useEffect, useRef } from 'react'
import { useTradingStore } from '@/store/trading'
import { api } from '@/lib/api'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'

export function useSystem() {
  const { setWsStatus, setBotRunning, setStats, setLastEvent } = useTradingStore()
  const wsRef    = useRef<WebSocket | null>(null)
  const retryRef = useRef<ReturnType<typeof setTimeout>>()
  const pollRef  = useRef<ReturnType<typeof setInterval>>()

  useEffect(() => {
    // WebSocket for system events
    function connect() {
      setWsStatus('system', 'connecting')
      const ws = new WebSocket(`${WS_URL}/ws/system`)
      wsRef.current = ws

      ws.onopen  = () => setWsStatus('system', 'connected')

      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          if (msg.event === 'ping') return
          if (msg.event === 'risk.emergency_stop') {
            setLastEvent('⚠ EMERGENCY STOP TRIGGERED')
          }
        } catch {}
      }

      ws.onclose = () => {
        setWsStatus('system', 'disconnected')
        retryRef.current = setTimeout(connect, 3000)
      }

      ws.onerror = () => ws.close()
    }

    connect()

    // Poll health + summary every 10s
    async function pollStats() {
      try {
        const [health, summary] = await Promise.all([
          api.health(),
          api.summary(),
        ])
        setBotRunning(health.trading_bot_running)
        if (summary.data) setStats(summary.data)
      } catch {}
    }

    pollStats()
    pollRef.current = setInterval(pollStats, 10_000)

    return () => {
      clearTimeout(retryRef.current)
      clearInterval(pollRef.current)
      wsRef.current?.close()
    }
  }, [])
}
