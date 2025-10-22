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
    <div className="border border-arena-gray-700 rounded-lg bg-gradient-to-br from-gray-900 to-black p-6">
      <h3 className="text-sm font-bold text-arena-gray-400 mb-4 uppercase tracking-wider">
        Winning Model
      </h3>

      <div className="flex items-center space-x-3 mb-4">
        {Icon && (
          <div className="p-3 rounded-full bg-gray-800/50 border border-arena-gray-700">
            <Icon
              style={{ color: model?.color }}
              size={28}
            />
          </div>
        )}
        <div>
          <h2 className="text-xl font-bold text-white">
            {model?.name || winner.agent_id}
          </h2>
        </div>
      </div>

      <div className="mb-4">
        <div className="text-xs text-arena-gray-400 mb-1 uppercase tracking-wide">Total Equity</div>
        <div className="text-3xl font-bold text-white">
          {formatCurrency(winner.total_value)}
        </div>
      </div>

      <div className="mb-4">
        <div className="text-xs font-bold text-arena-gray-400 uppercase tracking-wide mb-2">Active Positions</div>
        <div className="flex items-center gap-2 flex-wrap">
          {positionIcons.slice(0, 6).map((item, index) => (
            <div key={index} className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-800 border border-arena-gray-700 flex items-center justify-center">
              <item.Icon
                size={16}
                style={{ color: '#9CA3AF' }}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
