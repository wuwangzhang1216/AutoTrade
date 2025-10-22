# Heroku Deployment Guide

This guide will help you deploy the AutoTrade platform to Heroku.

## Architecture

The application consists of:
- **Market Data Service** (Port 8001): Collects cryptocurrency market data
- **Decision Engine** (Port 8002): AI-powered trading decision maker
- **Trading Service** (Port 8003): Executes trades and manages portfolios
- **GUI Frontend**: React-based dashboard

Each service will be deployed as a separate Heroku app.

## Prerequisites

1. Heroku CLI installed
2. Git repository initialized
3. OpenRouter API key for AI models

## Quick Start (Automated)

Run the automated deployment script:

```bash
chmod +x deploy-to-heroku.sh
./deploy-to-heroku.sh
```

This script will:
- Create 4 Heroku apps
- Add PostgreSQL and Redis add-ons
- Configure environment variables
- Provide deployment commands

## Manual Deployment Steps

### 1. Login to Heroku

```bash
heroku login
```

### 2. Create Heroku Apps

Replace `YOUR_PREFIX` with your unique app name prefix:

```bash
export APP_PREFIX="your-trading-app"

heroku create ${APP_PREFIX}-market-data --region us
heroku create ${APP_PREFIX}-decision-engine --region us
heroku create ${APP_PREFIX}-trading-service --region us
heroku create ${APP_PREFIX}-gui --region us
```

### 3. Add Database and Cache Add-ons

```bash
# Add PostgreSQL to trading service
heroku addons:create heroku-postgresql:essential-0 -a ${APP_PREFIX}-trading-service

# Add Redis to market data service
heroku addons:create heroku-redis:mini -a ${APP_PREFIX}-market-data
```

### 4. Get Database and Redis URLs

```bash
DATABASE_URL=$(heroku config:get DATABASE_URL -a ${APP_PREFIX}-trading-service)
REDIS_URL=$(heroku config:get REDIS_URL -a ${APP_PREFIX}-market-data)

echo "DATABASE_URL: ${DATABASE_URL}"
echo "REDIS_URL: ${REDIS_URL}"
```

### 5. Configure Environment Variables

#### Market Data Service
```bash
heroku config:set \
  REDIS_URL="${REDIS_URL}" \
  DATABASE_URL="${DATABASE_URL}" \
  DATA_COLLECTION_INTERVAL=5 \
  SYMBOLS="BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,DOGEUSDT,XRPUSDT" \
  -a ${APP_PREFIX}-market-data
```

#### Decision Engine
```bash
heroku config:set \
  REDIS_URL="${REDIS_URL}" \
  DATABASE_URL="${DATABASE_URL}" \
  OPENROUTER_API_KEY="your-api-key-here" \
  INITIAL_BALANCE=10000.0 \
  MAX_POSITION_SIZE=0.3 \
  RISK_PER_TRADE=0.02 \
  DECISION_INTERVAL=60 \
  MARKET_DATA_SERVICE_URL="https://${APP_PREFIX}-market-data.herokuapp.com" \
  -a ${APP_PREFIX}-decision-engine
```

#### Trading Service
```bash
heroku config:set \
  DATABASE_URL="${DATABASE_URL}" \
  DECISION_ENGINE_URL="https://${APP_PREFIX}-decision-engine.herokuapp.com" \
  COMMISSION_RATE=0.001 \
  SLIPPAGE_RATE=0.0005 \
  -a ${APP_PREFIX}-trading-service
```

### 6. Deploy Each Service

Since this is a monorepo, we'll use git subtree to deploy each service:

#### Deploy Market Data Service
```bash
git subtree push --prefix market_data_service https://git.heroku.com/${APP_PREFIX}-market-data.git main
# If that fails, use:
git push https://git.heroku.com/${APP_PREFIX}-market-data.git `git subtree split --prefix market_data_service main`:main --force
```

#### Deploy Decision Engine
```bash
git subtree push --prefix decision_engine https://git.heroku.com/${APP_PREFIX}-decision-engine.git main
# If that fails, use:
git push https://git.heroku.com/${APP_PREFIX}-decision-engine.git `git subtree split --prefix decision_engine main`:main --force
```

