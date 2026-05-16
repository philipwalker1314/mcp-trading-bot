'use client'

import { useEffect, useRef } from 'react'
import { useAnalyticsStore } from '@/store/analytics'

export function EquityChart() {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef     = useRef<any>(null)
  const seriesRef    = useRef<any>(null)
  const { equityCurve, loading } = useAnalyticsStore()

  // Inicializar chart
  useEffect(() => {
    if (!containerRef.current) return

    import('lightweight-charts').then(({ createChart, CrosshairMode, LineStyle }) => {
      const chart = createChart(containerRef.current!, {
        layout: {
          background: { color: '#080c0f' },
          textColor:  '#8ba8bc',
          fontFamily: 'JetBrains Mono, monospace',
          fontSize:   11,
        },
        grid: {
          vertLines: { color: '#1a2530', style: LineStyle.Dotted },
          horzLines: { color: '#1a2530', style: LineStyle.Dotted },
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
          borderColor:    '#1a2530',
          textColor:      '#8ba8bc',
          timeVisible:    true,
          secondsVisible: false,
        },
        handleScroll: true,
        handleScale:  true,
      })

      // Área bajo la curva
      const areaSeries = chart.addAreaSeries({
        lineColor:        '#00d4a0',
        topColor:         'rgba(0, 212, 160, 0.15)',
        bottomColor:      'rgba(0, 212, 160, 0.0)',
        lineWidth:        2,
        priceLineVisible: false,
        crosshairMarkerVisible: true,
        crosshairMarkerRadius:  4,
        crosshairMarkerBorderColor: '#00d4a0',
        crosshairMarkerBackgroundColor: '#080c0f',
      })

      chartRef.current  = chart
      seriesRef.current = areaSeries

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

  // Actualizar datos cuando cambia equityCurve
  useEffect(() => {
    if (!seriesRef.current || equityCurve.length === 0) return

    // Detectar si hay pérdidas para colorear el área de rojo
    const lastValue = equityCurve[equityCurve.length - 1]?.cumulative_pnl ?? 0
    const isNegative = lastValue < 0

    seriesRef.current.applyOptions({
      lineColor:   isNegative ? '#ff4c6a' : '#00d4a0',
      topColor:    isNegative ? 'rgba(255, 76, 106, 0.15)' : 'rgba(0, 212, 160, 0.15)',
      bottomColor: isNegative ? 'rgba(255, 76, 106, 0.0)' : 'rgba(0, 212, 160, 0.0)',
    })

    // Convertir fechas a timestamps Unix (segundos)
    const data = equityCurve.map(point => ({
      time:  Math.floor(new Date(point.date).getTime() / 1000) as any,
      value: point.cumulative_pnl,
    }))

    seriesRef.current.setData(data)
    chartRef.current?.timeScale().fitContent()
  }, [equityCurve])

  const isEmpty = equityCurve.length === 0

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-terminal-border">
        <div className="flex items-center gap-2">
          <span className="text-terminal-dim text-xs uppercase tracking-widest">
            Equity Curve
          </span>
          <span className="text-terminal-dim text-xs">30d</span>
        </div>
        {loading && (
          <span className="text-terminal-dim text-xs animate-pulse">LOADING_</span>
        )}
        {!loading && !isEmpty && (
          <span className={`text-xs font-mono font-semibold ${
            (equityCurve[equityCurve.length - 1]?.cumulative_pnl ?? 0) >= 0
              ? 'text-terminal-green'
              : 'text-terminal-red'
          }`}>
            {(() => {
              const v = equityCurve[equityCurve.length - 1]?.cumulative_pnl ?? 0
              return (v >= 0 ? '+' : '') + v.toFixed(2)
            })()}
          </span>
        )}
      </div>

      {isEmpty && !loading ? (
        <div className="flex items-center justify-center flex-1 text-terminal-dim text-xs">
          <span>SIN DATOS<span className="blink ml-1">_</span></span>
        </div>
      ) : (
        <div ref={containerRef} className="w-full" style={{ height: 'calc(100vh - 160px)' }} />
      )}
    </div>
  )
}
