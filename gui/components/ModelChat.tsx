import React, { useState, useEffect, useCallback, useRef } from 'react';
import { MODELS_DATA } from '../constants';

interface Decision {
  id: string;
  timestamp: string;
  action: 'buy' | 'sell' | 'hold' | 'close';
  symbol: string;
  quantity: number;
  reasoning: string;
  confidence: number;
  agent_id?: string;
}

interface AgentDecisionsResponse {
  agent_id: string;
  decisions: Decision[];
  count: number;
}

const formatDate = (dateString: string) => {
  // Handle timestamp without timezone by appending 'Z' for UTC
  const normalizedDateString = dateString.includes('Z') || dateString.includes('+')
    ? dateString
    : dateString + 'Z';

  const date = new Date(normalizedDateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;

  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const getActionColor = (action: string) => {
  switch (action.toLowerCase()) {
    case 'buy':
      return 'text-green-400';
    case 'sell':
    case 'close':
      return 'text-red-400';
    case 'hold':
      return 'text-yellow-400';
    default:
      return 'text-arena-gray-400';
  }
};

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return 'text-green-400';
  if (confidence >= 0.5) return 'text-yellow-400';
  return 'text-red-400';
};

export const ModelChat: React.FC = () => {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchAllDecisions = useCallback(async () => {
    try {
      // Fetch decisions from all agents
      const agents = MODELS_DATA.filter(m => m.id !== 'btcHold').map(m => m.id);
      const responses = await Promise.all(
        agents.map(agentId =>
          fetch(`http://localhost:8002/api/agents/${agentId}/decisions?limit=50`)
            .then(res => res.ok ? res.json() : null)
            .catch(() => null)
        )
      );

      // Merge all decisions and add agent_id to each decision
      const allDecisions: (Decision & { agent_id?: string })[] = [];
      responses.forEach((data, index) => {
        if (data && data.decisions) {
          data.decisions.forEach((decision: Decision) => {
            allDecisions.push({
              ...decision,
              agent_id: agents[index]
            });
          });
        }
      });

      // Sort by timestamp (most recent first) and limit to 50
      allDecisions.sort((a, b) => {
        const dateA = new Date(a.timestamp).getTime();
        const dateB = new Date(b.timestamp).getTime();
        return dateB - dateA;
      });

      setDecisions(allDecisions.slice(0, 50));
      setError(null);
    } catch (err) {
      console.error('Error fetching decisions:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch decisions');
      setDecisions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    fetchAllDecisions();

    // Auto-refresh every 10 seconds
    intervalRef.current = setInterval(() => {
      fetchAllDecisions();
    }, 10000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchAllDecisions]);

  const hasLiveData = !loading && !error && decisions.length > 0;

  return (
    <div className="bg-gray-900 bg-opacity-40 backdrop-blur-sm text-arena-gray-200 text-sm font-sans py-3 sm:py-4">
      {/* Header */}
      <div className="px-3 sm:px-4 mb-3 sm:mb-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
        <div className="flex items-center space-x-3">
          <h3 className="text-arena-gray-400 font-bold text-[10px] sm:text-xs">ALL AGENTS - DECISION HISTORY</h3>
        </div>
        <div className="flex items-center space-x-2">
          {loading ? (
            <span className="text-[10px] sm:text-xs text-yellow-400 flex items-center">
              <div className="w-2 h-2 bg-yellow-400 rounded-full mr-2 animate-pulse" />
              Loading...
            </span>
          ) : hasLiveData ? (
            <span className="text-[10px] sm:text-xs text-green-400 flex items-center">
              <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse" />
              Live Data
            </span>
          ) : (
            <span className="text-[10px] sm:text-xs text-red-400 flex items-center">
              <div className="w-2 h-2 bg-red-400 rounded-full mr-2" />
              No Data
            </span>
          )}
        </div>
      </div>

      {/* Decisions Display */}
      {hasLiveData ? (
        <div className="px-3 sm:px-4">
          <h4 className="font-bold text-sm sm:text-base mb-2 sm:mb-3 text-white">
            LATEST 50 DECISIONS ({decisions.length})
          </h4>

          <div className="space-y-2 sm:space-y-3 max-h-[40vh] overflow-y-auto">
            {decisions.map((decision, index) => {
              const decisionWithAgent = decision as Decision & { agent_id?: string };
              const agentModel = MODELS_DATA.find(m => m.id === decisionWithAgent.agent_id);
              const AgentIcon = agentModel?.icon;

              return (
                <div
                  key={decision.id || index}
                  className="border border-arena-gray-800 rounded p-2 sm:p-3 hover:border-gray-700 transition-colors bg-gray-900 bg-opacity-40"
                >
                  {/* Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-2 gap-2">
                    <div className="flex items-center flex-wrap gap-x-1.5 sm:gap-x-2 gap-y-1">
                      {/* Agent Info - Icon only on mobile */}
                      {agentModel && AgentIcon && (
                        <div className="flex items-center space-x-1">
                          <AgentIcon style={{ color: agentModel.color }} size={14} title={agentModel.name} />
                          <span className="hidden sm:inline text-xs font-semibold" style={{ color: agentModel.color }}>
                            {agentModel.name}
                          </span>
                        </div>
                      )}
                      <span className="text-arena-gray-600 hidden sm:inline">•</span>
                      <span className={`font-bold uppercase text-[10px] sm:text-xs ${getActionColor(decision.action)}`}>
                        {decision.action}
                      </span>
                      {decision.symbol && (
                        <span className="font-bold text-[10px] sm:text-xs text-white">{decision.symbol}</span>
                      )}
                      {decision.quantity > 0 && (
                        <span className="hidden sm:inline text-xs text-arena-gray-400">
                          Qty: {decision.quantity.toFixed(4)}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                      <span className={`text-[10px] sm:text-xs font-bold ${getConfidenceColor(decision.confidence)}`}>
                        {(decision.confidence * 100).toFixed(0)}%
                      </span>
                      <span className="text-[10px] sm:text-xs text-arena-gray-500">
                        {formatDate(decision.timestamp)}
                      </span>
                    </div>
                  </div>

                  {/* Reasoning - Hidden on mobile */}
                  {decision.reasoning && (
                    <div className="hidden sm:block text-xs text-arena-gray-300 leading-relaxed mt-2 p-2 bg-gray-900 bg-opacity-60 rounded">
                      <span className="text-arena-gray-500 font-bold">REASONING: </span>
                      {decision.reasoning}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ) : loading ? (
        <div className="px-3 sm:px-4 py-6 sm:py-8 text-center text-arena-gray-500">
          <div className="animate-spin w-6 sm:w-8 h-6 sm:h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2 sm:mb-3" />
          <p className="text-xs sm:text-sm">Loading decisions from all agents...</p>
        </div>
      ) : (
        <div className="px-3 sm:px-4 py-6 sm:py-8 text-center text-arena-gray-500">
          <p className="text-xs sm:text-sm">{error ? `Error: ${error}` : 'No decisions from any agents yet'}</p>
          <p className="text-[10px] sm:text-xs mt-2">AI agents will make decisions automatically</p>
        </div>
      )}
    </div>
  );
};
