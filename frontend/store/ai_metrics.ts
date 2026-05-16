import { create } from 'zustand'

export interface RecentCall {
  ts:        string
  symbol:    string
  signal:    string
  strength:  number
  status:    'SKIP' | 'AI'
  ai_result: string | null
}

export interface AIMetricsData {
  session_start:          string
  session_duration_min:   number
  total_signals:          number
  calls_skipped:          number
  calls_made:             number
  skip_rate:              number
  ai_call_rate:           number
  estimated_tokens:       number
  estimated_cost_usd:     number
  ai_buy_signals:         number
  ai_sell_signals:        number
  ai_hold_signals:        number
  ai_hold_rate:           number
  last_call_at:           string | null
  last_signal_strength:   number | null
  recent_calls:           RecentCall[]
}

interface AIMetricsStore {
  data:       AIMetricsData | null
  loading:    boolean
  setData:    (data: AIMetricsData) => void
  setLoading: (loading: boolean) => void
  reset:      () => void
}

export const useAIMetricsStore = create<AIMetricsStore>((set) => ({
  data:    null,
  loading: false,

  setData:    (data)    => set({ data }),
  setLoading: (loading) => set({ loading }),
  reset:      ()        => set({ data: null }),
}))
