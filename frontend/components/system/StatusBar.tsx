'use client'

import { useState, useEffect } from 'react'
import { useTradingStore, WsStatus } from '@/store/trading'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function Dot({ status }: { status: WsStatus }) {
  const color =
    status === 'connected'  ? 'bg-terminal-green shadow-[0_0_6px_#00d4a0]' :
    status === 'connecting' ? 'bg-terminal-yellow animate-pulse' :
                              'bg-terminal-red'
  return <span className={`inline-block w-1.5 h-1.5 rounded-full ${color}`} />
}

export function StatusBar() {
  const { wsPositions, wsMarket, wsSystem, botRunning, lastEvent, prices } = useTradingStore()

  const btcPrice = prices['BTC/USDT']

  // ── AI toggle state ───────────────────────
  const [aiEnabled, setAiEnabled]     = useState<boolean | null>(null)
  const [aiLoading, setAiLoading]     = useState(false)

  async function fetchAiStatus() {
    try {
      const res  = await fetch(`${BASE}/ai-trading/status`)
      const json = await res.json()
      setAiEnabled(json.data?.ai_trading_enabled ?? false)
    } catch {}
  }

  async function toggleAI() {
    setAiLoading(true)
    try {
      const res  = await fetch(`${BASE}/ai-trading/toggle`, { method: 'POST' })
      const json = await res.json()
      setAiEnabled(json.data?.ai_trading_enabled ?? false)
    } catch {
    } finally {
      setAiLoading(false)
    }
  }

  useEffect(() => {
    fetchAiStatus()
    const interval = setInterval(fetchAiStatus, 15_000)
    return () => clearInterval(interval)
  }, [])

  return (
    <header className="relative z-10 flex items-center justify-between px-4 py-2 border-b border-terminal-border bg-terminal-surface">
      {/* Left — brand */}
      <div className="flex items-center gap-3">
        <span className="font-display text-terminal-white font-semibold tracking-widest text-xs uppercase">
          MCP<span className="text-terminal-green">://</span>TRADING
        </span>
        <span className="text-terminal-dim text-xs">v1.0</span>
      </div>

      {/* Center — BTC price */}
      {btcPrice && (
        <div className="absolute left-1/2 -translate-x-1/2 flex items-center gap-2">
          <span className="text-terminal-dim text-xs">BTC/USDT</span>
          <span className="text-terminal-white font-mono font-semibold text-sm">
            ${btcPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>
      )}

      {/* Right — status indicators + AI toggle */}
      <div className="flex items-center gap-3 text-xs text-terminal-dim">
        {lastEvent && (
          <span className="text-terminal-yellow text-xs hidden md:block truncate max-w-48">
            {lastEvent}
          </span>
        )}

        <div className="flex items-center gap-1.5">
          <Dot status={wsPositions} />
          <span>POS</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Dot status={wsMarket} />
          <span>MKT</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Dot status={wsSystem} />
          <span>SYS</span>
        </div>

        <div className="flex items-center gap-1.5 pl-2 border-l border-terminal-border">
          <span className={`inline-block w-1.5 h-1.5 rounded-full ${
            botRunning ? 'bg-terminal-green animate-pulse' : 'bg-terminal-dim'
          }`} />
          <span className={botRunning ? 'text-terminal-green' : 'text-terminal-dim'}>
            BOT {botRunning ? 'LIVE' : 'OFF'}
          </span>
        </div>

        {/* AI toggle button */}
        <div className="pl-2 border-l border-terminal-border">
          <button
            onClick={toggleAI}
            disabled={aiLoading || aiEnabled === null}
            title={aiEnabled ? 'Click to disable AI filter' : 'Click to enable AI filter'}
            className={`
              flex items-center gap-1.5 text-xs font-mono uppercase tracking-widest
              border px-2 py-0.5 transition-all
              ${aiLoading || aiEnabled === null
                ? 'border-terminal-border text-terminal-dim cursor-not-allowed opacity-50'
                : aiEnabled
                ? 'border-terminal-blue/50 text-terminal-blue hover:border-terminal-red hover:text-terminal-red'
                : 'border-terminal-yellow/50 text-terminal-yellow hover:border-terminal-blue hover:text-terminal-blue'
              }
            `}
          >
            <span className={`inline-block w-1.5 h-1.5 rounded-full ${
              aiEnabled === null ? 'bg-terminal-dim' :
              aiEnabled ? 'bg-terminal-blue shadow-[0_0_4px_#4a9eff]' :
              'bg-terminal-yellow'
            }`} />
            {aiLoading ? '...' : aiEnabled ? 'AI ON' : 'AI OFF'}
          </button>
        </div>
      </div>
    </header>
  )
}
