import { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

class ChartErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
    }
  }

  static getDerivedStateFromError(error: Error): State {
    console.error('Chart Error Boundary caught error:', error)
    return {
      hasError: true,
      error,
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Chart error details:', error)
    console.error('Error info:', errorInfo)
  }

  resetError = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="card">
          <div className="flex flex-col items-center justify-center h-[350px] text-center">
            <div className="text-red-400 mb-4">
              <svg
                className="w-12 h-12 mx-auto mb-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <p className="text-sm font-semibold">Chart Rendering Error</p>
            </div>
            <p className="text-xs text-silver-400 mb-4">
              The chart encountered a temporary issue
            </p>
            <button
              onClick={this.resetError}
              className="px-4 py-2 bg-gold-500/20 hover:bg-gold-500/30 text-gold-400 text-xs rounded transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ChartErrorBoundary
