'use client'

import { useTradingStore } from '@/store/trading'
import { PositionRow } from './PositionRow'

const HEADERS = ['Symbol', 'Entry', 'Price', 'Qty', 'PnL', 'SL / TP', 'Strategy', 'Status', '']

export function PositionsPanel() {
  const { positions, prices } = useTradingStore()

  const sorted = [...positions].sort((a, b) => {
    // Open positions first
    const aOpen = a.status === 'FILLED' || a.status === 'PARTIALLY_FILLED'
    const bOpen = b.status === 'FILLED' || b.status === 'PARTIALLY_FILLED'
    if (aOpen !== bOpen) return aOpen ? -1 : 1
    return (b.id - a.id)
  })

  return (
    <div className="relative z-10 flex flex-col h-full">
      {/* Panel header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-terminal-border">
        <div className="flex items-center gap-2">
          <span className="text-terminal-dim text-xs uppercase tracking-widest">Positions</span>
          <span className="text-terminal-green text-xs font-mono">
            [{positions.filter(p => p.status === 'FILLED' || p.status === 'PARTIALLY_FILLED').length} open]
          </span>
        </div>
        <span className="text-terminal-dim text-xs">
          {positions.length} total
        </span>
      </div>

      {/* Table */}
      <div className="overflow-auto flex-1">
        {positions.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-terminal-dim text-xs">
            <span>NO POSITIONS<span className="blink ml-1">_</span></span>
          </div>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-terminal-border">
                {HEADERS.map((h) => (
                  <th
                    key={h}
                    className="px-3 py-2 text-left text-terminal-dim font-normal uppercase tracking-widest text-xs whitespace-nowrap"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((position) => (
                <PositionRow
                  key={position.id}
                  position={position}
                  livePrice={prices[position.symbol]}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
