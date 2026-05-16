import { StrategyConfig, StrategyVersion, ValidationResult } from '@/store/strategies'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json()
}

export const api = {
  // Health
  health: () => request<{ status: string; trading_enabled: boolean; trading_bot_running: boolean }>('/health'),
  status: () => request<{ environment: string; paper_trading: boolean; trading_enabled: boolean; open_positions: number }>('/status'),

  // Positions
  positions: (params?: { status?: string; symbol?: string; limit?: number }) => {
    const q = new URLSearchParams(params as any).toString()
    return request<{ data: any[]; meta: any }>(`/positions/${q ? '?' + q : ''}`)
  },
  openPositions: () => request<{ data: any[]; meta: any }>('/positions/open'),
  getPosition:   (id: number) => request<{ data: any }>(`/positions/${id}`),
  getEvents:     (id: number) => request<{ data: any[] }>(`/positions/${id}/events`),
  closePosition: (id: number, exit_price: number) =>
    request<{ data: any }>(`/positions/${id}/close`, {
      method: 'POST',
      body: JSON.stringify({ exit_price }),
    }),
  emergencyClose: () =>
    request<{ data: any }>('/positions/emergency-close', {
      method: 'POST',
      body: JSON.stringify({ confirm: true }),
    }),

  // Analytics
  dailyStats: (date?: string) => {
    const q = date ? `?date_filter=${date}` : ''
    return request<{ data: any }>(`/analytics/daily${q}`)
  },
  summary: () => request<{ data: any }>('/analytics/summary'),

  // Strategies — Phase 5
  strategies: {
    list: (enabledOnly?: boolean) =>
      request<{ data: StrategyConfig[]; meta: any }>(
        `/strategies/${enabledOnly ? '?enabled_only=true' : ''}`
      ),

    get: (id: number) =>
      request<{ data: StrategyConfig }>(`/strategies/${id}`),

    create: (data: Partial<StrategyConfig>) =>
      request<{ data: StrategyConfig }>('/strategies/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    update: (id: number, data: Partial<StrategyConfig>) =>
      request<{ data: StrategyConfig }>(`/strategies/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),

    delete: (id: number) =>
      request<{ data: any }>(`/strategies/${id}`, { method: 'DELETE' }),

    enable: (id: number) =>
      request<{ data: StrategyConfig }>(`/strategies/${id}/enable`, { method: 'POST' }),

    disable: (id: number) =>
      request<{ data: StrategyConfig }>(`/strategies/${id}/disable`, { method: 'POST' }),

    rollback: (id: number, targetVersion: number) =>
      request<{ data: StrategyConfig }>(`/strategies/${id}/rollback`, {
        method: 'POST',
        body: JSON.stringify({ target_version: targetVersion }),
      }),

    versions: (id: number) =>
      request<{ data: StrategyVersion[] }>(`/strategies/${id}/versions`),

    validate: (data: Partial<StrategyConfig>) =>
      request<{ data: ValidationResult }>('/strategies/validate', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  },

  // Copilot — Phase 6
  copilot: {
    chat: (message: string, conversationHistory: { role: string; content: string }[]) =>
      request<{ data: { response: string; actions_taken: any[]; data: any } }>('/copilot/chat', {
        method: 'POST',
        body: JSON.stringify({
          message,
          conversation_history: conversationHistory,
        }),
      }),
  },
}
