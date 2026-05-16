'use client'

import { useAIMetricsStore, RecentCall } from '@/store/ai_metrics'
import { useAIMetrics } from '@/hooks/useAIMetrics'

// ─────────────────────────────────────────────
// Stat cell
// ─────────────────────────────────────────────

function Stat({
  label,
  value,
  sub,
  color,
}: {
  label: string
  value: string
  sub?:  string
  color?: string
}) {
  return (
    <div className="flex flex-col gap-0.5 p-3 border border-terminal-border">
      <span className="text-terminal-dim text-xs uppercase tracking-widest">{label}</span>
      <span className={`font-mono font-bold text-lg leading-none ${color ?? 'text-terminal-white'}`}>
        {value}
      </span>
      {sub && <span className="text-terminal-dim text-xs">{sub}</span>}
    </div>
  )
}

// ─────────────────────────────────────────────
// Bar progress
// ─────────────────────────────────────────────

function Bar({ value, color }: { value: number; color: string }) {
  const pct = Math.min(Math.max(value * 100, 0), 100)
  return (
    <div className="w-full h-1.5 bg-terminal-border rounded-full overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-500 ${color}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}

// ─────────────────────────────────────────────
// Section header
// ─────────────────────────────────────────────

function SectionHeader({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 pt-2">
      <span className="text-terminal-dim text-xs uppercase tracking-widest whitespace-nowrap">
        {label}
      </span>
      <div className="flex-1 h-px bg-terminal-border" />
    </div>
  )
}

// ─────────────────────────────────────────────
// Recent call row
// ─────────────────────────────────────────────

function CallRow({ call }: { call: RecentCall }) {
  const isSkip    = call.status === 'SKIP'
  const isHold    = call.ai_result === 'HOLD'
  const strengthPct = Math.round(call.strength * 100)

  return (
    <div className="flex items-center gap-2 py-1 border-b border-terminal-border/30 text-xs font-mono">
      {/* Time */}
      <span className="text-terminal-dim w-20 flex-shrink-0">
        {new Date(call.ts).toLocaleTimeString('en-US', {
          hour: '2-digit', minute: '2-digit', second: '2-digit',
        })}
      </span>

      {/* Symbol + signal */}
      <span className="text-terminal-text w-20 flex-shrink-0">{call.symbol}</span>
      <span className={`w-10 flex-shrink-0 font-bold ${
        call.signal === 'BUY' ? 'text-terminal-green' : 'text-terminal-red'
      }`}>
        {call.signal}
      </span>

      {/* Strength bar */}
      <div className="flex items-center gap-1 w-24 flex-shrink-0">
        <div className="flex-1">
          <Bar
            value={call.strength}
            color={call.strength >= 0.75 ? 'bg-terminal-green' : call.strength >= 0.5 ? 'bg-terminal-yellow' : 'bg-terminal-red'}
          />
        </div>
        <span className="text-terminal-dim text-xs w-8 text-right">{strengthPct}%</span>
      </div>

      {/* Status badge */}
      <span className={`px-1.5 py-0.5 border text-xs flex-shrink-0 ${
        isSkip
          ? 'border-terminal-green/40 text-terminal-green'
          : isHold
          ? 'border-terminal-red/40 text-terminal-red'
          : 'border-terminal-blue/40 text-terminal-blue'
      }`}>
        {isSkip ? 'SKIP' : call.ai_result ?? 'AI'}
      </span>
    </div>
  )
}

// ─────────────────────────────────────────────
// Main component
// ─────────────────────────────────────────────

export function AITokenMonitor() {
  const { data, loading } = useAIMetricsStore()
  const { resetMetrics }  = useAIMetrics()

  if (!data && loading) {
    return (
      <div className="flex items-center justify-center h-32 text-terminal-dim text-xs animate-pulse">
        LOADING_
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center h-32 text-terminal-dim text-xs">
        <span>NO DATA — bot not running<span className="blink ml-1">_</span></span>
      </div>
    )
  }

  const fmt = (n: number, d = 0) =>
    n.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d })

  return (
    <div className="flex flex-col h-full overflow-auto">

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-terminal-border sticky top-0 bg-terminal-bg z-10">
        <div className="flex items-center gap-2">
          <span className="text-terminal-dim text-xs uppercase tracking-widest">
            AI Filter Monitor
          </span>
          <span className="text-terminal-dim text-xs font-mono">
            — {data.session_duration_min}m session
          </span>
        </div>
        <button
          onClick={resetMetrics}
          className="text-terminal-dim text-xs font-mono border border-terminal-border px-2 py-0.5 hover:border-terminal-red hover:text-terminal-red transition-colors"
        >
          [ RESET ]
        </button>
      </div>

      <div className="p-4 flex flex-col gap-3">

        {/* Skip rate highlight */}
        <div className="p-3 border border-terminal-border bg-terminal-surface/40">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-terminal-dim text-xs uppercase tracking-widest">
              Skip Rate (AI saved)
            </span>
            <span className={`font-mono font-bold text-lg ${
              data.skip_rate >= 0.5 ? 'text-terminal-green' : 'text-terminal-yellow'
            }`}>
              {fmt(data.skip_rate * 100, 1)}%
            </span>
          </div>
          <Bar
            value={data.skip_rate}
            color={data.skip_rate >= 0.5 ? 'bg-terminal-green' : 'bg-terminal-yellow'}
          />
          <div className="flex justify-between mt-1">
            <span className="text-terminal-dim text-xs">
              {data.calls_skipped} skipped · {data.calls_made} AI calls
            </span>
            <span className="text-terminal-dim text-xs">
              {data.total_signals} total signals
            </span>
          </div>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-1">
          <SectionHeader label="Token Budget" />

          <Stat
            label="Tokens Used"
            value={fmt(data.estimated_tokens)}
            sub="this session"
            color="text-terminal-blue"
          />
          <Stat
            label="Est. Cost"
            value={`$${data.estimated_cost_usd.toFixed(5)}`}
            sub="~$0.14/1M tokens"
            color="text-terminal-text"
          />

          <SectionHeader label="AI Decisions" />

          <Stat
            label="BUY"
            value={fmt(data.ai_buy_signals)}
            color="text-terminal-green"
          />
          <Stat
            label="SELL"
            value={fmt(data.ai_sell_signals)}
            color="text-terminal-red"
          />
          <Stat
            label="HOLD (filtered)"
            value={fmt(data.ai_hold_signals)}
            sub={`${fmt(data.ai_hold_rate * 100, 1)}% filter rate`}
            color="text-terminal-dim"
          />
          <Stat
            label="Last Strength"
            value={data.last_signal_strength != null
              ? `${fmt(data.last_signal_strength * 100, 1)}%`
              : '—'
            }
            color={
              data.last_signal_strength == null ? 'text-terminal-dim'
              : data.last_signal_strength >= 0.75 ? 'text-terminal-green'
              : data.last_signal_strength >= 0.5  ? 'text-terminal-yellow'
              : 'text-terminal-red'
            }
          />
        </div>

        {/* Recent calls */}
        {data.recent_calls.length > 0 && (
          <>
            <SectionHeader label={`Recent Calls (last ${data.recent_calls.length})`} />
            <div className="flex flex-col">
              {[...data.recent_calls].reverse().map((call, i) => (
                <CallRow key={i} call={call} />
              ))}
            </div>
          </>
        )}

        {data.recent_calls.length === 0 && (
          <div className="flex items-center justify-center h-16 text-terminal-dim text-xs">
            <span>Waiting for signals<span className="blink ml-1">_</span></span>
          </div>
        )}

      </div>
    </div>
  )
}
