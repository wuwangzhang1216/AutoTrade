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
    <div className="text-arena-gray-100">
      {/* Header */}
      <div className="mb-4 sm:mb-6">
        <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white">LEADERBOARD</h1>
      </div>

      {/* Tabs */}
      <div className="mb-4 sm:mb-6 flex bg-gray-900 bg-opacity-40 backdrop-blur-sm border border-arena-gray-700 rounded-md p-0.5 w-full sm:w-fit">
        <button
          onClick={() => setActiveTab('overall')}
          className={`flex-1 sm:flex-none px-3 sm:px-6 py-2 text-[10px] sm:text-xs font-bold rounded ${
            activeTab === 'overall'
              ? 'bg-arena-gray-100 text-arena-black'
              : 'text-arena-gray-400 hover:bg-arena-gray-800'
          }`}
        >
          OVERALL STATS
        </button>
        <button
          onClick={() => setActiveTab('analytics')}
          className={`flex-1 sm:flex-none px-3 sm:px-6 py-2 text-[10px] sm:text-xs font-bold rounded ${
            activeTab === 'analytics'
              ? 'bg-arena-gray-100 text-arena-black'
              : 'text-arena-gray-400 hover:bg-arena-gray-800'
          }`}
        >
          ADVANCED ANALYTICS
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
        <div className="space-y-6">
          {/* Leaderboard Table */}
          <div>
            <LeaderboardTable leaderboard={leaderboard} viewType={activeTab} onAgentSelect={onAgentSelect} />
          </div>

          {/* Bottom Section: Winning Model Card + Chart */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Winning Model Card */}
            {winner && (
              <div className="lg:col-span-1">
                <WinningModelCard winner={winner} positions={winnerPositions} />
              </div>
            )}

            {/* Model Comparison Chart */}
            <div className="lg:col-span-2">
              <ModelComparisonChart leaderboard={leaderboard} />
            </div>
          </div>

          {/* Footer Note */}
          <div className="mt-4 p-4 bg-gray-900 bg-opacity-40 backdrop-blur-sm border border-arena-gray-700 rounded-lg">
            <p className="text-sm text-arena-gray-400">
              <span className="font-bold text-arena-gray-300">Note:</span> All statistics (except{' '}
              <span className="font-semibold text-arena-gray-300">Account Value</span> and{' '}
              <span className="font-semibold text-arena-gray-300">P&L</span>) reflect{' '}
              <span className="font-semibold text-arena-gray-300">completed trades only</span>. Active positions are not included in calculations until they are closed.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
