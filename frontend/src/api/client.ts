import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8888'

// PERFORMANCE: Add timeout and optimizations
// BUGFIX: Increased timeout to 30s to handle slow initial loads
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout (increased from 10s for slow initial loads)
  // Enable compression
  decompress: true,
})

// PERFORMANCE: Add retry logic for failed requests
let retryCount = 0
const MAX_RETRIES = 2

api.interceptors.response.use(
  (response) => {
    retryCount = 0 // Reset on success
    return response
  },
  async (error) => {
    const config = error.config

    // Log different error types
    if (error.code === 'ECONNABORTED') {
      console.error('Request timeout - server is slow or unresponsive')
    } else if (error.response?.status === 500) {
      console.error('Server error:', error.response.data)
    } else if (!error.response) {
      console.error('Network error - check if backend is running')
    }

    // PERFORMANCE: Auto-retry on timeout (but not indefinitely)
    if (error.code === 'ECONNABORTED' && retryCount < MAX_RETRIES) {
      retryCount++
      console.log(`Retrying request (attempt ${retryCount}/${MAX_RETRIES})...`)

      // Exponential backoff: wait 1s, then 2s
      await new Promise(resolve => setTimeout(resolve, 1000 * retryCount))

      return api.request(config)
    }

    retryCount = 0 // Reset for next request
    return Promise.reject(error)
  }
)

// Account
export async function fetchAccountStatus() {
  const response = await api.get('/api/account')
  return response.data
}

// Positions
export async function fetchPositions() {
  const response = await api.get('/api/positions')
  return response.data
}

// Trades (with pagination support)
export async function fetchTrades(page = 1, per_page = 20, symbol?: string) {
  const response = await api.get('/api/trades', {
    params: { page, per_page, symbol },
  })
  // Return only data array for backward compatibility
  return response.data.data
}

// Trades with metadata (full pagination response)
export async function fetchTradesPaginated(page = 1, per_page = 20, symbol?: string) {
  const response = await api.get('/api/trades', {
    params: { page, per_page, symbol },
  })
  return response.data // Returns { data: [...], meta: {...} }
}

// AI Decisions (with pagination support)
export async function fetchAIDecisions(page = 1, per_page = 20, symbol?: string) {
  const response = await api.get('/api/ai-decisions', {
    params: { page, per_page, symbol },
  })
  // Return only data array for backward compatibility
  return response.data.data
}

// AI Decisions with metadata (full pagination response)
export async function fetchAIDecisionsPaginated(page = 1, per_page = 20, symbol?: string) {
  const response = await api.get('/api/ai-decisions', {
    params: { page, per_page, symbol },
  })
  return response.data // Returns { data: [...], meta: {...} }
}

// AI Decision Detail (with reasoning)
export async function fetchAIDecisionDetail(decisionId: number) {
  const response = await api.get(`/api/ai-decisions/${decisionId}`)
  return response.data
}

// Market Data
export async function fetchMarketData(symbol: string) {
  const response = await api.get('/api/market-data', {
    params: { symbol },
  })
  return response.data
}

// OHLCV
export async function fetchOHLCV(symbol: string, timeframe = '15m', limit = 100) {
  const response = await api.get('/api/ohlcv', {
    params: { symbol, timeframe, limit },
  })
  return response.data
}

// Equity Curve
export async function fetchEquityCurve(days = 30) {
  const response = await api.get('/api/equity-curve', {
    params: { days },
  })
  return response.data
}

// Performance
export async function fetchPerformance() {
  const response = await api.get('/api/performance')
  return response.data
}

// Trading Pairs
export async function fetchTradingPairs() {
  const response = await api.get('/api/trading-pairs')
  return response.data
}

// Market Events
export async function fetchMarketEvents(
  limit = 10,
  event_type?: string,
  severity?: string,
  symbol?: string
) {
  const response = await api.get('/api/market-events', {
    params: { limit, event_type, severity, symbol }
  })
  return response.data
}

export async function fetchMarketEventsStats() {
  const response = await api.get('/api/market-events/stats')
  return response.data
}

export default api
