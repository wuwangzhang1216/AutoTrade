// API Service Layer for connecting to backend microservices
// Rebuild trigger

export interface ApiConfig {
  marketDataUrl: string;
  decisionEngineUrl: string;
  tradingServiceUrl: string;
}

// Support both unified service and separate services
// If VITE_UNIFIED_SERVICE_URL is set, use it for all services
// Otherwise, fall back to separate service URLs
const UNIFIED_URL = import.meta.env.VITE_UNIFIED_SERVICE_URL;

const API_CONFIG: ApiConfig = {
  marketDataUrl: UNIFIED_URL || import.meta.env.VITE_MARKET_DATA_URL || 'http://localhost:8080',
  decisionEngineUrl: UNIFIED_URL || import.meta.env.VITE_DECISION_ENGINE_URL || 'http://localhost:8080',
  tradingServiceUrl: UNIFIED_URL || import.meta.env.VITE_TRADING_SERVICE_URL || 'http://localhost:8080',
};

// Market Data Service Types
export interface MarketDataResponse {
  symbol: string;
  price: number;
  volume_24h: number;
  change_24h: number;
  timestamp: string;
}

export interface TechnicalIndicators {
  symbol: string;
  rsi: number;
  macd: {
    macd: number;
    signal: number;
    histogram: number;
  };
  bollinger_bands: {
    upper: number;
    middle: number;
    lower: number;
  };
  timestamp: string;
}

// Decision Engine Types
export interface TradingSignal {
  symbol: string;
  signal: 'buy' | 'sell' | 'hold';
  confidence: number;
  strategy: string;
  reasoning: string;
  suggested_position_size: number;
  timestamp: string;
}

// Trading Service Types
export interface Order {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  order_type: 'market' | 'limit';
  quantity: number;
  price?: number;
  status: 'pending' | 'filled' | 'cancelled' | 'rejected';
  filled_quantity: number;
  average_price: number;
  created_at: string;
  updated_at: string;
}

export interface Position {
  symbol: string;
  side: 'long' | 'short';
  quantity: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
}

export interface Portfolio {
  total_value: number;
  cash_balance: number;
  positions_value: number;
  total_pnl: number;
  total_pnl_percent: number;
  positions: Position[];
  updated_at: string;
}

export interface PerformanceMetrics {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  average_profit: number;
  average_loss: number;
  profit_factor: number;
  sharpe_ratio: number;
  max_drawdown: number;
  total_return: number;
  total_return_percent: number;
}

// Multi-Agent Types
export interface AgentLeaderboardEntry {
  agent_id: string;
  total_value: number;
  total_pnl: number;
  total_pnl_percent: number;
  cash_balance: number;
  positions_count: number;
  trades_count: number;
  rank: number;
  // Analytics fields
  avg_trade_size?: number;
  median_trade_size?: number;
  avg_hold_time?: string;
  median_hold_time?: string;
  percent_long?: number;
  expectancy?: number;
  avg_confidence?: number;
  median_confidence?: number;
  win_rate?: number;
  biggest_win?: number;
  biggest_loss?: number;
  total_fees?: number;
  sharpe_ratio?: number;
}

export interface AggregateStats {
  total_agents: number;
  total_value: number;
  total_initial: number;
  total_pnl: number;
  avg_pnl_percent: number;
  total_trades: number;
  total_positions: number;
  best_performer: {
    agent_id: string;
    value: number;
    pnl_percent: number;
  };
  worst_performer: {
    agent_id: string;
    value: number;
    pnl_percent: number;
  };
  timestamp: string;
}

// API Error handling
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public service?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Generic fetch wrapper with error handling
async function fetchApi<T>(
  url: string,
  options?: RequestInit,
  serviceName?: string
): Promise<T> {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        // 防止浏览器缓存 API 响应
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new ApiError(
        `API request failed: ${errorText}`,
        response.status,
        serviceName
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      undefined,
      serviceName
    );
  }
}

// ============================================================================
// Market Data Service API
// ============================================================================

