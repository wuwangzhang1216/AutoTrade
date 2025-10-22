#!/bin/bash

# Deploy Unified Trading Platform to Heroku

set -e

APP_NAME="${1:-autotrade-unified}"

echo "============================================"
echo "Deploying Unified Trading Platform to Heroku"
echo "App Name: $APP_NAME"
echo "============================================"

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "Error: Heroku CLI is not installed"
    echo "Please install it from: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check if logged in to Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo "Error: Not logged in to Heroku"
    echo "Please run: heroku login"
    exit 1
fi

echo ""
echo "Step 1: Creating/Verifying Heroku app..."
if heroku apps:info -a $APP_NAME &> /dev/null; then
    echo "✓ App $APP_NAME already exists"
else
    echo "Creating new app: $APP_NAME"
    heroku create $APP_NAME
fi

echo ""
echo "Step 2: Adding PostgreSQL addon..."
if heroku addons:info heroku-postgresql -a $APP_NAME &> /dev/null; then
    echo "✓ PostgreSQL addon already exists"
else
    echo "Adding PostgreSQL addon..."
    heroku addons:create heroku-postgresql:essential-0 -a $APP_NAME
fi

echo ""
echo "Step 3: Adding Redis addon..."
if heroku addons:info heroku-redis -a $APP_NAME &> /dev/null; then
    echo "✓ Redis addon already exists"
else
    echo "Adding Redis addon..."
    heroku addons:create heroku-redis:mini -a $APP_NAME
fi

echo ""
echo "Step 4: Setting environment variables..."

# Read .env file if exists
if [ -f .env ]; then
    echo "Reading from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Set environment variables
heroku config:set \
    OPENROUTER_API_KEY="${OPENROUTER_API_KEY}" \
    DATA_COLLECTION_INTERVAL="5" \
    SYMBOLS="BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,DOGEUSDT,XRPUSDT" \
    INITIAL_BALANCE="10000.0" \
    MAX_POSITION_SIZE="0.3" \
    RISK_PER_TRADE="0.02" \
    DECISION_INTERVAL="60" \
    COMMISSION_RATE="0.001" \
    SLIPPAGE_RATE="0.0005" \
    -a $APP_NAME

echo ""
echo "Step 5: Setting buildpack..."
heroku buildpacks:clear -a $APP_NAME
heroku buildpacks:add heroku/python -a $APP_NAME

echo ""
echo "Step 6: Pushing code to Heroku..."

# Initialize git if not already
if [ ! -d .git ]; then
    git init
    git add .
    git commit -m "Initial commit for unified service"
fi

# Add Heroku remote if not exists
if ! git remote | grep heroku-unified &> /dev/null; then
    heroku git:remote -a $APP_NAME -r heroku-unified
fi

# Push to Heroku
git push heroku-unified main --force || git push heroku-unified master --force

echo ""
echo "Step 7: Initializing database..."
heroku run "cd unified_service && python -c 'from market_data_service.app.storage.timescale_db import TimescaleDB; from decision_engine.app.database import Database; from app.config import get_settings; s = get_settings(); TimescaleDB(s.database_url).initialize(); Database(s.database_url).initialize()'" -a $APP_NAME

echo ""
echo "Step 8: Scaling dyno..."
heroku ps:scale web=1 -a $APP_NAME

echo ""
echo "============================================"
echo "✓ Deployment Complete!"
echo "============================================"
echo ""
echo "App URL: https://$APP_NAME.herokuapp.com"
echo ""
echo "Useful commands:"
echo "  View logs: heroku logs --tail -a $APP_NAME"
echo "  Open app: heroku open -a $APP_NAME"
echo "  Check status: heroku ps -a $APP_NAME"
echo ""
