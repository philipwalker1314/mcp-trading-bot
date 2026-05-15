'use client'

import { useEffect, useRef, useState } from 'react'
import { Position } from '@/store/trading'
import { api } from '@/lib/api'

interface Props {
  position: Position
  livePrice?: number
}

export function PositionRow({ position, livePrice }: Props) {
  const prevPnl   = useRef<number>(position.unrealized_pnl)
  const [flash, setFlash] = useState<'green' | 'red' | null>(null)

  // Live unrealized PnL from price feed
  const livePnl = livePrice
    ? (position.side === 'BUY'
        ? (livePrice - position.avg_entry_price) * position.remaining_qty
        : (position.avg_entry_price - livePrice) * position.remaining_qty)
    : position.unrealized_pnl

  // Flash on PnL change
  useEffect(() => {
    if (Math.abs(livePnl - prevPnl.current) < 0.001) return
    setFlash(livePnl > prevPnl.current ? 'green' : 'red')
    prevPnl.current = livePnl
    const t = setTimeout(() => setFlash(null), 500)
    return () => clearTimeout(t)
  }, [livePnl])

  const pnlColor  = livePnl >= 0 ? 'text-terminal-green' : 'text-terminal-red'
  const sideColor = position.side === 'BUY' ? 'text-terminal-green' : 'text-terminal-red'
  const rowFlash  = flash === 'green' ? 'flash-green' : flash === 'red' ? 'flash-red' : ''

  const fmt2 = (n: number) => n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  const fmtPnl = (n: number) => (n >= 0 ? '+' : '') + fmt2(n)

  const isOpen = position.status === 'FILLED' || position.status === 'PARTIALLY_FILLED'

  return (
    <tr className={`border-b border-terminal-border/50 hover:bg-terminal-muted/30 transition-colors ${rowFlash}`}>
      {/* Symbol + side */}
      <td className="px-3 py-2">
        <div className="flex items-center gap-2">
          <span className={`text-xs font-bold px-1 py-0.5 border ${
            position.side === 'BUY'
              ? 'border-terminal-green/40 text-terminal-green'
              : 'border-terminal-red/40 text-terminal-red'
          }`}>
            {position.side}
          </span>
          <span className="text-terminal-white font-semibold">{position.symbol}</span>
        </div>
      </td>

      {/* Entry */}
      <td className="px-3 py-2 text-terminal-text font-mono">
        ${fmt2(position.avg_entry_price)}
      </td>

      {/* Live price */}
      <td className="px-3 py-2 font-mono">
        {livePrice
          ? <span className="text-terminal-white">${fmt2(livePrice)}</span>
          : <span className="text-terminal-dim">—</span>
        }
      </td>

      {/* Qty */}
      <td className="px-3 py-2 text-terminal-text font-mono">
        {position.remaining_qty.toFixed(4)}
      </td>

      {/* Unrealized PnL */}
      <td className={`px-3 py-2 font-mono font-semibold ${pnlColor}`}>
        {isOpen ? fmtPnl(livePnl) : '—'}
      </td>

      {/* SL / TP */}
      <td className="px-3 py-2 text-terminal-dim font-mono text-xs">
        <div className="flex flex-col">
          <span className="text-terminal-red/70">SL {position.stop_loss ? fmt2(position.stop_loss) : '—'}</span>
          <span className="text-terminal-green/70">TP {position.take_profit ? fmt2(position.take_profit) : '—'}</span>
        </div>
      </td>

      {/* Strategy */}
      <td className="px-3 py-2 text-terminal-dim text-xs">
        {position.strategy || '—'}
      </td>

      {/* Status */}
      <td className="px-3 py-2">
        <span className={`text-xs px-1.5 py-0.5 ${
          isOpen
            ? 'text-terminal-green border border-terminal-green/30'
            : 'text-terminal-dim border border-terminal-dim/30'
        }`}>
          {position.status}
        </span>
      </td>

      {/* Close button */}
      <td className="px-3 py-2">
        {isOpen && livePrice && (
          <button
            onClick={async () => {
              if (!confirm(`Close position ${position.id} at $${fmt2(livePrice)}?`)) return
              try {
                await api.closePosition(position.id, livePrice)
              } catch (e) {
                alert('Close failed — check backend logs')
              }
            }}
            className="text-xs text-terminal-dim border border-terminal-border px-2 py-0.5 hover:border-terminal-red hover:text-terminal-red transition-colors"
          >
            CLOSE
          </button>
        )}
      </td>
    </tr>
  )
}
