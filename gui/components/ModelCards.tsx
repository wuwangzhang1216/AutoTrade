
import React from 'react';
import { MODELS_DATA } from '../constants';
import type { ModelData } from '../types';
import { useLeaderboard } from '../hooks/useApi';

interface ModelCardProps {
  model: ModelData;
  isLive?: boolean;
  liveValue?: number;
  liveReturn?: number;
  onSelect?: (modelId: string) => void;
}

const ModelCard: React.FC<ModelCardProps> = ({ model, isLive, liveValue, liveReturn, onSelect }) => {
  const { name, value, icon: Icon, color, id } = model;
  const displayValue = liveValue !== undefined ? liveValue : value;
  const returnPercent = liveReturn !== undefined ? liveReturn : ((value - 10000) / 10000) * 100;
  const isPositive = returnPercent >= 0;

  return (
    <div
      className="border border-arena-gray-700 hover:border-gray-600 p-3 sm:p-4 rounded-lg text-sm text-center transition-all hover:shadow-lg hover:shadow-blue-500/10 bg-gray-900 bg-opacity-40 backdrop-blur-sm relative group cursor-pointer min-h-[100px] sm:min-h-0 active:scale-95 active:bg-gray-800/60"
      onClick={() => onSelect?.(id)}
    >
      {isLive && (
        <div className="absolute top-2 right-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
        </div>
      )}
      <div className="flex items-center justify-center space-x-2 text-arena-gray-400 mb-2">
        <Icon className="transition-transform group-hover:scale-110" style={{ color }} size={18} />
      </div>
      <div className="text-[10px] sm:text-xs text-arena-gray-400 mb-1 font-semibold truncate">{name}</div>
      <p className="font-bold text-white text-sm sm:text-base lg:text-lg mb-1">
        ${displayValue.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
      </p>
      <div className={`text-[10px] sm:text-xs font-bold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
        {isPositive ? '+' : ''}{returnPercent.toFixed(2)}%
      </div>
    </div>
  );
};

interface ModelCardsProps {
  onModelSelect?: (modelId: string) => void;
}

export const ModelCards: React.FC<ModelCardsProps> = ({ onModelSelect }) => {
  const { data: leaderboard, loading: leaderboardLoading } = useLeaderboard(10000);

  // Create a map of agent values from leaderboard
  const agentValues = React.useMemo(() => {
    if (!leaderboard) return {};
    const map: Record<string, { value: number; pnl_percent: number }> = {};
    leaderboard.forEach(entry => {
      map[entry.agent_id] = {
        value: entry.total_value,
        pnl_percent: entry.total_pnl_percent
      };
    });
    return map;
  }, [leaderboard]);

  return (
    <div>
      {/* Model Comparison Cards */}
      <div>
        <h4 className="text-[10px] sm:text-xs md:text-sm font-bold text-arena-gray-400 mb-2 sm:mb-3 uppercase tracking-wider">
          Model Comparison {leaderboardLoading && '(Loading...)'} {!leaderboardLoading && leaderboard && leaderboard.length > 0 && '(Live Data)'}
        </h4>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-7 gap-2 sm:gap-3">
          {MODELS_DATA.filter(m => m.id !== 'btcHold').map((model) => {
            const agentData = agentValues[model.id];
            return (
              <ModelCard
                key={model.id}
                model={model}
                isLive={!!agentData}
                liveValue={agentData?.value}
                liveReturn={agentData?.pnl_percent}
                onSelect={onModelSelect}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
};
