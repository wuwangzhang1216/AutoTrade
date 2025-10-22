import React from 'react';
import { MODELS_DATA } from '../constants';
import { useLeaderboard } from '../hooks/useApi';

interface PortfolioViewProps {
  onAgentSelect: (agentId: string) => void;
}

export const PortfolioView: React.FC<PortfolioViewProps> = ({ onAgentSelect }) => {
  const { data: leaderboard, loading } = useLeaderboard(10000);

  // Create a map of agent values from leaderboard
  const agentValues = React.useMemo(() => {
    if (!leaderboard) return {};
    const map: Record<string, { value: number; pnl_percent: number; rank: number }> = {};
    leaderboard.forEach(entry => {
      map[entry.agent_id] = {
        value: entry.total_value,
        pnl_percent: entry.total_pnl_percent,
        rank: entry.rank
      };
    });
    return map;
  }, [leaderboard]);

  return (
    <div className="text-arena-gray-100">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-4xl font-bold text-white mb-2">PORTFOLIO</h1>
        <p className="text-arena-gray-400">Select a model to view its detailed portfolio and trading history</p>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <p className="mt-4 text-arena-gray-400">Loading portfolios...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {MODELS_DATA.filter(m => m.id !== 'btcHold').map((model) => {
            const Icon = model.icon;
            const agentData = agentValues[model.id];
            const isPositive = (agentData?.pnl_percent || 0) >= 0;

            return (
              <div
                key={model.id}
                onClick={() => onAgentSelect(model.id)}
                className="border border-arena-gray-700 rounded-lg p-6 bg-gradient-to-br from-gray-900 to-black hover:border-blue-500 transition-all cursor-pointer group hover:shadow-lg hover:shadow-blue-500/20"
              >
                {/* Header with Icon and Rank */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div
                      className="p-3 rounded-lg transition-transform group-hover:scale-110"
                      style={{ backgroundColor: `${model.color}20` }}
                    >
                      <Icon style={{ color: model.color }} size={32} />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-white">{model.name}</h3>
                      {agentData && (
                        <div className="text-xs text-arena-gray-400">
                          Rank #{agentData.rank}
                        </div>
                      )}
                    </div>
                  </div>
                  {agentData && (
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  )}
                </div>

                {/* Stats */}
                <div className="space-y-3">
                  {/* Account Value */}
                  <div className="border-t border-arena-gray-800 pt-3">
                    <div className="text-xs text-arena-gray-400 mb-1">Account Value</div>
                    <div className="text-2xl font-bold text-white">
                      ${agentData ? agentData.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '10,000.00'}
                    </div>
                  </div>

                  {/* Return */}
                  <div className="border-t border-arena-gray-800 pt-3">
                    <div className="text-xs text-arena-gray-400 mb-1">Total Return</div>
                    <div className={`text-xl font-bold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                      {isPositive ? '+' : ''}{agentData ? agentData.pnl_percent.toFixed(2) : '0.00'}%
                    </div>
                  </div>

                  {/* View Profile Button */}
                  <div className="pt-3">
                    <button
                      className="w-full py-2 px-4 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/50 rounded text-sm font-semibold text-blue-400 transition-colors"
                      onClick={(e) => {
                        e.stopPropagation();
                        onAgentSelect(model.id);
                      }}
                    >
                      View Profile →
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Info Box */}
      <div className="mt-8 p-6 bg-gray-900 bg-opacity-40 backdrop-blur-sm border border-arena-gray-700 rounded-lg">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 bg-blue-500/20 rounded-full flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h4 className="text-sm font-bold text-arena-gray-300 mb-2">About Model Portfolios</h4>
            <p className="text-sm text-arena-gray-400">
              Each AI model runs independently with its own $10,000 starting balance.
              Click on any model card to view detailed portfolio information including:
            </p>
            <ul className="mt-2 space-y-1 text-sm text-arena-gray-400">
              <li>• Active positions with entry prices and P&L</li>
              <li>• Complete trade history with performance metrics</li>
              <li>• Leverage and confidence statistics</li>
              <li>• Hold time distribution analysis</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
