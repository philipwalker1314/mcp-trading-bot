'use client'

import { useEffect, useRef, KeyboardEvent } from 'react'
import { useCopilot } from '@/hooks/useCopilot'
import { CopilotMessage, ActionRecord } from '@/store/copilot'

// ─────────────────────────────────────────────
// Suggested commands
// ─────────────────────────────────────────────

const SUGGESTIONS = [
  "What's my current PnL?",
  "List all strategies",
  "Show my analytics summary",
  "How many trades today?",
  "Disable all strategies",
  "What's the BTC price?",
]

// ─────────────────────────────────────────────
// Action badge
// ─────────────────────────────────────────────

function ActionBadge({ action }: { action: ActionRecord }) {
  const colorMap: Record<string, string> = {
    enable_strategy:       'text-terminal-green border-terminal-green/40',
    disable_strategy:      'text-terminal-red border-terminal-red/40',
    disable_all_strategies:'text-terminal-red border-terminal-red/40',
    update_strategy_risk:  'text-terminal-yellow border-terminal-yellow/40',
    close_position:        'text-terminal-yellow border-terminal-yellow/40',
    close_all_positions:   'text-terminal-red border-terminal-red/40',
  }
  const color = colorMap[action.action] ?? 'text-terminal-dim border-terminal-border'
  const label = action.action.replace(/_/g, ' ').toUpperCase()

  return (
    <span className={`inline-flex items-center gap-1 text-xs font-mono px-1.5 py-0.5 border ${color}`}>
      ⚡ {label}
      {action.result === 'ok' && <span className="text-terminal-green">✓</span>}
      {action.result === 'error' && <span className="text-terminal-red">✗</span>}
    </span>
  )
}

// ─────────────────────────────────────────────
// Data table — renders structured results
// ─────────────────────────────────────────────

