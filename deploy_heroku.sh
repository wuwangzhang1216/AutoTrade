#!/bin/bash

# AutoTrade AI - Heroku Deployment Script
# This script deploys both backend and frontend to Heroku

set -e  # Exit on error

echo "=================================================="
echo "  AutoTrade AI - Heroku Deployment"
echo "=================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo -e "${RED}Error: Heroku CLI is not installed.${NC}"
    echo "Install from: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check if logged in to Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo -e "${YELLOW}Not logged in to Heroku. Logging in...${NC}"
    heroku login
fi

echo -e "${GREEN}✓ Heroku CLI detected${NC}"
echo ""

# Get app names from user
echo "Enter your desired app names (or press Enter to let Heroku generate):"
echo ""

read -p "Backend app name (e.g., autotrade-backend-john): " BACKEND_APP
read -p "Frontend app name (e.g., autotrade-frontend-john): " FRONTEND_APP

echo ""
read -p "Enter your OpenRouter API key: " OPENROUTER_KEY

if [ -z "$OPENROUTER_KEY" ]; then
    echo -e "${RED}Error: OpenRouter API key is required${NC}"
    exit 1
fi

echo ""
echo "=================================================="
echo "  Deploying Backend"
echo "=================================================="
echo ""

cd backend

# Initialize git if not already
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit for Heroku deployment"
fi

# Create Heroku app
if [ -z "$BACKEND_APP" ]; then
    echo "Creating Heroku app (auto-generated name)..."
    BACKEND_URL=$(heroku create --json | grep -o '"web_url":"[^"]*' | cut -d'"' -f4)
    BACKEND_APP=$(heroku apps:info --json | grep -o '"name":"[^"]*' | cut -d'"' -f4)
else
    echo "Creating Heroku app: $BACKEND_APP"
    heroku create $BACKEND_APP
    BACKEND_URL="https://$BACKEND_APP.herokuapp.com"
fi

echo -e "${GREEN}✓ Backend app created: $BACKEND_APP${NC}"
echo "  URL: $BACKEND_URL"

# Set environment variables
echo "Setting environment variables..."
heroku config:set OPENROUTER_API_KEY=$OPENROUTER_KEY -a $BACKEND_APP
heroku config:set INITIAL_CAPITAL=10000 -a $BACKEND_APP
heroku config:set LEVERAGE=10 -a $BACKEND_APP
heroku config:set COMMISSION_RATE=0.001 -a $BACKEND_APP
heroku config:set TRADING_INTERVAL_MINUTES=15 -a $BACKEND_APP
heroku config:set MAX_POSITIONS=5 -a $BACKEND_APP
heroku config:set POSITION_SIZE_PERCENT=20 -a $BACKEND_APP
heroku config:set CONFIDENCE_THRESHOLD=0.60 -a $BACKEND_APP

echo -e "${GREEN}✓ Environment variables set${NC}"

# Deploy backend
echo "Deploying backend to Heroku..."
git push heroku main 2>/dev/null || git push heroku master

# Scale dyno
heroku ps:scale web=1 -a $BACKEND_APP

echo -e "${GREEN}✓ Backend deployed successfully!${NC}"
echo ""

cd ..

echo "=================================================="
echo "  Deploying Frontend"
echo "=================================================="
echo ""

cd frontend

# Initialize git if not already
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit for Heroku deployment"
fi

# Create Heroku app
if [ -z "$FRONTEND_APP" ]; then
    echo "Creating Heroku app (auto-generated name)..."
    FRONTEND_URL=$(heroku create --json | grep -o '"web_url":"[^"]*' | cut -d'"' -f4)
    FRONTEND_APP=$(heroku apps:info --json | grep -o '"name":"[^"]*' | cut -d'"' -f4)
else
    echo "Creating Heroku app: $FRONTEND_APP"
    heroku create $FRONTEND_APP
    FRONTEND_URL="https://$FRONTEND_APP.herokuapp.com"
fi

echo -e "${GREEN}✓ Frontend app created: $FRONTEND_APP${NC}"
echo "  URL: $FRONTEND_URL"

# Set backend URL
echo "Setting backend URL..."
heroku config:set VITE_API_URL=$BACKEND_URL -a $FRONTEND_APP

# Add buildpacks
echo "Adding buildpacks..."
heroku buildpacks:add heroku/nodejs -a $FRONTEND_APP
heroku buildpacks:add https://github.com/heroku/heroku-buildpack-static.git -a $FRONTEND_APP

echo -e "${GREEN}✓ Buildpacks added${NC}"

# Deploy frontend
echo "Deploying frontend to Heroku..."
git push heroku main 2>/dev/null || git push heroku master

echo -e "${GREEN}✓ Frontend deployed successfully!${NC}"

cd ..

echo ""
echo "=================================================="
echo "  🎉 Deployment Complete!"
echo "=================================================="
echo ""
echo -e "${GREEN}Backend:${NC}  $BACKEND_URL"
echo -e "${GREEN}Frontend:${NC} $FRONTEND_URL"
echo ""
echo "Next steps:"
echo "1. Update CORS in backend/api.py to include frontend URL"
echo "2. Redeploy backend: cd backend && git push heroku main"
echo "3. Visit $FRONTEND_URL to see your app!"
echo ""
echo "View logs:"
echo "  Backend:  heroku logs --tail -a $BACKEND_APP"
echo "  Frontend: heroku logs --tail -a $FRONTEND_APP"
echo ""
echo "=================================================="
