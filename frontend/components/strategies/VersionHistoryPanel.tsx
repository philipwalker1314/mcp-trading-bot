'use client'

import { useStrategiesStore, StrategyVersion } from '@/store/strategies'

interface Props {
  strategyId:  number
  currentVersion: number
  onRollback:  (targetVersion: number) => Promise<void>
  onClose:     () => void
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month:   'short',
    day:     'numeric',
    hour:    '2-digit',
    minute:  '2-digit',
  })
}

export function VersionHistoryPanel({ strategyId, currentVersion, onRollback, onClose }: Props) {
  const { versions, versionsLoading } = useStrategiesStore()

  return (
    <div className="flex flex-col h-full border-l border-terminal-border bg-terminal-surface/30">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-terminal-border">
        <span className="text-terminal-dim text-xs uppercase tracking-widest">
          Version History
        </span>
        <button
          onClick={onClose}
          className="text-terminal-dim text-xs hover:text-terminal-white transition-colors font-mono"
        >
          [ × CLOSE ]
        </button>
      </div>

      {/* List */}
      <div className="flex-1 overflow-auto">
        {versionsLoading ? (
          <div className="flex items-center justify-center h-20 text-terminal-dim text-xs animate-pulse">
            LOADING_
          </div>
        ) : versions.length === 0 ? (
          <div className="flex items-center justify-center h-20 text-terminal-dim text-xs">
            NO VERSION HISTORY
          </div>
        ) : (
          <div className="flex flex-col">
            {versions.map((v) => {
              const isCurrent = v.version === currentVersion
              return (
                <div
                  key={v.id}
                  className={`px-4 py-3 border-b border-terminal-border/50 flex flex-col gap-1.5
                    ${isCurrent ? 'bg-terminal-surface/60' : ''}
                  `}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-mono font-bold ${
                        isCurrent ? 'text-terminal-green' : 'text-terminal-white'
                      }`}>
                        v{v.version}
                      </span>
                      {isCurrent && (
                        <span className="text-xs font-mono text-terminal-green border border-terminal-green/40 px-1 py-0.5">
                          CURRENT
                        </span>
                      )}
                    </div>
                    {!isCurrent && (
                      <button
                        onClick={async () => {
                          const ok = window.confirm(
                            `Restore v${v.version}? This will create v${currentVersion + 1}.`
                          )
                          if (!ok) return
                          await onRollback(v.version)
                        }}
                        className="text-xs font-mono uppercase tracking-widest border border-terminal-border text-terminal-dim px-2 py-0.5 hover:border-terminal-yellow hover:text-terminal-yellow transition-colors"
                      >
                        [ RESTORE ]
                      </button>
                    )}
                  </div>
                  <span className="text-terminal-dim text-xs font-mono">
                    {fmtDate(v.created_at)}
                  </span>
                  {v.change_summary && (
                    <span className="text-terminal-text text-xs">
                      {v.change_summary}
                    </span>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
