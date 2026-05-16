'use client'

interface Props {
  enabled: boolean
  size?: 'sm' | 'md'
}

export function StrategyStatusBadge({ enabled, size = 'sm' }: Props) {
  return (
    <span className={`inline-flex items-center gap-1.5 font-mono uppercase tracking-widest ${
      size === 'md' ? 'text-xs' : 'text-xs'
    } ${enabled ? 'text-terminal-green' : 'text-terminal-dim'}`}>
      <span className={`inline-block rounded-full flex-shrink-0 ${
        size === 'md' ? 'w-2 h-2' : 'w-1.5 h-1.5'
      } ${
        enabled
          ? 'bg-terminal-green shadow-[0_0_6px_#00d4a0]'
          : 'bg-terminal-dim'
      }`} />
      {enabled ? 'LIVE' : 'OFF'}
    </span>
  )
}
