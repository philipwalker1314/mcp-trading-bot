'use client'

import dynamic from 'next/dynamic'
import { useState } from 'react'
import { usePositions }      from '@/hooks/usePositions'
import { useMarket }         from '@/hooks/useMarket'
import { useSystem }         from '@/hooks/useSystem'
import { useAnalytics }      from '@/hooks/useAnalytics'
import { useStrategies }     from '@/hooks/useStrategies'
import { useAIMetrics }      from '@/hooks/useAIMetrics'
import { useStrategiesStore } from '@/store/strategies'
import { StatusBar }         from '@/components/system/StatusBar'
import { StatsBar }          from '@/components/analytics/StatsBar'
import { PositionsPanel }    from '@/components/positions/PositionsPanel'
import { EmergencyButton }   from '@/components/positions/EmergencyButton'
import { MetricsPanel }      from '@/components/analytics/MetricsPanel'
import { StrategyList }      from '@/components/strategies/StrategyList'
import { StrategyEditor }    from '@/components/strategies/StrategyEditor'
import { CopilotChat }       from '@/components/copilot/CopilotChat'
import { AITokenMonitor }    from '@/components/ai/AITokenMonitor'

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
  useStrategies()
  useAIMetrics()
  return null
}

// Tab button
function TabButton({
  label,
  active,
  onClick,
  highlight,
  badge,
}: {
  label:      string
  active:     boolean
  onClick:    () => void
  highlight?: boolean
  badge?:     string
}) {
  return (
    <button
      onClick={onClick}
      className={`
        relative px-4 py-1.5 text-xs font-mono uppercase tracking-widest border-b-2 transition-colors
        ${active
          ? 'border-terminal-green text-terminal-green'
          : highlight
          ? 'border-transparent text-terminal-blue hover:text-terminal-white hover:border-terminal-blue'
          : 'border-transparent text-terminal-dim hover:text-terminal-text hover:border-terminal-border'
        }
      `}
    >
      {label}
      {badge && (
        <span className="ml-1.5 text-xs font-mono text-terminal-yellow">{badge}</span>
      )}
    </button>
  )
}

// ─────────────────────────────────────────────
// Dashboard principal
// ─────────────────────────────────────────────

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<
    'trading' | 'analytics' | 'strategies' | 'copilot' | 'ai_monitor'
  >('trading')

  const [isCreating, setIsCreating] = useState(false)
  const { setSelectedId } = useStrategiesStore()

  function handleNewStrategy() {
    setSelectedId(null)
    setIsCreating(true)
  }

  function handleCancelNew() {
    setIsCreating(false)
  }

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
        <TabButton
          label="[ STRATEGIES ]"
          active={activeTab === 'strategies'}
          onClick={() => setActiveTab('strategies')}
        />
        <TabButton
          label="[ COPILOT ]"
          active={activeTab === 'copilot'}
          onClick={() => setActiveTab('copilot')}
          highlight
        />
        <TabButton
          label="[ AI MONITOR ]"
          active={activeTab === 'ai_monitor'}
          onClick={() => setActiveTab('ai_monitor')}
          highlight
        />
      </div>

      {/* Vista TRADING */}
      {activeTab === 'trading' && (
        <div className="flex flex-1 overflow-hidden">
          <div className="flex-1 border-r border-terminal-border overflow-hidden">
            <PriceChart />
          </div>
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
          <div className="flex-1 border-r border-terminal-border overflow-hidden" style={{ minHeight: 0 }}>
            <EquityChart />
          </div>
          <div className="w-[420px] overflow-hidden">
            <MetricsPanel />
          </div>
        </div>
      )}

      {/* Vista STRATEGIES */}
      {activeTab === 'strategies' && (
        <div className="flex flex-1 overflow-hidden">
          <div className="w-[320px] border-r border-terminal-border overflow-hidden flex flex-col">
            <StrategyList onNew={handleNewStrategy} />
          </div>
          <div className="flex-1 overflow-auto">
            <StrategyEditor
              isCreating={isCreating}
              onCancelNew={handleCancelNew}
            />
          </div>
        </div>
      )}

      {/* Vista COPILOT */}
      {activeTab === 'copilot' && (
        <div className="flex flex-1 overflow-hidden">
          <div className="flex-1 overflow-hidden">
            <CopilotChat />
          </div>
        </div>
      )}

      {/* Vista AI MONITOR — Phase 7 */}
      {activeTab === 'ai_monitor' && (
        <div className="flex flex-1 overflow-hidden">
          {/* Left: token monitor */}
          <div className="flex-1 border-r border-terminal-border overflow-hidden">
            <AITokenMonitor />
          </div>
          {/* Right: strategies quick view with AI config */}
          <div className="w-[380px] overflow-hidden flex flex-col">
            <div className="px-4 py-2 border-b border-terminal-border flex-shrink-0">
              <span className="text-terminal-dim text-xs uppercase tracking-widest">
                Strategy AI Config
              </span>
            </div>
            <div className="flex-1 overflow-auto">
              <AIStrategyConfig />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────
// Right panel: strategy AI thresholds
// ─────────────────────────────────────────────

import { useStrategiesStore as useStrStore } from '@/store/strategies'

function AIStrategyConfig() {
  const { strategies } = useStrStore()

  if (strategies.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-terminal-dim text-xs">
        <span>No strategies<span className="blink ml-1">_</span></span>
      </div>
    )
  }

  return (
    <div className="flex flex-col divide-y divide-terminal-border/40">
      {strategies.map((s) => {
        const threshold = (s as any).confidence_threshold ?? 0.75
        const aiRequired = (s as any).ai_validation_required ?? true

        return (
          <div key={s.id} className="px-4 py-3 flex flex-col gap-2">
            {/* Name + status */}
            <div className="flex items-center justify-between">
              <span className={`text-xs font-mono font-semibold truncate ${
                s.enabled ? 'text-terminal-white' : 'text-terminal-dim'
              }`}>
                {s.name}
              </span>
              <span className={`text-xs font-mono px-1.5 py-0.5 border ${
                s.enabled
                  ? 'border-terminal-green/40 text-terminal-green'
                  : 'border-terminal-border text-terminal-dim'
              }`}>
                {s.enabled ? 'LIVE' : 'OFF'}
              </span>
            </div>

            {/* AI required */}
            <div className="flex items-center justify-between">
              <span className="text-terminal-dim text-xs">AI Validation</span>
              <span className={`text-xs font-mono ${
                aiRequired ? 'text-terminal-blue' : 'text-terminal-yellow'
              }`}>
                {aiRequired ? 'ENABLED' : 'DISABLED'}
              </span>
            </div>

            {/* Threshold bar */}
            {aiRequired && (
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between">
                  <span className="text-terminal-dim text-xs">Confidence Threshold</span>
                  <span className="text-terminal-white text-xs font-mono">
                    {Math.round(threshold * 100)}%
                  </span>
                </div>
                <div className="w-full h-1 bg-terminal-border rounded-full overflow-hidden">
                  <div
                    className="h-full bg-terminal-blue rounded-full"
                    style={{ width: `${threshold * 100}%` }}
                  />
                </div>
                <span className="text-terminal-dim text-xs">
                  Signals above {Math.round(threshold * 100)}% strength skip AI
                </span>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
