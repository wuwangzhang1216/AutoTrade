# Heroku Deployment Guide

Complete guide to deploy AutoTrade AI to Heroku with both backend and frontend.

## 📋 Prerequisites

1. **Heroku Account**: Sign up at [heroku.com](https://heroku.com)
2. **Heroku CLI**: Install from [devcenter.heroku.com/articles/heroku-cli](https://devcenter.heroku.com/articles/heroku-cli)
3. **Git**: Ensure git is installed
4. **OpenRouter API Key**: Get from [openrouter.ai](https://openrouter.ai)

### Verify Heroku CLI Installation

```bash
heroku --version
heroku login
```

## 🚀 Quick Deploy (Both Backend & Frontend)

### Option 1: Deploy Both with One Command

```bash
# From project root
chmod +x deploy_heroku.sh
./deploy_heroku.sh
```

### Option 2: Manual Step-by-Step Deployment

Follow the detailed instructions below.

---

## 🔧 Backend Deployment (FastAPI)

### Step 1: Prepare Backend

```bash
cd backend
```

Verify these files exist:
- ✅ `Procfile` - Heroku process configuration
- ✅ `runtime.txt` - Python version
- ✅ `requirements.txt` - Python dependencies
- ✅ `.slugignore` - Files to exclude from deployment

### Step 2: Create Heroku App

```bash
# Create app (choose unique name)
heroku create autotrade-backend-YOUR_NAME

# Or let Heroku generate name
heroku create
```

### Step 3: Set Environment Variables

```bash
# Required
heroku config:set OPENROUTER_API_KEY=your_openrouter_key_here

# Optional - Trading Configuration
heroku config:set INITIAL_CAPITAL=10000
heroku config:set LEVERAGE=10
heroku config:set COMMISSION_RATE=0.001
heroku config:set TRADING_INTERVAL_MINUTES=15
heroku config:set MAX_POSITIONS=5
heroku config:set POSITION_SIZE_PERCENT=20
heroku config:set CONFIDENCE_THRESHOLD=0.60

# Optional - AI Models
heroku config:set AI_MODEL_PRIMARY=deepseek/deepseek-chat-v3.1
heroku config:set AI_MODEL_SECONDARY=qwen/qwen3-vl-235b-a22b-instruct
heroku config:set AI_VOTING_STRATEGY=majority

# Optional - Data Providers
heroku config:set COINGECKO_API_KEY=your_coingecko_key
```

### Step 4: Initialize Git (if not already)

```bash
# If backend is not in git repo
git init
git add .
git commit -m "Initial backend commit for Heroku"
```

### Step 5: Deploy Backend

```bash
# Add Heroku remote
heroku git:remote -a autotrade-backend-YOUR_NAME

# Deploy
git push heroku main

# Or if on master branch
git push heroku master
```

### Step 6: Scale Dyno & Check Logs

```bash
# Scale up web dyno
heroku ps:scale web=1

# View logs
heroku logs --tail

# Check app status
heroku ps

# Open app
heroku open
```

### Step 7: Test Backend API

```bash
# Get your backend URL
heroku info -s | grep web_url

# Test API
curl https://your-app-name.herokuapp.com/api/account
```

**Backend URL**: `https://autotrade-backend-YOUR_NAME.herokuapp.com`

---

## 🎨 Frontend Deployment (React + Vite)

### Option A: Deploy to Heroku (Static Site)

#### Step 1: Prepare Frontend

```bash
cd frontend
```

Verify these files exist:
- ✅ `static.json` - Static site configuration
- ✅ `package.json` with `heroku-postbuild` script

#### Step 2: Create Heroku App

```bash
heroku create autotrade-frontend-YOUR_NAME
```

#### Step 3: Set Backend URL

```bash
# Set your backend URL
heroku config:set VITE_API_URL=https://autotrade-backend-YOUR_NAME.herokuapp.com
```

#### Step 4: Add Buildpacks

```bash
# Add Node.js buildpack
heroku buildpacks:add heroku/nodejs

# Add static buildpack
heroku buildpacks:add https://github.com/heroku/heroku-buildpack-static.git
```

#### Step 5: Deploy Frontend

```bash
# Initialize git if needed
git init
git add .
git commit -m "Initial frontend commit for Heroku"

# Add Heroku remote
heroku git:remote -a autotrade-frontend-YOUR_NAME

# Deploy
git push heroku main
```

#### Step 6: Open Frontend

```bash
heroku open
```

**Frontend URL**: `https://autotrade-frontend-YOUR_NAME.herokuapp.com`

### Option B: Deploy Frontend to Vercel/Netlify

Frontend can also be deployed to:
- **Vercel**: `vercel --prod`
- **Netlify**: `netlify deploy --prod`

Just set `VITE_API_URL` to your Heroku backend URL.

---

## 🔗 Connect Frontend to Backend

### Update CORS in Backend

After deploying frontend, update CORS settings:

```bash
# SSH into backend app
heroku run bash -a autotrade-backend-YOUR_NAME

# Or update api.py and redeploy
```

Edit `backend/api.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5888",
        "https://autotrade-frontend-YOUR_NAME.herokuapp.com"  # Add this
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Redeploy backend:
```bash
cd backend
git add api.py
git commit -m "Update CORS for production"
git push heroku main
```

---

## 📊 Database & Storage

### Database Options

Heroku provides **ephemeral filesystem** (files are lost on restart). For persistence:

#### Option 1: Heroku Postgres (Recommended)

```bash
# Add Postgres addon
heroku addons:create heroku-postgresql:mini -a autotrade-backend-YOUR_NAME

# Get database URL
heroku config:get DATABASE_URL
```

Update `backend/database/db_manager.py` to use PostgreSQL instead of SQLite.

#### Option 2: External Database

Use external services:
- **Supabase** (PostgreSQL)
- **PlanetScale** (MySQL)
- **MongoDB Atlas**

### File Storage

For logs and cache, use:
- **AWS S3**
- **Cloudinary**
- **Heroku's own storage addons**

---

## 🌍 Environment Variables Summary

### Backend Environment Variables

```bash
# Required
OPENROUTER_API_KEY=sk-or-...

# Trading Config
INITIAL_CAPITAL=10000
LEVERAGE=10
COMMISSION_RATE=0.001
TRADING_INTERVAL_MINUTES=15
MAX_POSITIONS=5
POSITION_SIZE_PERCENT=20
CONFIDENCE_THRESHOLD=0.60

# AI Models
AI_MODEL_PRIMARY=deepseek/deepseek-chat-v3.1
AI_MODEL_SECONDARY=qwen/qwen3-vl-235b-a22b-instruct
AI_VOTING_STRATEGY=majority

# Optional
COINGECKO_API_KEY=CG-...
```

### Frontend Environment Variables

```bash
VITE_API_URL=https://autotrade-backend-YOUR_NAME.herokuapp.com
```

---

## 🔍 Monitoring & Logs

### View Logs

```bash
# Backend logs
heroku logs --tail -a autotrade-backend-YOUR_NAME

# Frontend logs
heroku logs --tail -a autotrade-frontend-YOUR_NAME

# Filter for errors
heroku logs --tail -a autotrade-backend-YOUR_NAME | grep ERROR
```

### Monitor App Health

```bash
# Check dyno status
heroku ps -a autotrade-backend-YOUR_NAME

# View metrics
heroku metrics -a autotrade-backend-YOUR_NAME
```

### Install Addons for Monitoring

```bash
# Papertrail (logging)
heroku addons:create papertrail:choklad

# New Relic (APM)
heroku addons:create newrelic:wayne
```

---

## 💰 Cost Estimation

### Free Tier (Hobby Dynos)
- ✅ **Backend**: Free dyno (sleeps after 30min inactivity)
- ✅ **Frontend**: Free dyno or free on Vercel/Netlify
- ⚠️ **Database**: SQLite won't persist (use addon)

**Total**: $0/month (with limitations)

### Production (Recommended)

- **Backend**: Basic dyno ($7/month)
- **Frontend**: Free on Vercel/Netlify
- **Postgres**: Mini addon ($5/month)
- **OpenRouter API**: ~$2-20/month

**Total**: ~$15-35/month

---

## 🐛 Troubleshooting

### Backend Issues

**App crashes on startup:**
```bash
heroku logs --tail -a autotrade-backend-YOUR_NAME
```

Check for:
- Missing environment variables
- Python dependency errors
- Port binding issues

**Fix port binding:**
Ensure `Procfile` uses `${PORT:-8888}` not just `8888`.

### Frontend Issues

**White screen / Can't connect to backend:**
1. Check `VITE_API_URL` is set correctly
2. Verify CORS is configured in backend
3. Check browser console for errors

**Build fails:**
```bash
heroku logs --tail -a autotrade-frontend-YOUR_NAME
```

Common issues:
- TypeScript errors
- Missing dependencies
- Build script errors

---

## 🔄 Continuous Deployment

### Setup GitHub Integration

1. Go to Heroku Dashboard
2. Select your app
3. Go to **Deploy** tab
4. Connect to GitHub
5. Enable **Automatic Deploys** from `main` branch

Now every push to GitHub will auto-deploy!

### Or use Heroku CLI

```bash
# Deploy backend
cd backend
git push heroku main

# Deploy frontend
cd frontend
git push heroku main
```

---

## 📝 Post-Deployment Checklist

- [ ] Backend API responding at `/api/account`
- [ ] Frontend loading successfully
- [ ] WebSocket connection working
- [ ] CORS configured correctly
- [ ] Environment variables set
- [ ] Database persistence working (if using addon)
- [ ] Logs are being generated
- [ ] OpenRouter API key working
- [ ] Trading system can make decisions (if enabled)

---

## 🎯 Next Steps

1. **Set up database persistence** (Postgres addon)
2. **Configure custom domain** (`heroku domains:add`)
3. **Enable HTTPS** (automatic on Heroku)
4. **Set up monitoring** (Papertrail, New Relic)
5. **Configure CI/CD** (GitHub Actions)
6. **Add error tracking** (Sentry)

---

## 📚 Useful Commands

```bash
# Restart app
heroku restart -a APP_NAME

# Run one-off commands
heroku run bash -a APP_NAME
heroku run python main.py -a APP_NAME

# View config
heroku config -a APP_NAME

# Scale dynos
heroku ps:scale web=1 -a APP_NAME

# Open app in browser
heroku open -a APP_NAME

# View releases
heroku releases -a APP_NAME

# Rollback to previous release
heroku rollback -a APP_NAME
```

---

## 🔗 Resources

- [Heroku Dev Center](https://devcenter.heroku.com/)
- [Heroku Python Support](https://devcenter.heroku.com/articles/python-support)
- [Heroku Node.js Support](https://devcenter.heroku.com/articles/nodejs-support)
- [Buildpacks](https://elements.heroku.com/buildpacks)

---

## 🎉 Success!

Your AutoTrade AI system is now live on Heroku!

**Backend**: `https://autotrade-backend-YOUR_NAME.herokuapp.com`
**Frontend**: `https://autotrade-frontend-YOUR_NAME.herokuapp.com`

Visit the frontend URL to see your trading dashboard live! 🚀📈
