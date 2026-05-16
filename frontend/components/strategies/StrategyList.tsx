'use client'

import { useStrategiesStore } from '@/store/strategies'
import { StrategyStatusBadge } from './StrategyStatusBadge'

interface Props {
  onNew: () => void
}

export function StrategyList({ onNew }: Props) {
  const { strategies, selectedId, setSelectedId, loading } = useStrategiesStore()

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-terminal-border">
        <span className="text-terminal-dim text-xs uppercase tracking-widest">
          Strategies
        </span>
        <span className="text-terminal-dim text-xs font-mono">
          [{strategies.length}]
        </span>
      </div>

      {/* New button */}
      <div className="px-3 py-2 border-b border-terminal-border">
        <button
          onClick={onNew}
          className="w-full text-xs font-mono uppercase tracking-widest border border-terminal-border text-terminal-dim px-3 py-1.5 hover:border-terminal-green hover:text-terminal-green transition-colors"
        >
          [ + NEW STRATEGY ]
        </button>
      </div>

      {/* List */}
      <div className="flex-1 overflow-auto">
        {loading && strategies.length === 0 ? (
          <div className="flex items-center justify-center h-20 text-terminal-dim text-xs animate-pulse">
            LOADING_
          </div>
        ) : strategies.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 gap-3 px-4">
            <span className="text-terminal-dim text-xs text-center">
              NO STRATEGIES DEFINED
            </span>
            <button
              onClick={onNew}
              className="text-xs font-mono uppercase tracking-widest border border-terminal-green text-terminal-green px-3 py-1.5 hover:bg-terminal-green/10 transition-colors"
            >
              [ + CREATE FIRST STRATEGY ]
            </button>
          </div>
        ) : (
          <div className="flex flex-col">
            {strategies.map((s) => {
              const isSelected = s.id === selectedId
              return (
                <button
                  key={s.id}
                  onClick={() => setSelectedId(s.id)}
                  className={`
                    w-full text-left px-3 py-2.5 border-b border-terminal-border/50
                    transition-colors flex flex-col gap-1
                    ${isSelected
                      ? 'border-l-2 border-l-terminal-green bg-terminal-surface/80'
                      : 'border-l-2 border-l-transparent hover:bg-terminal-surface/40'
                    }
                  `}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className={`text-xs font-mono font-semibold truncate ${
                      s.enabled ? 'text-terminal-white' : 'text-terminal-dim'
                    }`}>
                      {s.name}
                    </span>
                    <StrategyStatusBadge enabled={s.enabled} />
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono px-1 py-0.5 border border-terminal-border text-terminal-dim">
                      v{s.version}
                    </span>
                    <span className="text-xs font-mono px-1 py-0.5 border border-terminal-border text-terminal-dim">
                      {s.timeframe}
                    </span>
                    {s.symbols.slice(0, 1).map((sym) => (
                      <span key={sym} className="text-xs font-mono text-terminal-dim truncate">
                        {sym}
                      </span>
                    ))}
                  </div>
                </button>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
