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

  const getShortName = (fullName: string, isMobile: boolean = false) => {
    // Mobile: Ultra short names, Desktop: Short names
    if (isMobile) {
      if (fullName.includes('DEEPSEEK')) return 'DEEP';
      if (fullName.includes('CLAUDE')) return 'CLAU';
      if (fullName.includes('GROK')) return 'GROK';
      if (fullName.includes('QWEN')) return 'QWEN';
      if (fullName.includes('GPT')) return 'GPT';
      if (fullName.includes('GEMINI')) return 'GEMI';
      return fullName.substring(0, 4).toUpperCase();
    }
    // Desktop short names
    if (fullName.includes('DEEPSEEK')) return 'DEEPSEEK';
    if (fullName.includes('CLAUDE')) return 'CLAUDE';
    if (fullName.includes('GROK')) return 'GROK 4';
    if (fullName.includes('QWEN')) return 'QWEN';
    if (fullName.includes('GPT')) return 'GPT 5';
    if (fullName.includes('GEMINI')) return 'GEMINI';
    return fullName;
  };

  return (
    <div className="-mx-2 sm:mx-0 border border-arena-gray-700 rounded-lg bg-gradient-to-br from-gray-900 to-black p-1.5 sm:p-4 md:p-6 overflow-hidden">
      <h3 className="text-[9px] sm:text-xs md:text-sm font-bold text-arena-gray-400 mb-1 sm:mb-4 md:mb-6 uppercase tracking-wider truncate">
        <span className="sm:hidden">COMPARISON</span>
        <span className="hidden sm:inline">Performance Comparison</span>
      </h3>
      <div className="flex items-end justify-between h-32 sm:h-56 md:h-72 gap-1 sm:gap-2 md:gap-4">
        {sortedData.map((entry, index) => {
          const model = modelMap.get(entry.agent_id);
          const Icon = model?.icon;
          // Ensure minimum height of 20% even for small values
          const heightPercent = Math.max((entry.total_value / maxValue) * 100, 20);
          const isTop = index === 0;

          return (
            <div key={entry.agent_id} className="flex-1 flex flex-col items-center justify-end h-full group min-w-0">
              {/* Value label with background */}
              <div className={`text-[8px] sm:text-[10px] md:text-xs font-bold mb-0.5 sm:mb-3 px-0.5 sm:px-2 py-0.5 sm:py-1 rounded whitespace-nowrap ${
                isTop
                  ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                  : 'bg-gray-800/50 text-arena-gray-300 border border-arena-gray-700'
              }`}>
                <span className="md:hidden">${(entry.total_value / 1000).toFixed(1)}k</span>
                <span className="hidden md:inline">{formatCurrency(entry.total_value)}</span>
              </div>

              {/* Bar container with perspective effect */}
              <div
                className="w-full flex flex-col items-center justify-end relative transition-all duration-300 group-hover:scale-105"
                style={{ height: `${heightPercent}%` }}
              >
                {/* Glow effect for top performer - hidden on mobile */}
                {isTop && (
                  <div
                    className="hidden sm:block absolute inset-0 blur-xl opacity-50"
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
                        size={16}
                        className="sm:w-6 sm:h-6 md:w-7 md:h-7"
                      />
                    </div>
                  )}

                  {/* Top highlight line */}
                  <div
                    className="absolute top-0 left-0 right-0 h-0.5 sm:h-1 opacity-60"
                    style={{
                      background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent)',
                    }}
                  />
                </div>

                {/* Rank badge for top 3 - hidden on mobile */}
                {index < 3 && (
                  <div className={`hidden sm:flex absolute -top-6 sm:-top-8 -right-1 sm:-right-2 w-5 h-5 sm:w-6 sm:h-6 rounded-full items-center justify-center text-[10px] sm:text-xs font-bold shadow-lg ${
                    index === 0 ? 'bg-yellow-500 text-black' :
                    index === 1 ? 'bg-gray-400 text-black' :
                    'bg-orange-600 text-white'
                  }`}>
                    {index + 1}
                  </div>
                )}
              </div>

              {/* Model name with icon */}
              <div className="mt-0.5 sm:mt-3 text-center w-full">
                <div className="text-[7px] sm:text-[10px] md:text-xs font-bold text-arena-gray-400 group-hover:text-arena-gray-200 transition-colors truncate px-0.5">
                  <span className="md:hidden">{getShortName(model?.name || entry.agent_id, true)}</span>
                  <span className="hidden md:inline">{getShortName(model?.name || entry.agent_id, false)}</span>
                </div>
                {/* Progress indicator - hidden on mobile */}
                <div className="hidden sm:block mt-1 h-0.5 w-full bg-gray-800 rounded-full overflow-hidden">
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

      {/* Legend - hidden on mobile */}
      <div className="hidden sm:block mt-3 sm:mt-4 md:mt-6 pt-2 sm:pt-3 md:pt-4 border-t border-arena-gray-800">
        <div className="flex items-center justify-center gap-2 sm:gap-3 md:gap-4 text-[9px] sm:text-[10px] md:text-xs text-arena-gray-400 flex-wrap">
          <div className="flex items-center gap-1 sm:gap-1.5">
            <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-yellow-500 flex-shrink-0" />
            <span className="whitespace-nowrap">1st</span>
          </div>
          <div className="flex items-center gap-1 sm:gap-1.5">
            <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-gray-400 flex-shrink-0" />
            <span className="whitespace-nowrap">2nd</span>
          </div>
          <div className="flex items-center gap-1 sm:gap-1.5">
            <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-orange-600 flex-shrink-0" />
            <span className="whitespace-nowrap">3rd</span>
          </div>
        </div>
      </div>
    </div>
  );
};
