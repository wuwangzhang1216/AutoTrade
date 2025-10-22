
import React, { useState } from 'react';
import { Header } from './components/Header';
import { ChartSection } from './components/ChartSection';
import { InfoSidebar } from './components/InfoSidebar';
import { ModelCards } from './components/ModelCards';
import { Leaderboard } from './components/Leaderboard';
import { AgentProfile } from './components/AgentProfile';
import { PortfolioView } from './components/PortfolioView';

type ViewType = 'dashboard' | 'leaderboard' | 'portfolio' | 'agent-profile';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewType>('dashboard');
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [previousView, setPreviousView] = useState<ViewType>('dashboard');

  const handleAgentSelect = (agentId: string) => {
    setPreviousView(currentView);
    setSelectedAgentId(agentId);
    setCurrentView('agent-profile');
  };

  const handleBackFromProfile = () => {
    setSelectedAgentId(null);
    setCurrentView(previousView);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 font-mono text-arena-gray-100">
      <div className="h-screen w-full max-w-[1600px] mx-auto flex flex-col px-2 py-2 sm:p-3 md:p-4 lg:p-6 overflow-x-hidden">
        <Header currentView={currentView} onViewChange={(view) => setCurrentView(view as ViewType)} />

        <main className="mt-2 sm:mt-3 md:mt-4 flex-1 overflow-y-auto pb-3 sm:pb-4 overflow-x-hidden">
          {currentView === 'dashboard' && (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 sm:gap-4 lg:gap-6">
                <div className="lg:col-span-2">
                  <ChartSection />
                </div>
                <div className="lg:col-span-1">
                  <InfoSidebar />
                </div>
              </div>
              <div className="mt-3 sm:mt-4 border-t border-arena-gray-800 pt-3 sm:pt-4">
                <ModelCards onModelSelect={handleAgentSelect} />
              </div>
            </>
          )}

          {currentView === 'leaderboard' && <Leaderboard onAgentSelect={handleAgentSelect} />}

          {currentView === 'agent-profile' && selectedAgentId && (
            <AgentProfile agentId={selectedAgentId} onBack={handleBackFromProfile} previousView={previousView} />
          )}

          {currentView === 'portfolio' && <PortfolioView onAgentSelect={handleAgentSelect} />}
        </main>
      </div>
    </div>
  );
};

export default App;
