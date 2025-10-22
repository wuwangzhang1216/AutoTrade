import React from 'react';
import { useAllTrades } from '../hooks/useApi';
import { BtcIcon, EthIcon, SolIcon, BnbIcon, DogeIcon, XrpIcon } from './Icons';
import { MODELS_DATA } from '../constants';

const CRYPTO_ICONS: Record<string, any> = {
  'BTC': BtcIcon,
  'ETH': EthIcon,
  'SOL': SolIcon,
  'BNB': BnbIcon,
  'DOGE': DogeIcon,
  'XRP': XrpIcon,
};

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
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

const PnL: React.FC<{ value: number }> = ({ value }) => {
  const isPositive = value >= 0;
  const color = isPositive ? 'text-green-400' : 'text-red-500';
  const sign = isPositive ? '+' : '';

  return (
    <span className={`${color} font-bold`}>
      {sign}${Math.abs(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
    </span>
  );
};

export const CompletedTrades: React.FC = () => {
  const { data: trades, loading, error } = useAllTrades(100, 10000);

  const hasLiveData = !loading && !error && trades && trades.length > 0;

  return (
    <div className="bg-gray-900 bg-opacity-40 backdrop-blur-sm text-arena-gray-200 text-sm font-sans py-4">
      {/* Status Indicator */}
      <div className="px-4 mb-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <label className="text-arena-gray-500 font-bold mr-2 text-xs">STATUS:</label>
          {loading ? (
            <span className="text-xs text-yellow-400 flex items-center">
              <div className="w-2 h-2 bg-yellow-400 rounded-full mr-2 animate-pulse" />
              Loading...
            </span>
          ) : hasLiveData ? (
            <span className="text-xs text-green-400 flex items-center">
              <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse" />
              Live Data
            </span>
          ) : (
            <span className="text-xs text-red-400 flex items-center">
              <div className="w-2 h-2 bg-red-400 rounded-full mr-2" />
              No Data Available
            </span>
          )}
        </div>
      </div>

      {/* Live Trades Table */}
      {hasLiveData ? (
        <div className="px-4">
          <h4 className="font-bold text-base mb-3 text-white">TRADE HISTORY</h4>

          {/* Table Header */}
          <div className="grid grid-cols-12 gap-3 text-xs text-arena-gray-500 mb-2 font-mono">
            <div className="col-span-2">TIME</div>
            <div className="col-span-2">AGENT</div>
            <div className="col-span-2">SYMBOL</div>
            <div className="col-span-1">SIDE</div>
            <div className="col-span-1 text-center">LEVERAGE</div>
            <div className="col-span-2 text-right">PRICE</div>
            <div className="col-span-2 text-right">QTY</div>
          </div>

          {/* Table Body */}
          <div className="space-y-1 font-mono max-h-[40vh] overflow-y-auto">
            {trades.map((trade: any, index: number) => {
              const CoinIcon = CRYPTO_ICONS[trade.symbol] || BtcIcon;
              const sideColor = trade.side === 'buy' ? 'text-green-400' : 'text-red-400';
              const pnl = trade.pnl || 0;
              const agentModel = MODELS_DATA.find(m => m.id === trade.agent_id);
              const AgentIcon = agentModel?.icon;
              const leverage = trade.leverage || 1.0;

              // Leverage颜色：高杠杆用红色/橙色警告
              const leverageColor = leverage >= 7 ? 'text-red-400' : leverage >= 4 ? 'text-orange-400' : 'text-blue-400';

              return (
                <div key={index} className="grid grid-cols-12 gap-3 items-center border-b border-arena-gray-900 py-2 text-sm hover:bg-gray-900 hover:bg-opacity-30 transition-colors">
                  <div className="col-span-2 text-arena-gray-400 text-xs">
                    {formatDate(trade.timestamp || trade.created_at || trade.updated_at)}
                  </div>
                  <div className="col-span-2 flex items-center space-x-1">
                    {AgentIcon && <AgentIcon style={{color: agentModel?.color}} size={16} />}
                    <span className="font-bold text-xs">{agentModel?.name || trade.agent_id}</span>
                  </div>
                  <div className="col-span-2 flex items-center space-x-2">
                    <CoinIcon className="w-5 h-5" />
                    <span className="font-bold">{trade.symbol}</span>
                  </div>
                  <div className={`col-span-1 font-bold uppercase ${sideColor}`}>
                    {trade.side}
                  </div>
                  <div className={`col-span-1 text-center font-bold ${leverageColor}`}>
                    {leverage.toFixed(1)}x
                  </div>
                  <div className="col-span-2 text-right text-arena-gray-400">
                    ${(trade.price || trade.average_price || trade.entry_price || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </div>
                  <div className="col-span-2 text-right">
                    {(trade.quantity || trade.filled_quantity || 0).toFixed(4)}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : loading ? (
        <div className="px-4 py-8 text-center text-arena-gray-500">
          <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-3" />
          <p>Loading trade history...</p>
        </div>
      ) : (
        <div className="px-4 py-8 text-center text-arena-gray-500">
          <p>{error ? `Error: ${error}` : 'No trades completed yet'}</p>
          <p className="text-xs mt-2">Start trading to see your history here</p>
        </div>
      )}
    </div>
  );
};