export const marketDataApi = {
  /**
   * Get current market data for a symbol
   */
  getMarketData: async (symbol: string): Promise<MarketDataResponse> => {
    // Try unified service endpoint first, then fall back to market prefix
    const url = UNIFIED_URL
      ? `${API_CONFIG.marketDataUrl}/api/market/${symbol}`
      : `${API_CONFIG.marketDataUrl}/market/api/market/${symbol}`;
    return fetchApi<MarketDataResponse>(
      url,
      undefined,
      'Market Data Service'
    );
  },

  /**
   * Get market data for multiple symbols
   */
  getMultipleMarketData: async (symbols: string[]): Promise<MarketDataResponse[]> => {
    const promises = symbols.map(symbol =>
      marketDataApi.getMarketData(symbol).catch(() => null)
    );
    const results = await Promise.all(promises);
    return results.filter((r): r is MarketDataResponse => r !== null);
  },

  /**
   * Get technical indicators for a symbol
   */
  getTechnicalIndicators: async (symbol: string): Promise<TechnicalIndicators> => {
    return fetchApi<TechnicalIndicators>(
      `${API_CONFIG.marketDataUrl}/api/indicators/${symbol}`,
      undefined,
      'Market Data Service'
    );
  },

  /**
   * Get historical price data
   */
  getHistoricalData: async (
    symbol: string,
    interval: string = '1h',
    limit: number = 100
  ): Promise<any[]> => {
    return fetchApi<any[]>(
      `${API_CONFIG.marketDataUrl}/api/historical/${symbol}?interval=${interval}&limit=${limit}`,
      undefined,
      'Market Data Service'
    );
  },

  /**
   * Check service health
   */
  healthCheck: async (): Promise<{ status: string }> => {
    return fetchApi<{ status: string }>(
      `${API_CONFIG.marketDataUrl}/health`,
      undefined,
      'Market Data Service'
    );
  },
};

// ============================================================================
// Decision Engine API
// ============================================================================

export const decisionEngineApi = {
  /**
   * Get trading signal for a symbol
   */
  getSignal: async (symbol: string, strategy?: string): Promise<TradingSignal> => {
    const url = strategy
      ? `${API_CONFIG.decisionEngineUrl}/api/signal/${symbol}?strategy=${strategy}`
      : `${API_CONFIG.decisionEngineUrl}/api/signal/${symbol}`;

    return fetchApi<TradingSignal>(
      url,
      undefined,
      'Decision Engine'
    );
  },

  /**
   * Get signals for multiple symbols
   */
  getMultipleSignals: async (symbols: string[]): Promise<TradingSignal[]> => {
    const promises = symbols.map(symbol =>
      decisionEngineApi.getSignal(symbol).catch(() => null)
    );
    const results = await Promise.all(promises);
    return results.filter((r): r is TradingSignal => r !== null);
  },

  /**
   * Get available strategies
   */
  getStrategies: async (): Promise<string[]> => {
    return fetchApi<string[]>(
      `${API_CONFIG.decisionEngineUrl}/api/strategies`,
      undefined,
      'Decision Engine'
    );
  },

  /**
   * Check service health
   */
  healthCheck: async (): Promise<{ status: string }> => {
    return fetchApi<{ status: string }>(
      `${API_CONFIG.decisionEngineUrl}/health`,
      undefined,
      'Decision Engine'
    );
  },
};

// ============================================================================
// Trading Service API
// ============================================================================