#### Deploy Trading Service
```bash
git subtree push --prefix trading_service https://git.heroku.com/${APP_PREFIX}-trading-service.git main
# If that fails, use:
git push https://git.heroku.com/${APP_PREFIX}-trading-service.git `git subtree split --prefix trading_service main`:main --force
```

### 7. Initialize Database

Connect to your Heroku Postgres database and run the initialization script:

```bash
heroku pg:psql -a ${APP_PREFIX}-trading-service < init-db.sql
```

### 8. Deploy GUI Frontend

First, update the GUI to point to your trading service:

```bash
cd gui
# Update constants.ts with your API URL
# Then build
npm install
npm run build
```

For the GUI, you have two options:

#### Option A: Deploy as Static Site (Recommended)
```bash
# Add Node.js buildpack
heroku buildpacks:set heroku/nodejs -a ${APP_PREFIX}-gui

# Add static buildpack
heroku buildpacks:add https://github.com/heroku/heroku-buildpack-static -a ${APP_PREFIX}-gui

# Deploy
git subtree push --prefix gui https://git.heroku.com/${APP_PREFIX}-gui.git main
```

#### Option B: Use Heroku Static Buildpack with package.json
Create a package.json in the gui directory with build scripts, then deploy.

### 9. Verify Deployment

Check if all services are running:

```bash
heroku ps -a ${APP_PREFIX}-market-data
heroku ps -a ${APP_PREFIX}-decision-engine
heroku ps -a ${APP_PREFIX}-trading-service
heroku ps -a ${APP_PREFIX}-gui
```

View logs:
```bash
heroku logs --tail -a ${APP_PREFIX}-trading-service
```

### 10. Open Your Apps

```bash
heroku open -a ${APP_PREFIX}-gui
heroku open -a ${APP_PREFIX}-trading-service
```

## Updating Your Apps

To update any service after making changes:

```bash
# Commit your changes
git add .
git commit -m "Update service"

# Push to specific service
git push https://git.heroku.com/${APP_PREFIX}-trading-service.git `git subtree split --prefix trading_service main`:main --force
```

## Troubleshooting

### Check Logs
```bash
heroku logs --tail -a ${APP_PREFIX}-service-name
```

### Check Config
```bash
heroku config -a ${APP_PREFIX}-service-name
```

### Restart Service
```bash
heroku restart -a ${APP_PREFIX}-service-name
```

### Database Issues
```bash
# Connect to database
heroku pg:psql -a ${APP_PREFIX}-trading-service

# Reset database
heroku pg:reset -a ${APP_PREFIX}-trading-service
heroku pg:psql -a ${APP_PREFIX}-trading-service < init-db.sql
```

## Cost Estimation

- **Hobby Dyno** (Free): 1 dyno per app, sleeps after 30 mins of inactivity
- **Essential Postgres** (~$5/month): 1GB storage, shared database
- **Mini Redis** (~$3/month): 25MB cache

**Total for 4 services**: ~$8-10/month (or free with hobby dynos + free postgres)

## Important Notes

1. **Database Sharing**: All services share the same PostgreSQL database
2. **Redis Sharing**: Market data and decision engine share Redis
3. **CORS**: Make sure to configure CORS in your backend services to allow requests from the GUI domain
4. **Environment Variables**: Heroku automatically provides PORT variable; services must listen on $PORT
5. **Timeouts**: Heroku has a 30-second timeout for HTTP requests

## Security Recommendations

1. Use Heroku's config vars for sensitive data (API keys, database URLs)
2. Enable SSL (automatic with Heroku)
3. Consider using Heroku Private Spaces for production
4. Regularly rotate API keys and credentials

## Next Steps

1. Set up monitoring with Heroku metrics
2. Configure alerts for errors
3. Set up CI/CD with GitHub Actions
4. Consider upgrading to paid dynos for better performance
5. Implement proper error handling and logging
