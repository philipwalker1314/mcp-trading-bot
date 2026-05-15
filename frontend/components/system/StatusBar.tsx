'use client'

import { useTradingStore, WsStatus } from '@/store/trading'

function Dot({ status }: { status: WsStatus }) {
  const color =
    status === 'connected'    ? 'bg-terminal-green shadow-[0_0_6px_#00d4a0]' :
    status === 'connecting'   ? 'bg-terminal-yellow animate-pulse' :
                                'bg-terminal-red'
  return <span className={`inline-block w-1.5 h-1.5 rounded-full ${color}`} />
}

export function StatusBar() {
  const { wsPositions, wsMarket, wsSystem, botRunning, lastEvent, prices } = useTradingStore()

  const btcPrice = prices['BTC/USDT']

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

      {/* Right — status indicators */}
      <div className="flex items-center gap-4 text-xs text-terminal-dim">
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
          <span
            className={`inline-block w-1.5 h-1.5 rounded-full ${
              botRunning ? 'bg-terminal-green animate-pulse' : 'bg-terminal-dim'
            }`}
          />
          <span className={botRunning ? 'text-terminal-green' : 'text-terminal-dim'}>
            BOT {botRunning ? 'LIVE' : 'OFF'}
          </span>
        </div>
      </div>
    </header>
  )
}
