import React from 'react';
import { MODELS_DATA } from '../constants';
import type { AgentLeaderboardEntry } from '../services/api';

interface LeaderboardTableProps {
  leaderboard: AgentLeaderboardEntry[];
  viewType: 'overall' | 'analytics';
  onAgentSelect?: (agentId: string) => void;
}

export const LeaderboardTable: React.FC<LeaderboardTableProps> = ({ leaderboard, viewType, onAgentSelect }) => {
  // Create a lookup map for model metadata
  const modelMap = React.useMemo(() => {
    const map = new Map();
    MODELS_DATA.forEach(model => {
      map.set(model.id, model);
    });
    return map;
  }, []);

  const formatCurrency = (value: number) => {
    return `$${value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
  };

  const formatPercent = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const formatNumber = (value: number) => {
    return value.toLocaleString('en-US');
  };

  // Get trade stats from leaderboard entry if available
  const getTradeStats = (entry: AgentLeaderboardEntry) => {
    return {
      avgTradeSize: entry.avg_trade_size || 0,
      medianTradeSize: entry.median_trade_size || 0,
      avgHold: entry.avg_hold_time || 'N/A',
      medianHold: entry.median_hold_time || 'N/A',
      percentLong: entry.percent_long || 0,
      expectancy: entry.expectancy || 0,
      avgConfidence: entry.avg_confidence || 0,
      medianConfidence: entry.median_confidence || 0,
    };
  };

  return (
    <div className="w-full overflow-x-auto border border-arena-gray-700 rounded-lg bg-gray-900 bg-opacity-40 backdrop-blur-sm -mx-3 sm:mx-0">
      <div className="min-w-[900px] lg:min-w-0">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-arena-gray-700">
              {viewType === 'overall' ? (
                <>
                  <th className="px-2 py-3 text-left text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">RANK</th>
                  <th className="px-2 py-3 text-left text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">MODEL</th>
                  <th className="px-2 py-3 text-right text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">ACCT VALUE ↓</th>
                  <th className="px-2 py-3 text-right text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">RETURN %</th>
                  <th className="px-2 py-3 text-right text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">TOTAL P&L</th>
                  <th className="px-2 py-3 text-right text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">FEES</th>
                  <th className="px-2 py-3 text-right text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">WIN RATE</th>
                  <th className="px-2 py-3 text-right text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">BIGGEST WIN</th>
                  <th className="px-2 py-3 text-right text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">BIGGEST LOSS</th>
                  <th className="px-2 py-3 text-right text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">SHARPE</th>
                  <th className="px-2 py-3 text-right text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider">TRADES</th>
                </>
              ) : (
                <>
                  <th className="px-2 py-3 text-left text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">RANK</th>
                  <th className="px-2 py-3 text-left text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">MODEL</th>
                  <th className="px-2 py-3 text-right text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">ACCT VALUE ↓</th>
                  <th className="px-2 py-3 text-right text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">AVG TRADE SIZE</th>
                  <th className="px-2 py-3 text-right text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">MEDIAN TRADE SIZE</th>
                  <th className="px-2 py-3 text-right text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">AVG HOLD</th>
                  <th className="px-2 py-3 text-right text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">MEDIAN HOLD</th>
                  <th className="px-2 py-3 text-right text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">% LONG</th>
                  <th className="px-2 py-3 text-right text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">EXPECTANCY</th>
                  <th className="px-2 py-3 text-right text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider border-r border-arena-gray-800">AVG CONFIDENCE</th>
                  <th className="px-2 py-3 text-right text-[10px] sm:text-xs font-bold text-arena-gray-400 uppercase tracking-wider">MEDIAN CONFIDENCE</th>
                </>
              )}
            </tr>
          </thead>
        <tbody>
          {leaderboard.map((entry, index) => {
            const model = modelMap.get(entry.agent_id);
            const Icon = model?.icon;
            const isPositive = entry.total_pnl_percent >= 0;
            const stats = getTradeStats(entry);
            const sharpe = entry.total_pnl_percent / 100;

            return (
              <tr
                key={entry.agent_id}
                className="border-b border-arena-gray-800 hover:bg-arena-gray-800/50 transition-colors cursor-pointer"
                onClick={() => onAgentSelect?.(entry.agent_id)}
              >
                {viewType === 'overall' ? (
                  <>
                    {/* Rank */}
                    <td className="px-2 py-3 text-center border-r border-arena-gray-800">
                      <div className="text-sm font-bold text-white">{entry.rank}</div>
                    </td>

                    {/* Model */}
                    <td className="px-2 py-3 border-r border-arena-gray-800">
                      <div className="flex items-center space-x-2">
                        {Icon && (
                          <Icon
                            style={{ color: model?.color }}
                            size={16}
                          />
                        )}
                        <span className="text-xs font-bold text-arena-gray-100">
                          {model?.name || entry.agent_id}
                        </span>
                      </div>
                    </td>

                    {/* Account Value */}
                    <td className="px-2 py-3 text-right border-r border-arena-gray-800">
                      <div className="text-sm font-bold text-white">
                        {formatCurrency(entry.total_value)}
                      </div>
                    </td>

                    {/* Return % */}
                    <td className="px-2 py-3 text-right border-r border-arena-gray-800">
                      <div className={`text-sm font-bold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                        {formatPercent(entry.total_pnl_percent)}
                      </div>
                    </td>

                    {/* Total P&L */}
                    <td className="px-2 py-3 text-right border-r border-arena-gray-800">
                      <div className={`text-sm font-bold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                        {formatCurrency(entry.total_pnl)}
                      </div>
                    </td>

                    {/* Fees */}
                    <td className="px-2 py-3 text-right border-r border-arena-gray-800">
                      <div className="text-sm text-arena-gray-300">
                        {formatCurrency(entry.cash_balance * 0.01)}
                      </div>
                    </td>

                    {/* Win Rate - would need to fetch from performance API */}
                    <td className="px-2 py-3 text-right border-r border-arena-gray-800">
                      <div className="text-sm text-arena-gray-300">
                        {entry.trades_count > 0 ? '0%' : '0%'}
                      </div>
                    </td>

                    {/* Biggest Win - would need to fetch from trade history */}
                    <td className="px-2 py-3 text-right border-r border-arena-gray-800">
                      <div className="text-sm text-green-400">
                        $0
                      </div>
                    </td>

                    {/* Biggest Loss - would need to fetch from trade history */}
                    <td className="px-2 py-3 text-right border-r border-arena-gray-800">
                      <div className="text-sm text-red-400">
                        $0
                      </div>
                    </td>

                    {/* Sharpe */}
                    <td className="px-2 py-3 text-right border-r border-arena-gray-800">
                      <div className="text-sm text-arena-gray-300">
                        {sharpe.toFixed(3)}
                      </div>
                    </td>

                    {/* Trades */}
                    <td className="px-2 py-3 text-right">
                      <div className="text-sm text-arena-gray-300">
                        {formatNumber(entry.trades_count)}
                      </div>
                    </td>
                  </>
                ) : (
                  <>
                    {/* Rank */}
                    <td className="px-2 py-3 text-center border-r border-arena-gray-800">
                      <div className="text-sm font-bold text-white">{entry.rank}</div>
                    </td>

                    {/* Model */}
                    <td className="px-2 py-3 border-r border-arena-gray-800">
                      <div className="flex items-center space-x-2">
                        {Icon && (
                          <Icon
                            style={{ color: model?.color }}
                            size={16}
                          />
                        )}
                        <span className="text-xs font-bold text-arena-gray-100">
                          {model?.name || entry.agent_id}
                        </span>
                      </div>
                    </td>

                    {/* Account Value */}
                    <td className="px-2 py-3 text-right border-r border-arena-gray-800">
                      <div className="text-sm font-bold text-white">
                        {formatCurrency(entry.total_value)}
                      </div>
                    </td>

                    {/* Avg Trade Size */}
                    <td className="px-2 py-3 text-right border-r border-arena-gray-800">
                      <div className="text-sm text-arena-gray-300">
                        {formatCurrency(stats.avgTradeSize)}
                      </div>
                    </td>

                    {/* Median Trade Size */}
                    <td className="px-2 py-3 text-right border-r border-arena-gray-800">
                      <div className="text-sm text-arena-gray-300">
                        {formatCurrency(stats.medianTradeSize)}
                      </div>
                    </td>

                    {/* Avg Hold */}
                    <td className="px-2 py-3 text-right border-r border-arena-gray-800">
                      <div className="text-sm text-arena-gray-300">{stats.avgHold}</div>
                    </td>

                    {/* Median Hold */}
                    <td className="px-2 py-3 text-right border-r border-arena-gray-800">
                      <div className="text-sm text-arena-gray-300">{stats.medianHold}</div>
                    </td>

                    {/* % Long */}
                    <td className="px-2 py-3 text-right border-r border-arena-gray-800">
                      <div className="text-sm text-arena-gray-300">{stats.percentLong.toFixed(2)}%</div>
                    </td>

                    {/* Expectancy */}
                    <td className="px-2 py-3 text-right border-r border-arena-gray-800">
                      <div className={`text-sm ${stats.expectancy >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {formatCurrency(stats.expectancy)}
                      </div>
                    </td>

                    {/* Avg Confidence */}
                    <td className="px-2 py-3 text-right border-r border-arena-gray-800">
                      <div className="text-sm text-arena-gray-300">{stats.avgConfidence.toFixed(1)}%</div>
                    </td>

                    {/* Median Confidence */}
                    <td className="px-2 py-3 text-right">
                      <div className="text-sm text-arena-gray-300">{stats.medianConfidence.toFixed(1)}%</div>
                    </td>
                  </>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
      </div>
    </div>
  );
};
