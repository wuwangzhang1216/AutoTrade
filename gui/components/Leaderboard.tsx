import React, { useState } from 'react';
import { useLeaderboard, useAggregateStats, useAllPositions } from '../hooks/useApi';
import { LeaderboardTable } from './LeaderboardTable';
import { WinningModelCard } from './WinningModelCard';
import { ModelComparisonChart } from './ModelComparisonChart';

type TabType = 'overall' | 'analytics';

interface LeaderboardProps {
  onAgentSelect?: (agentId: string) => void;
}

export const Leaderboard: React.FC<LeaderboardProps> = ({ onAgentSelect }) => {
  const [activeTab, setActiveTab] = useState<TabType>('overall');
  const { data: leaderboard, loading: leaderboardLoading, error: leaderboardError } = useLeaderboard(10000);
  const { data: aggregateStats } = useAggregateStats(10000);
  const { data: positions } = useAllPositions(10000);

  const winner = leaderboard && leaderboard.length > 0 ? leaderboard[0] : null;

  // Filter positions for the winning model
  const winnerPositions = React.useMemo(() => {
    if (!winner || !positions) return [];
    return positions.filter((pos: any) => pos.agent_id === winner.agent_id);
  }, [winner, positions]);

  return (
    <div className="text-arena-gray-100 overflow-x-hidden">
      {/* Header */}
      <div className="mb-2 sm:mb-4 md:mb-6">
        <h1 className="text-lg sm:text-2xl md:text-3xl lg:text-4xl font-bold text-white truncate">LEADERBOARD</h1>
      </div>

      {/* Tabs */}
      <div className="mb-2 sm:mb-4 md:mb-6 flex bg-gray-900 bg-opacity-40 backdrop-blur-sm border border-arena-gray-700 rounded-md p-0.5 w-full sm:w-fit">
        <button
          onClick={() => setActiveTab('overall')}
          className={`flex-1 sm:flex-none px-2 sm:px-4 md:px-6 py-1.5 sm:py-2 text-[9px] sm:text-xs font-bold rounded min-h-[36px] sm:min-h-0 ${
            activeTab === 'overall'
              ? 'bg-arena-gray-100 text-arena-black'
              : 'text-arena-gray-400 hover:bg-arena-gray-800'
          }`}
        >
          <span className="sm:hidden">STATS</span>
          <span className="hidden sm:inline">OVERALL STATS</span>
        </button>
        <button
          onClick={() => setActiveTab('analytics')}
          className={`flex-1 sm:flex-none px-2 sm:px-4 md:px-6 py-1.5 sm:py-2 text-[9px] sm:text-xs font-bold rounded min-h-[36px] sm:min-h-0 ${
            activeTab === 'analytics'
              ? 'bg-arena-gray-100 text-arena-black'
              : 'text-arena-gray-400 hover:bg-arena-gray-800'
          }`}
        >
          <span className="sm:hidden">ANALYTICS</span>
          <span className="hidden sm:inline">ADVANCED ANALYTICS</span>
        </button>
      </div>

      {/* Content */}
      {leaderboardLoading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <p className="mt-4 text-arena-gray-400">Loading leaderboard...</p>
        </div>
      )}

      {leaderboardError && (
        <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-6 text-center">
          <p className="text-red-400 font-semibold">Error loading leaderboard</p>
          <p className="text-sm text-arena-gray-400 mt-2">{leaderboardError}</p>
        </div>
      )}

      {!leaderboardLoading && !leaderboardError && leaderboard && (
        <div className="space-y-2 sm:space-y-4 md:space-y-6 overflow-x-hidden">
          {/* Leaderboard Table */}
          <div className="overflow-x-auto">
            <LeaderboardTable leaderboard={leaderboard} viewType={activeTab} onAgentSelect={onAgentSelect} />
          </div>

          {/* Bottom Section: Winning Model Card + Chart */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-2 sm:gap-4 md:gap-6">
            {/* Winning Model Card */}
            {winner && (
              <div className="lg:col-span-1">
                <WinningModelCard winner={winner} positions={winnerPositions} />
              </div>
            )}

            {/* Model Comparison Chart */}
            <div className="lg:col-span-2 overflow-hidden">
              <ModelComparisonChart leaderboard={leaderboard} />
            </div>
          </div>

          {/* Footer Note */}
          <div className="mt-2 sm:mt-4 p-1.5 sm:p-3 md:p-4 bg-gray-900 bg-opacity-40 backdrop-blur-sm border border-arena-gray-700 rounded-lg">
            <p className="text-[8px] sm:text-xs md:text-sm text-arena-gray-400 leading-relaxed">
              <span className="font-bold text-arena-gray-300">Note:</span>
              {' '}
              <span className="hidden sm:inline">
                All statistics (except{' '}
                <span className="font-semibold text-arena-gray-300">Account Value</span> and{' '}
                <span className="font-semibold text-arena-gray-300">P&L</span>) reflect{' '}
                <span className="font-semibold text-arena-gray-300">completed trades only</span>. Active positions are not included in calculations until they are closed.
              </span>
              <span className="sm:hidden">
                Stats show <span className="font-semibold text-arena-gray-300">completed trades</span> only. Active positions excluded.
              </span>
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
