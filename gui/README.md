# AI Trading Platform - Web Interface

A modern, real-time web interface for the AI Trading Platform. Built with React, TypeScript, and Vite, this dashboard provides live monitoring of trading activities, portfolio performance, and market data.

## Features

- **Real-Time Market Data**: Live cryptocurrency prices with 24h change indicators
- **Service Health Monitoring**: Visual indicators for all backend microservices
- **Portfolio Dashboard**: Live portfolio value, P&L tracking, and positions
- **Performance Metrics**: Win rate, Sharpe ratio, drawdown analysis
- **Auto-Refresh**: Automatic data updates for real-time monitoring
- **Fallback UI**: Graceful degradation to demo data when services are offline
- **Professional Design**: Modern, responsive UI with gradient effects and animations

## Architecture

The frontend connects to three backend microservices:

- **Market Data Service** (Port 8001): Real-time market data and technical indicators
- **Decision Engine** (Port 8002): AI-powered trading signals and strategies
- **Trading Service** (Port 8003): Order execution, portfolio, and performance tracking

## Prerequisites

- Node.js 18+ and npm
- Backend services running (see main [README.md](../README.md))

## Quick Start

### 1. Install Dependencies

```bash
cd gui
npm install
```

### 2. Start the Development Server

```bash
npm run dev
```

The application will be available at: http://localhost:5173

### 3. Build for Production

```bash
npm run build
```

The production build will be in the `dist/` directory.

### 4. Preview Production Build

```bash
npm run preview
```

## Project Structure

```
gui/
├── components/           # React components
│   ├── Header.tsx       # Navigation and market ticker
│   ├── ChartSection.tsx # Performance charts
│   ├── InfoSidebar.tsx  # Portfolio info and tabs
│   ├── ModelCards.tsx   # Performance overview cards
│   ├── PositionsContent.tsx  # Live positions table
│   ├── ServiceHealthIndicator.tsx  # Service status
│   └── Icons.tsx        # Icon components
├── hooks/               # Custom React hooks
│   └── useApi.ts        # API data fetching hooks
├── services/            # Backend API integration
│   └── api.ts           # API service layer
├── types.ts             # TypeScript type definitions
├── constants.ts         # Demo data and constants
├── App.tsx              # Main application component
├── index.tsx            # Application entry point
├── index.html           # HTML template
└── package.json         # Dependencies and scripts
```

## API Integration

The frontend uses a comprehensive API service layer ([services/api.ts](services/api.ts)) with:

- Type-safe API calls with TypeScript
- Automatic error handling and retry logic
- Support for all backend endpoints
- Combined dashboard data fetching

### Example API Usage

```typescript
import { marketDataApi, tradingServiceApi } from './services/api';

// Get market data
const btcData = await marketDataApi.getMarketData('BTC');

// Get portfolio
const portfolio = await tradingServiceApi.getPortfolio();

// Place an order
const order = await tradingServiceApi.placeOrder({
  symbol: 'BTC',
  side: 'buy',
  quantity: 0.1,
  order_type: 'market'
});
```

## Custom Hooks

The application uses React hooks for data management:

### useMarketData

```typescript
const { data, loading, error, refetch } = useMarketData(['BTC', 'ETH'], 30000);
```

Fetches market data with auto-refresh (default: 30 seconds).

### usePortfolio

```typescript
const { data, loading, error } = usePortfolio(10000);
```

Fetches portfolio data with auto-refresh (default: 10 seconds).

### usePositions

```typescript
const { data, loading, error } = usePositions(10000);
```

Fetches open positions with auto-refresh.

### useServicesHealth

```typescript
const { health, checking, refetch } = useServicesHealth(60000);
```

Monitors health of all backend services.

## Configuration

### API Endpoints

Edit [services/api.ts](services/api.ts) to change backend URLs:

```typescript
const API_CONFIG: ApiConfig = {
  marketDataUrl: 'http://localhost:8001',
  decisionEngineUrl: 'http://localhost:8002',
  tradingServiceUrl: 'http://localhost:8003',
};
```

### Refresh Intervals

Customize auto-refresh intervals in component hooks:

- Market Data: 30 seconds
- Portfolio: 10 seconds
- Positions: 10 seconds
- Service Health: 60 seconds

## Backend Services

Before running the GUI, ensure backend services are running:

```bash
# From project root
docker-compose up -d

# Or use the startup script
./start.sh
```

Verify services are running:
```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

## Features in Detail

### Service Health Indicator

- Real-time monitoring of all 3 backend services
- Visual status indicators (green = online, red = offline)
- Expandable panel with detailed service information
- Automatic health checks every 60 seconds

### Live Market Data

- Cryptocurrency price ticker with 6 major coins
- 24h price change percentage
- Live data indicator (green pulse)
- Fallback to cached data when service unavailable

### Portfolio Dashboard

- Real-time portfolio value tracking
- Total P&L with percentage
- Cash balance and positions value
- Performance metrics (win rate, Sharpe ratio, drawdown)

### Positions Table

- Live open positions with real-time P&L
- Entry price vs current price comparison
- Side indicators (long/short)
- Individual position P&L tracking

## Styling

The application uses Tailwind CSS with custom configuration:

- Custom color palette (`arena-black`, `arena-gray-*`)
- Gradient backgrounds
- Glass morphism effects (backdrop blur)
- Responsive breakpoints
- Smooth animations and transitions

## Development Tips

### Hot Reload

Vite provides instant hot module replacement (HMR). Changes to components will reflect immediately without page refresh.

### Type Safety

All API responses are typed. Use TypeScript definitions in [types.ts](types.ts) and [services/api.ts](services/api.ts).

### Error Handling

The API layer includes comprehensive error handling:
- Network errors
- Service unavailability
- Invalid responses
- Automatic fallback to demo data

### Debugging

Enable console logging for API calls:

```typescript
// In services/api.ts, errors are logged automatically
console.error('API call failed:', err);
```

## Troubleshooting

### Backend Services Not Connecting

1. Verify services are running:
   ```bash
   docker-compose ps
   ```

2. Check service health:
   ```bash
   curl http://localhost:8001/health
   ```

3. Check browser console for CORS errors

4. Ensure ports 8001, 8002, 8003 are not blocked

### Demo Data Showing Instead of Live Data

- Check Service Health Indicator (top of page)
- Verify backend services are running
- Check browser console for API errors
- Try refreshing the page

### Build Errors

1. Clear node_modules and reinstall:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

2. Clear Vite cache:
   ```bash
   rm -rf node_modules/.vite
   ```

## Performance

- Optimized API calls with caching
- Auto-refresh intervals to prevent overloading
- Lazy loading for heavy components
- Memoized calculations

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Contributing

When adding new features:

1. Add TypeScript types in [types.ts](types.ts)
2. Create API functions in [services/api.ts](services/api.ts)
3. Create custom hooks in [hooks/useApi.ts](hooks/useApi.ts)
4. Build UI components in `components/`
5. Test with both live and demo data

## License

This project is for educational and research purposes.

## Support

For issues:
- Check the main project [README.md](../README.md)
- Review API service logs
- Check browser console for errors
