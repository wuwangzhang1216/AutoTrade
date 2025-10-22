
import React from 'react';
import { CRYPTO_TICKER_DATA } from '../constants';
import { BtcIcon, EthIcon, SolIcon, BnbIcon, DogeIcon, XrpIcon } from './Icons';
import { useMarketData } from '../hooks/useApi';

const ExternalLinkIcon: React.FC = () => (
  <svg width="12" height="12" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="inline-block ml-1 opacity-70">
    <path d="M3.64645 11.3536C3.45118 11.1583 3.45118 10.8417 3.64645 10.6465L10.2929 4L6 4C5.72386 4 5.5 3.77614 5.5 3.5C5.5 3.22386 5.72386 3 6 3L11.5 3C11.7761 3 12 3.22386 12 3.5V9C12 9.27614 11.7761 9.5 11.5 9.5C11.2239 9.5 11 9.27614 11 9V4.70711L4.35355 11.3536C4.15829 11.5488 3.84171 11.5488 3.64645 11.3536Z" fill="currentColor" clipRule="evenodd" fillRule="evenodd"></path>
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

interface CryptoTickerItemProps {
  symbol: string;
  price: number;
  change24h?: number;
  isLive?: boolean;
}

const CryptoTickerItem: React.FC<CryptoTickerItemProps> = ({ symbol, price, change24h, isLive }) => {
  const Icon = CRYPTO_ICONS[symbol] || BtcIcon;
  const isPositive = change24h && change24h > 0;
  const changeColor = isPositive ? 'text-green-400' : 'text-red-400';
  const changeBgColor = isPositive ? 'bg-green-500/10' : 'bg-red-500/10';
  const changeBorderColor = isPositive ? 'border-green-500/20' : 'border-red-500/20';

  return (
    <div className="group relative px-4 py-2 border-r border-arena-gray-800 last:border-r-0 transition-all duration-300 hover:bg-gray-800/30">
      {/* Background gradient on hover */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-gray-800/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

      {/* Live indicator */}
      {isLive && (
        <div className="absolute top-2 right-2 flex items-center space-x-1">
          <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse shadow-lg shadow-green-500/50" />
        </div>
      )}

      <div className="flex items-center space-x-3 relative">
        {/* Icon with container */}
        <div className="flex-shrink-0 w-9 h-9 rounded-full bg-gray-800/50 border border-arena-gray-700 flex items-center justify-center group-hover:border-arena-gray-600 group-hover:shadow-lg transition-all duration-300">
          <Icon className="h-5 w-5 transition-transform duration-300 group-hover:scale-110" />
        </div>

        {/* Price info */}
        <div className="flex flex-col">
          {/* Symbol */}
          <span className="text-xs font-bold text-arena-gray-400 uppercase tracking-wider group-hover:text-arena-gray-300 transition-colors">
            {symbol}
          </span>

          {/* Price and change */}
          <div className="flex items-center space-x-2 mt-0.5">
            <p className="text-sm font-bold text-white tabular-nums">
              ${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: price < 1 ? 4 : 2 })}
            </p>

            {change24h !== undefined && (
              <span className={`text-xs font-semibold px-1.5 py-0.5 rounded border ${changeColor} ${changeBgColor} ${changeBorderColor} tabular-nums`}>
                {change24h > 0 ? '+' : ''}{change24h.toFixed(2)}%
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

interface HeaderProps {
  currentView?: string;
  onViewChange?: (view: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ currentView = 'dashboard', onViewChange }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  // Fetch live market data every 30 seconds
  const { data: liveMarketData, loading, error } = useMarketData(
    ['BTC', 'ETH', 'SOL', 'BNB', 'DOGE', 'XRP'],
    30000
  );

  // Use live data if available, otherwise fall back to static data
  const displayData = !loading && liveMarketData && liveMarketData.length > 0
    ? liveMarketData.map(item => ({
        symbol: item.symbol,
        price: item.price,
        change24h: item.change_24h,
        isLive: true,
      }))
    : CRYPTO_TICKER_DATA.map(item => ({
        symbol: item.name,
        price: item.price,
        change24h: undefined,
        isLive: false,
      }));

  const handleNavClick = (view: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    if (onViewChange) {
      onViewChange(view);
    }
    setMobileMenuOpen(false);
  };

  return (
    <header className="font-sans">
      <div className="flex justify-between items-center">
        <div className="flex items-end space-x-2 sm:space-x-3">
          <h1 className="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-black tracking-tighter bg-gradient-to-r from-green-400 to-emerald-600 bg-clip-text text-transparent" style={{fontFamily: "'Bit_VCR', monospace"}}>
            TradeForge
          </h1>
        </div>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex text-sm font-bold tracking-wider">
          <a
            href="#"
            onClick={handleNavClick('dashboard')}
            className={`p-2 transition-colors ${currentView === 'dashboard' ? 'text-white' : 'text-arena-gray-400 hover:text-white'}`}
          >
            LIVE
          </a>
          <span className="text-arena-gray-700">|</span>
          <a
            href="#"
            onClick={handleNavClick('leaderboard')}
            className={`p-2 transition-colors ${currentView === 'leaderboard' ? 'text-white' : 'text-arena-gray-400 hover:text-white'}`}
          >
            LEADERBOARD
          </a>
          <span className="text-arena-gray-700">|</span>
          <a
            href="#"
            onClick={handleNavClick('portfolio')}
            className={`p-2 transition-colors ${currentView === 'portfolio' ? 'text-white' : 'text-arena-gray-400 hover:text-white'}`}
          >
            PORTFOLIO
          </a>
        </nav>

        {/* Mobile Menu Button */}
        <button
          className="md:hidden p-2 text-arena-gray-400 hover:text-white"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {mobileMenuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile Navigation */}
      {mobileMenuOpen && (
        <nav className="md:hidden mt-4 flex flex-col space-y-2 bg-gray-900 bg-opacity-60 backdrop-blur-sm border border-arena-gray-700 rounded-lg p-3">
          <a
            href="#"
            onClick={handleNavClick('dashboard')}
            className={`p-3 text-sm font-bold transition-colors rounded ${currentView === 'dashboard' ? 'bg-arena-gray-100 text-arena-black' : 'text-arena-gray-400 hover:bg-arena-gray-800 hover:text-white'}`}
          >
            LIVE
          </a>
          <a
            href="#"
            onClick={handleNavClick('leaderboard')}
            className={`p-3 text-sm font-bold transition-colors rounded ${currentView === 'leaderboard' ? 'bg-arena-gray-100 text-arena-black' : 'text-arena-gray-400 hover:bg-arena-gray-800 hover:text-white'}`}
          >
            LEADERBOARD
          </a>
          <a
            href="#"
            onClick={handleNavClick('portfolio')}
            className={`p-3 text-sm font-bold transition-colors rounded ${currentView === 'portfolio' ? 'bg-arena-gray-100 text-arena-black' : 'text-arena-gray-400 hover:bg-arena-gray-800 hover:text-white'}`}
          >
            PORTFOLIO
          </a>
        </nav>
      )}

      {/* Crypto Ticker Bar */}
      <div className="mt-4 relative overflow-hidden rounded-lg border border-arena-gray-800 bg-gradient-to-r from-gray-900/50 via-gray-800/30 to-gray-900/50 backdrop-blur-sm">
        {/* Subtle shine effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent opacity-0 hover:opacity-100 transition-opacity duration-700 pointer-events-none" />

        {/* Desktop/Tablet - Show all tickers */}
        <div className="hidden md:flex relative overflow-x-auto">
          {loading ? (
            <div className="w-full py-4 text-center text-sm text-gray-400 flex items-center justify-center space-x-2">
              <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              <span>Loading market data...</span>
            </div>
          ) : error ? (
            <div className="w-full py-4 text-center text-sm text-red-400 flex items-center justify-center space-x-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>Using cached prices - Live data unavailable</span>
            </div>
          ) : null}
          {displayData.map(item => (
            <CryptoTickerItem
              key={item.symbol}
              symbol={item.symbol}
              price={item.price}
              change24h={item.change24h}
              isLive={item.isLive}
            />
          ))}
        </div>

        {/* Mobile - Show summary with horizontal scroll for top items */}
        <div className="md:hidden">
          <div className="flex overflow-x-auto scrollbar-hide p-2 space-x-2">
            {loading ? (
              <div className="flex items-center justify-center space-x-2 w-full py-2">
                <div className="w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                <span className="text-xs text-arena-gray-400">Loading...</span>
              </div>
            ) : (
              displayData.slice(0, 3).map(item => (
                <div key={item.symbol} className="flex-shrink-0 px-3 py-2 border border-arena-gray-800 rounded bg-gray-900/50">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-arena-gray-400">{item.symbol}</span>
                    <span className="text-xs font-bold text-white tabular-nums">
                      ${item.price.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                    </span>
                    {item.change24h !== undefined && (
                      <span className={`text-xs font-semibold ${item.change24h > 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {item.change24h > 0 ? '+' : ''}{item.change24h.toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
