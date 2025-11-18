# Render Deployment Guide

Complete guide for deploying astro-server to Render.

## Prerequisites

1. **GitHub Repository**: Your code must be pushed to GitHub
2. **Render Account**: Sign up at https://render.com

## Step 1: Create PostgreSQL Database

1. Go to Render Dashboard → **New** → **PostgreSQL**
2. Configure:
   - **Name**: `astro-server-db` (or your preferred name)
   - **Database**: `astro_db`
   - **User**: (auto-generated)
   - **Region**: Choose closest to your users
   - **Plan**: Free (for testing) or Starter (for production)
3. Click **Create Database**
4. Wait for database to be ready (1-2 minutes)
5. **IMPORTANT**: Copy the **Internal Database URL** from the database info page
   - Format: `postgresql://user:password@hostname:5432/database`
   - You'll need this for the next step

## Step 2: Create Web Service

1. Go to Render Dashboard → **New** → **Web Service**
2. Connect your GitHub repository
3. Configure the service:
   - **Name**: `astro-server` (or your preferred name)
   - **Region**: Same as your database
   - **Branch**: `main` or `api/auth` (your deployment branch)
   - **Root Directory**: (leave blank)
   - **Runtime**: Docker
   - **Plan**: Free (for testing) or Starter (for production)

## Step 3: Configure Environment Variables

In the **Environment** section, add these variables:

### Required Variables

```bash
# Database (use Internal Database URL from Step 1)
DB_URI=postgresql+asyncpg://user:password@hostname.oregon-postgres.render.com:5432/database

# JWT Secret (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-characters-long

# SMTP Configuration (for OTP emails)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Astro Server

# LLM API Key (get from https://makersuite.google.com/app/apikey)
GEMINI_API_KEY=your-gemini-api-key-here
```

### Optional Variables

```bash
# Application Settings
LOGGING_LEVEL=INFO
BASE_URL=https://your-app.onrender.com
ROOT_PATH=

# JWT Settings (defaults shown)
JWT_ALGORITHM=HS512
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=720

# OTP Settings (defaults shown)
OTP_LENGTH=6
OTP_EXPIRE_MINUTES=10
OTP_MAX_ATTEMPTS=5
```

### Important Notes:

1. **DB_URI**: 
   - Must start with `postgresql+asyncpg://` (not just `postgresql://`)
   - Use the **Internal Database URL** from your Render PostgreSQL database
   - Replace `postgresql://` with `postgresql+asyncpg://`

2. **SMTP_PASSWORD**: 
   - For Gmail, you need an **App Password**, not your regular password
   - Enable 2FA on your Google account first
   - Generate App Password: https://myaccount.google.com/apppasswords

3. **GEMINI_API_KEY**:
   - Get free API key from: https://makersuite.google.com/app/apikey
   - Free tier includes 60 requests per minute

4. **BASE_URL**:
   - Set this to your Render app URL: `https://your-app.onrender.com`
   - This is used for keep-alive pings to prevent free tier sleep

## Step 4: Deploy

1. Click **Create Web Service**
2. Render will:
   - Build your Docker image
   - Install dependencies
   - Start the application
3. Wait 3-5 minutes for first deployment
4. Watch the logs for any errors

## Step 5: Verify Deployment

Once deployed, test your endpoints:

### Health Check
```bash
curl https://your-app.onrender.com/
```

Expected response:
```json
{
  "status": "ok",
  "message": "astro-server API is running"
}
```

### API Documentation
Visit: `https://your-app.onrender.com/docs`

### Test OTP Flow
```bash
curl -X POST https://your-app.onrender.com/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

## Troubleshooting

### Issue: "No open HTTP ports detected"

**Causes:**
1. Missing required environment variables (DB_URI, JWT_SECRET_KEY, etc.)
2. Database connection failed
3. Application crashed during startup

**Solution:**
1. Check Render logs for error messages
2. Verify all required environment variables are set correctly
3. Ensure DB_URI uses `postgresql+asyncpg://` prefix
4. Check database is running and accessible

### Issue: Workers keep restarting

**Causes:**
1. Missing SMTP credentials
2. Invalid database URL format
3. Missing LLM API key

**Solution:**
1. Check logs: Click on your service → **Logs** tab
2. Look for error messages mentioning missing variables
3. Add missing environment variables
4. Redeploy: **Manual Deploy** → **Deploy latest commit**

### Issue: Database connection timeout

**Causes:**
1. Using External Database URL instead of Internal
2. Wrong database credentials
3. Database not in same region

**Solution:**
1. Use **Internal Database URL** for better performance
2. Verify URL format: `postgresql+asyncpg://user:pass@host:5432/db`
3. Ensure database and web service are in same region

### Issue: 500 errors on API calls

**Causes:**
1. Missing GEMINI_API_KEY for chat endpoints
2. Invalid SMTP configuration for OTP
3. Database migration needed

**Solution:**
1. Add GEMINI_API_KEY environment variable
2. Test SMTP credentials with Gmail App Password
3. Check application logs for specific errors

## Free Tier Limitations

### Render Free Tier:
- **Sleep after 15 minutes of inactivity**
- First request after sleep takes ~30 seconds
- 750 hours/month (enough for one service)

### Solutions:
1. **Keep-Alive Service** (Built-in):
   - App automatically pings itself every 14 minutes
   - Prevents sleep during active hours
   - Set `BASE_URL` to your Render URL

2. **Upgrade to Starter Plan** ($7/month):
   - No sleep
   - Better performance
   - 512MB RAM

## Production Checklist

Before going live:

- [ ] Use strong JWT_SECRET_KEY (min 32 chars)
- [ ] Configure real SMTP credentials
- [ ] Set up production database (Starter plan minimum)
- [ ] Enable database backups
- [ ] Set LOGGING_LEVEL=WARNING or ERROR
- [ ] Configure CORS allowed origins (in code)
- [ ] Add health monitoring (UptimeRobot, etc.)
- [ ] Set up custom domain (optional)
- [ ] Enable HTTPS (automatic on Render)
- [ ] Test all API endpoints
- [ ] Set BASE_URL to production URL

## Monitoring

### View Logs
- Render Dashboard → Your Service → **Logs** tab
- Real-time streaming logs
- Filter by error level

### Metrics
- Render Dashboard → Your Service → **Metrics** tab
- CPU usage
- Memory usage
- Request rates
- Response times

### Alerts
- Render Dashboard → Your Service → **Settings** → **Notifications**
- Configure email/Slack alerts for:
  - Deploy failures
  - Service crashes
  - High error rates

## Updating Your App

### Automatic Deploys (Recommended)
1. Push to your GitHub branch
2. Render automatically rebuilds and deploys
3. Zero downtime deployment

### Manual Deploy
1. Render Dashboard → Your Service
2. **Manual Deploy** → **Deploy latest commit**
3. Or use Render CLI: `render deploy`

## Support

- Render Documentation: https://render.com/docs
- Render Community: https://community.render.com
- Project Issues: https://github.com/Rupesh-Singh-Karki/astro-server/issues

---

**Last Updated**: November 18, 2025
