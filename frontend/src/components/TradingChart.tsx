import { useEffect, useRef, useState } from 'react'
import { createChart, IChartApi, ISeriesApi, CandlestickData } from 'lightweight-charts'

interface TradingChartProps {
  symbol: string
  data: CandlestickData[]
}

export default function TradingChart({ symbol, data }: TradingChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!chartContainerRef.current) return

    // Create chart with premium black theme
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 300,
      layout: {
        background: { color: '#000000' },
        textColor: '#a1a1aa',
      },
      grid: {
        vertLines: { color: '#0a0a0a' },
        horzLines: { color: '#0a0a0a' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#ca8a04',
      },
      timeScale: {
        borderColor: '#ca8a04',
        timeVisible: true,
        secondsVisible: false,
      },
    })

    chartRef.current = chart

    // Add candlestick series with premium colors
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#4ade80',
      downColor: '#f87171',
      borderVisible: false,
      wickUpColor: '#4ade80',
      wickDownColor: '#f87171',
    })

    candlestickSeriesRef.current = candlestickSeries

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      if (chartRef.current) {
        chartRef.current.remove()
      }
    }
  }, [])

  useEffect(() => {
    if (!candlestickSeriesRef.current) return

    try {
      // Reset error state
      setError(null)

      // Validate data before setting
      if (!data || data.length === 0) {
        console.log('No chart data available yet')
        return
      }

      // Additional validation: ensure all data points are valid
      const invalidPoint = data.find(
        (d) =>
          d.time == null ||
          d.open == null ||
          d.high == null ||
          d.low == null ||
          d.close == null ||
          isNaN(d.open) ||
          isNaN(d.high) ||
          isNaN(d.low) ||
          isNaN(d.close)
      )

      if (invalidPoint) {
        console.error('Invalid data point detected:', invalidPoint)
        setError('Invalid chart data detected')
        return
      }

      // Set data with try-catch protection
      candlestickSeriesRef.current.setData(data)

      // Fit content with error handling
      if (chartRef.current) {
        try {
          chartRef.current.timeScale().fitContent()
        } catch (fitError) {
          console.error('Error fitting chart content:', fitError)
        }
      }
    } catch (err) {
      console.error('Error updating chart data:', err)
      console.error('Data that caused error:', data)
      setError('Failed to render chart')
    }
  }, [data])

  return (
    <div className="card">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-lg font-bold bg-gradient-gold bg-clip-text text-transparent">{symbol}</h3>
        <div className="text-xs text-silver-400 font-medium">Live Chart</div>
      </div>
      {error ? (
        <div className="flex items-center justify-center h-[300px] text-silver-400">
          <div className="text-center">
            <p className="text-xs">{error}</p>
            <p className="text-[10px] mt-1">Please check data quality or try again later</p>
          </div>
        </div>
      ) : (
        <div ref={chartContainerRef} className="w-full rounded-lg overflow-hidden border border-primary-900/20" />
      )}
    </div>
  )
}
