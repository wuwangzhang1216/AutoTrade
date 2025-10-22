import React, { useState } from 'react';
import { POSITIONS_DATA, MODELS_DATA } from '../constants';
import { BtcIcon, EthIcon, SolIcon, BnbIcon, DogeIcon, XrpIcon } from './Icons';
import { useAggregateStats, useAllPositions } from '../hooks/useApi';

const DropdownIcon = () => (
  <svg width="12" height="12" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="inline-block ml-2">
    <path d="M4.18179 6.18181C4.35753 6.00608 4.64245 6.00608 4.81819 6.18181L7.49999 8.86362L10.1818 6.18181C10.3575 6.00608 10.6424 6.00608 10.8182 6.18181C10.9939 6.35755 10.9939 6.64247 10.8182 6.81821L7.81819 9.81821C7.64245 9.99394 7.35753 9.99394 7.18179 9.81821L4.18179 6.81821C4.00606 6.64247 4.00606 6.35755 4.18179 6.18181Z" fill="currentColor" fillRule="evenodd" clipRule="evenodd"></path>
  </svg>
);

const CRYPTO_ICONS: Record<string, any> = {
  'BTC': BtcIcon,
  'ETH': EthIcon,
  'SOL': SolIcon,
  'BNB': BnbIcon,
  'DOGE': DogeIcon,
  'XRP': XrpIcon,
};

const PnL: React.FC<{ value: number }> = ({ value }) => {
  const isPositive = value >= 0;
  const color = isPositive ? 'text-green-400' : 'text-red-500';
  const sign = isPositive ? '+' : '';

  // Simplify display for small values
  const displayValue = Math.abs(value) < 1000
    ? value.toFixed(2)
    : (value / 1000).toFixed(1) + 'k';

  return (
    <span className={`${color} font-bold text-[10px]`}>
      {sign}${displayValue}
    </span>
  );
};

const PnLPercent: React.FC<{ value: number }> = ({ value }) => {
  const isPositive = value >= 0;
  const color = isPositive ? 'text-green-400' : 'text-red-500';
  const sign = isPositive ? '+' : '';

  return (
    <span className={`${color} text-[9px]`}>
      ({sign}{value.toFixed(2)}%)
    </span>
  );
};

