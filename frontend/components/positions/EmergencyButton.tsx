'use client'

import { useState } from 'react'
import { api } from '@/lib/api'
import { useTradingStore } from '@/store/trading'

export function EmergencyButton() {
  const [confirming, setConfirming] = useState(false)
  const [loading, setLoading]       = useState(false)
  const { positions, setLastEvent }  = useTradingStore()

  const openCount = positions.filter(
    p => p.status === 'FILLED' || p.status === 'PARTIALLY_FILLED'
  ).length

  async function handleClick() {
    if (!confirming) {
      setConfirming(true)
      setTimeout(() => setConfirming(false), 3000)
      return
    }
    setLoading(true)
    try {
      await api.emergencyClose()
      setLastEvent('⚠ EMERGENCY CLOSE SENT')
    } catch {
      alert('Emergency close failed — check backend logs')
    } finally {
      setLoading(false)
      setConfirming(false)
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={loading || openCount === 0}
      className={`
        relative text-xs font-mono font-bold px-3 py-1.5 border transition-all
        ${confirming
          ? 'border-terminal-red text-terminal-red bg-terminal-red/10 animate-pulse'
          : openCount === 0
          ? 'border-terminal-border text-terminal-dim cursor-not-allowed'
          : 'border-terminal-border text-terminal-dim hover:border-terminal-red hover:text-terminal-red'
        }
      `}
    >
      {loading ? 'CLOSING...' : confirming ? '⚠ CONFIRM CLOSE ALL' : `EMERGENCY CLOSE (${openCount})`}
    </button>
  )
}
