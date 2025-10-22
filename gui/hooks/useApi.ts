import { useState, useEffect, useCallback, useRef } from 'react';
import {
  marketDataApi,
  decisionEngineApi,
  tradingServiceApi,
  getDashboardData,
  checkAllServicesHealth,
  type MarketDataResponse,
  type Portfolio,
  type PerformanceMetrics,
  type Position,
  type Order,
  type TradingSignal,
  type AgentLeaderboardEntry,
  type AggregateStats,
  ApiError,
} from '../services/api';

// Generic hook for API calls with loading and error states
export function useApiCall<T>(
  apiFunction: () => Promise<T>,
  dependencies: any[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiFunction();
      setData(result);
    } catch (err) {
      const errorMessage = err instanceof ApiError
        ? `${err.service || 'API'} Error: ${err.message}`
        : 'An unexpected error occurred';
      setError(errorMessage);
      console.error('API call failed:', err);
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// Hook for market data with auto-refresh
export function useMarketData(symbols: string[], refreshInterval: number = 30000) {
  const [data, setData] = useState<MarketDataResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const results = await marketDataApi.getMultipleMarketData(symbols);
      setData(results);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof ApiError
        ? err.message
        : 'Failed to fetch market data';
      setError(errorMessage);
      console.error('Market data fetch failed:', err);
    } finally {
      setLoading(false);
    }
  }, [symbols.join(',')]);

  useEffect(() => {
    fetchData();

    // Set up auto-refresh
    if (refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, refreshInterval]);

  return { data, loading, error, refetch: fetchData };
}

// Hook for portfolio data
export function usePortfolio(refreshInterval: number = 10000) {
  const [data, setData] = useState<Portfolio | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const result = await tradingServiceApi.getPortfolio();
      setData(result);
      setError(null);
      // Only set loading to false on first load
      if (loading) {
        setLoading(false);
      }
    } catch (err) {
      const errorMessage = err instanceof ApiError
        ? err.message
        : 'Failed to fetch portfolio';
      setError(errorMessage);
      console.error('Portfolio fetch failed:', err);
      if (loading) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    fetchData();

    // Set up auto-refresh
    if (refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, refreshInterval]);

  return { data, loading, error, refetch: fetchData };
}

// Hook for positions
export function usePositions(refreshInterval: number = 10000) {
  const [data, setData] = useState<Position[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const result = await tradingServiceApi.getPositions();
      setData(result);
      setError(null);
      if (loading) {
        setLoading(false);
      }
    } catch (err) {
      const errorMessage = err instanceof ApiError
        ? err.message
        : 'Failed to fetch positions';
      setError(errorMessage);
      console.error('Positions fetch failed:', err);
      if (loading) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    fetchData();

    if (refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, refreshInterval]);

  return { data, loading, error, refetch: fetchData };
}

// Hook for performance metrics
export function usePerformanceMetrics(refreshInterval: number = 30000) {
  const [data, setData] = useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const result = await tradingServiceApi.getPerformanceMetrics();
      setData(result);
      setError(null);
      if (loading) {
        setLoading(false);
      }
    } catch (err) {
      const errorMessage = err instanceof ApiError
        ? err.message
        : 'Failed to fetch performance metrics';
      setError(errorMessage);
      console.error('Performance metrics fetch failed:', err);
      if (loading) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    fetchData();

    if (refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, refreshInterval]);

  return { data, loading, error, refetch: fetchData };
}

// Hook for trade history with auto-refresh
export function useTradeHistory(limit: number = 50, refreshInterval: number = 10000) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const result = await tradingServiceApi.getTradeHistory(limit);
      setData(result);
      setError(null);
      if (loading) {
        setLoading(false);
      }
    } catch (err) {
      const errorMessage = err instanceof ApiError
        ? err.message
        : 'Failed to fetch trade history';
      setError(errorMessage);
      console.error('Trade history fetch failed:', err);
      if (loading) {
        setLoading(false);
      }
    }
  }, [limit]);

  useEffect(() => {
    fetchData();

    if (refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, refreshInterval]);

  return { data, loading, error, refetch: fetchData };
}

// Hook for trading signals
export function useTradingSignals(symbols: string[]) {
  return useApiCall(
    () => decisionEngineApi.getMultipleSignals(symbols),
    [symbols.join(',')]
  );
}

// Hook for service health check
export function useServicesHealth(checkInterval: number = 60000) {
  const [health, setHealth] = useState({
    marketData: false,
    decisionEngine: false,
    tradingService: false,
    allHealthy: false,
  });
  const [checking, setChecking] = useState<boolean>(true);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      const result = await checkAllServicesHealth();
      setHealth(result);
    } catch (err) {
      console.error('Health check failed:', err);
      setHealth({
        marketData: false,
        decisionEngine: false,
        tradingService: false,
        allHealthy: false,
      });
    } finally {
      if (checking) {
        setChecking(false);
      }
    }
  }, []);

  useEffect(() => {
    checkHealth();

    if (checkInterval > 0) {
      intervalRef.current = setInterval(checkHealth, checkInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [checkHealth, checkInterval]);

  return { health, checking, refetch: checkHealth };
}

// Hook for dashboard data (combines multiple sources)
export function useDashboardData(
  symbols: string[] = ['BTC', 'ETH', 'SOL'],
  refreshInterval: number = 30000
) {
  const [data, setData] = useState<{
    marketData: MarketDataResponse[];
    portfolio: Portfolio | null;
    performance: PerformanceMetrics | null;
  } | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const result = await getDashboardData(symbols);
      setData(result);
      setError(null);
      if (loading) {
        setLoading(false);
      }
    } catch (err) {
      const errorMessage = err instanceof Error
        ? err.message
        : 'Failed to fetch dashboard data';
      setError(errorMessage);
      console.error('Dashboard data fetch failed:', err);
      if (loading) {
        setLoading(false);
      }
    }
  }, [symbols.join(',')]);

  useEffect(() => {
    fetchData();

    if (refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, refreshInterval]);

  return { data, loading, error, refetch: fetchData };
}

