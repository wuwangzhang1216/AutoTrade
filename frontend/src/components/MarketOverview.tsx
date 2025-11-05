import { useEffect, useState } from 'react'
import { fetchTradingPairs } from '../api/client'

export default function MarketOverview() {
  const [pairs, setPairs] = useState<string[]>([])

  useEffect(() => {
    const loadPairs = async () => {
      try {
        const data = await fetchTradingPairs()
        setPairs(data.pairs)
      } catch (error) {
        console.error('Failed to load trading pairs:', error)
      }
    }

    loadPairs()
  }, [])

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-white mb-4">Market Overview</h3>
      <div className="flex flex-wrap gap-2">
        {pairs.map((pair) => (
          <div key={pair} className="bg-gray-700 px-3 py-2 rounded-lg text-sm">
            {pair}
          </div>
        ))}
      </div>
    </div>
  )
}
