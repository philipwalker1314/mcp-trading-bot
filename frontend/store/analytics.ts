import { create } from 'zustand'

export interface EquityPoint {
  date:           string
  daily_pnl:      number
  cumulative_pnl: number
  total_trades:   number
  win_rate:       number
}

export interface SharpeData {
  sharpe_ratio:     number
  days_used:        number
  mean_daily_pnl:   number
  std_daily_pnl:    number
  insufficient_data: boolean
}

export interface DrawdownData {
  max_drawdown:     number
  max_drawdown_pct: number
  days_used:        number
}

export interface TradeStatsData {
  total_closed:       number
  avg_duration_sec:   number
  avg_duration_human: string
  min_duration_sec:   number
  max_duration_sec:   number
  by_close_reason:    Record<string, { count: number; avg_sec: number }>
}

export interface AiPerformanceData {
  total_trades:       number
  ai_validated:       number
  overall_win_rate:   number
  ai_signal_count:    number
  avg_ai_confidence:  number
  total_realized_pnl: number
}

interface AnalyticsStore {
  equityCurve:   EquityPoint[]
  sharpe:        SharpeData | null
  drawdown:      DrawdownData | null
  tradeStats:    TradeStatsData | null
  aiPerformance: AiPerformanceData | null
  loading:       boolean

  setEquityCurve:   (data: EquityPoint[]) => void
  setSharpe:        (data: SharpeData) => void
  setDrawdown:      (data: DrawdownData) => void
  setTradeStats:    (data: TradeStatsData) => void
  setAiPerformance: (data: AiPerformanceData) => void
  setLoading:       (loading: boolean) => void
}

export const useAnalyticsStore = create<AnalyticsStore>((set) => ({
  equityCurve:   [],
  sharpe:        null,
  drawdown:      null,
  tradeStats:    null,
  aiPerformance: null,
  loading:       false,

  setEquityCurve:   (equityCurve) => set({ equityCurve }),
  setSharpe:        (sharpe) => set({ sharpe }),
  setDrawdown:      (drawdown) => set({ drawdown }),
  setTradeStats:    (tradeStats) => set({ tradeStats }),
  setAiPerformance: (aiPerformance) => set({ aiPerformance }),
  setLoading:       (loading) => set({ loading }),
}))
