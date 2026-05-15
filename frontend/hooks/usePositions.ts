'use client'

import { useEffect, useRef } from 'react'
import { useTradingStore } from '@/store/trading'

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'

export function usePositions() {
  const { setPositions, upsertPosition, setWsStatus, setLastEvent } = useTradingStore()
  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    function connect() {
      setWsStatus('positions', 'connecting')

      const ws = new WebSocket(`${WS_URL}/ws/positions`)
      wsRef.current = ws

      ws.onopen = () => {
        setWsStatus('positions', 'connected')
      }

      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)

          if (msg.event === 'ping') return

          setLastEvent(`${msg.event} @ ${new Date().toLocaleTimeString()}`)

          switch (msg.event) {
            case 'snapshot':
              setPositions(msg.payload || [])
              break
            case 'position.opened':
            case 'position.updated':
            case 'position.stop_loss_hit':
            case 'position.take_profit_hit':
              if (msg.payload) upsertPosition(msg.payload)
              break
            case 'position.closed':
              if (msg.payload) upsertPosition(msg.payload)
              break
          }
        } catch (err) {
          console.error('positions ws parse error', err)
        }
      }

      ws.onclose = () => {
        setWsStatus('positions', 'disconnected')
        retryRef.current = setTimeout(connect, 3000)
      }

      ws.onerror = () => {
        ws.close()
      }
    }

    connect()

    return () => {
      clearTimeout(retryRef.current)
      wsRef.current?.close()
    }
  }, [])
}
