import { create } from 'zustand'

// ─────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────

export interface Position {
  id:              number
  symbol:          string
  side:            'BUY' | 'SELL'
  status:          string
  avg_entry_price: number
  exit_price:      number | null
  remaining_qty:   number
  unrealized_pnl:  number
  realized_pnl:    number
  stop_loss:       number | null
  take_profit:     number | null
  trailing_stop:   number | null
  close_reason:    string | null
  strategy:        string | null
  opened_at:       string | null
  closed_at:       string | null
  mfe:             number
  mae:             number
}

export interface MarketTick {
  symbol:    string
  price:     number
  volume:    number
  timestamp: string
}

export interface DailyStats {
  open_positions:   number
  total_unrealized: number
  total_realized:   number
  total_exposure:   number
}

export type WsStatus = 'connecting' | 'connected' | 'disconnected'

// ─────────────────────────────────────────────
// Store
// ─────────────────────────────────────────────

interface TradingStore {
  // Positions
  positions:     Position[]
  setPositions:  (positions: Position[]) => void
  upsertPosition:(position: Position) => void
  removePosition:(id: number) => void

  // Market
  prices:        Record<string, number>
  setPrice:      (symbol: string, price: number) => void

  // Stats
  stats:         DailyStats | null
  setStats:      (stats: DailyStats) => void

  // WebSocket status
  wsPositions:   WsStatus
  wsMarket:      WsStatus
  wsSystem:      WsStatus
  setWsStatus:   (channel: 'positions' | 'market' | 'system', status: WsStatus) => void

  // System
  botRunning:    boolean
  setBotRunning: (running: boolean) => void
  lastEvent:     string | null
  setLastEvent:  (event: string) => void
}

export const useTradingStore = create<TradingStore>((set) => ({
  // Positions
  positions: [],
  setPositions: (positions) => set({ positions }),
  upsertPosition: (position) =>
    set((state) => {
      const idx = state.positions.findIndex((p) => p.id === position.id)
      if (idx >= 0) {
        const next = [...state.positions]
        next[idx] = position
        return { positions: next }
      }
      return { positions: [position, ...state.positions] }
    }),
  removePosition: (id) =>
    set((state) => ({
      positions: state.positions.filter((p) => p.id !== id),
    })),

  // Market
  prices: {},
  setPrice: (symbol, price) =>
    set((state) => ({
      prices: { ...state.prices, [symbol]: price },
    })),

  // Stats
  stats: null,
  setStats: (stats) => set({ stats }),

  // WebSocket status
  wsPositions: 'disconnected',
  wsMarket:    'disconnected',
  wsSystem:    'disconnected',
  setWsStatus: (channel, status) =>
    set({ [`ws${channel.charAt(0).toUpperCase() + channel.slice(1)}`]: status } as any),

  // System
  botRunning:    false,
  setBotRunning: (botRunning) => set({ botRunning }),
  lastEvent:     null,
  setLastEvent:  (lastEvent) => set({ lastEvent }),
}))
