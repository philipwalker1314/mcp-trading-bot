'use client'

import { useEffect, useRef } from 'react'
import { useTradingStore } from '@/store/trading'

export function PriceChart() {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef     = useRef<any>(null)
  const seriesRef    = useRef<any>(null)
  const { prices }   = useTradingStore()

  // Init chart
  useEffect(() => {
    if (!containerRef.current) return

    import('lightweight-charts').then(({ createChart, CrosshairMode }) => {
      const chart = createChart(containerRef.current!, {
        layout: {
          background: { color: '#080c0f' },
          textColor:  '#8ba8bc',
          fontFamily: 'JetBrains Mono, monospace',
          fontSize:   11,
        },
        grid: {
          vertLines:   { color: '#1a2530', style: 1 },
          horzLines:   { color: '#1a2530', style: 1 },
        },
        crosshair: {
          mode: CrosshairMode.Normal,
          vertLine: { color: '#3d5a6e', labelBackgroundColor: '#0d1317' },
          horzLine: { color: '#3d5a6e', labelBackgroundColor: '#0d1317' },
        },
        rightPriceScale: {
          borderColor: '#1a2530',
          textColor:   '#8ba8bc',
        },
        timeScale: {
          borderColor:     '#1a2530',
          textColor:       '#8ba8bc',
          timeVisible:     true,
          secondsVisible:  false,
        },
        handleScroll:  true,
        handleScale:   true,
      })

      const series = chart.addCandlestickSeries({
        upColor:          '#00d4a0',
        downColor:        '#ff4c6a',
        borderUpColor:    '#00d4a0',
        borderDownColor:  '#ff4c6a',
        wickUpColor:      '#00d4a040',
        wickDownColor:    '#ff4c6a40',
      })

      chartRef.current  = chart
      seriesRef.current = series

      // Load historical data
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/positions/`)
        .catch(() => {})

      // Fetch OHLCV from Binance public API for chart seed
      fetch('https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=200')
        .then(r => r.json())
        .then((candles: any[]) => {
          const data = candles.map((c: any) => ({
            time:  Math.floor(c[0] / 1000) as any,
            open:  parseFloat(c[1]),
            high:  parseFloat(c[2]),
            low:   parseFloat(c[3]),
            close: parseFloat(c[4]),
          }))
          series.setData(data)
          chart.timeScale().fitContent()
        })
        .catch(() => {})

      // Resize observer
      const ro = new ResizeObserver(() => {
        if (containerRef.current) {
          chart.applyOptions({
            width:  containerRef.current.clientWidth,
            height: containerRef.current.clientHeight,
          })
        }
      })
      ro.observe(containerRef.current!)

      return () => {
        ro.disconnect()
        chart.remove()
      }
    })
  }, [])

  // Update last candle with live price
  useEffect(() => {
    const price = prices['BTC/USDT']
    if (!seriesRef.current || !price) return

    const now = Math.floor(Date.now() / 1000)
    const barTime = Math.floor(now / 60) * 60 as any

    seriesRef.current.update({
      time:  barTime,
      open:  price,
      high:  price,
      low:   price,
      close: price,
    })
  }, [prices['BTC/USDT']])

  return (
    <div className="relative z-10 flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-terminal-border">
        <span className="text-terminal-dim text-xs uppercase tracking-widest">
          BTC/USDT <span className="text-terminal-muted">1m</span>
        </span>
        <span className="text-terminal-dim text-xs">Binance</span>
      </div>
      <div ref={containerRef} className="flex-1 w-full" />
    </div>
  )
}
