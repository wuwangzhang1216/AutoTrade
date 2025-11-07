import { useEffect, useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { Tab } from '@headlessui/react'
import clsx from 'clsx'
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/solid'
import { fetchMarketEvents, fetchMarketEventsStats } from '../api/client'
import { useWebSocket } from '../hooks/useWebSocket'
import { getWebSocketURL } from '../config/api'
import { motion, AnimatePresence } from 'framer-motion'

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
const severityConfig: Record<string, { bg: string; border: string; text: string; icon: string; badge: string }> = {
  critical: {
    bg: 'bg-red-950/20',
    border: 'border-l-4 border-red-500',
    text: 'text-red-400',
    icon: '🔴',
    badge: 'bg-red-500/20 text-red-400 border-red-500/50'
  },
  high: {
    bg: 'bg-orange-950/20',
    border: 'border-l-4 border-orange-500',
    text: 'text-orange-400',
    icon: '🚨',
    badge: 'bg-orange-500/20 text-orange-400 border-orange-500/50'
  },
  medium: {
    bg: 'bg-yellow-950/20',
    border: 'border-l-4 border-yellow-500',
    text: 'text-yellow-400',
    icon: '⚠️',
    badge: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50'
  },
  low: {
    bg: 'bg-blue-950/20',
    border: 'border-l-4 border-blue-500',
    text: 'text-blue-400',
    icon: 'ℹ️',
    badge: 'bg-blue-500/20 text-blue-400 border-blue-500/50'
  }
}

export default function MarketEventsPanel() {
  const [events, setEvents] = useState<MarketEvent[]>([])
  const [stats, setStats] = useState<MarketEventsStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedFilter, setSelectedFilter] = useState(0)
  const [expandedEvent, setExpandedEvent] = useState<number | null>(null)
  const [latestEventId, setLatestEventId] = useState<number | null>(null)
  const { lastMessage } = useWebSocket(getWebSocketURL())

  // 过滤器配置
  const filters = [
    { name: 'All', value: null },
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
        // 检查是否已存在（避免重复）
        const exists = prevEvents.some(e => e.id === newEvent.id)
        if (exists) {
          return prevEvents
        }

        // 添加到顶部并高亮
        setLatestEventId(newEvent.id)

        // 5秒后移除高亮
        setTimeout(() => {
          setLatestEventId(null)
        }, 5000)

        // 保留最多50条
        return [newEvent, ...prevEvents].slice(0, 50)
      })

      // 更新统计（简单计数）
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
    if (!filter.types) return true // "All" filter
    return filter.types.includes(event.event_type)
  })

  if (loading) {
    return (
      <div className="card">
        <div className="flex items-center justify-center p-8">
          <motion.div
            className="h-8 w-8 border-4 border-primary-600 border-t-transparent rounded-full"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          />
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
      <div className="space-y-2 overflow-y-auto" style={{ maxHeight: '400px' }}>
        <AnimatePresence>
          {filteredEvents.length === 0 ? (
            <div className="text-center py-8 text-silver-400">
              <p className="text-sm">📊 No events detected</p>
              <p className="text-xs mt-1">System is monitoring market...</p>
            </div>
          ) : (
            filteredEvents.map((event) => (
              <EventItem
                key={event.id}
                event={event}
                isLatest={event.id === latestEventId}
                isExpanded={expandedEvent === event.id}
                onToggleExpand={() => setExpandedEvent(expandedEvent === event.id ? null : event.id)}
              />
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

// 单个事件组件
function EventItem({
  event,
  isLatest,
  isExpanded,
  onToggleExpand
}: {
  event: MarketEvent
  isLatest: boolean
  isExpanded: boolean
  onToggleExpand: () => void
}) {
  const config = severityConfig[event.severity] || severityConfig.low
  const timeAgo = formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })

  return (
    <motion.div
      initial={{ x: 100, opacity: 0 }}
      animate={{
        x: 0,
        opacity: 1,
        boxShadow: isLatest && event.severity === 'critical'
          ? [
              '0 0 0px rgba(239, 68, 68, 0)',
              '0 0 20px rgba(239, 68, 68, 0.6)',
              '0 0 0px rgba(239, 68, 68, 0)',
            ]
          : 'none'
      }}
      exit={{ x: -100, opacity: 0 }}
      transition={{
        duration: 0.3,
        boxShadow: {
          duration: 2,
          repeat: event.severity === 'critical' ? Infinity : 0
        }
      }}
      className={clsx(
        'rounded-lg p-3',
        config.bg,
        config.border,
        'hover:bg-opacity-40 transition-all duration-200 cursor-pointer'
      )}
      onClick={onToggleExpand}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-1">
        <div className="flex items-center space-x-2">
          <span className="text-base">{config.icon}</span>
          <span className="text-xs text-silver-400">{timeAgo}</span>
        </div>
        <span className={clsx(
          'px-2 py-0.5 rounded-full text-xs font-medium border',
          config.badge
        )}>
          {event.severity.toUpperCase()}
        </span>
      </div>

      {/* Event Info */}
      <div className="flex items-center space-x-2 mb-1">
        <span className="font-bold text-white text-sm">{event.symbol}</span>
        <span className="text-silver-500 text-xs">•</span>
        <span className="text-silver-300 text-xs">{eventTypeLabels[event.event_type] || event.event_type}</span>
      </div>

      {/* Description */}
      <p className="text-sm text-silver-200 mb-2">{event.description}</p>

      {/* Suggested Action */}
      {event.suggested_action && (
        <div className="flex items-start space-x-1 text-xs text-silver-400 mb-2">
          <span>💡</span>
          <span>{event.suggested_action}</span>
        </div>
      )}

      {/* Expand/Collapse Metrics */}
      {Object.keys(event.metrics || {}).length > 0 && (
        <div className="mt-2">
          <button
            onClick={(e) => {
              e.stopPropagation()
              onToggleExpand()
            }}
            className="flex items-center space-x-1 text-xs text-primary-400 hover:text-primary-300 transition-colors"
          >
            <span>View Details</span>
            {isExpanded ? (
              <ChevronUpIcon className="w-3 h-3" />
            ) : (
              <ChevronDownIcon className="w-3 h-3" />
            )}
          </button>

          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="mt-2 p-2 rounded bg-black/40 overflow-hidden"
              >
                <pre className="text-xs text-silver-300 font-mono overflow-x-auto">
                  {JSON.stringify(event.metrics, null, 2)}
                </pre>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </motion.div>
  )
}
