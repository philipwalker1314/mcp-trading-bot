'use client'

import { useEffect, useRef } from 'react'
import { useTradingStore } from '@/store/trading'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'

export function useMarket() {
  const { setPrice, setWsStatus } = useTradingStore()
  const wsRef   = useRef<WebSocket | null>(null)
  const retryRef = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    function connect() {
      setWsStatus('market', 'connecting')

      const ws = new WebSocket(`${WS_URL}/ws/market`)
      wsRef.current = ws

      ws.onopen  = () => setWsStatus('market', 'connected')

      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          if (msg.event === 'ping') return
          if (msg.event === 'market.tick' && msg.payload?.symbol) {
            setPrice(msg.payload.symbol, parseFloat(msg.payload.price))
          }
        } catch (err) {
          console.error('market ws parse error', err)
        }
      }

      ws.onclose = () => {
        setWsStatus('market', 'disconnected')
        retryRef.current = setTimeout(connect, 3000)
      }

      ws.onerror = () => ws.close()
    }

    connect()

    return () => {
      clearTimeout(retryRef.current)
      wsRef.current?.close()
    }
  }, [])
}
