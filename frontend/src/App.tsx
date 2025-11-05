import Dashboard from './components/Dashboard'
import { useWebSocket } from './hooks/useWebSocket'
import { Spotlight } from './components/ui/spotlight'
import { GridBackground } from './components/ui/grid-background'
import { motion } from 'framer-motion'
import { getWebSocketURL } from './config/api'

function App() {
  const { isConnected } = useWebSocket(getWebSocketURL())

  return (
    <GridBackground className="min-h-screen">
      <div className="min-h-screen bg-black/80 relative overflow-hidden">
        {/* Spotlight effects */}
        <Spotlight className="-top-40 left-0 md:left-60 md:-top-20" fill="#eab308" />

        {/* Header */}
        <motion.header
          className="bg-elite-950/80 border-b border-primary-900/20 shadow-premium backdrop-blur-xl relative z-20"
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <div className="max-w-7xl mx-auto px-2 sm:px-3 lg:px-4 py-3">
            <div className="flex items-center justify-between">
              <motion.div
                className="flex items-center space-x-3"
                initial={{ x: -50, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.2 }}
              >
                <img
                  src="/logo.svg"
                  alt="AutoTrade AI"
                  className="h-12 w-12 drop-shadow-[0_0_15px_rgba(234,179,8,0.5)]"
                />
                <div className="flex flex-col">
                  <h1 className="text-2xl font-bold bg-gradient-gold bg-clip-text text-transparent">
                    AutoTrade
                  </h1>
                  <span className="text-xs text-silver-400 font-light tracking-wider -mt-1">
                    Powered by W Axis Inc
                  </span>
                </div>
              </motion.div>

              {/* Connection status */}
              <motion.div
                className="flex items-center space-x-2 px-4 py-2 rounded-full bg-elite-975/80 border border-silver-800/30 backdrop-blur-sm hover:border-primary-600/50 transition-all duration-300"
                initial={{ x: 50, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                whileHover={{ scale: 1.05 }}
              >
                <motion.div
                  className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}
                  animate={isConnected ? {
                    boxShadow: [
                      '0 0 8px rgba(74,222,128,0.6)',
                      '0 0 15px rgba(74,222,128,0.9)',
                      '0 0 8px rgba(74,222,128,0.6)',
                    ]
                  } : {
                    boxShadow: [
                      '0 0 8px rgba(248,113,113,0.6)',
                      '0 0 15px rgba(248,113,113,0.9)',
                      '0 0 8px rgba(248,113,113,0.6)',
                    ]
                  }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
                <span className="text-xs text-silver-300 font-medium tracking-wide">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </motion.div>
            </div>
          </div>
        </motion.header>

        {/* Main content */}
        <main className="max-w-7xl mx-auto px-2 sm:px-3 lg:px-4 py-4 relative z-10">
          <Dashboard />
        </main>
      </div>
    </GridBackground>
  )
}

export default App