function DataTable({ data }: { data: any }) {
  if (!data) return null

  // Array of objects — render as table
  if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object') {
    const keys = Object.keys(data[0])
    return (
      <div className="mt-2 overflow-x-auto">
        <table className="text-xs font-mono w-full">
          <thead>
            <tr className="border-b border-terminal-border">
              {keys.map((k) => (
                <th key={k} className="px-2 py-1 text-left text-terminal-dim uppercase tracking-widest whitespace-nowrap">
                  {k}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row: any, i: number) => (
              <tr key={i} className="border-b border-terminal-border/30 hover:bg-terminal-muted/20">
                {keys.map((k) => {
                  const val = row[k]
                  let display = val === null || val === undefined ? '—' : String(val)
                  let cls = 'text-terminal-text'
                  if (k.includes('pnl') || k.includes('profit') || k.includes('loss')) {
                    const n = parseFloat(display)
                    if (!isNaN(n)) {
                      cls = n >= 0 ? 'text-terminal-green' : 'text-terminal-red'
                      display = (n >= 0 ? '+' : '') + n.toFixed(4)
                    }
                  }
                  if (k === 'enabled') {
                    display = val ? 'LIVE' : 'OFF'
                    cls = val ? 'text-terminal-green' : 'text-terminal-dim'
                  }
                  return (
                    <td key={k} className={`px-2 py-1 whitespace-nowrap ${cls}`}>
                      {display}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  // Single object — render as key-value pairs
  if (typeof data === 'object' && !Array.isArray(data)) {
    // Handle nested objects like open_positions inside portfolio
    const topKeys = Object.keys(data)
    if (topKeys.includes('open_positions') && Array.isArray(data.open_positions)) {
      return <DataTable data={data.open_positions} />
    }
    return (
      <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-0.5">
        {topKeys.filter(k => typeof data[k] !== 'object').map((k) => {
          const val = data[k]
          let display = val === null || val === undefined ? '—' : String(val)
          let cls = 'text-terminal-white'
          if (typeof val === 'number') {
            if (k.includes('pnl') || k.includes('profit') || k.includes('drawdown')) {
              cls = val >= 0 ? 'text-terminal-green' : 'text-terminal-red'
              display = (val >= 0 ? '+' : '') + val.toFixed(4)
            } else if (k.includes('rate') || k.includes('pct')) {
              display = (val * 100).toFixed(2) + '%'
            } else {
              display = val.toFixed(4)
            }
          }
          return (
            <div key={k} className="flex gap-2 text-xs font-mono">
              <span className="text-terminal-dim uppercase tracking-widest whitespace-nowrap">
                {k.replace(/_/g, ' ')}:
              </span>
              <span className={cls}>{display}</span>
            </div>
          )
        })}
      </div>
    )
  }

  return null
}

// ─────────────────────────────────────────────
// Message bubble
// ─────────────────────────────────────────────

function MessageBubble({ msg }: { msg: CopilotMessage }) {
  const isUser = msg.role === 'user'
  const time   = new Date(msg.timestamp).toLocaleTimeString('en-US', {
    hour:   '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })

  if (isUser) {
    return (
      <div className="flex items-start gap-2 py-2">
        <span className="text-terminal-green font-mono text-xs flex-shrink-0 pt-0.5 select-none">
          &gt;_
        </span>
        <div className="flex-1">
          <span className="text-terminal-white font-mono text-sm">{msg.content}</span>
          <span className="text-terminal-dim font-mono text-xs ml-2">{time}</span>
        </div>
      </div>
    )
  }

  // Assistant message
  return (
    <div className="flex items-start gap-2 py-2 pl-1">
      <span className="text-terminal-blue font-mono text-xs flex-shrink-0 pt-0.5 select-none">
        AI
      </span>
      <div className="flex-1">
        {msg.loading ? (
          <span className="text-terminal-dim font-mono text-xs animate-pulse">
            processing<span className="blink">_</span>
          </span>
        ) : (
          <>
            {/* Actions taken */}
            {msg.actions_taken.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-2">
                {msg.actions_taken.map((a, i) => (
                  <ActionBadge key={i} action={a} />
                ))}
              </div>
            )}

            {/* Response text */}
            <div className="text-terminal-text font-mono text-sm whitespace-pre-wrap leading-relaxed">
              {msg.content}
            </div>

            {/* Data table */}
            {msg.data && <DataTable data={msg.data} />}

            <span className="text-terminal-dim font-mono text-xs mt-0.5 block">{time}</span>
          </>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────
// Main CopilotChat
// ─────────────────────────────────────────────

export function CopilotChat() {
  const {
    messages,
    loading,
    inputText,
    setInputText,
    sendMessage,
    clearMessages,
  } = useCopilot()

  const scrollRef  = useRef<HTMLDivElement>(null)
  const inputRef   = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(inputText)
    }
  }

  const isEmpty = messages.length === 0

  return (
    <div className="flex flex-col h-full overflow-hidden">

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-terminal-border flex-shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-terminal-blue font-mono text-xs uppercase tracking-widest">
            AI COPILOT
          </span>
          <span className="text-terminal-dim text-xs font-mono">
            — natural language trading interface
          </span>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearMessages}
            className="text-terminal-dim text-xs font-mono hover:text-terminal-red transition-colors"
          >
            [ CLEAR ]
          </button>
        )}
      </div>

      {/* Message area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-2"
      >
        {isEmpty ? (
          /* Empty state */
          <div className="flex flex-col items-center justify-center h-full gap-6">
            <div className="flex flex-col items-center gap-2">
              <div className="text-terminal-blue font-mono text-4xl opacity-20 select-none">
                ◈
              </div>
              <p className="text-terminal-dim text-xs font-mono uppercase tracking-widest">
                Trading copilot ready
              </p>
              <p className="text-terminal-dim text-xs font-mono opacity-60">
                Ask anything. Execute commands. Manage your bot.
              </p>
            </div>

            {/* Suggestions */}
            <div className="flex flex-col gap-2 w-full max-w-lg">
              <span className="text-terminal-dim text-xs font-mono uppercase tracking-widest text-center mb-1">
                try these
              </span>
              <div className="grid grid-cols-2 gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => sendMessage(s)}
                    className="text-left text-xs font-mono text-terminal-text border border-terminal-border px-3 py-2 hover:border-terminal-blue hover:text-terminal-white transition-colors"
                  >
                    &gt; {s}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Messages */
          <div className="flex flex-col divide-y divide-terminal-border/30">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} msg={msg} />
            ))}
          </div>
        )}
      </div>

      {/* Divider */}
      <div className="flex-shrink-0 h-px bg-terminal-border" />

      {/* Input area */}
      <div className="flex-shrink-0 px-4 py-3">
        <div className="flex items-end gap-2">
          <span className="text-terminal-green font-mono text-sm pb-1.5 flex-shrink-0 select-none">
            &gt;_
          </span>
          <textarea
            ref={inputRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            placeholder={loading ? 'processing...' : 'Type a command or question... (Enter to send)'}
            rows={1}
            className={`
              flex-1 bg-transparent border-b font-mono text-sm resize-none
              text-terminal-white placeholder-terminal-dim
              focus:outline-none focus:border-terminal-green
              transition-colors leading-relaxed
              ${loading
                ? 'border-terminal-dim opacity-50 cursor-not-allowed'
                : 'border-terminal-border'
              }
            `}
            style={{ minHeight: '28px', maxHeight: '120px' }}
            onInput={(e) => {
              // Auto-resize textarea
              const el = e.currentTarget
              el.style.height = 'auto'
              el.style.height = Math.min(el.scrollHeight, 120) + 'px'
            }}
          />
          <button
            onClick={() => sendMessage(inputText)}
            disabled={loading || !inputText.trim()}
            className={`
              flex-shrink-0 text-xs font-mono uppercase tracking-widest border px-3 py-1.5 transition-colors
              ${loading || !inputText.trim()
                ? 'border-terminal-border text-terminal-dim cursor-not-allowed'
                : 'border-terminal-green text-terminal-green hover:bg-terminal-green/10'
              }
            `}
          >
            {loading ? '...' : 'SEND'}
          </button>
        </div>
        <p className="text-terminal-dim text-xs font-mono mt-1.5 pl-6">
          Enter to send · Shift+Enter for new line · DeepSeek AI
        </p>
      </div>
    </div>
  )
}
