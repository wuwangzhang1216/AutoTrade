import { useEffect, useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { Tab, Disclosure } from '@headlessui/react'
import clsx from 'clsx'
import { ChevronUpIcon } from '@heroicons/react/24/solid'
import { fetchMarketEvents, fetchMarketEventsStats } from '../api/client'
import { useWebSocket } from '../hooks/useWebSocket'
import { getWebSocketURL } from '../config/api'

interface MarketEvent {
  id: number
  timestamp: string
  symbol: string
  event_type: string
  severity: string
  description: string
  suggested_action: string | null
  metrics: Record<string, any>
}

interface MarketEventsStats {
  total_events: number
  events_by_severity: Record<string, number>
  events_by_type: Record<string, number>
}

// 事件类型标签映射
const eventTypeLabels: Record<string, string> = {
  flash_crash: 'Flash Crash',
  flash_rally: 'Flash Rally',
  volume_spike: 'Volume Spike',
  volume_dry: 'Volume Dry',
  volatility_spike: 'Volatility Spike',
  liquidation_risk: 'Liquidation Risk',
}

// 严重程度配置
const severityConfig: Record<string, { border: string; icon: string; badge: string }> = {
  critical: {
    border: 'border-2 border-red-500',
    icon: '🔴',
    badge: 'bg-red-500/20 text-red-400 border-red-500/50'
  },
  high: {
    border: 'border border-orange-500/50',
    icon: '🚨',
    badge: 'bg-orange-500/20 text-orange-400 border-orange-500/50'
  },
  medium: {
    border: 'border border-yellow-500/50',
    icon: '⚠️',
    badge: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50'
  },
  low: {
    border: 'border border-blue-500/50',
    icon: 'ℹ️',
    badge: 'bg-blue-500/20 text-blue-400 border-blue-500/50'
  }
}

export default function MarketEventsPanel() {
  const [events, setEvents] = useState<MarketEvent[]>([])
  const [stats, setStats] = useState<MarketEventsStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedFilter, setSelectedFilter] = useState(0)
  const [latestEventId, setLatestEventId] = useState<number | null>(null)
  const { lastMessage } = useWebSocket(getWebSocketURL())

  // 过滤器配置
  const filters = [
    { name: 'All', types: undefined },
    { name: 'Flash Moves', types: ['flash_crash', 'flash_rally'] },
    { name: 'Volume', types: ['volume_spike', 'volume_dry'] },
    { name: 'Volatility', types: ['volatility_spike'] },
    { name: 'Liquidation', types: ['liquidation_risk'] },
  ]

  // 加载初始数据
  useEffect(() => {
    const loadData = async () => {
      try {
        const [eventsData, statsData] = await Promise.all([
          fetchMarketEvents(10),
          fetchMarketEventsStats()
        ])
        setEvents(eventsData)
        setStats(statsData)
      } catch (error) {
        console.error('Failed to load market events:', error)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  // WebSocket 实时更新
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'market_event') {
      const newEvent = lastMessage.data as MarketEvent

      setEvents(prevEvents => {
        const exists = prevEvents.some(e => e.id === newEvent.id)
        if (exists) return prevEvents

        setLatestEventId(newEvent.id)
        setTimeout(() => setLatestEventId(null), 5000)

        return [newEvent, ...prevEvents].slice(0, 50)
      })

      setStats(prev => {
        if (!prev) return null
        return {
          ...prev,
          total_events: prev.total_events + 1,
          events_by_severity: {
            ...prev.events_by_severity,
            [newEvent.severity]: (prev.events_by_severity[newEvent.severity] || 0) + 1
          },
          events_by_type: {
            ...prev.events_by_type,
            [newEvent.event_type]: (prev.events_by_type[newEvent.event_type] || 0) + 1
          }
        }
      })
    }
  }, [lastMessage])

  // 过滤事件
  const filteredEvents = events.filter(event => {
    const filter = filters[selectedFilter]
    if (!filter.types) return true
    return filter.types.includes(event.event_type)
  })

  if (loading) {
    return (
      <div className="card">
        <div className="flex items-center justify-center p-12">
          <div className="flex flex-col items-center gap-3">
            <div className="relative">
              <div className="w-12 h-12 rounded-full border-2 border-primary-900/20"></div>
              <div className="absolute inset-0 w-12 h-12 rounded-full border-2 border-transparent border-t-primary-500 animate-spin"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-3 h-3 rounded-full bg-primary-500 animate-pulse"></div>
              </div>
            </div>
            <div className="text-sm text-primary-400 font-medium flex items-center gap-1">
              <span>Loading events</span>
              <span className="flex gap-0.5">
                <span className="animate-bounce" style={{ animationDelay: '0ms' }}>.</span>
                <span className="animate-bounce" style={{ animationDelay: '150ms' }}>.</span>
                <span className="animate-bounce" style={{ animationDelay: '300ms' }}>.</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <span className="text-lg font-bold text-white">🔔 Market Events Monitor</span>
          {stats && (
            <span className="text-xs text-silver-400">
              Last 24h: {stats.total_events}
            </span>
          )}
        </div>

        {/* Severity badges */}
        {stats && (
          <div className="flex items-center space-x-2 text-xs">
            <span className="px-2 py-1 rounded-full bg-red-500/20 text-red-400 border border-red-500/50">
              🔴 {stats.events_by_severity.critical || 0}
            </span>
            <span className="px-2 py-1 rounded-full bg-orange-500/20 text-orange-400 border border-orange-500/50">
              🚨 {stats.events_by_severity.high || 0}
            </span>
            <span className="px-2 py-1 rounded-full bg-yellow-500/20 text-yellow-400 border border-yellow-500/50">
              ⚠️ {stats.events_by_severity.medium || 0}
            </span>
            <span className="px-2 py-1 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/50">
              ℹ️ {stats.events_by_severity.low || 0}
            </span>
          </div>
        )}
      </div>

      {/* Filter Tabs */}
      <Tab.Group selectedIndex={selectedFilter} onChange={setSelectedFilter}>
        <Tab.List className="flex space-x-0.5 rounded-lg bg-elite-975 p-0.5 mb-3 border border-primary-900/20">
          {filters.map((filter) => (
            <Tab
              key={filter.name}
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
              {filter.name}
            </Tab>
          ))}
        </Tab.List>
      </Tab.Group>

      {/* Events List */}
      {filteredEvents.length === 0 ? (
        <div className="text-center py-12 text-silver-400 bg-elite-975 rounded-lg border border-primary-900/20">
          <p className="text-sm">📊 No events detected</p>
          <p className="text-xs mt-1">System is monitoring market...</p>
        </div>
      ) : (
        <div className="space-y-1.5 overflow-y-auto max-h-[400px] pr-2 custom-scrollbar">
          {filteredEvents.map((event) => (
            <EventItem
              key={event.id}
              event={event}
              isLatest={event.id === latestEventId}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// 单个事件组件
function EventItem({ event, isLatest }: { event: MarketEvent; isLatest: boolean }) {
  const config = severityConfig[event.severity] || severityConfig.low
  const timeAgo = formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })

  return (
    <Disclosure>
      {({ open }) => (
        <>
          <Disclosure.Button
            className={clsx(
              'flex flex-col w-full rounded-lg px-2.5 py-2 text-left text-xs',
              'hover:bg-elite-950 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-600 focus-visible:ring-opacity-75',
              'transition-all duration-300',
              isLatest
                ? 'bg-primary-900/30 border-2 border-primary-500 shadow-[0_0_20px_rgba(212,175,55,0.3)] animate-pulse-slow'
                : clsx('bg-elite-975', config.border)
            )}
          >
            {/* Header */}
            <div className="flex items-center justify-between w-full mb-1">
              <div className="flex items-center space-x-2">
                <span className="text-base">{config.icon}</span>
                <span className="text-silver-400 text-[10px]">{timeAgo}</span>
                <span className="font-bold text-white text-xs">{event.symbol}</span>
                <span className={clsx('px-1.5 py-0.5 rounded-full text-[10px] font-medium border', config.badge)}>
                  {event.severity.toUpperCase()}
                </span>
              </div>
              <ChevronUpIcon
                className={`${open ? 'rotate-180 transform' : ''} h-3 w-3 text-primary-400 transition-transform flex-shrink-0`}
              />
            </div>

            {/* Event Type */}
            <div className="flex items-center space-x-2 mb-1">
              <span className="text-silver-400 text-[10px]">Type:</span>
              <span className="text-primary-400 font-semibold text-[10px]">
                {eventTypeLabels[event.event_type] || event.event_type}
              </span>
            </div>

            {/* Description */}
            <p className="text-silver-200 text-xs leading-snug mb-1">{event.description}</p>

            {/* Suggested Action */}
            {event.suggested_action && (
              <div className="flex items-start space-x-1 text-[10px] text-silver-400">
                <span>💡</span>
                <span>{event.suggested_action}</span>
              </div>
            )}
          </Disclosure.Button>

          {Object.keys(event.metrics || {}).length > 0 && (
            <Disclosure.Panel className="px-2.5 pt-2 pb-2 text-xs text-silver-200 bg-elite-950/80 rounded-lg mt-1 border border-primary-900/10 backdrop-blur-sm">
              <div className="bg-black/30 rounded-lg p-2 border border-primary-900/20">
                <h4 className="font-bold text-primary-400 mb-2 text-xs">Event Metrics</h4>
                <pre className="text-[10px] text-silver-300 font-mono overflow-x-auto leading-relaxed">
                  {JSON.stringify(event.metrics, null, 2)}
                </pre>
              </div>
            </Disclosure.Panel>
          )}
        </>
      )}
    </Disclosure>
  )
}