const ExitPlanPopover: React.FC<{
  position: any;
  onClose: () => void;
}> = ({ position, onClose }) => {
  const hasExitPlan = position.stop_loss || position.take_profit || position.exit_condition;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-gradient-to-br from-gray-900 to-black border border-arena-gray-700 rounded-lg p-4 max-w-md w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-3 pb-3 border-b border-arena-gray-700">
          <h3 className="font-bold text-white">EXIT PLAN</h3>
          <button
            onClick={onClose}
            className="text-arena-gray-400 hover:text-white"
          >
            ✕
          </button>
        </div>

        {hasExitPlan ? (
          <div className="space-y-2 text-sm">
            {position.leverage && (
              <div>
                <span className="text-arena-gray-400">Leverage: </span>
                <span className={`font-bold ${position.leverage >= 7 ? 'text-red-400' : position.leverage >= 4 ? 'text-orange-400' : 'text-blue-400'}`}>
                  {position.leverage.toFixed(1)}x
                </span>
                <span className="text-arena-gray-500 text-xs ml-2">
                  (多倍ETF)
                </span>
              </div>
            )}
            {position.take_profit && (
              <div>
                <span className="text-arena-gray-400">Target: </span>
                <span className="text-green-400 font-bold">
                  ${position.take_profit.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </span>
              </div>
            )}
            {position.stop_loss && (
              <div>
                <span className="text-arena-gray-400">Stop: </span>
                <span className="text-red-400 font-bold">
                  ${position.stop_loss.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </span>
              </div>
            )}
            {position.exit_condition && (
              <div>
                <span className="text-arena-gray-400">Invalid Condition: </span>
                <span className="text-white">{position.exit_condition}</span>
              </div>
            )}
            {position.reasoning && (
              <div className="mt-3 pt-3 border-t border-arena-gray-700">
                <div className="text-arena-gray-400 text-xs mb-1">REASONING:</div>
                <div className="text-white text-xs">{position.reasoning}</div>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            {position.leverage && (
              <div className="text-sm">
                <span className="text-arena-gray-400">Leverage: </span>
                <span className={`font-bold ${position.leverage >= 7 ? 'text-red-400' : position.leverage >= 4 ? 'text-orange-400' : 'text-blue-400'}`}>
                  {position.leverage.toFixed(1)}x
                </span>
                <span className="text-arena-gray-500 text-xs ml-2">
                  (多倍ETF)
                </span>
              </div>
            )}
            <div className="text-arena-gray-400 text-sm">
              No exit plan configured for this position.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export const PositionsContent: React.FC = () => {
  const { data: aggregate, loading: aggregateLoading, error: aggregateError } = useAggregateStats(10000);
  const { data: positions, loading: positionsLoading, error: positionsError } = useAllPositions(10000);
  const [selectedPosition, setSelectedPosition] = useState<any | null>(null);

  const loading = aggregateLoading || positionsLoading;
  const error = aggregateError || positionsError;

  // Use live data if available, otherwise fall back to static data
  const hasLiveData = !loading && !error && aggregate;
  const hasPositions = positions && positions.length > 0;

  return (
    <div className="bg-gray-900 bg-opacity-40 backdrop-blur-sm text-arena-gray-200 text-sm font-sans py-3 sm:py-4">
      {/* Status Indicator */}
      <div className="px-3 sm:px-4 mb-3 sm:mb-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <label className="text-arena-gray-500 font-bold mr-2 text-[10px] sm:text-xs">STATUS:</label>
          {loading ? (
            <span className="text-[10px] sm:text-xs text-yellow-400 flex items-center">
              <div className="w-2 h-2 bg-yellow-400 rounded-full mr-2 animate-pulse" />
              <span className="hidden sm:inline">Loading...</span>
            </span>
          ) : hasLiveData ? (
            <span className="text-[10px] sm:text-xs text-green-400 flex items-center">
              <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse" />
              <span className="hidden sm:inline">Live Data</span>
            </span>
          ) : (
            <span className="text-[10px] sm:text-xs text-red-400 flex items-center">
              <div className="w-2 h-2 bg-red-400 rounded-full mr-2" />
              <span className="hidden sm:inline">Using Demo Data</span>
            </span>
          )}
        </div>
      </div>

      {/* Live Positions Table - Grouped by Agent */}
      {hasLiveData && positions && positions.length > 0 ? (
        <div className="px-4">
          {/* Group positions by agent */}
          <div className="space-y-4 max-h-[40vh] overflow-y-auto pr-2">
            {MODELS_DATA.filter(m => m.id !== 'btcHold').map((model) => {
              const agentPositions = positions.filter(p => p.agent_id === model.id);

              if (agentPositions.length === 0) return null;

              // Calculate total unrealized P&L for this agent (考虑leverage)
              const totalPnL = agentPositions.reduce((sum, pos) => {
                const leverage = pos.leverage || 1.0;
                const side = pos.side || 'long';
                let pnl;
                if (side === 'long') {
                  pnl = (pos.current_price - pos.entry_price) * pos.quantity * leverage;
                } else {
                  pnl = (pos.entry_price - pos.current_price) * pos.quantity * leverage;
                }
                return sum + pnl;
              }, 0);

              // Calculate available cash (from agent value - positions value)
              const totalPositionValue = agentPositions.reduce((sum, pos) => sum + (pos.current_price * pos.quantity), 0);
              const agentValue = 10000 + totalPnL; // Approximate agent value
              const availableCash = agentValue - totalPositionValue;

              const AgentIcon = model.icon;

              return (
                <div key={model.id} className="bg-gray-900 bg-opacity-30 rounded-lg p-2 sm:p-3 border border-arena-gray-800">
                  {/* Agent Header */}
                  <div className="flex items-center justify-between mb-2 pb-2 border-b border-arena-gray-800">
                    <div className="flex items-center gap-1.5 sm:gap-2">
                      <AgentIcon style={{ color: model.color }} size={20} />
                      <h3 className="font-bold text-sm sm:text-base uppercase" style={{ color: model.color }}>
                        <span className="sm:hidden">{model.name.split(' ')[0]}</span>
                        <span className="hidden sm:inline">{model.name}</span>
                      </h3>
                    </div>
                    <div className="text-right">
                      <div className="text-[9px] sm:text-xs text-arena-gray-400">P&L:</div>
                      <div className="font-bold text-xs sm:text-base">
                        <PnL value={totalPnL} />
                      </div>
                    </div>
                  </div>

                  {/* Desktop: Table Header */}
                  <div className="hidden md:grid grid-cols-6 gap-2 text-[10px] text-arena-gray-500 mb-2 font-mono uppercase">
                    <div className="col-span-1">SIDE</div>
                    <div className="col-span-1">COIN</div>
                    <div className="col-span-1 text-center">LEV</div>
                    <div className="col-span-1 text-right">VALUE</div>
                    <div className="col-span-1 text-center">PLAN</div>
                    <div className="col-span-1 text-right">P&L</div>
                  </div>

                  {/* Mobile: Compact cards */}
                  <div className="md:hidden space-y-1.5">
                    {agentPositions.map((pos, index) => {
                      const CoinIcon = CRYPTO_ICONS[pos.symbol] || BtcIcon;
                      const sideColor = pos.side === 'long' ? 'text-green-400' : 'text-red-400';
                      const leverage = pos.leverage || 1.0;
                      const side = pos.side || 'long';

                      let unrealized_pnl;
                      if (side === 'long') {
                        unrealized_pnl = (pos.current_price - pos.entry_price) * pos.quantity * leverage;
                      } else {
                        unrealized_pnl = (pos.entry_price - pos.current_price) * pos.quantity * leverage;
                      }

                      const notional = pos.current_price * pos.quantity;
                      const leverageColor = leverage >= 7 ? 'text-red-400' : leverage >= 4 ? 'text-orange-400' : 'text-blue-400';

                      return (
                        <div key={index} className="border border-arena-gray-800 rounded p-1.5 bg-gray-900/30 text-[10px]">
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center gap-1">
                              <CoinIcon className="w-4 h-4" />
                              <span className="font-bold text-white">{pos.symbol}</span>
                              <span className={`font-bold uppercase ${sideColor} text-[9px]`}>{pos.side}</span>
                              <span className={`font-bold ${leverageColor} text-[9px]`}>{leverage.toFixed(1)}x</span>
                            </div>
                            <PnL value={unrealized_pnl} />
                          </div>
                          <div className="flex justify-between items-center text-arena-gray-400">
                            <span>${notional.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</span>
                            <button
                              onClick={() => setSelectedPosition(pos)}
                              className="border border-arena-gray-700 px-2 py-0.5 rounded text-[9px] hover:bg-arena-gray-800 transition-colors"
                            >
                              VIEW
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Desktop: Table rows */}
                  <div className="hidden md:block space-y-1 font-mono">
                    {agentPositions.map((pos, index) => {
                      const CoinIcon = CRYPTO_ICONS[pos.symbol] || BtcIcon;
                      const sideColor = pos.side === 'long' ? 'text-green-400' : 'text-red-400';
                      const leverage = pos.leverage || 1.0;
                      const side = pos.side || 'long';

                      let unrealized_pnl;
                      if (side === 'long') {
                        unrealized_pnl = (pos.current_price - pos.entry_price) * pos.quantity * leverage;
                      } else {
                        unrealized_pnl = (pos.entry_price - pos.current_price) * pos.quantity * leverage;
                      }

                      const notional = pos.current_price * pos.quantity;
                      const leverageColor = leverage >= 7 ? 'text-red-400' : leverage >= 4 ? 'text-orange-400' : 'text-blue-400';

                      return (
                        <div key={index} className="grid grid-cols-6 gap-2 items-center py-2 text-sm hover:bg-gray-800 hover:bg-opacity-30 transition-colors rounded">
                          <div className={`col-span-1 font-bold uppercase ${sideColor}`}>
                            {pos.side}
                          </div>
                          <div className="col-span-1 flex items-center space-x-2">
                            <CoinIcon className="w-5 h-5" />
                            <span className="font-bold">{pos.symbol}</span>
                          </div>
                          <div className={`col-span-1 text-center font-bold ${leverageColor}`}>
                            {leverage.toFixed(1)}x
                          </div>
                          <div className="col-span-1 text-right font-bold text-green-400">
                            ${notional.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                          </div>
                          <div className="col-span-1 text-center">
                            <button
                              onClick={() => setSelectedPosition(pos)}
                              className="border border-arena-gray-700 px-3 py-1 rounded text-xs hover:bg-arena-gray-800 transition-colors"
                            >
                              VIEW
                            </button>
                          </div>
                          <div className="col-span-1 text-right font-bold">
                            <PnL value={unrealized_pnl} />
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Available Cash */}
                  <div className="mt-2 pt-2 border-t border-arena-gray-800 text-[10px] sm:text-xs">
                    <span className="text-arena-gray-400">CASH: </span>
                    <span className="font-bold text-white">
                      ${availableCash.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : loading ? (
        <div className="px-4 py-8 text-center text-arena-gray-500">
          <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-3" />
          <p>Loading positions...</p>
        </div>
      ) : (
        <div className="px-4">
          <p className="text-center text-arena-gray-500 mb-4 text-xs">
            {error ? 'Live data unavailable - Showing demo data' : 'No live positions found - Showing demo data'}
          </p>

          {/* Demo Data Display */}
          <div className="space-y-4 max-h-[25vh] overflow-y-auto">
            {POSITIONS_DATA.map((modelPositions, idx) => (
              <div key={idx} className="border-t border-arena-gray-800 pt-4 first:border-t-0">
                <div className="mb-3">
                  <div className="text-xs">
                    <span className="text-arena-gray-400">TOTAL UNREALIZED P&L: </span>
                    <PnL value={modelPositions.totalUnrealizedPL} />
                  </div>
                </div>

                <div className="space-y-1 font-mono text-xs">
                  {modelPositions.positions.map((pos, index) => {
                    const { coinIcon: CoinIcon } = pos;
                    return (
                      <div key={index} className="grid grid-cols-10 gap-2 items-center border-b border-arena-gray-900 py-2">
                        <div className="col-span-1 font-bold text-green-400">{pos.side}</div>
                        <div className="col-span-3 flex items-center space-x-1">
                          <CoinIcon className="w-4 h-4" />
                          <span>{pos.coin}</span>
                        </div>
                        <div className="col-span-4 text-right font-bold text-green-400">
                          {pos.notional.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
                        </div>
                        <div className="col-span-2 text-right"><PnL value={pos.unrealPL} /></div>
                      </div>
                    );
                  })}
                </div>

                <div className="text-xs text-arena-gray-400 mt-3 font-mono">
                  AVAILABLE CASH: {modelPositions.availableCash.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Exit Plan Popover */}
      {selectedPosition && (
        <ExitPlanPopover
          position={selectedPosition}
          onClose={() => setSelectedPosition(null)}
        />
      )}
    </div>
  );
};
