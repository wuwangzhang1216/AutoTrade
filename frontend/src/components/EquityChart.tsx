import { useEffect, useRef, useState, useCallback } from 'react'
import { createChart, ColorType, IChartApi, ISeriesApi, LineData, Time } from 'lightweight-charts'
import { fetchEquityCurve } from '../api/client'
import { useWebSocket } from '../hooks/useWebSocket'
import { getWebSocketURL } from '../config/api'

interface EquityDataPoint {
  timestamp: number  // Backend sends Unix timestamp in milliseconds
  equity: number
  capital: number
  unrealized_pnl: number
}

// CRITICAL: Deep validation function to ensure data point is 100% valid
// This prevents ANY null/undefined/NaN values from reaching lightweight-charts
function isValidDataPoint(point: any): point is LineData {
  try {
    // Reject completely null/undefined objects
    if (point == null || typeof point !== 'object') {
      console.warn('Data point is null or not an object:', point)
      return false
    }

    const time = point.time as number
    const value = point.value

    // Check all fields exist (strict null check)
    if (time == null || value == null) {
      console.warn('Time or value is null/undefined:', { time, value })
      return false
    }

    // Check types
    if (typeof time !== 'number' || typeof value !== 'number') {
      console.warn('Time or value is not a number:', { time: typeof time, value: typeof value })
      return false
    }

    // Check for NaN and Infinity
    if (isNaN(time) || isNaN(value) || !isFinite(time) || !isFinite(value)) {
      console.warn('Time or value is NaN or Infinity:', { time, value })
      return false
    }

    // Check positive values for time, allow value >= 0 (equity can be 0)
    if (time <= 0 || value < 0) {
      console.warn('Time or value is out of valid range:', { time, value })
      return false
    }

    return true
  } catch (error) {
    console.error('Exception during validation:', error, point)
    return false
  }
}