// Hook for placing orders
export function usePlaceOrder() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [order, setOrder] = useState<Order | null>(null);

  const placeOrder = async (orderData: {
    symbol: string;
    side: 'buy' | 'sell';
    quantity: number;
    order_type: 'market' | 'limit';
    price?: number;
  }) => {
    setLoading(true);
    setError(null);
    try {
      const result = await tradingServiceApi.placeOrder(orderData);
      setOrder(result);
      return result;
    } catch (err) {
      const errorMessage = err instanceof ApiError
        ? err.message
        : 'Failed to place order';
      setError(errorMessage);
      console.error('Order placement failed:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { placeOrder, loading, error, order };
}

// Hook for agent leaderboard with auto-refresh
export function useLeaderboard(refreshInterval: number = 10000) {
  const [data, setData] = useState<AgentLeaderboardEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const result = await tradingServiceApi.getLeaderboard();
      setData(result);
      setError(null);
      if (loading) {
        setLoading(false);
      }
    } catch (err) {
      const errorMessage = err instanceof ApiError
        ? err.message
        : 'Failed to fetch leaderboard';
      setError(errorMessage);
      console.error('Leaderboard fetch failed:', err);
      if (loading) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    fetchData();

    if (refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, refreshInterval]);

  return { data, loading, error, refetch: fetchData };
}

// Hook for aggregate stats
export function useAggregateStats(refreshInterval: number = 10000) {
  const [data, setData] = useState<AggregateStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const result = await tradingServiceApi.getAggregateStats();
      setData(result);
      setError(null);
      if (loading) {
        setLoading(false);
      }
    } catch (err) {
      const errorMessage = err instanceof ApiError
        ? err.message
        : 'Failed to fetch aggregate stats';
      setError(errorMessage);
      console.error('Aggregate stats fetch failed:', err);
      if (loading) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    fetchData();

    if (refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, refreshInterval]);

  return { data, loading, error, refetch: fetchData };
}

// Hook for all positions across all agents
export function useAllPositions(refreshInterval: number = 10000) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const result = await tradingServiceApi.getAllPositions();
      setData(result);
      setError(null);
      if (loading) {
        setLoading(false);
      }
    } catch (err) {
      const errorMessage = err instanceof ApiError
        ? err.message
        : 'Failed to fetch all positions';
      setError(errorMessage);
      console.error('All positions fetch failed:', err);
      if (loading) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    fetchData();

    if (refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, refreshInterval]);

  return { data, loading, error, refetch: fetchData };
}

// Hook for all trades across all agents
export function useAllTrades(limit: number = 100, refreshInterval: number = 10000) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const result = await tradingServiceApi.getAllTrades(limit);
      setData(result);
      setError(null);
      if (loading) {
        setLoading(false);
      }
    } catch (err) {
      const errorMessage = err instanceof ApiError
        ? err.message
        : 'Failed to fetch all trades';
      setError(errorMessage);
      console.error('All trades fetch failed:', err);
      if (loading) {
        setLoading(false);
      }
    }
  }, [limit]);

  useEffect(() => {
    fetchData();

    if (refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, refreshInterval]);

  return { data, loading, error, refetch: fetchData };
}

// Hook for agent-specific portfolio
export function useAgentPortfolio(agentId: string, refreshInterval: number = 10000) {
  const [data, setData] = useState<Portfolio | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const result = await tradingServiceApi.getAgentPortfolio(agentId);
      setData(result);
      setError(null);
      if (loading) {
        setLoading(false);
      }
    } catch (err) {
      const errorMessage = err instanceof ApiError
        ? err.message
        : 'Failed to fetch agent portfolio';
      setError(errorMessage);
      console.error('Agent portfolio fetch failed:', err);
      if (loading) {
        setLoading(false);
      }
    }
  }, [agentId]);

  useEffect(() => {
    fetchData();

    if (refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, refreshInterval]);

  return { data, loading, error, refetch: fetchData };
}

// Hook for agent-specific trades
export function useAgentTrades(agentId: string, limit: number = 100, refreshInterval: number = 10000) {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const allTrades = await tradingServiceApi.getAllTrades(limit * 2); // Get more trades to ensure we have enough for filtering
      // Filter trades for this specific agent
      const agentTrades = allTrades.filter(trade => trade.agent_id === agentId).slice(0, limit);
      setData(agentTrades);
      setError(null);
      if (loading) {
        setLoading(false);
      }
    } catch (err) {
      const errorMessage = err instanceof ApiError
        ? err.message
        : 'Failed to fetch agent trades';
      setError(errorMessage);
      console.error('Agent trades fetch failed:', err);
      if (loading) {
        setLoading(false);
      }
    }
  }, [agentId, limit]);

  useEffect(() => {
    fetchData();

    if (refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, refreshInterval]);

  return { data, loading, error, refetch: fetchData };
}

