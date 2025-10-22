import React, { useState } from 'react';

interface ServiceHealth {
  marketData: boolean;
  decisionEngine: boolean;
  tradingService: boolean;
  allHealthy: boolean;
}

interface Props {
  health: ServiceHealth;
  checking: boolean;
}

export const ServiceHealthIndicator: React.FC<Props> = ({ health, checking }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getStatusColor = (healthy: boolean) => {
    return healthy ? 'bg-green-500' : 'bg-red-500';
  };

  const getStatusText = (healthy: boolean) => {
    return healthy ? 'Online' : 'Offline';
  };

  return (
    <div className="mb-4">
      {/* Compact Status Bar */}
      <div
        className="flex items-center justify-between bg-gray-800 bg-opacity-50 backdrop-blur-sm border border-gray-700 rounded-lg px-4 py-2 cursor-pointer hover:bg-opacity-70 transition-all"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-3">
          <div className={`w-2 h-2 rounded-full ${getStatusColor(health.allHealthy)} ${health.allHealthy ? 'animate-pulse' : ''}`} />
          <span className="text-sm font-semibold">
            {checking ? 'Checking Services...' : health.allHealthy ? 'All Services Online' : 'Service Issues Detected'}
          </span>
        </div>
        <svg
          className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      {/* Expanded Service Details */}
      {isExpanded && (
        <div className="mt-2 bg-gray-800 bg-opacity-50 backdrop-blur-sm border border-gray-700 rounded-lg p-4 space-y-3">
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Service Status</h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Market Data Service */}
            <div className="flex items-center justify-between p-3 bg-gray-900 bg-opacity-50 rounded border border-gray-700">
              <div className="flex flex-col">
                <span className="text-xs text-gray-400">Market Data</span>
                <span className="text-sm font-semibold mt-1">Port 8001</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`text-xs font-bold ${health.marketData ? 'text-green-400' : 'text-red-400'}`}>
                  {getStatusText(health.marketData)}
                </span>
                <div className={`w-3 h-3 rounded-full ${getStatusColor(health.marketData)}`} />
              </div>
            </div>

            {/* Decision Engine */}
            <div className="flex items-center justify-between p-3 bg-gray-900 bg-opacity-50 rounded border border-gray-700">
              <div className="flex flex-col">
                <span className="text-xs text-gray-400">Decision Engine</span>
                <span className="text-sm font-semibold mt-1">Port 8002</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`text-xs font-bold ${health.decisionEngine ? 'text-green-400' : 'text-red-400'}`}>
                  {getStatusText(health.decisionEngine)}
                </span>
                <div className={`w-3 h-3 rounded-full ${getStatusColor(health.decisionEngine)}`} />
              </div>
            </div>

            {/* Trading Service */}
            <div className="flex items-center justify-between p-3 bg-gray-900 bg-opacity-50 rounded border border-gray-700">
              <div className="flex flex-col">
                <span className="text-xs text-gray-400">Trading Service</span>
                <span className="text-sm font-semibold mt-1">Port 8003</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`text-xs font-bold ${health.tradingService ? 'text-green-400' : 'text-red-400'}`}>
                  {getStatusText(health.tradingService)}
                </span>
                <div className={`w-3 h-3 rounded-full ${getStatusColor(health.tradingService)}`} />
              </div>
            </div>
          </div>

          {!health.allHealthy && (
            <div className="mt-3 p-3 bg-red-900 bg-opacity-20 border border-red-700 rounded">
              <p className="text-xs text-red-400">
                <strong>Note:</strong> Some services are offline. Please ensure Docker containers are running with <code className="bg-gray-900 px-1 py-0.5 rounded">docker-compose up -d</code>
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
