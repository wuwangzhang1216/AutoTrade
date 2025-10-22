import React from 'react';
import { MODELS_DATA } from '../constants';
import type { AgentLeaderboardEntry } from '../services/api';
import { BtcIcon, EthIcon, SolIcon, DogeIcon, BnbIcon, XrpIcon } from './Icons';

interface WinningModelCardProps {
  winner: AgentLeaderboardEntry;
  positions?: any[];
}

export const WinningModelCard: React.FC<WinningModelCardProps> = ({ winner, positions = [] }) => {
  // Find model metadata
  const model = React.useMemo(() => {
    return MODELS_DATA.find(m => m.id === winner.agent_id);
  }, [winner.agent_id]);

  const Icon = model?.icon;

  const formatCurrency = (value: number) => {
    return `$${value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
  };

  // Mock crypto icons for active positions
  const positionIcons = [
    { Icon: XrpIcon, name: 'XRP' },
    { Icon: DogeIcon, name: 'DOGE' },
    { Icon: BtcIcon, name: 'BTC' },
    { Icon: EthIcon, name: 'ETH' },
    { Icon: SolIcon, name: 'SOL' },
    { Icon: BnbIcon, name: 'BNB' },
  ];

  return (
    <div className="-mx-2 sm:mx-0 border border-arena-gray-700 rounded-lg bg-gradient-to-br from-gray-900 to-black p-1.5 sm:p-4 md:p-6 overflow-hidden">
      <h3 className="text-[9px] sm:text-xs md:text-sm font-bold text-arena-gray-400 mb-1 sm:mb-4 uppercase tracking-wider truncate">
        <span className="sm:hidden">WINNER</span>
        <span className="hidden sm:inline">Winning Model</span>
      </h3>

      <div className="flex items-center gap-1.5 sm:gap-3 mb-1.5 sm:mb-4">
        {Icon && (
          <div className="p-1.5 sm:p-2.5 md:p-3 rounded-full bg-gray-800/50 border border-arena-gray-700 flex-shrink-0">
            <Icon
              style={{ color: model?.color }}
              size={16}
              className="sm:w-6 sm:h-6 md:w-7 md:h-7"
            />
          </div>
        )}
        <div className="min-w-0 flex-1">
          <h2 className="text-sm sm:text-lg md:text-xl font-bold text-white truncate">
            {model?.name || winner.agent_id}
          </h2>
        </div>
      </div>

      <div className="mb-1.5 sm:mb-4">
        <div className="text-[8px] sm:text-[10px] md:text-xs text-arena-gray-400 mb-0.5 sm:mb-1 uppercase tracking-wide">
          <span className="sm:hidden">EQUITY</span>
          <span className="hidden sm:inline">Total Equity</span>
        </div>
        <div className="text-base sm:text-2xl md:text-3xl font-bold text-white">
          {formatCurrency(winner.total_value)}
        </div>
      </div>

      <div>
        <div className="text-[8px] sm:text-[10px] md:text-xs font-bold text-arena-gray-400 uppercase tracking-wide mb-1 sm:mb-2">
          <span className="sm:hidden">POS</span>
          <span className="hidden sm:inline">Active Positions</span>
        </div>
        <div className="flex items-center gap-1 sm:gap-2 flex-wrap">
          {positionIcons.slice(0, 6).map((item, index) => (
            <div key={index} className="flex-shrink-0 w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-gray-800 border border-arena-gray-700 flex items-center justify-center">
              <item.Icon
                size={12}
                className="sm:w-4 sm:h-4"
                style={{ color: '#9CA3AF' }}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
