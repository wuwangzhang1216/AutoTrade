import { useEffect, useState } from 'react'
import { Menu } from '@headlessui/react'
import { ChevronDownIcon } from '@heroicons/react/24/solid'
import TradingChart from './TradingChart'
import { fetchOHLCV, fetchTradingPairs } from '../api/client'
import { CandlestickData } from 'lightweight-charts'

export default function TradingChartContainer() {
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/USDT')
  const [selectedTimeframe, setSelectedTimeframe] = useState('15m')
  const [pairs, setPairs] = useState<string[]>([])
  const [timeframes, setTimeframes] = useState<string[]>([])
  const [chartData, setChartData] = useState<CandlestickData[]>([])

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const data = await fetchTradingPairs()
        setPairs(data.pairs)
        setTimeframes(data.timeframes)
      } catch (error) {
        console.error('Failed to load config:', error)
      }
    }

    loadConfig()
  }, [])

  useEffect(() => {
    const loadChartData = async () => {
      try {
        const response = await fetchOHLCV(selectedSymbol, selectedTimeframe, 200)

        if (!response.data || response.data.length === 0) {
          console.warn('No OHLCV data received')
          setChartData([])
          return
        }

        // Convert to TradingView format with strict validation
        const formattedData: CandlestickData[] = response.data
          .filter((item: any) => {
            // Filter out items with null/undefined/invalid values
            return (
              item.timestamp != null &&
              item.open != null &&
              item.high != null &&
              item.low != null &&
              item.close != null &&
              !isNaN(item.open) &&
              !isNaN(item.high) &&
              !isNaN(item.low) &&
              !isNaN(item.close) &&
              isFinite(item.open) &&
              isFinite(item.high) &&
              isFinite(item.low) &&
              isFinite(item.close) &&
              item.high >= item.low && // Validate OHLC logic
              item.high >= item.open &&
              item.high >= item.close &&
              item.low <= item.open &&
              item.low <= item.close
            )
          })
          .map((item: any) => {
            const timestamp = new Date(item.timestamp).getTime() / 1000
            return {
              time: timestamp,
              open: item.open,
              high: item.high,
              low: item.low,
              close: item.close,
            }
          })
          .filter((item: CandlestickData) => {
            // Second pass: ensure converted values are valid
            return (
              !isNaN(item.time as number) &&
              isFinite(item.time as number) &&
              (item.time as number) > 0
            )
          })

        // Sort by time to ensure proper ordering
        formattedData.sort((a, b) => (a.time as number) - (b.time as number))

        if (formattedData.length === 0) {
          console.warn('No valid OHLCV data after filtering')
        }

        setChartData(formattedData)
      } catch (error) {
        console.error('Failed to load chart data:', error)
        setChartData([])
      }
    }

    loadChartData()
    const interval = setInterval(loadChartData, 60000) // Refresh every minute

    return () => clearInterval(interval)
  }, [selectedSymbol, selectedTimeframe])

  return (
    <div className="space-y-2">
      <div className="flex items-center space-x-2">
        {/* Symbol selector */}
        <Menu as="div" className="relative inline-block text-left">
          <div>
            <Menu.Button className="inline-flex w-full justify-center rounded-lg bg-elite-975 px-3 py-1.5 text-xs font-semibold text-white hover:bg-elite-950 hover:shadow-premium focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-600 focus-visible:ring-opacity-75 border border-primary-900/30 transition-all duration-300">
              {selectedSymbol}
              <ChevronDownIcon
                className="ml-1.5 -mr-0.5 h-4 w-4 text-primary-400"
                aria-hidden="true"
              />
            </Menu.Button>
          </div>
          <Menu.Items className="absolute left-0 mt-1 w-40 origin-top-left divide-y divide-primary-900/10 rounded-lg bg-elite-950 shadow-elite ring-1 ring-primary-900/30 focus:outline-none z-10 max-h-48 overflow-y-auto border border-primary-900/20 backdrop-blur-lg">
            <div className="px-1 py-1">
              {pairs.map((pair) => (
                <Menu.Item key={pair}>
                  {({ active }) => (
                    <button
                      className={`${
                        active ? 'bg-gradient-gold text-black font-semibold' : 'text-silver-300'
                      } group flex w-full items-center rounded-md px-2 py-1.5 text-xs transition-all duration-200`}
                      onClick={() => setSelectedSymbol(pair)}
                    >
                      {pair}
                    </button>
                  )}
                </Menu.Item>
              ))}
            </div>
          </Menu.Items>
        </Menu>

        {/* Timeframe selector */}
        <Menu as="div" className="relative inline-block text-left">
          <div>
            <Menu.Button className="inline-flex w-full justify-center rounded-lg bg-elite-975 px-3 py-1.5 text-xs font-semibold text-white hover:bg-elite-950 hover:shadow-premium focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-600 focus-visible:ring-opacity-75 border border-primary-900/30 transition-all duration-300">
              {selectedTimeframe}
              <ChevronDownIcon
                className="ml-1.5 -mr-0.5 h-4 w-4 text-primary-400"
                aria-hidden="true"
              />
            </Menu.Button>
          </div>
          <Menu.Items className="absolute left-0 mt-1 w-24 origin-top-left divide-y divide-primary-900/10 rounded-lg bg-elite-950 shadow-elite ring-1 ring-primary-900/30 focus:outline-none z-10 border border-primary-900/20 backdrop-blur-lg">
            <div className="px-1 py-1">
              {timeframes.map((tf) => (
                <Menu.Item key={tf}>
                  {({ active }) => (
                    <button
                      className={`${
                        active ? 'bg-gradient-gold text-black font-semibold' : 'text-silver-300'
                      } group flex w-full items-center rounded-md px-2 py-1.5 text-xs transition-all duration-200`}
                      onClick={() => setSelectedTimeframe(tf)}
                    >
                      {tf}
                    </button>
                  )}
                </Menu.Item>
              ))}
            </div>
          </Menu.Items>
        </Menu>
      </div>

      <TradingChart symbol={selectedSymbol} data={chartData} />
    </div>
  )
}
