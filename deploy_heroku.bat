@echo off
REM AutoTrade AI - Heroku Deployment Script (Windows)
REM This script deploys both backend and frontend to Heroku

echo ==================================================
echo   AutoTrade AI - Heroku Deployment
echo ==================================================
echo.

REM Check if Heroku CLI is installed
where heroku >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Heroku CLI is not installed.
    echo Install from: https://devcenter.heroku.com/articles/heroku-cli
    pause
    exit /b 1
)

REM Check if logged in to Heroku
heroku auth:whoami >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Not logged in to Heroku. Logging in...
    heroku login
)

echo [OK] Heroku CLI detected
echo.

REM Get app names from user
echo Enter your desired app names (or press Enter to let Heroku generate):
echo.

set /p BACKEND_APP="Backend app name (e.g., autotrade-backend-john): "
set /p FRONTEND_APP="Frontend app name (e.g., autotrade-frontend-john): "

echo.
set /p OPENROUTER_KEY="Enter your OpenRouter API key: "

if "%OPENROUTER_KEY%"=="" (
    echo Error: OpenRouter API key is required
    pause
    exit /b 1
)

echo.
echo ==================================================
echo   Deploying Backend
echo ==================================================
echo.

cd backend

REM Initialize git if not already
if not exist .git (
    echo Initializing git repository...
    git init
    git add .
    git commit -m "Initial commit for Heroku deployment"
)

REM Create Heroku app
if "%BACKEND_APP%"=="" (
    echo Creating Heroku app (auto-generated name)...
    heroku create
) else (
    echo Creating Heroku app: %BACKEND_APP%
    heroku create %BACKEND_APP%
)

echo [OK] Backend app created
echo.

REM Set environment variables
echo Setting environment variables...
heroku config:set OPENROUTER_API_KEY=%OPENROUTER_KEY%
heroku config:set INITIAL_CAPITAL=10000
heroku config:set LEVERAGE=10
heroku config:set COMMISSION_RATE=0.001
heroku config:set TRADING_INTERVAL_MINUTES=15
heroku config:set MAX_POSITIONS=5
heroku config:set POSITION_SIZE_PERCENT=20
heroku config:set CONFIDENCE_THRESHOLD=0.60

echo [OK] Environment variables set
echo.

REM Deploy backend
echo Deploying backend to Heroku...
git push heroku main 2>nul || git push heroku master

REM Scale dyno
heroku ps:scale web=1

echo [OK] Backend deployed successfully!
echo.

cd ..

echo ==================================================
echo   Deploying Frontend
echo ==================================================
echo.

cd frontend

REM Initialize git if not already
if not exist .git (
    echo Initializing git repository...
    git init
    git add .
    git commit -m "Initial commit for Heroku deployment"
)

REM Get backend URL
for /f "tokens=*" %%i in ('heroku info -s ^| findstr web_url') do set BACKEND_URL_LINE=%%i
for /f "tokens=2 delims==" %%a in ("%BACKEND_URL_LINE%") do set BACKEND_URL=%%a

REM Create Heroku app
if "%FRONTEND_APP%"=="" (
    echo Creating Heroku app (auto-generated name)...
    heroku create
) else (
    echo Creating Heroku app: %FRONTEND_APP%
    heroku create %FRONTEND_APP%
)

echo [OK] Frontend app created
echo.

REM Set backend URL
echo Setting backend URL...
heroku config:set VITE_API_URL=%BACKEND_URL%

REM Add buildpacks
echo Adding buildpacks...
heroku buildpacks:add heroku/nodejs
heroku buildpacks:add https://github.com/heroku/heroku-buildpack-static.git

echo [OK] Buildpacks added
echo.

REM Deploy frontend
echo Deploying frontend to Heroku...
git push heroku main 2>nul || git push heroku master

echo [OK] Frontend deployed successfully!
echo.

cd ..

echo.
echo ==================================================
echo   Deployment Complete!
echo ==================================================
echo.
echo Backend:  %BACKEND_URL%
for /f "tokens=*" %%i in ('heroku info -s ^| findstr web_url') do set FRONTEND_URL_LINE=%%i
for /f "tokens=2 delims==" %%a in ("%FRONTEND_URL_LINE%") do echo Frontend: %%a
echo.
echo Next steps:
echo 1. Update CORS in backend/api.py to include frontend URL
echo 2. Redeploy backend: cd backend ^&^& git push heroku main
echo 3. Visit frontend URL to see your app!
echo.
echo ==================================================
pause
