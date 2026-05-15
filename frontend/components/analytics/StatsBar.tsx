'use client'

import { useTradingStore } from '@/store/trading'

function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-terminal-dim text-xs uppercase tracking-widest">{label}</span>
      <span className={`font-mono font-semibold text-sm ${color || 'text-terminal-white'}`}>
        {value}
      </span>
    </div>
  )
}

export function StatsBar() {
  const { stats, positions } = useTradingStore()

  const openPositions   = positions.filter(p => p.status === 'FILLED' || p.status === 'PARTIALLY_FILLED')
  const totalUnrealized = openPositions.reduce((sum, p) => sum + (p.unrealized_pnl || 0), 0)
  const totalRealized   = stats?.total_realized ?? 0
  const exposure        = stats?.total_exposure ?? 0

  const fmt = (n: number) =>
    (n >= 0 ? '+' : '') +
    n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

  const pnlColor = (n: number) =>
    n > 0 ? 'text-terminal-green' : n < 0 ? 'text-terminal-red' : 'text-terminal-text'

  return (
    <div className="relative z-10 flex items-center gap-6 px-4 py-2 border-b border-terminal-border bg-terminal-surface/50">
      <Stat label="Open" value={`${openPositions.length} / 3`} color="text-terminal-white" />
      <div className="w-px h-6 bg-terminal-border" />
      <Stat label="Unrealized" value={`$${fmt(totalUnrealized)}`} color={pnlColor(totalUnrealized)} />
      <div className="w-px h-6 bg-terminal-border" />
      <Stat label="Realized" value={`$${fmt(totalRealized)}`} color={pnlColor(totalRealized)} />
      <div className="w-px h-6 bg-terminal-border" />
      <Stat
        label="Exposure"
        value={exposure > 0 ? `$${exposure.toLocaleString('en-US', { maximumFractionDigits: 0 })}` : '—'}
        color="text-terminal-blue"
      />
      <div className="w-px h-6 bg-terminal-border" />
      <Stat label="Mode" value="PAPER" color="text-terminal-yellow" />
    </div>
  )
}
