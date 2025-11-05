import { useEffect, useState } from 'react'
import { fetchPositions } from '../api/client'

interface Position {
  symbol: string
  side: string
  amount: number
  entry_price: number
  current_price: number
  unrealized_pnl: number
  unrealized_pnl_percent: number
  margin: number
  leverage: number
}

export default function PositionsList() {
  const [positions, setPositions] = useState<Position[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isInitialLoad = true

    const loadPositions = async () => {
      try {
        // PERFORMANCE: Only show loading on initial load
        if (isInitialLoad) {
          setLoading(true)
        }
        setError(null)

        const data = await fetchPositions()
        setPositions(data)

        if (isInitialLoad) {
          isInitialLoad = false
        }
      } catch (error) {
        console.error('Failed to load positions:', error)
        setError('Failed to load positions. Retrying...')

        // Don't hide loading on initial load failure
        if (!isInitialLoad) {
          // On subsequent failures, keep showing old data
        }
      } finally {
        if (isInitialLoad || loading) {
          setLoading(false)
        }
      }
    }

    loadPositions()
    // PERFORMANCE: Reduced polling from 5s to 15s (positions don't change that frequently)
    const interval = setInterval(loadPositions, 15000)

    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="relative rounded-lg border border-primary-900/20 bg-elite-975/50 backdrop-blur-sm overflow-hidden">
        {/* Table Header Skeleton */}
        <div className="bg-elite-950/50 px-1 py-1">
          <div className="flex gap-2">
            {['Symbol', 'Side', 'Amount', 'Entry', 'Current', 'P&L', 'Lev'].map((_, i) => (
              <div key={i} className="flex-1">
                <div className="h-3 bg-primary-900/20 rounded animate-pulse"></div>
              </div>
            ))}
          </div>
        </div>

        {/* Table Rows Skeleton */}
        <div className="divide-y divide-primary-900/10">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="px-1 py-1.5 flex gap-2 animate-pulse" style={{ animationDelay: `${i * 60}ms` }}>
              <div className="flex-1 h-4 bg-primary-900/10 rounded"></div>
              <div className="flex-1 h-4 bg-primary-900/10 rounded"></div>
              <div className="flex-1 h-4 bg-primary-900/10 rounded"></div>
              <div className="flex-1 h-4 bg-primary-900/10 rounded"></div>
              <div className="flex-1 h-4 bg-primary-900/10 rounded"></div>
              <div className="flex-1 h-4 bg-primary-900/10 rounded"></div>
              <div className="flex-1 h-4 bg-primary-900/10 rounded"></div>
            </div>
          ))}
        </div>

        {/* Loading Indicator with Animation */}
        <div className="absolute inset-0 bg-elite-975/80 backdrop-blur-sm flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="relative">
              {/* Spinning outer ring */}
              <div className="w-12 h-12 rounded-full border-2 border-primary-900/20"></div>
              <div className="absolute inset-0 w-12 h-12 rounded-full border-2 border-transparent border-t-primary-500 animate-spin"></div>

              {/* Pulsing inner dot */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-3 h-3 rounded-full bg-primary-500 animate-pulse"></div>
              </div>
            </div>

            {/* Loading text with dots animation */}
            <div className="text-sm text-primary-400 font-medium flex items-center gap-1">
              <span>Loading positions</span>
              <span className="flex gap-0.5">
                <span className="animate-bounce" style={{ animationDelay: '0ms' }}>.</span>
                <span className="animate-bounce" style={{ animationDelay: '150ms' }}>.</span>
                <span className="animate-bounce" style={{ animationDelay: '300ms' }}>.</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (positions.length === 0) {
    return (
      <div className="text-center py-12 text-silver-400 bg-elite-975 rounded-lg border border-primary-900/20">
        {error ? (
          <div className="flex flex-col items-center gap-2">
            <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-red-400">{error}</span>
          </div>
        ) : (
          'No open positions'
        )}
      </div>
    )
  }

  return (
    <div className="overflow-y-auto max-h-[365px] pr-2 custom-scrollbar">
      {/* Error banner for background refresh failures */}
      {error && (
        <div className="px-3 py-2 mb-2 bg-red-900/20 border border-red-500/30 rounded-lg flex items-center gap-2 text-xs text-red-400">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      <div className="rounded-lg border border-primary-900/20 bg-elite-975/50 backdrop-blur-sm overflow-hidden">
        <table className="w-full divide-y divide-primary-900/20 table-fixed">
        <thead className="sticky top-0 bg-elite-950/95 backdrop-blur-sm z-10">
          <tr>
            <th className="px-1 py-1 text-left text-[9px] font-semibold text-primary-400 uppercase w-[14%]">
              Symbol
            </th>
            <th className="px-1 py-1 text-left text-[9px] font-semibold text-primary-400 uppercase w-[11%]">
              Side
            </th>
            <th className="px-1 py-1 text-left text-[9px] font-semibold text-primary-400 uppercase w-[13%]">
              Amount
            </th>
            <th className="px-1 py-1 text-left text-[9px] font-semibold text-primary-400 uppercase w-[17%]">
              Entry
            </th>
            <th className="px-1 py-1 text-left text-[9px] font-semibold text-primary-400 uppercase w-[17%]">
              Current
            </th>
            <th className="px-1 py-1 text-left text-[9px] font-semibold text-primary-400 uppercase w-[20%]">
              P&L
            </th>
            <th className="px-1 py-1 text-left text-[9px] font-semibold text-primary-400 uppercase w-[8%]">
              Lev
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-primary-900/10">
          {positions.map((position) => (
            <tr key={position.symbol} className="hover:bg-elite-950/30 transition-colors">
              <td className="px-1 py-1.5 text-[10px] font-bold text-white truncate">
                {position.symbol}
              </td>
              <td className="px-1 py-1.5 text-[10px]">
                <span className={`badge ${position.side === 'LONG' ? 'badge-success' : 'badge-danger'}`}>
                  {position.side}
                </span>
              </td>
              <td className="px-1 py-1.5 text-[10px] text-silver-200 truncate">
                {position.amount.toFixed(4)}
              </td>
              <td className="px-1 py-1.5 text-[10px] text-silver-200 truncate">
                ${position.entry_price.toLocaleString()}
              </td>
              <td className="px-1 py-1.5 text-[10px] text-silver-200 truncate">
                ${position.current_price.toLocaleString()}
              </td>
              <td className="px-1 py-1.5 text-[10px]">
                <div className={position.unrealized_pnl >= 0 ? 'text-green-400 font-semibold' : 'text-red-400 font-semibold'}>
                  <div>{position.unrealized_pnl >= 0 ? '+' : ''}${position.unrealized_pnl.toFixed(2)}</div>
                  <div className="text-[9px] opacity-80">
                    ({position.unrealized_pnl_percent.toFixed(2)}%)
                  </div>
                </div>
              </td>
              <td className="px-1 py-1.5 text-[10px] text-primary-400 font-semibold truncate">
                {position.leverage}x
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  )
}
