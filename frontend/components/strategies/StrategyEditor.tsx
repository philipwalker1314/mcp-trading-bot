'use client'

import { useState, useEffect } from 'react'
import { useStrategiesStore, StrategyConfig, IndicatorConfig, Rule, Operator } from '@/store/strategies'
import { useStrategies } from '@/hooks/useStrategies'
import { StrategyStatusBadge } from './StrategyStatusBadge'
import { VersionHistoryPanel } from './VersionHistoryPanel'

// ─────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────

const TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d']
const INDICATOR_TYPES = ['ema', 'rsi', 'macd', 'atr', 'volatility', 'bbands', 'stoch', 'obv', 'vwap']
const OPERATORS: Operator[] = ['gt', 'lt', 'gte', 'lte', 'eq', 'between', 'crosses_above', 'crosses_below']
const CROSS_OPS: Operator[] = ['crosses_above', 'crosses_below']
const BETWEEN_OPS: Operator[] = ['between']

// ─────────────────────────────────────────────
// Shared style constants
// ─────────────────────────────────────────────

const inputCls =
  'bg-transparent border border-terminal-border text-terminal-white px-2 py-1.5 text-xs font-mono focus:border-terminal-green focus:outline-none w-full'
const selectCls =
  'bg-terminal-surface border border-terminal-border text-terminal-white px-2 py-1.5 text-xs font-mono focus:border-terminal-green focus:outline-none w-full cursor-pointer'
const btnBase =
  'text-xs font-mono uppercase tracking-widest border px-3 py-1.5 transition-colors'
const btnDefault = `${btnBase} border-terminal-border text-terminal-dim hover:border-terminal-text hover:text-terminal-text`
const btnGreen   = `${btnBase} border-terminal-green text-terminal-green hover:bg-terminal-green/10`
const btnRed     = `${btnBase} border-terminal-red text-terminal-red hover:bg-terminal-red/10`
const btnYellow  = `${btnBase} border-terminal-yellow text-terminal-yellow hover:bg-terminal-yellow/10`

// ─────────────────────────────────────────────
// Section header
// ─────────────────────────────────────────────

function SectionHeader({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 mt-4 mb-2">
      <span className="text-terminal-dim text-xs uppercase tracking-widest whitespace-nowrap">
        {label}
      </span>
      <div className="flex-1 h-px bg-terminal-border" />
    </div>
  )
}

// ─────────────────────────────────────────────
// Rule display (read mode)
// ─────────────────────────────────────────────

function RuleDisplay({ rule }: { rule: Rule }) {
  const parts: string[] = [rule.indicator, rule.op]
  if (BETWEEN_OPS.includes(rule.op as Operator)) {
    parts.push(`${rule.value_min} – ${rule.value_max}`)
  } else if (rule.target) {
    parts.push(rule.target)
  } else if (rule.value !== undefined) {
    parts.push(String(rule.value))
  }
  return (
    <div className="flex items-center gap-1 py-0.5">
      <span className="text-terminal-blue font-mono text-xs">{rule.indicator}</span>
      <span className="text-terminal-dim font-mono text-xs">{rule.op}</span>
      {BETWEEN_OPS.includes(rule.op as Operator) ? (
        <span className="text-terminal-white font-mono text-xs">
          {rule.value_min} – {rule.value_max}
        </span>
      ) : rule.target ? (
        <span className="text-terminal-green font-mono text-xs">{rule.target}</span>
      ) : rule.value !== undefined ? (
        <span className="text-terminal-white font-mono text-xs">{rule.value}</span>
      ) : null}
    </div>
  )
}

// ─────────────────────────────────────────────
// Indicator row (edit mode)
// ─────────────────────────────────────────────

