# AutoTrade AI - Frontend

Modern trading dashboard built with React, TypeScript, TradingView Lightweight Charts, and Headless UI.

## Features

- **Real-time Trading Dashboard**: Live updates via WebSocket
- **TradingView Charts**: Professional candlestick charts with multiple timeframes
- **Account Overview**: Track equity, P&L, and performance metrics
- **Position Management**: View all open positions in real-time
- **Trade History**: Complete trade log with P&L
- **AI Decisions**: See both AI models' reasoning and final decisions
- **Responsive Design**: Tailwind CSS with dark theme

## Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Development

The frontend will run on `http://localhost:5888` by default.

Make sure the backend API is running on `http://localhost:8888`.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TradingView Lightweight Charts** - Professional charting
- **Headless UI** - Accessible UI components
- **Heroicons** - Icon library
- **Tailwind CSS** - Styling
- **Axios** - API client
- **Zustand** - State management (if needed)
- **date-fns** - Date formatting

## Project Structure

```
src/
├── components/          # React components
│   ├── AccountSummary.tsx
│   ├── AIDecisionsList.tsx
│   ├── Dashboard.tsx
│   ├── MarketOverview.tsx
│   ├── PositionsList.tsx
│   ├── TradeHistory.tsx
│   ├── TradingChart.tsx
│   └── TradingChartContainer.tsx
├── api/                # API client
│   └── client.ts
├── hooks/              # Custom hooks
│   └── useWebSocket.ts
├── App.tsx             # Main app component
├── main.tsx            # Entry point
└── index.css           # Global styles
```

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8888`:

- **REST API**: For fetching data (account, trades, positions, etc.)
- **WebSocket**: For real-time updates (`ws://localhost:8888/ws`)

## Customization

### Change API URL

Edit `.env`:
```env
VITE_API_URL=http://your-api-url:8000
```

### Modify Theme

Edit `tailwind.config.js` to customize colors and theme.

### Add New Components

1. Create component in `src/components/`
2. Import in `Dashboard.tsx`
3. Add API calls in `src/api/client.ts` if needed

## Production Build

```bash
# Build
npm run build

# Output in dist/
# Deploy to any static hosting (Vercel, Netlify, etc.)
```

## WebSocket Connection

The dashboard automatically connects to the WebSocket endpoint and receives real-time updates:

- Account balance changes
- New positions
- Trade executions
- AI decisions

Connection status is shown in the header.

## Components Overview

### Dashboard
Main layout with tabs for different views

### TradingChart
TradingView Lightweight Charts integration with candlestick data

### AccountSummary
Shows total equity, P&L, positions, and win rate

### PositionsList
Real-time list of open positions with P&L

### TradeHistory
Complete trade log with filters

### AIDecisionsList
Expandable list showing both AI models' reasoning

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## License

MIT
