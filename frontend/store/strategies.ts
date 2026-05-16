import { create } from 'zustand'

// ─────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────

export interface IndicatorConfig {
  type:    'ema' | 'rsi' | 'macd' | 'atr' | 'volatility' | 'bbands' | 'stoch' | 'obv' | 'vwap'
  period?: number
  column?: string
  fast?:   number
  slow?:   number
  signal?: number
  std?:    number
  k?:      number
  d?:      number
}

export type Operator =
  | 'gt' | 'lt' | 'gte' | 'lte' | 'eq'
  | 'between' | 'crosses_above' | 'crosses_below'

export interface Rule {
  indicator:  string
  op:         Operator
  target?:    string
  value?:     number
  value_min?: number
  value_max?: number
}

export interface StrategyConfig {
  id:                number
  name:              string
  description:       string | null
  version:           number
  enabled:           boolean
  timeframe:         string
  symbols:           string[]
  stop_loss_pct:     number
  take_profit_pct:   number
  trailing_stop_pct: number | null
  indicators:        IndicatorConfig[]
  entry_rules:       Rule[]
  exit_rules:        Rule[] | null
  created_at:        string
  updated_at:        string
  created_by:        string | null
}

export interface StrategyVersion {
  id:             number
  strategy_id:    number
  version:        number
  change_summary: string | null
  created_at:     string
  snapshot:       StrategyConfig
}

export interface ValidationResult {
  valid:  boolean
  errors: string[]
}

// ─────────────────────────────────────────────
// Store
// ─────────────────────────────────────────────

interface StrategiesStore {
  strategies:       StrategyConfig[]
  selectedId:       number | null
  loading:          boolean
  saving:           boolean
  validating:       boolean
  validationResult: ValidationResult | null
  versions:         StrategyVersion[]
  versionsLoading:  boolean

  setStrategies:       (strategies: StrategyConfig[]) => void
  upsertStrategy:      (strategy: StrategyConfig) => void
  removeStrategy:      (id: number) => void
  setSelectedId:       (id: number | null) => void
  setLoading:          (loading: boolean) => void
  setSaving:           (saving: boolean) => void
  setValidating:       (validating: boolean) => void
  setValidationResult: (result: ValidationResult | null) => void
  setVersions:         (versions: StrategyVersion[]) => void
  setVersionsLoading:  (loading: boolean) => void
}

export const useStrategiesStore = create<StrategiesStore>((set) => ({
  strategies:       [],
  selectedId:       null,
  loading:          false,
  saving:           false,
  validating:       false,
  validationResult: null,
  versions:         [],
  versionsLoading:  false,

  setStrategies: (strategies) => set({ strategies }),

  upsertStrategy: (strategy) =>
    set((state) => {
      const idx = state.strategies.findIndex((s) => s.id === strategy.id)
      if (idx >= 0) {
        const next = [...state.strategies]
        next[idx] = strategy
        return { strategies: next }
      }
      return { strategies: [strategy, ...state.strategies] }
    }),

  removeStrategy: (id) =>
    set((state) => ({
      strategies: state.strategies.filter((s) => s.id !== id),
      selectedId: state.selectedId === id ? null : state.selectedId,
    })),

  setSelectedId:       (selectedId) => set({ selectedId }),
  setLoading:          (loading) => set({ loading }),
  setSaving:           (saving) => set({ saving }),
  setValidating:       (validating) => set({ validating }),
  setValidationResult: (validationResult) => set({ validationResult }),
  setVersions:         (versions) => set({ versions }),
  setVersionsLoading:  (versionsLoading) => set({ versionsLoading }),
}))