function IndicatorRow({
  indicator,
  onChange,
  onRemove,
}: {
  indicator: IndicatorConfig
  onChange: (updated: IndicatorConfig) => void
  onRemove: () => void
}) {
  return (
    <div className="flex items-center gap-2 py-1">
      <select
        value={indicator.type}
        onChange={(e) => onChange({ ...indicator, type: e.target.value as IndicatorConfig['type'] })}
        className={`${selectCls} w-28`}
      >
        {INDICATOR_TYPES.map((t) => (
          <option key={t} value={t}>{t}</option>
        ))}
      </select>

      {['ema', 'rsi', 'atr', 'volatility', 'bbands', 'stoch'].includes(indicator.type) && (
        <input
          type="number"
          placeholder="period"
          value={indicator.period ?? ''}
          onChange={(e) => onChange({ ...indicator, period: parseInt(e.target.value) || undefined })}
          className={`${inputCls} w-20`}
        />
      )}

      {['ema'].includes(indicator.type) && (
        <input
          type="text"
          placeholder="column (e.g. ema_8)"
          value={indicator.column ?? ''}
          onChange={(e) => onChange({ ...indicator, column: e.target.value || undefined })}
          className={`${inputCls} flex-1`}
        />
      )}

      <button onClick={onRemove} className="text-terminal-dim hover:text-terminal-red transition-colors font-mono text-xs px-1.5">
        ×
      </button>
    </div>
  )
}

// ─────────────────────────────────────────────
// Rule row (edit mode)
// ─────────────────────────────────────────────

function RuleRow({
  rule,
  onChange,
  onRemove,
}: {
  rule: Rule
  onChange: (updated: Rule) => void
  onRemove: () => void
}) {
  const isCross   = CROSS_OPS.includes(rule.op)
  const isBetween = BETWEEN_OPS.includes(rule.op)

  return (
    <div className="flex flex-wrap items-center gap-2 py-1">
      <input
        type="text"
        placeholder="indicator"
        value={rule.indicator}
        onChange={(e) => onChange({ ...rule, indicator: e.target.value })}
        className={`${inputCls} w-28`}
      />

      <select
        value={rule.op}
        onChange={(e) => onChange({ ...rule, op: e.target.value as Operator })}
        className={`${selectCls} w-36`}
      >
        {OPERATORS.map((op) => (
          <option key={op} value={op}>{op}</option>
        ))}
      </select>

      {isBetween ? (
        <>
          <input
            type="number"
            placeholder="min"
            value={rule.value_min ?? ''}
            onChange={(e) => onChange({ ...rule, value_min: parseFloat(e.target.value) || undefined })}
            className={`${inputCls} w-20`}
          />
          <span className="text-terminal-dim text-xs font-mono">–</span>
          <input
            type="number"
            placeholder="max"
            value={rule.value_max ?? ''}
            onChange={(e) => onChange({ ...rule, value_max: parseFloat(e.target.value) || undefined })}
            className={`${inputCls} w-20`}
          />
        </>
      ) : isCross ? (
        <input
          type="text"
          placeholder="target column"
          value={rule.target ?? ''}
          onChange={(e) => onChange({ ...rule, target: e.target.value || undefined })}
          className={`${inputCls} w-32`}
        />
      ) : (
        <input
          type="number"
          placeholder="value"
          value={rule.value ?? ''}
          onChange={(e) => onChange({ ...rule, value: parseFloat(e.target.value) || undefined })}
          className={`${inputCls} w-24`}
        />
      )}

      <button onClick={onRemove} className="text-terminal-dim hover:text-terminal-red transition-colors font-mono text-xs px-1.5">
        ×
      </button>
    </div>
  )
}

// ─────────────────────────────────────────────
// Empty state
// ─────────────────────────────────────────────

function EmptyState({ onNew }: { onNew: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 text-terminal-dim">
      <span className="text-xs uppercase tracking-widest">NO STRATEGIES DEFINED</span>
      <button onClick={onNew} className={btnGreen}>
        [ + CREATE FIRST STRATEGY ]
      </button>
    </div>
  )
}

// ─────────────────────────────────────────────
// Default form state
// ─────────────────────────────────────────────

function defaultForm(): Partial<StrategyConfig> {
  return {
    name:              '',
    description:       '',
    timeframe:         '1m',
    symbols:           ['BTC/USDT'],
    stop_loss_pct:     0.02,
    take_profit_pct:   0.04,
    trailing_stop_pct: null,
    indicators:        [],
    entry_rules:       [],
    exit_rules:        null,
  }
}

// ─────────────────────────────────────────────
// Main StrategyEditor
// ─────────────────────────────────────────────

