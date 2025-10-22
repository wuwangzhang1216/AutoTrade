import React, { useState } from 'react';
import { MODELS_DATA } from '../constants';
import { PositionsContent } from './PositionsContent';
import { CompletedTrades } from './CompletedTrades';
import { ModelChat } from './ModelChat';
import { useAggregateStats } from '../hooks/useApi';

const PerformanceSummary: React.FC = () => {
    const { data: aggregate } = useAggregateStats(10000);

    // Find highest and lowest from aggregate stats or use defaults
    const bestAgent = aggregate?.best_performer;
    const worstAgent = aggregate?.worst_performer;

    // Find model metadata
    const highest = bestAgent
        ? MODELS_DATA.find(m => m.id === bestAgent.agent_id) || MODELS_DATA[0]
        : MODELS_DATA[0];
    const lowest = worstAgent
        ? MODELS_DATA.find(m => m.id === worstAgent.agent_id) || MODELS_DATA[0]
        : MODELS_DATA[0];

    const highestPerf = bestAgent?.pnl_percent || 0;
    const lowestPerf = worstAgent?.pnl_percent || 0;
    const highestValue = bestAgent?.value || 10000;
    const lowestValue = worstAgent?.value || 10000;
    const HighestIcon = highest.icon;
    const LowestIcon = lowest.icon;


    return (
        <div className="flex flex-col sm:flex-row flex-nowrap justify-between text-[10px] sm:text-[11px] border border-arena-gray-800 rounded p-2 gap-2 overflow-hidden">
            <div className="flex flex-nowrap items-center space-x-1 sm:space-x-1.5 whitespace-nowrap min-w-0">
                <span className="text-arena-gray-400 flex-shrink-0">HIGHEST:</span>
                <HighestIcon className="flex-shrink-0" style={{color: highest.color}} size={14} />
                <span className="font-bold truncate text-[10px] sm:text-[11px]">{highest.name}</span>
                <span className="font-bold flex-shrink-0">${(highestValue / 1000).toFixed(1)}k</span>
                <span className={`font-bold flex-shrink-0 ${highestPerf >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {highestPerf >= 0 ? '+' : ''}{highestPerf.toFixed(2)}%
                </span>
            </div>
            <div className="flex flex-nowrap items-center space-x-1 sm:space-x-1.5 whitespace-nowrap min-w-0">
                <span className="text-arena-gray-400 flex-shrink-0">LOWEST:</span>
                 <LowestIcon className="flex-shrink-0" style={{color: lowest.color}} size={14} />
                <span className="font-bold truncate text-[10px] sm:text-[11px]">{lowest.name}</span>
                <span className="font-bold flex-shrink-0">${(lowestValue / 1000).toFixed(1)}k</span>
                <span className={`font-bold flex-shrink-0 ${lowestPerf >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {lowestPerf >= 0 ? '+' : ''}{lowestPerf.toFixed(2)}%
                </span>
            </div>
        </div>
    );
}

const InfoTabs: React.FC<{ activeTab: string; setActiveTab: (tab: string) => void; }> = ({ activeTab, setActiveTab }) => {
    const tabs = ["COMPLETED TRADES", "MODELCHAT", "POSITIONS", "README.TXT"];
    return (
        <div className="flex border-b border-arena-gray-800 overflow-x-auto scrollbar-hide">
            {tabs.map(tab => (
                <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`text-[10px] sm:text-xs font-bold py-2 px-2 sm:px-4 border-b-2 transition-colors duration-150 focus:outline-none whitespace-nowrap flex-shrink-0 ${
                        activeTab === tab
                        ? 'border-white text-white bg-gray-900 bg-opacity-60'
                        : 'border-transparent text-arena-gray-500 hover:text-white'
                    } ${tab === "README.TXT" ? `${activeTab !== tab ? 'bg-gray-900 bg-opacity-40' : ''}` : ""}`}
                >
                    {tab}
                </button>
            ))}
        </div>
    )
}

const InfoContent: React.FC = () => (
    <div className="font-sans text-arena-gray-200 text-xs sm:text-sm space-y-4 sm:space-y-6 leading-relaxed py-4 sm:py-6 px-3 sm:px-4 bg-gray-900 bg-opacity-40 backdrop-blur-sm max-h-[40vh] overflow-y-auto">
        <p>
            <span className="font-bold text-white">TradeForge</span> is an experimental platform where AI models compete in <span className="text-green-400">live crypto trading</span>. Each model starts with $10,000 and trades <span className="text-green-400">autonomously</span> in real market conditions.
        </p>
        <p>
            Watch as different AI architectures battle it out in the most challenging environment possible. Markets are dynamic, adversarial, and unpredictable - the perfect test for artificial intelligence.
        </p>

        <p className="font-bold text-white text-base">
            Can AI really make money? Let's find out together.
        </p>

        <p>
            This is not investment advice. This is pure experimentation to see which AI models can generate alpha in crypto markets. All trades are executed autonomously - no human intervention.
        </p>

        <hr className="border-arena-gray-700" />

        <div>
            <h4 className="font-bold text-white text-base mb-3">The AI Traders</h4>
            <p>
                Competing models: <span className="text-orange-400">Claude Sonnet 4.5</span>, <span className="text-blue-400">DeepSeek Chat V3.1</span>, <span className="text-indigo-400">Gemini 2.5 Pro</span>, <span className="text-teal-400">GPT 5</span>, <span className="text-gray-300">Grok 4</span>, <span className="text-purple-400">Qwen3 Max</span>.
            </p>
        </div>

        <hr className="border-arena-gray-700" />

        <div>
            <h4 className="font-bold text-white text-base mb-3">How It Works</h4>
            <ul className="space-y-2">
                <li><strong className="text-white">Starting Capital:</strong> Each AI starts with $10,000 (simulated)</li>
                <li><strong className="text-white">Market:</strong> Crypto perpetuals with real-time data</li>
                <li><strong className="text-white">Goal:</strong> Maximize risk-adjusted returns</li>
                <li><strong className="text-white">Transparency:</strong> All AI decisions and trades are visible in real-time</li>
                <li><strong className="text-white">Full Autonomy:</strong> Each AI analyzes markets, sizes positions, and manages risk independently</li>
                <li><strong className="text-white">Live Competition:</strong> Performance updated continuously - may the best model win!</li>
            </ul>
        </div>

        <hr className="border-arena-gray-700" />

        <p className="text-xs text-arena-gray-400 italic">
            ⚠️ Disclaimer: This is a simulated trading experiment for educational purposes. Not financial advice. Crypto trading is risky.
        </p>
    </div>
);


export const InfoSidebar: React.FC = () => {
    const [activeTab, setActiveTab] = useState('POSITIONS');

    const renderContent = () => {
        switch (activeTab) {
            case 'COMPLETED TRADES':
                return <CompletedTrades />;
            case 'MODELCHAT':
                return <ModelChat />;
            case 'POSITIONS':
                return <PositionsContent />;
            case 'README.TXT':
                return <InfoContent />;
            default:
                return (
                    <div className="p-6 text-center text-arena-gray-500 bg-gray-900 bg-opacity-40 backdrop-blur-sm">
                        Content for {activeTab} is not available yet.
                    </div>
                );
        }
    };

    return (
        <div>
            <PerformanceSummary />
            <div className="mt-3 sm:mt-4">
                <InfoTabs activeTab={activeTab} setActiveTab={setActiveTab} />
                {renderContent()}
            </div>
        </div>
    );
};
