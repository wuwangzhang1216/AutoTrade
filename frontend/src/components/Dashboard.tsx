import { useState } from 'react'
import { Tab } from '@headlessui/react'
import clsx from 'clsx'
import { BriefcaseIcon, ChartBarIcon, CpuChipIcon } from '@heroicons/react/24/solid'
import AccountSummary from './AccountSummary'
import PositionsList from './PositionsList'
import TradeHistory from './TradeHistory'
import AIDecisionsList from './AIDecisionsList'
import TradingChartContainer from './TradingChartContainer'
import EquityChart from './EquityChart'
import ChartErrorBoundary from './ChartErrorBoundary'

export default function Dashboard() {
  const [selectedTab, setSelectedTab] = useState(0)

  const tabs = [
    { name: 'Positions', icon: BriefcaseIcon },
    { name: 'Trades', icon: ChartBarIcon },
    { name: 'AI Decisions', icon: CpuChipIcon },
  ]

  return (
    <div className="space-y-2">
      {/* Account Summary */}
      <AccountSummary />

      {/* Equity Chart and Tabbed Interface - Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-2 lg:items-start">
        {/* Equity Chart - Left Side (60%) */}
        <div className="lg:col-span-3">
          <ChartErrorBoundary>
            <EquityChart />
          </ChartErrorBoundary>
        </div>

        {/* Tabbed Interface - Right Side (40%) */}
        <div className="lg:col-span-2">
          <div className="card flex flex-col lg:max-h-[435px]">
            <Tab.Group selectedIndex={selectedTab} onChange={setSelectedTab}>
              <Tab.List className="flex space-x-0.5 rounded-lg bg-elite-975 p-0.5 mb-2 border border-primary-900/20">
                {tabs.map((tab) => (
                  <Tab
                    key={tab.name}
                    className={({ selected }) =>
                      clsx(
                        'w-full rounded-md py-1.5 text-xs font-semibold leading-5 transition-all duration-300',
                        'focus:outline-none focus:ring-2 focus:ring-primary-600/50',
                        selected
                          ? 'bg-gradient-gold text-black shadow-gold'
                          : 'text-silver-300 hover:bg-elite-950 hover:text-primary-300'
                      )
                    }
                  >
                    <tab.icon className="w-4 h-4 inline-block mr-1" />
                    {tab.name}
                  </Tab>
                ))}
              </Tab.List>

              <Tab.Panels className="flex-1 overflow-hidden min-h-0">
                <Tab.Panel className="h-full overflow-y-auto">
                  <PositionsList />
                </Tab.Panel>

                <Tab.Panel className="h-full overflow-y-auto">
                  <TradeHistory />
                </Tab.Panel>

                <Tab.Panel className="h-full overflow-y-auto">
                  <AIDecisionsList />
                </Tab.Panel>
              </Tab.Panels>
            </Tab.Group>
          </div>
        </div>
      </div>

      {/* Trading Chart */}
      <ChartErrorBoundary>
        <TradingChartContainer />
      </ChartErrorBoundary>
    </div>
  )
}
