# Unified Trading Platform

This is a unified service that combines all three microservices (Market Data Service, Decision Engine, and Trading Service) into a single deployable application. This approach significantly reduces deployment costs on platforms like Heroku.

## Architecture

The unified service integrates:
- **Market Data Service** (Port 8001 → now internal)
- **Decision Engine** (Port 8002 → now internal)
- **Trading Service** (Port 8003 → now internal)

All services now run in a single process on **Port 8080** (configurable via `PORT` env var).

## Benefits

1. **Cost Savings**: Deploy one app instead of three on Heroku
2. **Simplified Management**: Single deployment, logging, and monitoring
3. **Reduced Latency**: Internal function calls instead of HTTP requests between services
4. **Shared Resources**: Single database connection pool, Redis connection, etc.

## API Endpoints

All original endpoints are preserved with their paths:

### Market Data Endpoints
- `GET /api/market/latest` - Get latest market snapshot
- `GET /api/market/{symbol}` - Get data for specific symbol
- `GET /api/market/history/{symbol}` - Get historical data
- `GET /api/market/symbols` - List monitored symbols
- `WS /ws/market` - WebSocket for real-time updates

### Decision Engine Endpoints
- `GET /api/agents` - List all AI agents
- `GET /api/agents/{agent_id}/account` - Get agent account state
- `GET /api/agents/{agent_id}/decisions` - Get agent decisions
- `GET /api/agents/{agent_id}/positions` - Get agent positions
- `GET /api/leaderboard` - Get agent leaderboard

### Trading Service Endpoints
- `GET /api/portfolio` - Get portfolio summary
- `GET /api/positions` - Get all positions
- `GET /api/positions/all` - Get positions across all agents
- `GET /api/trades/all` - Get all trades
- `GET /api/agents/leaderboard` - Get leaderboard
- `GET /api/agents/{agent_id}/portfolio` - Get agent portfolio
- `GET /api/performance/history` - Get performance history

### Health Check
- `GET /` - Service info
- `GET /api/health` - Health check for all components

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
TIMESCALE_HOST=localhost
TIMESCALE_PORT=5432
TIMESCALE_DB=trading_platform
TIMESCALE_USER=admin
TIMESCALE_PASSWORD=password

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Market Data Settings
DATA_COLLECTION_INTERVAL=5
SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,DOGEUSDT,XRPUSDT

# Decision Engine Settings
OPENROUTER_API_KEY=your_api_key_here
INITIAL_BALANCE=10000.0
MAX_POSITION_SIZE=0.3
RISK_PER_TRADE=0.02
DECISION_INTERVAL=60

# Trading Service Settings
COMMISSION_RATE=0.001
SLIPPAGE_RATE=0.0005

# Server
PORT=8080
```

## Local Development

### Using Docker Compose

```bash
# Start unified service with dependencies
docker-compose -f docker-compose.unified.yml up

# Stop services
docker-compose -f docker-compose.unified.yml down
```

### Manual Setup

1. Install dependencies:
```bash
cd unified_service
pip install -r requirements.txt
```

2. Set environment variables (copy .env.example to .env)

3. Run the service:
```bash
python -m app.main
# or
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Heroku Deployment

### Quick Deploy

```bash
# Make script executable
chmod +x deploy-unified.sh

# Deploy
./deploy-unified.sh your-app-name
```

### Manual Deployment

1. Create Heroku app:
```bash
heroku create your-app-name
```

2. Add addons:
```bash
heroku addons:create heroku-postgresql:essential-0
heroku addons:create heroku-redis:mini
```

3. Set environment variables:
```bash
heroku config:set OPENROUTER_API_KEY=your_key
# ... other variables
```

4. Deploy:
```bash
git add .
git commit -m "Deploy unified service"
git push heroku main
```

5. Scale:
```bash
heroku ps:scale web=1
```

## Migration from Separate Services

If you're currently running three separate services:

1. The unified service is **backward compatible** with the same API endpoints
2. Update your GUI environment variable:
   ```bash
   VITE_UNIFIED_SERVICE_URL=https://your-app.herokuapp.com
   ```
3. Deploy the unified service
4. Test thoroughly
5. Once confirmed working, you can delete the three separate Heroku apps

## Monitoring

```bash
# View logs
heroku logs --tail -a your-app-name

# Check status
heroku ps -a your-app-name

# Open app
heroku open -a your-app-name
```

## Troubleshooting

### Service won't start
- Check logs: `heroku logs --tail`
- Verify environment variables: `heroku config`
- Ensure DATABASE_URL and REDIS_URL are set by addons

### High memory usage
- Consider upgrading dyno type on Heroku
- Adjust `DATA_COLLECTION_INTERVAL` to reduce frequency

### API errors
- Verify all endpoints are accessible via `/api/health`
- Check Redis and PostgreSQL connections
- Ensure OPENROUTER_API_KEY is valid

## Performance Considerations

The unified service runs three major background tasks:
1. Market data collection (every 5 seconds)
2. Decision engine loop (every 60 seconds)
3. Trading execution loop (every 10 seconds)

For optimal performance on Heroku:
- Use at least a **Standard-1x dyno** ($25/month)
- Essential-0 PostgreSQL ($5/month)
- Mini Redis ($3/month)

**Total estimated cost: ~$33/month** vs **~$75/month** for three separate services

## Support

For issues or questions, please refer to the main project documentation or create an issue in the repository.
