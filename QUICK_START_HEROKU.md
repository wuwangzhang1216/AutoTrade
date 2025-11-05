# 🚀 Quick Start - Heroku Deployment

Deploy AutoTrade AI to Heroku in 5 minutes!

## Prerequisites (2 min)

```bash
# 1. Install Heroku CLI
# Windows: Download from https://devcenter.heroku.com/articles/heroku-cli
# Mac: brew tap heroku/brew && brew install heroku
# Linux: curl https://cli-assets.heroku.com/install.sh | sh

# 2. Login to Heroku
heroku login

# 3. Get OpenRouter API key
# Sign up at https://openrouter.ai/ and get your key
```

## One-Command Deploy (3 min)

### Linux/Mac

```bash
# Make script executable
chmod +x deploy_heroku.sh

# Run deployment
./deploy_heroku.sh
```

### Windows

```bash
# Run deployment
deploy_heroku.bat
```

## What the Script Does

1. ✅ Creates backend Heroku app
2. ✅ Creates frontend Heroku app
3. ✅ Sets environment variables
4. ✅ Configures buildpacks
5. ✅ Deploys both applications
6. ✅ Connects frontend to backend

## After Deployment

### 1. Update CORS (Required)

Edit `backend/api.py`:
```python
allow_origins=[
    "http://localhost:5888",
    "https://your-frontend-app.herokuapp.com"  # Add this line
]
```

### 2. Redeploy Backend

```bash
cd backend
git add api.py
git commit -m "Update CORS for production"
git push heroku main
```

### 3. Visit Your App

Open the frontend URL provided by the script!

## Manual Deployment

If you prefer manual control, see [HEROKU_DEPLOY.md](HEROKU_DEPLOY.md)

## Troubleshooting

### Backend won't start

```bash
# Check logs
heroku logs --tail -a your-backend-app

# Common fix: Ensure environment variables are set
heroku config -a your-backend-app
```

### Frontend can't connect to backend

```bash
# Check frontend environment
heroku config:get VITE_API_URL -a your-frontend-app

# Should match your backend URL
# If not, set it:
heroku config:set VITE_API_URL=https://your-backend-app.herokuapp.com -a your-frontend-app
```

### Database issues

Heroku's filesystem is ephemeral. For persistence:

```bash
# Add Postgres addon
heroku addons:create heroku-postgresql:mini -a your-backend-app

# Update database connection in code to use DATABASE_URL
```

## Cost

- **Free Tier**: $0 (with sleep after 30min inactivity)
- **Production**: ~$15/month (Basic dyno + Postgres)

## Support

- Full guide: [HEROKU_DEPLOY.md](HEROKU_DEPLOY.md)
- Main README: [README.md](README.md)
- Heroku Docs: https://devcenter.heroku.com/

## Success! 🎉

Your trading system is now live on Heroku!

**Backend**: https://your-backend-app.herokuapp.com
**Frontend**: https://your-frontend-app.herokuapp.com/api/docs

Visit the frontend to see your dashboard! 🚀📈