export default function EquityChart() {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const equitySeriesRef = useRef<ISeriesApi<'Area'> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [chartKey, setChartKey] = useState(0) // Key to force chart rebuild
  const { lastMessage } = useWebSocket(getWebSocketURL())
  const lastUpdateTimeRef = useRef<number>(0) // Track last update to avoid too frequent updates
  const isMountedRef = useRef(true) // Track if component is mounted

  // Safe chart update function with validation
  const safeSetData = useCallback((chartData: LineData[]) => {
    // Triple validation before setting data
    if (!isMountedRef.current) {
      console.warn('Cannot set data: component not mounted')
      return false
    }
    if (!equitySeriesRef.current) {
      console.warn('Cannot set data: series not initialized')
      return false
    }
    if (!chartRef.current) {
      console.warn('Cannot set data: chart not initialized')
      return false
    }

    // Validate input is array
    if (!Array.isArray(chartData)) {
      console.error('Chart data is not an array:', chartData)
      return false
    }

    // Validate ALL data points
    const validData = chartData.filter(isValidDataPoint)

    if (validData.length === 0) {
      console.warn('No valid data points to set after filtering')
      return false
    }

    // CRITICAL: Deep clone and sanitize data before passing to chart
    // This ensures no reference issues can cause null values
    const sanitizedData = validData.map(point => ({
      time: Number(point.time) as Time,
      value: Number(point.value)
    }))

    // Final validation after sanitization
    const finalValidData = sanitizedData.filter(isValidDataPoint)

    if (finalValidData.length === 0) {
      console.error('All data became invalid after sanitization')
      return false
    }

    try {
      equitySeriesRef.current.setData(finalValidData)
      console.log(`Successfully set ${finalValidData.length} data points`)
      return true
    } catch (error) {
      console.error('Chart setData failed with error:', error)
      console.error('Failed data sample:', finalValidData.slice(0, 3))
      // Try to rebuild chart on next render
      setChartKey(prev => prev + 1)
      return false
    }
  }, [])

  // Safe chart update function for single point
  const safeUpdatePoint = useCallback((point: LineData) => {
    // Triple validation before updating
    if (!isMountedRef.current) {
      console.warn('Cannot update point: component not mounted')
      return false
    }
    if (!equitySeriesRef.current) {
      console.warn('Cannot update point: series not initialized')
      return false
    }
    if (!chartRef.current) {
      console.warn('Cannot update point: chart not initialized')
      return false
    }

    // Validate the point
    if (!isValidDataPoint(point)) {
      console.warn('Invalid data point, skipping update:', point)
      return false
    }

    // CRITICAL: Sanitize point before update to prevent reference issues
    const sanitizedPoint = {
      time: Number(point.time) as Time,
      value: Number(point.value)
    }

    // Validate sanitized point
    if (!isValidDataPoint(sanitizedPoint)) {
      console.error('Point became invalid after sanitization:', point, sanitizedPoint)
      return false
    }

    try {
      equitySeriesRef.current.update(sanitizedPoint)
      console.log('Successfully updated chart point:', sanitizedPoint)
      return true
    } catch (error) {
      console.error('Chart update failed with error:', error)
      console.error('Failed point:', sanitizedPoint)
      // Try to rebuild chart on next render
      setChartKey(prev => prev + 1)
      return false
    }
  }, [])

  // Initialize chart
  useEffect(() => {
    isMountedRef.current = true
    if (!chartContainerRef.current) return

    try {
      const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#d4af37',
        fontSize: 10,
      },
      grid: {
        vertLines: { color: 'rgba(212, 175, 55, 0.1)' },
        horzLines: { color: 'rgba(212, 175, 55, 0.1)' },
      },
      rightPriceScale: {
        borderColor: 'rgba(212, 175, 55, 0.3)',
      },
      timeScale: {
        borderColor: 'rgba(212, 175, 55, 0.3)',
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 5, // Add some padding on the right for smoother updates
        barSpacing: 6,
      },
      crosshair: {
        vertLine: {
          color: 'rgba(212, 175, 55, 0.6)',
          width: 1,
          style: 1,
        },
        horzLine: {
          color: 'rgba(212, 175, 55, 0.6)',
          width: 1,
          style: 1,
        },
      },
      width: chartContainerRef.current.clientWidth,
      height: 350,
      // Enable smooth scrolling and animations
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: false,
      },
      handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true,
      },
    })

    const equitySeries = chart.addAreaSeries({
      lineColor: '#d4af37',
      topColor: 'rgba(212, 175, 55, 0.4)',
      bottomColor: 'rgba(212, 175, 55, 0.0)',
      lineWidth: 2,
      priceFormat: {
        type: 'price',
        precision: 2,
        minMove: 0.01,
      },
    })

    chartRef.current = chart
    equitySeriesRef.current = equitySeries

    // CRITICAL: Initialize with empty data to prevent null errors
    // This "primes" the chart and prevents lightweight-charts internal null issues
    try {
      equitySeries.setData([])
      console.log('Chart initialized with empty dataset')
    } catch (initError) {
      console.error('Failed to initialize chart with empty data:', initError)
    }

    // Handle resize with error protection
    const handleResize = () => {
      try {
        if (chartContainerRef.current && chartRef.current) {
          chartRef.current.applyOptions({
            width: chartContainerRef.current.clientWidth,
          })
        }
      } catch (resizeError) {
        console.error('Error during chart resize:', resizeError)
      }
    }

      window.addEventListener('resize', handleResize)

      return () => {
        isMountedRef.current = false
        window.removeEventListener('resize', handleResize)
        // Clear refs before removing chart to prevent updates during unmount
        equitySeriesRef.current = null
        chartRef.current = null
        try {
          chart.remove()
        } catch (error) {
          console.error('Error removing chart:', error)
        }
      }
    } catch (error) {
      console.error('Error initializing chart:', error)
      setError('Failed to initialize chart')
    }
  }, [chartKey]) // Rebuild when chartKey changes

  // Load equity data
  useEffect(() => {
    let isMounted = true // Track if component is still mounted
    let isFirstLoad = true // Track if this is the first load

    const loadEquityData = async () => {
      try {
        if (!isMounted) return // Don't proceed if unmounted

        setLoading(true)
        setError(null)

        const data: EquityDataPoint[] = await fetchEquityCurve(30)

        if (!isMounted) return // Check again after async operation

        if (data.length === 0) {
          setError('No equity data available yet')
          return
        }

        // Convert to lightweight-charts format and filter out invalid data
        const chartData: LineData[] = data
          .filter((point) => {
            // Filter out points with null/undefined/NaN equity or timestamp
            return (
              point != null &&
              point.timestamp != null &&
              point.equity != null &&
              typeof point.timestamp === 'number' &&
              typeof point.equity === 'number' &&
              !isNaN(point.equity) &&
              !isNaN(point.timestamp) &&
              isFinite(point.equity) &&
              isFinite(point.timestamp) &&
              point.timestamp > 0 &&
              point.equity >= 0  // Allow 0 equity
            )
          })
          .map((point) => {
            const time = Math.floor(point.timestamp / 1000)
            const value = Number(point.equity)  // Explicitly convert to number

            // Return null for invalid conversions, will be filtered out
            if (!isFinite(time) || !isFinite(value) || time <= 0 || value < 0) {
              return null
            }

            return {
              time: time as Time,
              value: value,
            }
          })
          .filter((point): point is LineData => {
            // Type guard: ensure point is not null and has valid properties
            if (point == null) return false

            const time = point.time as number
            const value = point.value

            // Second pass: ensure converted values are valid
            return (
              time != null &&
              value != null &&
              typeof time === 'number' &&
              typeof value === 'number' &&
              !isNaN(time) &&
              !isNaN(value) &&
              isFinite(time) &&
              isFinite(value) &&
              time > 0 &&
              value >= 0  // Allow 0 equity
            )
          })

        // Validate we have data after filtering
        if (chartData.length === 0) {
          console.warn('No valid chart data after filtering')
          setError('No valid equity data available')
          return
        }

        // Sort by time
        chartData.sort((a, b) => (a.time as number) - (b.time as number))

        // CRITICAL: Use safe function to set data with full validation
        const success = safeSetData(chartData)

        if (!success) {
          setError('Error rendering chart')
          return
        }

        // Fit content only on first load to avoid jumping on updates
        if (chartRef.current && isFirstLoad && isMountedRef.current) {
          try {
            chartRef.current.timeScale().fitContent()
            isFirstLoad = false // Mark as no longer first load
          } catch (fitError) {
            console.error('Error fitting chart content:', fitError)
          }
        }
      } catch (err) {
        console.error('Failed to load equity curve:', err)
        setError('Failed to load equity data')
      } finally {
        setLoading(false)
      }
    }

    loadEquityData()

    // Refresh every 60 seconds (reduced from 30s for smoother experience)
    // WebSocket updates handle real-time changes
    const interval = setInterval(loadEquityData, 60000)

    return () => {
      isMounted = false // Mark component as unmounted
      clearInterval(interval)
    }
  }, [safeSetData])

  // Update chart with WebSocket data (with throttling for smooth updates)
  useEffect(() => {
    if (!lastMessage || lastMessage.type !== 'account_update') return
    if (!isMountedRef.current) return

    const data = lastMessage.data
    const now = Date.now()

    // Throttle updates: only update every 3 seconds to avoid choppy/frequent redraws
    if (now - lastUpdateTimeRef.current < 3000) {
      return
    }

    // Strict validation: ensure equity is a valid number
    if (
      data != null &&
      data.equity != null &&
      typeof data.equity === 'number' &&
      !isNaN(data.equity) &&
      isFinite(data.equity) &&
      data.equity >= 0  // Allow 0 equity
    ) {
      const time = Math.floor(now / 1000)
      const value = Number(data.equity)  // Explicitly convert to number

      // Validate both time and value are valid before creating point
      if (
        !isNaN(time) &&
        !isNaN(value) &&
        isFinite(time) &&
        isFinite(value) &&
        time > 0 &&
        value >= 0
      ) {
        const newPoint: LineData = {
          time: time as Time,
          value: value,
        }

        // CRITICAL: Use safe function to update with full validation
        const success = safeUpdatePoint(newPoint)

        if (success) {
          lastUpdateTimeRef.current = now // Update last update time only on success
        }
      } else {
        console.warn('Invalid WebSocket data point, skipping update:', { time, value, raw: data.equity })
      }
    }
  }, [lastMessage, safeUpdatePoint])

  // Manual chart rebuild function
  const rebuildChart = useCallback(() => {
    setChartKey(prev => prev + 1)
    setError(null)
    setLoading(true)
  }, [])

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h3 className="text-sm font-semibold text-white">Total Equity</h3>
          <p className="text-[10px] text-silver-400 mt-0.5">Account value over time</p>
        </div>
        <div className="flex items-center gap-2">
          {loading && (
            <div className="text-[10px] text-silver-400">Loading...</div>
          )}
          {error && (
            <button
              onClick={rebuildChart}
              className="text-[10px] px-2 py-1 bg-gold-500/20 hover:bg-gold-500/30 text-gold-400 rounded transition-colors"
            >
              Retry
            </button>
          )}
        </div>
      </div>

      {error ? (
        <div className="flex items-center justify-center h-[350px] w-full text-silver-400">
          <div className="text-center">
            <p className="text-xs">{error}</p>
            <p className="text-[10px] mt-1">Click Retry to reload the chart</p>
          </div>
        </div>
      ) : (
        <div
          ref={chartContainerRef}
          className="relative rounded-lg overflow-hidden border border-primary-900/20"
        />
      )}
    </div>
  )
}
