'use client'

import dynamic from 'next/dynamic'
import { usePositions }    from '@/hooks/usePositions'
import { useMarket }       from '@/hooks/useMarket'
import { useSystem }       from '@/hooks/useSystem'
import { StatusBar }       from '@/components/system/StatusBar'
import { StatsBar }        from '@/components/analytics/StatsBar'
import { PositionsPanel }  from '@/components/positions/PositionsPanel'
import { EmergencyButton } from '@/components/positions/EmergencyButton'

const PriceChart = dynamic(
  () => import('@/components/chart/PriceChart').then(m => m.PriceChart),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-full text-terminal-dim text-xs">
        LOADING CHART<span className="blink ml-1">_</span>
      </div>
    ),
  }
)

function WsProviders() {
  usePositions()
  useMarket()
  useSystem()
  return null
}

export default function Dashboard() {
  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <WsProviders />
      <StatusBar />
      <StatsBar />
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 border-r border-terminal-border overflow-hidden">
          <PriceChart />
        </div>
        <div className="w-[600px] flex flex-col overflow-hidden">
          <div className="flex-1 overflow-hidden">
            <PositionsPanel />
          </div>
          <div className="px-4 py-2 border-t border-terminal-border flex items-center justify-between">
            <span className="text-terminal-dim text-xs">
              PAPER MODE — no real orders
            </span>
            <EmergencyButton />
          </div>
        </div>
      </div>
    </div>
  )
}
