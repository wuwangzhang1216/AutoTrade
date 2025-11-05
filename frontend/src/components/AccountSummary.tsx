import { useEffect, useState } from 'react'
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon, ChartBarIcon, CurrencyDollarIcon, RocketLaunchIcon, TrophyIcon } from '@heroicons/react/24/solid'
import { fetchAccountStatus } from '../api/client'
import { BackgroundGradient } from './ui/background-gradient'
import { motion } from 'framer-motion'

interface AccountStatus {
  capital: number
  total_equity: number
  total_pnl: number
  total_pnl_percent: number
  unrealized_pnl: number
  open_positions: number
  total_trades: number
  win_rate: number
  winning_trades: number
  losing_trades: number
}

export default function AccountSummary() {
  const [account, setAccount] = useState<AccountStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadAccount = async () => {
      try {
        const data = await fetchAccountStatus()
        setAccount(data)
      } catch (error) {
        console.error('Failed to load account:', error)
      } finally {
        setLoading(false)
      }
    }

    loadAccount()
    const interval = setInterval(loadAccount, 5000) // Refresh every 5 seconds

    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <motion.div
          className="h-8 w-8 border-4 border-primary-600 border-t-transparent rounded-full"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
      </div>
    )
  }

  if (!account) {
    return <div className="card">No account data</div>
  }

  const isProfitable = account.total_pnl >= 0

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {/* Total Equity */}
      <BackgroundGradient className="rounded-[22px] p-[1px]">
        <motion.div
          className="bg-elite-950 rounded-[21px] p-4 relative overflow-hidden group"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          whileHover={{ y: -5 }}
        >
          <div className="absolute top-2 right-2 opacity-20 group-hover:opacity-40 transition-opacity">
            <ChartBarIcon className="w-16 h-16 text-primary-600" />
          </div>
          <h3 className="text-xs font-semibold text-silver-400 mb-2 tracking-wide uppercase relative z-10">
            Total Equity
          </h3>
          <p className="text-2xl font-bold text-white leading-tight relative z-10">
            ${account.total_equity.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
          <div className={`flex items-center mt-2 text-xs font-medium ${isProfitable ? 'text-green-400' : 'text-red-400'} relative z-10`}>
            {isProfitable ? (
              <ArrowTrendingUpIcon className="w-4 h-4 mr-1" />
            ) : (
              <ArrowTrendingDownIcon className="w-4 h-4 mr-1" />
            )}
            <span className="px-2 py-1 rounded-full bg-black/60 border border-current/30 backdrop-blur-sm">
              {isProfitable ? '+' : ''}${account.total_pnl.toFixed(2)} ({account.total_pnl_percent.toFixed(2)}%)
            </span>
          </div>
        </motion.div>
      </BackgroundGradient>

      {/* Available Capital */}
      <BackgroundGradient className="rounded-[22px] p-[1px]">
        <motion.div
          className="bg-elite-950 rounded-[21px] p-4 relative overflow-hidden group"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          whileHover={{ y: -5 }}
        >
          <div className="absolute top-2 right-2 opacity-20 group-hover:opacity-40 transition-opacity">
            <CurrencyDollarIcon className="w-16 h-16 text-primary-600" />
          </div>
          <h3 className="text-xs font-semibold text-silver-400 mb-2 tracking-wide uppercase relative z-10">
            Available Capital
          </h3>
          <p className="text-2xl font-bold text-white leading-tight relative z-10">
            ${account.capital.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
          <p className="text-xs text-silver-400 mt-2 px-2 py-1 rounded-lg bg-black/60 inline-block backdrop-blur-sm relative z-10">
            Unrealized: <span className="text-primary-400 font-semibold">${account.unrealized_pnl.toFixed(2)}</span>
          </p>
        </motion.div>
      </BackgroundGradient>

      {/* Open Positions */}
      <BackgroundGradient className="rounded-[22px] p-[1px]">
        <motion.div
          className="bg-elite-950 rounded-[21px] p-4 relative overflow-hidden group"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          whileHover={{ y: -5 }}
        >
          <div className="absolute top-2 right-2 opacity-20 group-hover:opacity-40 transition-opacity">
            <RocketLaunchIcon className="w-16 h-16 text-primary-600" />
          </div>
          <h3 className="text-xs font-semibold text-silver-400 mb-2 tracking-wide uppercase relative z-10">
            Open Positions
          </h3>
          <p className="text-2xl font-bold bg-gradient-gold bg-clip-text text-transparent leading-tight relative z-10">
            {account.open_positions}
          </p>
          <p className="text-xs text-silver-400 mt-2 relative z-10">Active trades</p>
        </motion.div>
      </BackgroundGradient>

      {/* Win Rate */}
      <BackgroundGradient className="rounded-[22px] p-[1px]">
        <motion.div
          className="bg-elite-950 rounded-[21px] p-4 relative overflow-hidden group"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
          whileHover={{ y: -5 }}
        >
          <div className="absolute top-2 right-2 opacity-20 group-hover:opacity-40 transition-opacity">
            <TrophyIcon className="w-16 h-16 text-primary-600" />
          </div>
          <h3 className="text-xs font-semibold text-silver-400 mb-2 tracking-wide uppercase relative z-10">
            Win Rate
          </h3>
          <p className="text-2xl font-bold bg-gradient-gold bg-clip-text text-transparent leading-tight relative z-10">
            {account.win_rate.toFixed(1)}%
          </p>
          <p className="text-xs text-silver-400 mt-2 relative z-10">
            {account.winning_trades + account.losing_trades} completed ({account.winning_trades}W / {account.losing_trades}L)
          </p>
        </motion.div>
      </BackgroundGradient>
    </div>
  )
}
