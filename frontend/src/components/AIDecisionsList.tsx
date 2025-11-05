import { useEffect, useState } from 'react'
import { format } from 'date-fns'
import { Disclosure } from '@headlessui/react'
import { ChevronUpIcon, SparklesIcon, CpuChipIcon } from '@heroicons/react/24/solid'
import { fetchAIDecisions, fetchAIDecisionDetail } from '../api/client'
import { useWebSocket } from '../hooks/useWebSocket'
import { getWebSocketURL } from '../config/api'

interface AIDecisionSummary {
  id: number
  timestamp: string
  symbol: string
  model_1_decision: string
  model_1_confidence: number
  model_2_decision: string
  model_2_confidence: number
  final_decision: string
  executed: boolean
}

interface AIDecisionDetail extends AIDecisionSummary {
  model_1_reasoning: string
  model_2_reasoning: string
}

export default function AIDecisionsList() {
  const [decisions, setDecisions] = useState<AIDecisionSummary[]>([])
  const [decisionDetails, setDecisionDetails] = useState<Map<number, AIDecisionDetail>>(new Map())
  const [loadingDetails, setLoadingDetails] = useState<Set<number>>(new Set())
  const [loading, setLoading] = useState(true)
  const [latestDecisionId, setLatestDecisionId] = useState<number | null>(null)
  const { lastMessage } = useWebSocket(getWebSocketURL())

  // PERFORMANCE: Lazy load decision details (with reasoning) only when expanded
  const loadDecisionDetail = async (decisionId: number) => {
    // Already loaded or loading
    if (decisionDetails.has(decisionId) || loadingDetails.has(decisionId)) {
      return
    }

    setLoadingDetails(prev => new Set(prev).add(decisionId))

    try {
      const detail = await fetchAIDecisionDetail(decisionId)
      setDecisionDetails(prev => new Map(prev).set(decisionId, detail))
    } catch (error) {
      console.error('Failed to load decision detail:', error)
    } finally {
      setLoadingDetails(prev => {
        const next = new Set(prev)
        next.delete(decisionId)
        return next
      })
    }
  }

  // Handle WebSocket messages for real-time AI decisions
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'ai_decision') {
      const newDecision = lastMessage.data as AIDecisionSummary

      // Add new decision to the top of the list
      setDecisions(prevDecisions => {
        // Check if decision already exists to avoid duplicates
        const exists = prevDecisions.some(d => d.id === newDecision.id)
        if (exists) {
          return prevDecisions
        }

        // Add to top and highlight
        setLatestDecisionId(newDecision.id)

        // Remove highlight after 5 seconds
        setTimeout(() => {
          setLatestDecisionId(null)
        }, 5000)

        return [newDecision, ...prevDecisions].slice(0, 50) // Keep only latest 50
      })
    }
  }, [lastMessage])

  useEffect(() => {
    const loadDecisions = async () => {
      try {
        const data = await fetchAIDecisions(1, 30)  // page=1, per_page=30
        setDecisions(data)
      } catch (error) {
        console.error('Failed to load AI decisions:', error)
      } finally {
        setLoading(false)
      }
    }

    loadDecisions()
    // PERFORMANCE: Reduced polling from 30s to 60s (WebSocket handles real-time updates)
    const interval = setInterval(loadDecisions, 60000)

    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="relative space-y-1.5 overflow-hidden">
        {/* Skeleton Cards */}
        {[...Array(6)].map((_, i) => (
          <div key={i} className="rounded-lg px-2.5 py-2 bg-elite-975/50 border border-primary-900/20 animate-pulse" style={{ animationDelay: `${i * 80}ms` }}>
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center space-x-2 flex-1">
                <div className="h-3 w-20 bg-primary-900/20 rounded"></div>
                <div className="h-3 w-16 bg-primary-900/20 rounded"></div>
                <div className="h-3 w-12 bg-primary-900/20 rounded"></div>
              </div>
              <div className="h-3 w-3 bg-primary-900/20 rounded"></div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="h-2.5 w-24 bg-primary-900/10 rounded"></div>
              <div className="h-2.5 w-24 bg-primary-900/10 rounded"></div>
            </div>
          </div>
        ))}

        {/* Loading Overlay with Animation */}
        <div className="absolute inset-0 bg-elite-975/80 backdrop-blur-sm flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="relative">
              {/* Spinning outer ring */}
              <div className="w-12 h-12 rounded-full border-2 border-primary-900/20"></div>
              <div className="absolute inset-0 w-12 h-12 rounded-full border-2 border-transparent border-t-primary-500 animate-spin"></div>

              {/* Pulsing inner dot */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-3 h-3 rounded-full bg-primary-500 animate-pulse"></div>
              </div>
            </div>

            {/* Loading text with dots animation */}
            <div className="text-sm text-primary-400 font-medium flex items-center gap-1">
              <span>Loading AI decisions</span>
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

  if (decisions.length === 0) {
    return (
      <div className="text-center py-12 text-silver-400 bg-elite-975 rounded-lg border border-primary-900/20">
        No AI decisions yet
      </div>
    )
  }

  return (
    <div className="space-y-1.5 overflow-y-auto max-h-[365px] pr-2 custom-scrollbar">
      {decisions.map((decision) => {
        const isLatest = decision.id === latestDecisionId
        const detail = decisionDetails.get(decision.id)
        const isLoadingDetail = loadingDetails.has(decision.id)

        return (
          <Disclosure key={decision.id}>
            {({ open }) => {
              // Load details when expanded
              if (open && !detail && !isLoadingDetail) {
                loadDecisionDetail(decision.id)
              }

              return (
              <>
                <Disclosure.Button className={`flex flex-col w-full rounded-lg px-2.5 py-2 text-left text-xs font-semibold text-white hover:bg-elite-950 hover:shadow-premium focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-600 focus-visible:ring-opacity-75 transition-all duration-300 ${
                  isLatest
                    ? 'bg-primary-900/30 border-2 border-primary-500 shadow-[0_0_20px_rgba(212,175,55,0.3)] animate-pulse-slow'
                    : 'bg-elite-975 border border-primary-900/20'
                }`}>
                <div className="flex items-center justify-between w-full mb-1">
                  <div className="flex items-center space-x-2">
                    {isLatest && (
                      <SparklesIcon className="h-3 w-3 text-primary-400 animate-pulse" />
                    )}
                    <span className="text-silver-400 font-medium text-[10px]">
                      {format(new Date(decision.timestamp), 'MMM dd, HH:mm:ss')}
                    </span>
                    <span className="font-bold text-white text-xs">{decision.symbol}</span>
                    <span className={`badge ${
                      decision.final_decision === 'BUY' ? 'badge-success' :
                      decision.final_decision === 'SELL' ? 'badge-danger' :
                      'badge-warning'
                    }`}>
                      {decision.final_decision}
                    </span>
                    {decision.executed && (
                      <span className="badge badge-info">EXEC</span>
                    )}
                  </div>
                  <ChevronUpIcon
                    className={`${open ? 'rotate-180 transform' : ''} h-3 w-3 text-primary-400 transition-transform flex-shrink-0`}
                  />
                </div>
                <div className="flex items-center space-x-2 text-[10px] text-silver-400">
                  <span>M1: <span className="text-primary-400 font-semibold">{decision.model_1_decision}</span> ({(decision.model_1_confidence * 100).toFixed(0)}%)</span>
                  <span className="text-primary-900">|</span>
                  <span>M2: <span className="text-primary-400 font-semibold">{decision.model_2_decision}</span> ({(decision.model_2_confidence * 100).toFixed(0)}%)</span>
                </div>
              </Disclosure.Button>
              <Disclosure.Panel className="px-2.5 pt-2 pb-2 text-xs text-silver-200 bg-elite-950/80 rounded-lg mt-1.5 border border-primary-900/10 backdrop-blur-sm">
                {isLoadingDetail ? (
                  <div className="text-center py-4 text-silver-400 text-xs">
                    Loading details...
                  </div>
                ) : detail ? (
                  <div className="grid grid-cols-1 gap-2">
                    {/* Model 1 */}
                    <div className="bg-black/30 rounded-lg p-2.5 border border-primary-900/20">
                      <h4 className="font-bold text-primary-400 mb-1.5 text-xs flex items-center">
                        <CpuChipIcon className="w-4 h-4 mr-1.5" />
                        Model 1 (DeepSeek)
                      </h4>
                      <div className="space-y-1.5">
                        <div className="flex items-center space-x-2">
                          <span className="text-silver-400 text-[10px] uppercase tracking-wide">Decision:</span>
                          <span className={`badge ${
                            detail.model_1_decision === 'BUY' ? 'badge-success' :
                            detail.model_1_decision === 'SELL' ? 'badge-danger' :
                            'badge-warning'
                          }`}>
                            {detail.model_1_decision}
                          </span>
                          <span className="text-silver-400 text-[10px]">Conf:</span>
                          <span className="text-white font-semibold text-[10px]">
                            {(detail.model_1_confidence * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div>
                          <span className="text-silver-400 text-[10px] uppercase tracking-wide block mb-0.5">Reasoning:</span>
                          <p className="text-white text-[11px] leading-snug bg-black/20 p-2 rounded border border-primary-900/10">
                            {detail.model_1_reasoning || 'No reasoning provided'}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Model 2 */}
                    <div className="bg-black/30 rounded-lg p-2.5 border border-primary-900/20">
                      <h4 className="font-bold text-primary-400 mb-1.5 text-xs flex items-center">
                        <CpuChipIcon className="w-4 h-4 mr-1.5" />
                        Model 2 (Qwen)
                      </h4>
                      <div className="space-y-1.5">
                        <div className="flex items-center space-x-2">
                          <span className="text-silver-400 text-[10px] uppercase tracking-wide">Decision:</span>
                          <span className={`badge ${
                            detail.model_2_decision === 'BUY' ? 'badge-success' :
                            detail.model_2_decision === 'SELL' ? 'badge-danger' :
                            'badge-warning'
                          }`}>
                            {detail.model_2_decision}
                          </span>
                          <span className="text-silver-400 text-[10px]">Conf:</span>
                          <span className="text-white font-semibold text-[10px]">
                            {(detail.model_2_confidence * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div>
                          <span className="text-silver-400 text-[10px] uppercase tracking-wide block mb-0.5">Reasoning:</span>
                          <p className="text-white text-[11px] leading-snug bg-black/20 p-2 rounded border border-primary-900/10">
                            {detail.model_2_reasoning || 'No reasoning provided'}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-2 text-silver-400 text-xs">
                    Click to view details
                  </div>
                )}
              </Disclosure.Panel>
              </>
              )
            }}
          </Disclosure>
        )
      })}
    </div>
  )
}
