'use client'

import dynamic from 'next/dynamic'
import { useState } from 'react'
import { usePositions }    from '@/hooks/usePositions'
import { useMarket }       from '@/hooks/useMarket'
import { useSystem }       from '@/hooks/useSystem'
import { useAnalytics }    from '@/hooks/useAnalytics'
import { StatusBar }       from '@/components/system/StatusBar'
import { StatsBar }        from '@/components/analytics/StatsBar'
import { PositionsPanel }  from '@/components/positions/PositionsPanel'
import { EmergencyButton } from '@/components/positions/EmergencyButton'
import { MetricsPanel }    from '@/components/analytics/MetricsPanel'

const PriceChart = dynamic(
  () => import('@/components/chart/PriceChart').then(m => m.PriceChart),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-full text-terminal-dim text-xs">
        LOADING CHART<span className="blink ml-1">_</span>
      </div>
    ),
  }
)

const EquityChart = dynamic(
  () => import('@/components/analytics/EquityChart').then(m => m.EquityChart),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-full text-terminal-dim text-xs">
        LOADING CHART<span className="blink ml-1">_</span>
      </div>
    ),
  }
)

// Hook provider invisible
function WsProviders() {
  usePositions()
  useMarket()
  useSystem()
  useAnalytics()
  return null
}

// Tab button
function TabButton({
  label,
  active,
  onClick,
}: {
  label: string
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={`
        px-4 py-1.5 text-xs font-mono uppercase tracking-widest border-b-2 transition-colors
        ${active
          ? 'border-terminal-green text-terminal-green'
          : 'border-transparent text-terminal-dim hover:text-terminal-text hover:border-terminal-border'
        }
      `}
    >
      {label}
    </button>
  )
}

// ─────────────────────────────────────────────
// Dashboard principal
// ─────────────────────────────────────────────

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<'trading' | 'analytics'>('trading')

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <WsProviders />

      {/* Header universal */}
      <StatusBar />
      <StatsBar />

      {/* Tabs de navegación */}
      <div className="relative z-10 flex items-center gap-0 px-4 border-b border-terminal-border bg-terminal-surface/30">
        <TabButton
          label="[ TRADING ]"
          active={activeTab === 'trading'}
          onClick={() => setActiveTab('trading')}
        />
        <TabButton
          label="[ ANALYTICS ]"
          active={activeTab === 'analytics'}
          onClick={() => setActiveTab('analytics')}
        />
      </div>

      {/* Vista TRADING */}
      {activeTab === 'trading' && (
        <div className="flex flex-1 overflow-hidden">
          {/* Chart */}
          <div className="flex-1 border-r border-terminal-border overflow-hidden">
            <PriceChart />
          </div>

          {/* Panel derecho: posiciones + emergency */}
          <div className="w-[600px] flex flex-col overflow-hidden">
            <div className="flex-1 overflow-hidden">
              <PositionsPanel />
            </div>
            <div className="px-4 py-2 border-t border-terminal-border flex items-center justify-between">
              <span className="text-terminal-dim text-xs">
                PAPER MODE — no real orders
              </span>
              <EmergencyButton />
            </div>
          </div>
        </div>
      )}

      {/* Vista ANALYTICS */}
      {activeTab === 'analytics' && (
        <div className="flex flex-1 overflow-hidden">
          {/* Equity chart — lado izquierdo */}
	  <div className="flex-1 border-r border-terminal-border overflow-hidden" style={{ minHeight: 0 }}>
            <EquityChart />
          </div>

          {/* Metrics panel — lado derecho */}
          <div className="w-[420px] overflow-hidden">
            <MetricsPanel />
          </div>
        </div>
      )}
    </div>
  )
}
