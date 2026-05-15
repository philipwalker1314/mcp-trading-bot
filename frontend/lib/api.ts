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
  positions:     (params?: { status?: string; symbol?: string; limit?: number }) => {
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
  dailyStats:    (date?: string) => {
    const q = date ? `?date_filter=${date}` : ''
    return request<{ data: any }>(`/analytics/daily${q}`)
  },
  summary:       () => request<{ data: any }>('/analytics/summary'),
}
