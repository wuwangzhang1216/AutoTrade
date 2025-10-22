import React from 'react';
import { MODELS_DATA } from '../constants';
import type { AgentLeaderboardEntry } from '../services/api';

interface ModelComparisonChartProps {
  leaderboard: AgentLeaderboardEntry[];
}

export const ModelComparisonChart: React.FC<ModelComparisonChartProps> = ({ leaderboard }) => {
  // Create a lookup map for model metadata
  const modelMap = React.useMemo(() => {
    const map = new Map();
    MODELS_DATA.forEach(model => {
      map.set(model.id, model);
    });
    return map;
  }, []);

  // Sort by total value and get max for scaling
  const sortedData = React.useMemo(() => {
    return [...leaderboard].sort((a, b) => b.total_value - a.total_value);
  }, [leaderboard]);

  const maxValue = sortedData.length > 0 ? sortedData[0].total_value : 10000;

  const formatCurrency = (value: number) => {
    return `$${value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
  };

  const getShortName = (fullName: string) => {
    // Shorten names for display
    if (fullName.includes('DEEPSEEK')) return 'DEEPSEEK CHA...';
    if (fullName.includes('CLAUDE')) return 'CLAUDE SONNE...';
    if (fullName.includes('GROK')) return 'GROK 4';
    if (fullName.includes('QWEN')) return 'QWEN3 MAX';
    if (fullName.includes('GPT')) return 'GPT 5';
    if (fullName.includes('GEMINI')) return 'GEMINI 2.5 P...';
    return fullName;
  };

  return (
    <div className="border border-arena-gray-700 rounded-lg bg-gradient-to-br from-gray-900 to-black p-6">
      <h3 className="text-sm font-bold text-arena-gray-400 mb-6 uppercase tracking-wider">
        Performance Comparison
      </h3>
      <div className="flex items-end justify-between h-72 gap-4">
        {sortedData.map((entry, index) => {
          const model = modelMap.get(entry.agent_id);
          const Icon = model?.icon;
          // Ensure minimum height of 20% even for small values
          const heightPercent = Math.max((entry.total_value / maxValue) * 100, 20);
          const isTop = index === 0;

          return (
            <div key={entry.agent_id} className="flex-1 flex flex-col items-center justify-end h-full group">
              {/* Value label with background */}
              <div className={`text-xs font-bold mb-3 px-2 py-1 rounded ${
                isTop
                  ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                  : 'bg-gray-800/50 text-arena-gray-300 border border-arena-gray-700'
              }`}>
                {formatCurrency(entry.total_value)}
              </div>

              {/* Bar container with perspective effect */}
              <div
                className="w-full flex flex-col items-center justify-end relative transition-all duration-300 group-hover:scale-105"
                style={{ height: `${heightPercent}%` }}
              >
                {/* Glow effect for top performer */}
                {isTop && (
                  <div
                    className="absolute inset-0 blur-xl opacity-50"
                    style={{
                      backgroundColor: model?.color || '#6b7280',
                    }}
                  />
                )}

                {/* Main bar with gradient and shadow */}
                <div
                  className="w-full flex items-center justify-center rounded-t-lg relative overflow-hidden shadow-lg transition-all duration-300 group-hover:shadow-2xl"
                  style={{
                    background: `linear-gradient(180deg, ${model?.color || '#6b7280'} 0%, ${model?.color || '#6b7280'}CC 100%)`,
                    height: '100%',
                    boxShadow: `0 -4px 20px ${model?.color || '#6b7280'}40`,
                  }}
                >
                  {/* Shine effect overlay */}
                  <div
                    className="absolute inset-0 opacity-20 transition-opacity duration-300 group-hover:opacity-40"
                    style={{
                      background: 'linear-gradient(180deg, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0) 50%, rgba(0,0,0,0.2) 100%)',
                    }}
                  />

                  {/* Icon with drop shadow */}
                  {Icon && (
                    <div className="relative z-10 drop-shadow-lg">
                      <Icon
                        style={{ color: 'white' }}
                        size={28}
                      />
                    </div>
                  )}

                  {/* Top highlight line */}
                  <div
                    className="absolute top-0 left-0 right-0 h-1 opacity-60"
                    style={{
                      background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent)',
                    }}
                  />
                </div>

                {/* Rank badge for top 3 */}
                {index < 3 && (
                  <div className={`absolute -top-8 -right-2 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shadow-lg ${
                    index === 0 ? 'bg-yellow-500 text-black' :
                    index === 1 ? 'bg-gray-400 text-black' :
                    'bg-orange-600 text-white'
                  }`}>
                    {index + 1}
                  </div>
                )}
              </div>

              {/* Model name with icon */}
              <div className="mt-3 text-center">
                <div className="text-xs font-bold text-arena-gray-400 group-hover:text-arena-gray-200 transition-colors">
                  {getShortName(model?.name || entry.agent_id)}
                </div>
                {/* Progress indicator */}
                <div className="mt-1 h-0.5 w-full bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className="h-full transition-all duration-500"
                    style={{
                      width: `${heightPercent}%`,
                      backgroundColor: model?.color || '#6b7280',
                    }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-6 pt-4 border-t border-arena-gray-800">
        <div className="flex items-center justify-center gap-4 text-xs text-arena-gray-400">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-500" />
            <span>1st Place</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gray-400" />
            <span>2nd Place</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-orange-600" />
            <span>3rd Place</span>
          </div>
        </div>
      </div>
    </div>
  );
};
