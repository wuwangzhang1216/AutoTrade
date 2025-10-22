# Quick Start - Heroku Deployment

## Deploy Everything in One Command

```bash
./deploy.sh
```

That's it! The script will:
1. ✅ Create 4 Heroku apps
2. ✅ Add PostgreSQL and Redis
3. ✅ Configure all environment variables
4. ✅ Deploy all services
5. ✅ Initialize the database
6. ✅ Deploy the GUI
7. ✅ Open your dashboard in browser

## What You Need

1. **Heroku CLI** - Already installed ✅
2. **OpenRouter API Key** - You'll be prompted for this
3. **App Name Prefix** - Choose a unique name (e.g., "my-trading")

## During Deployment

You'll be asked for:
- App name prefix (lowercase, letters, numbers, hyphens)
- OpenRouter API key (if not in .env file)
- Confirmation to proceed

## After Deployment

Your apps will be available at:
- **GUI**: `https://your-prefix-gui.herokuapp.com`
- **API**: `https://your-prefix-trading-service.herokuapp.com`

## Useful Commands

```bash
# View logs
heroku logs --tail -a your-prefix-trading-service

# Check status
heroku ps -a your-prefix-trading-service

# Restart a service
heroku restart -a your-prefix-trading-service

# Open GUI
heroku open -a your-prefix-gui

# Database console
heroku pg:psql -a your-prefix-trading-service
```

## Cost

- **Free Tier**: All apps can run on free dynos
- **Recommended**:
  - Essential Postgres: ~$5/month
  - Mini Redis: ~$3/month
  - Total: ~$8/month

## Troubleshooting

If deployment fails:
1. Check logs: `heroku logs --tail -a app-name`
2. Verify config: `heroku config -a app-name`
3. See [HEROKU_DEPLOYMENT.md](HEROKU_DEPLOYMENT.md) for detailed guide

## Manual Deployment

If you prefer manual control, see [HEROKU_DEPLOYMENT.md](HEROKU_DEPLOYMENT.md) for step-by-step instructions.