interface Props {
  isCreating:   boolean
  onCancelNew:  () => void
}

export function StrategyEditor({ isCreating, onCancelNew }: Props) {
  const {
    strategies,
    selectedId,
    saving,
    validating,
    validationResult,
    setValidationResult,
  } = useStrategiesStore()

  const {
    createStrategy,
    updateStrategy,
    deleteStrategy,
    enableStrategy,
    disableStrategy,
    rollbackStrategy,
    validateStrategy,
    loadVersions,
  } = useStrategies()

  const selected = strategies.find((s) => s.id === selectedId) ?? null

  // edit / create mode
  const [isEditing,      setIsEditing]      = useState(false)
  const [showVersions,   setShowVersions]   = useState(false)
  const [form,           setForm]           = useState<Partial<StrategyConfig>>(defaultForm())
  const [formErrors,     setFormErrors]     = useState<string[]>([])
  const [saveSuccess,    setSaveSuccess]    = useState(false)

  // Sync form when selected changes or entering create mode
  useEffect(() => {
    if (isCreating) {
      setForm(defaultForm())
      setIsEditing(true)
      setShowVersions(false)
      setFormErrors([])
      setValidationResult(null)
    } else if (selected && !isEditing) {
      setForm({ ...selected })
    }
  }, [isCreating, selected?.id])

  // Reset edit mode when selection changes
  useEffect(() => {
    if (!isCreating) {
      setIsEditing(false)
      setShowVersions(false)
      setFormErrors([])
      setValidationResult(null)
    }
  }, [selectedId])

  // ── Helpers ──────────────────────────────

  function setField<K extends keyof StrategyConfig>(key: K, value: StrategyConfig[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  function parseSymbols(raw: string): string[] {
    return raw.split(',').map((s) => s.trim().toUpperCase()).filter(Boolean)
  }

  function addIndicator() {
    setForm((prev) => ({
      ...prev,
      indicators: [...(prev.indicators ?? []), { type: 'ema', period: 8, column: 'ema_8' }],
    }))
  }

  function updateIndicator(idx: number, updated: IndicatorConfig) {
    setForm((prev) => {
      const next = [...(prev.indicators ?? [])]
      next[idx] = updated
      return { ...prev, indicators: next }
    })
  }

  function removeIndicator(idx: number) {
    setForm((prev) => ({
      ...prev,
      indicators: (prev.indicators ?? []).filter((_, i) => i !== idx),
    }))
  }

  function addRule(field: 'entry_rules' | 'exit_rules') {
    const blank: Rule = { indicator: '', op: 'gt', value: 0 }
    setForm((prev) => ({
      ...prev,
      [field]: [...((prev[field] as Rule[]) ?? []), blank],
    }))
  }

  function updateRule(field: 'entry_rules' | 'exit_rules', idx: number, updated: Rule) {
    setForm((prev) => {
      const next = [...((prev[field] as Rule[]) ?? [])]
      next[idx] = updated
      return { ...prev, [field]: next }
    })
  }

  function removeRule(field: 'entry_rules' | 'exit_rules', idx: number) {
    setForm((prev) => ({
      ...prev,
      [field]: ((prev[field] as Rule[]) ?? []).filter((_, i) => i !== idx),
    }))
  }

  // ── Actions ───────────────────────────────

  async function handleValidate() {
    setFormErrors([])
    await validateStrategy(form)
  }

  async function handleSave() {
    setFormErrors([])
    try {
      if (isCreating) {
        await createStrategy(form)
        onCancelNew()
      } else if (selected) {
        await updateStrategy(selected.id, form)
        setIsEditing(false)
      }
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
    } catch (e: any) {
      setFormErrors([e.message ?? 'Save failed'])
    }
  }

  async function handleDelete() {
    if (!selected) return
    if (!window.confirm(`Delete strategy "${selected.name}"? This cannot be undone.`)) return
    await deleteStrategy(selected.id)
  }

  async function handleToggleEnabled() {
    if (!selected) return
    if (selected.enabled) {
      await disableStrategy(selected.id)
    } else {
      await enableStrategy(selected.id)
    }
  }

  async function handleShowVersions() {
    if (!selected) return
    setShowVersions(true)
    await loadVersions(selected.id)
  }

  async function handleRollback(targetVersion: number) {
    if (!selected) return
    await rollbackStrategy(selected.id, targetVersion)
    setShowVersions(false)
  }

  // ── Nothing selected, not creating ───────

  if (!selected && !isCreating) {
    return (
      <EmptyState onNew={() => {}} />
    )
  }

  // ── EDIT / CREATE MODE ────────────────────

  if (isEditing || isCreating) {
    const isNew = isCreating

    return (
      <div className="flex flex-col h-full overflow-auto">
        {/* Form header */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-terminal-border sticky top-0 bg-terminal-bg z-10">
          <span className="text-terminal-dim text-xs uppercase tracking-widest">
            {isNew ? '[ NEW STRATEGY ]' : `[ EDIT ] ${selected?.name}`}
          </span>
        </div>

        <div className="px-4 py-4 flex flex-col gap-1 flex-1">

          {/* Basic fields */}
          <SectionHeader label="Basic" />

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-terminal-dim text-xs uppercase tracking-widest">Name *</label>
              <input
                type="text"
                value={form.name ?? ''}
                onChange={(e) => setField('name', e.target.value)}
                className={inputCls}
                placeholder="my_strategy"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-terminal-dim text-xs uppercase tracking-widest">Timeframe</label>
              <select
                value={form.timeframe ?? '1m'}
                onChange={(e) => setField('timeframe', e.target.value)}
                className={selectCls}
              >
                {TIMEFRAMES.map((tf) => (
                  <option key={tf} value={tf}>{tf}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex flex-col gap-1 mt-2">
            <label className="text-terminal-dim text-xs uppercase tracking-widest">Description</label>
            <textarea
              value={form.description ?? ''}
              onChange={(e) => setField('description', e.target.value)}
              className={`${inputCls} resize-none`}
              rows={2}
              placeholder="Short description of what this strategy does"
            />
          </div>

          <div className="flex flex-col gap-1 mt-2">
            <label className="text-terminal-dim text-xs uppercase tracking-widest">
              Symbols (comma-separated)
            </label>
            <input
              type="text"
              value={(form.symbols ?? []).join(', ')}
              onChange={(e) => setField('symbols', parseSymbols(e.target.value))}
              className={inputCls}
              placeholder="BTC/USDT, ETH/USDT"
            />
          </div>

          {/* Risk */}
          <SectionHeader label="Risk Config" />

          <div className="grid grid-cols-3 gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-terminal-dim text-xs uppercase tracking-widest">Stop Loss %</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={((form.stop_loss_pct ?? 0.02) * 100).toFixed(2)}
                onChange={(e) => setField('stop_loss_pct', parseFloat(e.target.value) / 100)}
                className={inputCls}
                placeholder="2.00"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-terminal-dim text-xs uppercase tracking-widest">Take Profit %</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={((form.take_profit_pct ?? 0.04) * 100).toFixed(2)}
                onChange={(e) => setField('take_profit_pct', parseFloat(e.target.value) / 100)}
                className={inputCls}
                placeholder="4.00"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-terminal-dim text-xs uppercase tracking-widest">Trailing %</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={form.trailing_stop_pct != null ? (form.trailing_stop_pct * 100).toFixed(2) : ''}
                onChange={(e) => {
                  const v = e.target.value
                  setField('trailing_stop_pct', v === '' ? null : parseFloat(v) / 100)
                }}
                className={inputCls}
                placeholder="— none —"
              />
            </div>
          </div>

          {/* Indicators */}
          <SectionHeader label="Indicators" />
          <div className="flex flex-col gap-0.5">
            {(form.indicators ?? []).map((ind, idx) => (
              <IndicatorRow
                key={idx}
                indicator={ind}
                onChange={(updated) => updateIndicator(idx, updated)}
                onRemove={() => removeIndicator(idx)}
              />
            ))}
            <button onClick={addIndicator} className={`${btnDefault} self-start mt-1`}>
              [ + ADD INDICATOR ]
            </button>
          </div>

          {/* Entry Rules */}
          <SectionHeader label="Entry Rules (AND)" />
          <div className="flex flex-col gap-0.5">
            {(form.entry_rules ?? []).map((rule, idx) => (
              <RuleRow
                key={idx}
                rule={rule}
                onChange={(updated) => updateRule('entry_rules', idx, updated)}
                onRemove={() => removeRule('entry_rules', idx)}
              />
            ))}
            <button onClick={() => addRule('entry_rules')} className={`${btnDefault} self-start mt-1`}>
              [ + ADD ENTRY RULE ]
            </button>
          </div>

          {/* Exit Rules */}
          <SectionHeader label="Exit Rules (optional)" />
          <div className="flex flex-col gap-0.5">
            {(form.exit_rules ?? []).map((rule, idx) => (
              <RuleRow
                key={idx}
                rule={rule}
                onChange={(updated) => updateRule('exit_rules', idx, updated)}
                onRemove={() => removeRule('exit_rules', idx)}
              />
            ))}
            <button onClick={() => addRule('exit_rules')} className={`${btnDefault} self-start mt-1`}>
              [ + ADD EXIT RULE ]
            </button>
            {(form.exit_rules ?? []).length > 0 && (
              <button
                onClick={() => setField('exit_rules', null)}
                className="text-xs font-mono text-terminal-dim hover:text-terminal-red transition-colors self-start"
              >
                clear all exit rules
              </button>
            )}
          </div>

          {/* Validation result */}
          {validationResult && (
            <div className={`mt-3 p-3 border ${
              validationResult.valid
                ? 'border-terminal-green/40 bg-terminal-green/5'
                : 'border-terminal-red/40 bg-terminal-red/5'
            }`}>
              <span className={`text-xs font-mono font-bold ${
                validationResult.valid ? 'text-terminal-green' : 'text-terminal-red'
              }`}>
                {validationResult.valid ? '✓ VALID' : '✗ INVALID'}
              </span>
              {validationResult.errors.length > 0 && (
                <ul className="mt-1 flex flex-col gap-0.5">
                  {validationResult.errors.map((err, i) => (
                    <li key={i} className="text-terminal-red text-xs">— {err}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* Form errors */}
          {formErrors.length > 0 && (
            <div className="mt-2 p-3 border border-terminal-red/40 bg-terminal-red/5">
              {formErrors.map((err, i) => (
                <p key={i} className="text-terminal-red text-xs">— {err}</p>
              ))}
            </div>
          )}

          {/* Action row */}
          <div className="flex items-center gap-2 mt-4 pt-4 border-t border-terminal-border">
            <button onClick={handleValidate} disabled={validating} className={btnYellow}>
              {validating ? 'VALIDATING...' : '[ VALIDATE ]'}
            </button>
            <button onClick={handleSave} disabled={saving} className={btnGreen}>
              {saving
                ? 'SAVING...'
                : saveSuccess
                ? '✓ SAVED'
                : isNew
                ? '[ CREATE ]'
                : '[ SAVE ]'
              }
            </button>
            <button
              onClick={() => {
                if (isNew) { onCancelNew() } else { setIsEditing(false) }
                setFormErrors([])
                setValidationResult(null)
              }}
              className={btnDefault}
            >
              [ CANCEL ]
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ── VIEW MODE ─────────────────────────────

  if (!selected) return null

  return (
    <div className="flex h-full overflow-hidden">
      {/* Main view */}
      <div className="flex-1 flex flex-col overflow-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-terminal-border sticky top-0 bg-terminal-bg z-10">
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-terminal-white font-mono font-bold text-sm">
              {selected.name}
            </span>
            <StrategyStatusBadge enabled={selected.enabled} size="md" />
            <span className="text-xs font-mono px-1.5 py-0.5 border border-terminal-border text-terminal-dim">
              v{selected.version}
            </span>
            <span className="text-xs font-mono px-1.5 py-0.5 border border-terminal-border text-terminal-dim">
              {selected.timeframe}
            </span>
            {selected.symbols.map((sym) => (
              <span key={sym} className="text-xs font-mono px-1.5 py-0.5 border border-terminal-border text-terminal-dim">
                {sym}
              </span>
            ))}
          </div>
        </div>

        {/* Action row */}
        <div className="flex items-center gap-2 px-4 py-2 border-b border-terminal-border flex-wrap">
          <button
            onClick={() => {
              setForm({ ...selected })
              setIsEditing(true)
            }}
            className={btnDefault}
          >
            [ EDIT ]
          </button>
          <button
            onClick={handleToggleEnabled}
            className={selected.enabled ? btnRed : btnGreen}
          >
            {selected.enabled ? '[ DISABLE ]' : '[ ENABLE ]'}
          </button>
          <button onClick={handleShowVersions} className={btnDefault}>
            [ VERSION HISTORY ]
          </button>
          <button onClick={handleDelete} className={btnRed}>
            [ DELETE ]
          </button>
        </div>

        <div className="px-4 py-4 flex flex-col gap-1">
          {/* Description */}
          {selected.description && (
            <p className="text-terminal-text text-xs mb-2">{selected.description}</p>
          )}

          {/* Risk */}
          <SectionHeader label="Risk Config" />
          <div className="grid grid-cols-3 gap-2">
            <div className="border border-terminal-border p-2">
              <div className="text-terminal-dim text-xs uppercase tracking-widest">Stop Loss</div>
              <div className="text-terminal-white font-mono text-sm mt-0.5">
                {(selected.stop_loss_pct * 100).toFixed(1)}%
              </div>
            </div>
            <div className="border border-terminal-border p-2">
              <div className="text-terminal-dim text-xs uppercase tracking-widest">Take Profit</div>
              <div className="text-terminal-white font-mono text-sm mt-0.5">
                {(selected.take_profit_pct * 100).toFixed(1)}%
              </div>
            </div>
            <div className="border border-terminal-border p-2">
              <div className="text-terminal-dim text-xs uppercase tracking-widest">Trailing</div>
              <div className="text-terminal-white font-mono text-sm mt-0.5">
                {selected.trailing_stop_pct != null
                  ? `${(selected.trailing_stop_pct * 100).toFixed(1)}%`
                  : '— none —'}
              </div>
            </div>
          </div>

          {/* Indicators */}
          {selected.indicators.length > 0 && (
            <>
              <SectionHeader label="Indicators" />
              <div className="flex flex-wrap gap-2">
                {selected.indicators.map((ind, i) => (
                  <span key={i} className="text-xs font-mono px-2 py-1 border border-terminal-border text-terminal-text bg-terminal-surface/40">
                    {ind.type}{ind.period ? `(${ind.period})` : ''}{ind.column ? ` → ${ind.column}` : ''}
                  </span>
                ))}
              </div>
            </>
          )}

          {/* Entry rules */}
          {selected.entry_rules.length > 0 && (
            <>
              <SectionHeader label="Entry Rules" />
              <div className="flex flex-col gap-0.5 pl-1">
                {selected.entry_rules.map((rule, i) => (
                  <RuleDisplay key={i} rule={rule} />
                ))}
              </div>
            </>
          )}

          {/* Exit rules */}
          <SectionHeader label="Exit Rules" />
          {selected.exit_rules && selected.exit_rules.length > 0 ? (
            <div className="flex flex-col gap-0.5 pl-1">
              {selected.exit_rules.map((rule, i) => (
                <RuleDisplay key={i} rule={rule} />
              ))}
            </div>
          ) : (
            <span className="text-terminal-dim text-xs font-mono pl-1">— none —</span>
          )}

          {/* Audit */}
          <SectionHeader label="Audit" />
          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            <div className="text-terminal-dim">
              Created: <span className="text-terminal-text">{new Date(selected.created_at).toLocaleString()}</span>
            </div>
            <div className="text-terminal-dim">
              Updated: <span className="text-terminal-text">{new Date(selected.updated_at).toLocaleString()}</span>
            </div>
            {selected.created_by && (
              <div className="text-terminal-dim">
                By: <span className="text-terminal-text">{selected.created_by}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Version history slide-in */}
      {showVersions && selected && (
        <div className="w-72 flex-shrink-0 overflow-hidden flex flex-col border-l border-terminal-border">
          <VersionHistoryPanel
            strategyId={selected.id}
            currentVersion={selected.version}
            onRollback={handleRollback}
            onClose={() => setShowVersions(false)}
          />
        </div>
      )}
    </div>
  )
}
