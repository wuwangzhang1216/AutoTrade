import React, { useMemo } from 'react';
import { MODELS_DATA } from '../constants';
import { useAgentPortfolio, useAgentTrades, useAllPositions } from '../hooks/useApi';
import { BtcIcon, EthIcon, SolIcon, BnbIcon, DogeIcon, XrpIcon } from './Icons';

interface AgentProfileProps {
  agentId: string;
  onBack: () => void;
  previousView?: 'dashboard' | 'leaderboard' | 'portfolio';
}

const CRYPTO_ICONS: Record<string, React.ComponentType<any>> = {
  BTC: BtcIcon,
  ETH: EthIcon,
  SOL: SolIcon,
  BNB: BnbIcon,
  DOGE: DogeIcon,
  XRP: XrpIcon,
};

export const AgentProfile: React.FC<AgentProfileProps> = ({ agentId, onBack, previousView = 'dashboard' }) => {
  const { data: portfolio, loading: portfolioLoading } = useAgentPortfolio(agentId, 5000);
  const { data: trades, loading: tradesLoading } = useAgentTrades(agentId, 100, 5000);
  const { data: allPositions } = useAllPositions(5000);
  const [currentPage, setCurrentPage] = React.useState(1);
  const tradesPerPage = 10;

  // Get the back button text based on previous view
  const getBackButtonText = () => {
    switch (previousView) {
      case 'portfolio':
        return '← BACK TO PORTFOLIO';
      case 'leaderboard':
        return '← BACK TO LEADERBOARD';
      case 'dashboard':
        return '← BACK TO DASHBOARD';
      default:
        return '← BACK';
    }
  };

  // Find agent model data
  const modelData = MODELS_DATA.find(m => m.id === agentId);

  // Filter positions for this agent
  const agentPositions = useMemo(() => {
    return allPositions.filter(pos => pos.agent_id === agentId);
  }, [allPositions, agentId]);

  // Calculate aggregated stats
  const stats = useMemo(() => {
    if (!portfolio || !trades) return null;

    const longTrades = trades.filter(t => t.side === 'buy');
    const shortTrades = trades.filter(t => t.side === 'sell');

    // Calculate unrealized P&L from active positions (考虑leverage)
    const unrealizedPnL = agentPositions.reduce((sum, p) => {
      const leverage = p.leverage || 1.0;
      const side = p.side || 'long';
      let pnl;
      if (side === 'long') {
        pnl = (p.current_price - p.entry_price) * p.quantity * leverage;
      } else {
        pnl = (p.entry_price - p.current_price) * p.quantity * leverage;
      }
      return sum + pnl;
    }, 0);

    // Get REAL total P&L from portfolio (includes all realized + unrealized)
    // Total P&L = Total Account Value - Initial Balance
    const totalPnL = portfolio.total_pnl || 0;

    // Calculate realized P&L (Total - Unrealized)
    const realizedPnL = totalPnL - unrealizedPnL;

    // Calculate total fees
    const totalFees = trades.reduce((sum, t) => sum + (t.commission || 0), 0);

    // Calculate average leverage from active positions
    const avgLeverage = agentPositions.length > 0
      ? agentPositions.reduce((sum, p) => sum + (p.leverage || 1.0), 0) / agentPositions.length
      : 1.0;

    // Calculate hold times
    const now = new Date().getTime();
    const holdTimes = agentPositions.map(pos => {
      const entryTime = new Date(pos.entry_time || Date.now()).getTime();
      return now - entryTime;
    });

    const avgHoldTime = holdTimes.length > 0
      ? holdTimes.reduce((sum, t) => sum + t, 0) / holdTimes.length
      : 0;

    const longHoldTime = agentPositions.filter(p => p.side === 'long').length;
    const shortHoldTime = agentPositions.filter(p => p.side === 'short').length;
    const flatHoldTime = agentPositions.length === 0 ? 1 : 0;

    const totalHold = longHoldTime + shortHoldTime + flatHoldTime;
    const longPercent = totalHold > 0 ? (longHoldTime / totalHold) * 100 : 0;
    const shortPercent = totalHold > 0 ? (shortHoldTime / totalHold) * 100 : 0;
    const flatPercent = totalHold > 0 ? (flatHoldTime / totalHold) * 100 : 0;

    // Calculate wins/losses
    const completedTrades = trades.filter(t => {
      // A trade is complete if there's an opposite trade for the same symbol
      return true; // Simplified for now
    });

    const wins = completedTrades.filter(t => (t.pnl || 0) > 0);
    const losses = completedTrades.filter(t => (t.pnl || 0) < 0);

    const biggestWin = wins.length > 0
      ? Math.max(...wins.map(t => t.pnl || 0))
      : 0;

    const biggestLoss = losses.length > 0
      ? Math.min(...losses.map(t => t.pnl || 0))
      : 0;

    return {
      totalPnL,
      totalFees,
      avgLeverage: avgLeverage.toFixed(1),
      avgConfidence: 62.0, // Placeholder - would need to get from decision data
      biggestWin,
      biggestLoss,
      longPercent,
      shortPercent,
      flatPercent,
      unrealizedPnL,
      realizedPnL,
    };
  }, [portfolio, trades, agentPositions]);

  if (!modelData) {
    return (
      <div className="p-8 text-center">
        <p className="text-red-400">Agent not found</p>
        <button onClick={onBack} className="mt-4 text-blue-400 hover:underline">
          Back to Leaderboard
        </button>
      </div>
    );
  }

  const Icon = modelData.icon;

  // Pagination logic
  const totalPages = Math.ceil(trades.length / tradesPerPage);
  const startIndex = (currentPage - 1) * tradesPerPage;
  const endIndex = startIndex + tradesPerPage;
  const currentTrades = trades.slice(startIndex, endIndex);

  const goToNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const goToPreviousPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  // Reset to page 1 when agentId changes
  React.useEffect(() => {
    setCurrentPage(1);
  }, [agentId]);

  return (
    <div className="text-arena-gray-100">
      {/* Header */}
      <div className="mb-4 sm:mb-6 border border-arena-gray-700 rounded-lg p-3 sm:p-6 bg-gray-900 bg-opacity-40 backdrop-blur-sm">
        <button
          onClick={onBack}
          className="mb-3 sm:mb-4 text-xs sm:text-sm text-blue-400 hover:text-blue-300 flex items-center gap-2"
        >
          {getBackButtonText()}
        </button>

        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4">
          <div className="p-2 sm:p-3 rounded-lg" style={{ backgroundColor: `${modelData.color}20` }}>
            <Icon style={{ color: modelData.color }} size={36} className="sm:w-12 sm:h-12" />
          </div>
          <div className="flex-1 w-full">
            <div className="flex items-center gap-3">
              <h1 className="text-xl sm:text-2xl font-bold">{modelData.name}</h1>
            </div>
            <div className="mt-2 flex flex-col sm:flex-row sm:items-baseline gap-2 sm:gap-4">
              <div>
                <span className="text-xs sm:text-sm text-arena-gray-400">Total Account Value: </span>
                <span className="text-base sm:text-xl font-bold">
                  ${portfolio?.total_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
                </span>
              </div>
              <div>
                <span className="text-xs sm:text-sm text-arena-gray-400">Available Cash: </span>
                <span className="text-sm sm:text-lg font-semibold text-green-400">
                  ${portfolio?.cash.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 mb-4 sm:mb-6">
        {/* Total P&L */}
        <div className="border border-arena-gray-700 rounded-lg p-4 bg-gray-900 bg-opacity-40 backdrop-blur-sm">
          <div className="text-xs text-arena-gray-400 mb-1">Total P&L (Unrealized + Realized):</div>
          <div className={`text-2xl font-bold ${(stats?.totalPnL || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {(stats?.totalPnL || 0) >= 0 ? '+' : ''}${stats?.totalPnL.toLocaleString('en-US', { minimumFractionDigits: 2 }) || '0.00'}
          </div>
          <div className="text-xs text-arena-gray-500 mt-1 italic">
            Unrealized: ${stats?.unrealizedPnL.toFixed(2) || '0.00'}
          </div>
        </div>

        {/* Total Fees */}
        <div className="border border-arena-gray-700 rounded-lg p-4 bg-gray-900 bg-opacity-40 backdrop-blur-sm">
          <div className="text-xs text-arena-gray-400 mb-1">Total Fees:</div>
          <div className="text-2xl font-bold text-orange-400">${stats?.totalFees.toFixed(2) || '0.00'}</div>
          <div className="text-xs text-arena-gray-500 mt-1 italic">
            Trading commissions
          </div>
        </div>

        {/* Net P&L */}
        <div className="border border-arena-gray-700 rounded-lg p-4 bg-gray-900 bg-opacity-40 backdrop-blur-sm">
          <div className="text-xs text-arena-gray-400 mb-1">Net P&L (After Fees):</div>
          <div className={`text-2xl font-bold ${(stats?.totalPnL || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {(stats?.totalPnL || 0) >= 0 ? '+' : ''}${(stats?.totalPnL || 0).toFixed(2)}
          </div>
          <div className="text-xs text-arena-gray-500 mt-1 italic">
            True profit/loss (fees already deducted)
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 mb-4 sm:mb-6">
        <div className="border border-arena-gray-700 rounded-lg p-4 bg-gray-900 bg-opacity-40 backdrop-blur-sm">
          <div className="text-xs text-arena-gray-400 mb-3 uppercase">Performance</div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-arena-gray-400">Average Leverage:</span>
              <span className="font-semibold">{stats?.avgLeverage || '0.0'}x</span>
            </div>
            <div className="flex justify-between">
              <span className="text-arena-gray-400">Average Confidence:</span>
              <span className="font-semibold">{stats?.avgConfidence.toFixed(1) || '0.0'}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-arena-gray-400">Biggest Win:</span>
              <span className="font-semibold text-green-400">
                ${Math.abs(stats?.biggestWin || 0).toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-arena-gray-400">Biggest Loss:</span>
              <span className="font-semibold text-red-400">
                -${Math.abs(stats?.biggestLoss || 0).toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Hold Times */}
        <div className="border border-arena-gray-700 rounded-lg p-4 bg-gray-900 bg-opacity-40 backdrop-blur-sm">
          <div className="text-xs text-arena-gray-400 mb-3 uppercase">Hold Times</div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-arena-gray-400">Long:</span>
              <span className="font-semibold text-green-400">{stats?.longPercent.toFixed(1) || '0.0'}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-arena-gray-400">Short:</span>
              <span className="font-semibold text-red-400">{stats?.shortPercent.toFixed(1) || '0.0'}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-arena-gray-400">Flat:</span>
              <span className="font-semibold">{stats?.flatPercent.toFixed(1) || '0.0'}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Account Balance Explanation */}
      <div className="border border-blue-500/30 bg-blue-500/10 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <div className="text-blue-400 text-xl">ℹ️</div>
          <div className="flex-1 text-xs">
            <div className="font-semibold text-blue-300 mb-1">Understanding Leveraged Trading Balance</div>
            <div className="text-arena-gray-300 space-y-1">
              <p>• <span className="font-semibold">Available Cash</span> = Initial ${portfolio?.cash_balance || 10000} - Margin Locked - Fees</p>
              <p>• <span className="font-semibold">Total Account Value</span> = Available Cash + Locked Margin + Unrealized P&L</p>
              <p>• <span className="font-semibold">Margin</span> is not a loss - it's returned when positions close</p>
              <p>• Current margin locked: ${agentPositions.reduce((sum, p) => sum + (p.margin || 0), 0).toFixed(2)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Net Realized */}
      <div className="border border-arena-gray-700 rounded-lg p-4 bg-gray-900 bg-opacity-40 backdrop-blur-sm mb-6">
        <div className="text-xs text-arena-gray-400 mb-1 italic">
          All closed positions (fees already deducted from account balance)
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm">Realized P&L from Closed Trades:</span>
          <span className={`text-2xl font-bold ${(stats?.realizedPnL || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {(stats?.realizedPnL || 0) >= 0 ? '+' : ''}${stats?.realizedPnL.toFixed(2) || '0.00'}
          </span>
        </div>
      </div>

      {/* Active Positions */}
      <div className="border border-arena-gray-700 rounded-lg p-4 bg-gray-900 bg-opacity-40 backdrop-blur-sm mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-sm font-bold uppercase">Active Positions</h2>
          <div className="text-xs text-arena-gray-400">
            Total Unrealized P&L:
            <span className={`ml-2 font-semibold ${(stats?.unrealizedPnL || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              ${stats?.unrealizedPnL.toFixed(2) || '0.00'}
            </span>
          </div>
        </div>

        {portfolioLoading ? (
          <div className="text-center py-8 text-arena-gray-400">Loading positions...</div>
        ) : agentPositions.length === 0 ? (
          <div className="text-center py-8 text-arena-gray-400">No active positions</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agentPositions.map((position, idx) => {
              const symbol = position.symbol.replace('USDT', '');
              const CryptoIcon = CRYPTO_ICONS[symbol] || BtcIcon;
              const unrealizedPnL = position.unrealized_pnl || 0;

              return (
                <div key={idx} className="border border-arena-gray-700 rounded-lg p-3 bg-gradient-to-br from-gray-900 to-black">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-bold px-2 py-1 rounded ${
                        position.side === 'long' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                      }`}>
                        {position.side === 'long' ? 'LONG' : 'SHORT'}
                      </span>
                      <CryptoIcon className="w-5 h-5" />
                    </div>
                    <button className="text-xs text-blue-400 hover:underline">VIEW</button>
                  </div>

                  <div className="text-xs space-y-1">
                    <div className="flex justify-between">
                      <span className="text-arena-gray-400">Entry Time:</span>
                      <span>{new Date(position.entry_time || Date.now()).toLocaleTimeString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-arena-gray-400">Entry Price:</span>
                      <span>${position.entry_price?.toFixed(2) || '0.00'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-arena-gray-400">Leverage:</span>
                      <span className={`font-bold ${
                        (position.leverage || 1.0) >= 7 ? 'text-red-400' :
                        (position.leverage || 1.0) >= 4 ? 'text-orange-400' :
                        'text-blue-400'
                      }`}>
                        {(position.leverage || 1.0).toFixed(1)}x
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-arena-gray-400">Side:</span>
                      <span className={position.side === 'long' ? 'text-green-400' : 'text-red-400'}>
                        {position.side?.toUpperCase()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-arena-gray-400">Quantity:</span>
                      <span>{position.quantity?.toFixed(4) || '0'}</span>
                    </div>
                    <div className="flex justify-between font-semibold">
                      <span className="text-arena-gray-400">Unrealized P&L:</span>
                      <span className={unrealizedPnL >= 0 ? 'text-green-400' : 'text-red-400'}>
                        ${unrealizedPnL.toFixed(2)}
                      </span>
                    </div>
                  </div>

                  <div className="mt-2 pt-2 border-t border-arena-gray-700">
                    <div className="text-xs text-arena-gray-400">Exit Plan:</div>
                    <div className="text-xs mt-1 space-y-1">
                      <button className="w-full text-left hover:bg-arena-gray-800 px-2 py-1 rounded">
                        VIEW
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Trade History with Pagination */}
      <div className="border border-arena-gray-700 rounded-lg p-3 sm:p-4 bg-gray-900 bg-opacity-40 backdrop-blur-sm">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-3 sm:mb-4 gap-2">
          <h2 className="text-xs sm:text-sm font-bold uppercase">Trade History</h2>
          <div className="text-xs text-arena-gray-400">
            Total Trades: {trades.length}
          </div>
        </div>

        {tradesLoading ? (
          <div className="text-center py-8 text-arena-gray-400">Loading trades...</div>
        ) : trades.length === 0 ? (
          <div className="text-center py-8 text-arena-gray-400">No trades yet</div>
        ) : (
          <>
            <div className="overflow-x-auto -mx-3 sm:mx-0">
              <div className="min-w-[800px]">
                <table className="w-full text-[10px] sm:text-xs">
                <thead>
                  <tr className="border-b border-arena-gray-700 text-arena-gray-400">
                    <th className="text-left py-2 px-2">SIDE</th>
                    <th className="text-left py-2 px-2">COIN</th>
                    <th className="text-right py-2 px-2">ENTRY PRICE</th>
                    <th className="text-right py-2 px-2">EXIT PRICE</th>
                    <th className="text-right py-2 px-2">QUANTITY</th>
                    <th className="text-right py-2 px-2">HOLDING TIME</th>
                    <th className="text-right py-2 px-2">NOTIONAL ENTRY</th>
                    <th className="text-right py-2 px-2">NOTIONAL EXIT</th>
                    <th className="text-right py-2 px-2">TOTAL FEES</th>
                    <th className="text-right py-2 px-2">NET P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {currentTrades.map((trade, idx) => {
                  const symbol = trade.symbol?.replace('USDT', '') || 'BTC';
                  const CryptoIcon = CRYPTO_ICONS[symbol] || BtcIcon;
                  const notional = (trade.quantity || 0) * (trade.price || 0);
                  const fees = trade.commission || 0;

                  // 判断是否为未平仓交易（没有exit_price或pnl为null/undefined）
                  const isClosed = trade.exit_price != null || trade.pnl != null;
                  const netPnl = isClosed ? (trade.pnl || 0) - fees : null;
                  const holdingTime = trade.holding_time || 'N/A';
                  const notionalExit = trade.exit_price ? (trade.quantity || 0) * trade.exit_price : null;

                  return (
                    <tr key={idx} className="border-b border-arena-gray-800 hover:bg-arena-gray-800">
                      <td className="py-2 px-2">
                        <span className={`font-semibold ${
                          trade.side === 'buy' ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {trade.side === 'buy' ? 'LONG' : 'SHORT'}
                        </span>
                      </td>
                      <td className="py-2 px-2">
                        <div className="flex items-center gap-1">
                          <CryptoIcon className="w-4 h-4" />
                          <span className="font-mono">{symbol}</span>
                        </div>
                      </td>
                      <td className="text-right py-2 px-2">${trade.price?.toFixed(2) || '0.00'}</td>
                      <td className="text-right py-2 px-2">{trade.exit_price ? `$${trade.exit_price.toFixed(2)}` : '-'}</td>
                      <td className="text-right py-2 px-2">{trade.quantity?.toFixed(2) || '0.00'}</td>
                      <td className="text-right py-2 px-2">{holdingTime}</td>
                      <td className="text-right py-2 px-2">${notional.toLocaleString('en-US')}</td>
                      <td className="text-right py-2 px-2">{notionalExit ? `$${notionalExit.toLocaleString('en-US')}` : '-'}</td>
                      <td className="text-right py-2 px-2">${fees.toFixed(2)}</td>
                      <td className={`text-right py-2 px-2 font-semibold ${
                        netPnl != null ? (netPnl >= 0 ? 'text-green-400' : 'text-red-400') : 'text-arena-gray-400'
                      }`}>
                        {netPnl != null ? `${netPnl >= 0 ? '+' : ''}$${netPnl.toFixed(2)}` : '-'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
              </div>
            </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex flex-col sm:flex-row justify-between items-center mt-4 pt-4 border-t border-arena-gray-700 gap-3">
              <button
                onClick={goToPreviousPage}
                disabled={currentPage === 1}
                className={`w-full sm:w-auto px-3 sm:px-4 py-2 text-xs font-semibold rounded ${
                  currentPage === 1
                    ? 'bg-gray-800 text-arena-gray-600 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                ← PREVIOUS
              </button>

              <div className="text-xs text-arena-gray-400 text-center">
                Page {currentPage} of {totalPages} ({currentTrades.length} trades on this page)
              </div>

              <button
                onClick={goToNextPage}
                disabled={currentPage === totalPages}
                className={`w-full sm:w-auto px-3 sm:px-4 py-2 text-xs font-semibold rounded ${
                  currentPage === totalPages
                    ? 'bg-gray-800 text-arena-gray-600 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                NEXT →
              </button>
            </div>
          )}
        </>
        )}
      </div>
    </div>
  );
};