export const tradingServiceApi = {
  /**
   * Get current portfolio
   */
  getPortfolio: async (): Promise<Portfolio> => {
    return fetchApi<Portfolio>(
      `${API_CONFIG.tradingServiceUrl}/api/portfolio`,
      undefined,
      'Trading Service'
    );
  },

  /**
   * Get all positions
   */
  getPositions: async (): Promise<Position[]> => {
    return fetchApi<Position[]>(
      `${API_CONFIG.tradingServiceUrl}/api/positions`,
      undefined,
      'Trading Service'
    );
  },

  /**
   * Place a new order
   */
  placeOrder: async (order: {
    symbol: string;
    side: 'buy' | 'sell';
    quantity: number;
    order_type: 'market' | 'limit';
    price?: number;
  }): Promise<Order> => {
    return fetchApi<Order>(
      `${API_CONFIG.tradingServiceUrl}/api/orders`,
      {
        method: 'POST',
        body: JSON.stringify(order),
      },
      'Trading Service'
    );
  },

  /**
   * Get order by ID
   */
  getOrder: async (orderId: string): Promise<Order> => {
    return fetchApi<Order>(
      `${API_CONFIG.tradingServiceUrl}/api/orders/${orderId}`,
      undefined,
      'Trading Service'
    );
  },

  /**
   * Get all orders
   */
  getOrders: async (status?: string): Promise<Order[]> => {
    const url = status
      ? `${API_CONFIG.tradingServiceUrl}/api/orders?status=${status}`
      : `${API_CONFIG.tradingServiceUrl}/api/orders`;

    return fetchApi<Order[]>(
      url,
      undefined,
      'Trading Service'
    );
  },

  /**
   * Cancel an order
   */
  cancelOrder: async (orderId: string): Promise<Order> => {
    return fetchApi<Order>(
      `${API_CONFIG.tradingServiceUrl}/api/orders/${orderId}/cancel`,
      {
        method: 'POST',
      },
      'Trading Service'
    );
  },

  /**
   * Get performance metrics
   */
  getPerformanceMetrics: async (): Promise<PerformanceMetrics> => {
    return fetchApi<PerformanceMetrics>(
      `${API_CONFIG.tradingServiceUrl}/api/performance`,
      undefined,
      'Trading Service'
    );
  },

  /**
   * Get trade history
   */
  getTradeHistory: async (limit: number = 50): Promise<any[]> => {
    return fetchApi<any[]>(
      `${API_CONFIG.tradingServiceUrl}/api/trades?limit=${limit}`,
      undefined,
      'Trading Service'
    );
  },

  /**
   * Check service health
   */
  healthCheck: async (): Promise<{ status: string }> => {
    return fetchApi<{ status: string }>(
      `${API_CONFIG.tradingServiceUrl}/health`,
      undefined,
      'Trading Service'
    );
  },

  /**
   * Get agent leaderboard (multi-agent)
   */
  getLeaderboard: async (): Promise<AgentLeaderboardEntry[]> => {
    return fetchApi<AgentLeaderboardEntry[]>(
      `${API_CONFIG.tradingServiceUrl}/api/agents/leaderboard`,
      undefined,
      'Trading Service'
    );
  },

  /**
   * Get aggregate statistics across all agents
   */
  getAggregateStats: async (): Promise<AggregateStats> => {
    return fetchApi<AggregateStats>(
      `${API_CONFIG.tradingServiceUrl}/api/agents/aggregate`,
      undefined,
      'Trading Service'
    );
  },

  /**
   * Get portfolio for specific agent
   */
  getAgentPortfolio: async (agentId: string): Promise<Portfolio> => {
    return fetchApi<Portfolio>(
      `${API_CONFIG.tradingServiceUrl}/api/agents/${agentId}/portfolio`,
      undefined,
      'Trading Service'
    );
  },

  /**
   * Get all positions across all agents
   */
  getAllPositions: async (): Promise<any[]> => {
    return fetchApi<any[]>(
      `${API_CONFIG.tradingServiceUrl}/api/positions/all`,
      undefined,
      'Trading Service'
    );
  },

  /**
   * Get all trades across all agents
   */
  getAllTrades: async (limit: number = 100): Promise<any[]> => {
    return fetchApi<any[]>(
      `${API_CONFIG.tradingServiceUrl}/api/trades/all?limit=${limit}`,
      undefined,
      'Trading Service'
    );
  },

};

// ============================================================================
// Combined API Functions
// ============================================================================

/**
 * Get dashboard data (combines data from multiple services)
 */
export const getDashboardData = async (symbols: string[] = ['BTC', 'ETH', 'SOL']) => {
  try {
    const [marketData, portfolio, performance] = await Promise.all([
      marketDataApi.getMultipleMarketData(symbols),
      tradingServiceApi.getPortfolio().catch(() => null),
      tradingServiceApi.getPerformanceMetrics().catch(() => null),
    ]);

    return {
      marketData,
      portfolio,
      performance,
    };
  } catch (error) {
    console.error('Error fetching dashboard data:', error);
    throw error;
  }
};

/**
 * Check health of all services
 */
export const checkAllServicesHealth = async () => {
  const results = await Promise.allSettled([
    marketDataApi.healthCheck(),
    decisionEngineApi.healthCheck(),
    tradingServiceApi.healthCheck(),
  ]);

  return {
    marketData: results[0].status === 'fulfilled',
    decisionEngine: results[1].status === 'fulfilled',
    tradingService: results[2].status === 'fulfilled',
    allHealthy: results.every(r => r.status === 'fulfilled'),
  };
};

export default {
  marketDataApi,
  decisionEngineApi,
  tradingServiceApi,
  getDashboardData,
  checkAllServicesHealth,
};
