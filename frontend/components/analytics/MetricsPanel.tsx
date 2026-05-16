'use client'

import { useAnalyticsStore } from '@/store/analytics'

// ─────────────────────────────────────────────
// Celda individual de métrica
// ─────────────────────────────────────────────

interface MetricCellProps {
  label:    string
  value:    string
  sub?:     string
  color?:   string
  accent?:  boolean
}

function MetricCell({ label, value, sub, color, accent }: MetricCellProps) {
  return (
    <div className={`
      flex flex-col gap-1 p-3 border border-terminal-border
      ${accent ? 'bg-terminal-surface/80' : 'bg-transparent'}
    `}>
      <span className="text-terminal-dim text-xs uppercase tracking-widest leading-none">
        {label}
      </span>
      <span className={`font-mono font-bold text-lg leading-none ${color || 'text-terminal-white'}`}>
        {value}
      </span>
      {sub && (
        <span className="text-terminal-dim text-xs leading-none">{sub}</span>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────
// Separador de sección
// ─────────────────────────────────────────────

function SectionLabel({ label }: { label: string }) {
  return (
    <div className="col-span-full flex items-center gap-3 pt-1">
      <span className="text-terminal-dim text-xs uppercase tracking-widest">{label}</span>
      <div className="flex-1 h-px bg-terminal-border" />
    </div>
  )
}

// ─────────────────────────────────────────────
// MetricsPanel
// ─────────────────────────────────────────────

export function MetricsPanel() {
  const { sharpe, drawdown, tradeStats, aiPerformance, loading } = useAnalyticsStore()

  const fmt = (n: number, decimals = 2) =>
    n.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })

  const pnlColor = (n: number) =>
    n > 0 ? 'text-terminal-green' : n < 0 ? 'text-terminal-red' : 'text-terminal-text'

  const sharpeColor = (n: number) =>
    n >= 1.5 ? 'text-terminal-green'
    : n >= 0.5 ? 'text-terminal-yellow'
    : n < 0 ? 'text-terminal-red'
    : 'text-terminal-text'

  // ── Sharpe ────────────────────────────────
  const sharpeVal   = sharpe?.sharpe_ratio ?? 0
  const sharpeLabel = sharpe?.insufficient_data
    ? 'INSUF. DATOS'
    : fmt(sharpeVal, 2)

  // ── Drawdown ──────────────────────────────
  const ddAbs = drawdown?.max_drawdown ?? 0
  const ddPct = drawdown?.max_drawdown_pct ?? 0

  // ── Trade stats ───────────────────────────
  const totalClosed  = tradeStats?.total_closed ?? 0
  const avgDuration  = tradeStats?.avg_duration_human ?? '—'

  // ── AI performance ────────────────────────
  const winRate      = aiPerformance?.overall_win_rate ?? 0
  const totalTrades  = aiPerformance?.total_trades ?? 0
  const aiValidated  = aiPerformance?.ai_validated ?? 0
  const totalPnl     = aiPerformance?.total_realized_pnl ?? 0

  const hasData = totalTrades > 0

  return (
    <div className="flex flex-col h-full overflow-auto">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-terminal-border sticky top-0 bg-terminal-bg z-10">
        <span className="text-terminal-dim text-xs uppercase tracking-widest">
          Métricas de Performance
        </span>
        {loading && (
          <span className="text-terminal-dim text-xs animate-pulse">CARGANDO_</span>
        )}
      </div>

      <div className="p-3 flex flex-col gap-1 flex-1">

        {/* Sin datos */}
        {!hasData && !loading && (
          <div className="flex items-center justify-center h-24 text-terminal-dim text-xs">
            <span>SIN TRADES CERRADOS<span className="blink ml-1">_</span></span>
          </div>
        )}

        {/* Grid de métricas */}
        <div className="grid grid-cols-2 gap-1">

          {/* — Riesgo ajustado — */}
          <SectionLabel label="Riesgo Ajustado" />

          <MetricCell
            label="Sharpe Ratio"
            value={sharpeLabel}
            sub={`${sharpe?.days_used ?? 0}d · anualizado`}
            color={sharpeColor(sharpeVal)}
            accent
          />
          <MetricCell
            label="Max Drawdown"
            value={ddAbs > 0 ? `-$${fmt(ddAbs)}` : '—'}
            sub={ddPct > 0 ? `-${fmt(ddPct, 1)}%` : undefined}
            color={ddAbs > 0 ? 'text-terminal-red' : 'text-terminal-dim'}
            accent
          />

          {/* — Trades — */}
          <SectionLabel label="Rendimiento de Trades" />

          <MetricCell
            label="Win Rate"
            value={hasData ? `${(winRate * 100).toFixed(1)}%` : '—'}
            color={winRate >= 0.5 ? 'text-terminal-green' : winRate > 0 ? 'text-terminal-yellow' : 'text-terminal-dim'}
          />
          <MetricCell
            label="Total PnL"
            value={hasData ? `${totalPnl >= 0 ? '+' : ''}$${fmt(totalPnl)}` : '—'}
            color={pnlColor(totalPnl)}
          />
          <MetricCell
            label="Trades Cerrados"
            value={totalClosed > 0 ? String(totalClosed) : '—'}
            color="text-terminal-white"
          />
          <MetricCell
            label="Duración Media"
            value={totalClosed > 0 ? avgDuration : '—'}
            color="text-terminal-text"
          />

          {/* — AI Filter — */}
          <SectionLabel label="AI Filter" />

          <MetricCell
            label="Señales AI"
            value={aiValidated > 0 ? String(aiValidated) : '—'}
            sub={totalTrades > 0 ? `de ${totalTrades} totales` : undefined}
            color="text-terminal-blue"
          />
          <MetricCell
            label="Confianza Media"
            value={aiPerformance?.avg_ai_confidence
              ? `${(aiPerformance.avg_ai_confidence * 100).toFixed(0)}%`
              : '—'}
            color="text-terminal-text"
          />

          {/* — Por razón de cierre — */}
          {tradeStats?.by_close_reason && Object.keys(tradeStats.by_close_reason).length > 0 && (
            <>
              <SectionLabel label="Cierres por Razón" />
              {Object.entries(tradeStats.by_close_reason).map(([reason, data]) => (
                <MetricCell
                  key={reason}
                  label={reason.replace('_', ' ')}
                  value={String(data.count)}
                  sub={`~${Math.floor(data.avg_sec / 60)}m avg`}
                  color={
                    reason === 'TAKE_PROFIT' ? 'text-terminal-green'
                    : reason === 'STOP_LOSS' || reason === 'TRAILING_STOP' ? 'text-terminal-red'
                    : reason === 'EMERGENCY' ? 'text-terminal-yellow'
                    : 'text-terminal-text'
                  }
                />
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
