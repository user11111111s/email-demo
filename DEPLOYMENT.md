# Deployment Guide: Render.com

This guide walks you through deploying the Email Automation System to Render.com's free tier.

---

## 📋 Prerequisites

1. **GitHub Account**: Your code must be in a GitHub repository
2. **Render Account**: Sign up at [render.com](https://render.com) (free)
3. **SendGrid Account**: You need a SendGrid API key and verified sender email

---

## 🚀 Deployment Steps

### Step 1: Push Code to GitHub

If you haven't already, push your code to GitHub:

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Prepare for Render deployment"

# Add remote (replace with your repository URL)
git remote add origin https://github.com/yourusername/email-demo-2.git

# Push to GitHub
git push -u origin main
```

---

### Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Click **"Get Started"**
3. Sign up with GitHub (recommended) or email

---

### Step 3: Create New Web Service

1. In Render Dashboard, click **"New +"** → **"Web Service"**
2. Click **"Connect a repository"**
3. Authorize Render to access your GitHub account
4. Select your `email-demo-2` repository
5. Click **"Connect"**

---

### Step 4: Configure the Service

Render will auto-detect settings from `render.yaml`, but verify:

#### Basic Settings:
- **Name**: `email-automation` (or your preferred name)
- **Region**: Choose closest to you (e.g., Oregon)
- **Branch**: `main`
- **Runtime**: `Python 3`

#### Build & Deploy:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn run:app`

---

### Step 5: Set Environment Variables

Click **"Environment"** tab and add these variables:

| Key | Value | Notes |
|-----|-------|-------|
| `SENDGRID_API_KEY` | `SG.xxxxx...` | Your SendGrid API key |
| `SENDER_EMAIL` | `your@email.com` | Verified sender in SendGrid |
| `FLASK_ENV` | `production` | Sets production mode |
| `PYTHON_VERSION` | `3.11.0` | Python version |

> **Important**: Make sure your `SENDER_EMAIL` is verified in SendGrid Dashboard → Settings → Sender Authentication

---

### Step 6: Deploy

1. Click **"Create Web Service"** button
2. Render will start building your application
3. Wait for deployment to complete (2-5 minutes)
4. You'll see **"Live"** status when ready

---

## ✅ Verify Deployment

Once deployed, Render will give you a URL like: `https://email-automation-xxxx.onrender.com`

### Test Health Check:
```bash
curl https://your-app-url.onrender.com/ping
```

Expected response:
```json
{
  "message": "Server is running!"
}
```

### Test Email Sending:
```bash
curl -X POST https://your-app-url.onrender.com/send-email \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test User"}'
```

---

## 📊 Access Your Application

- **Web Interface**: Visit `https://your-app-url.onrender.com` in your browser
- **API Endpoints**: Use the deployed URL for all API calls
- **Logs**: View in Render Dashboard → Logs tab
- **Metrics**: Available in Dashboard (CPU, Memory, Requests)

---

## 🔄 Automatic Deployments

Render is configured for automatic deployments:
- Any push to the `main` branch triggers a new deployment
- Render pulls latest code, rebuilds, and redeploys
- Zero downtime deployments

To disable auto-deploy:
1. Go to Settings → **"Auto-Deploy"**
2. Toggle off

---

## ⚠️ Important Notes

### Free Tier Limitations:
- **Spin Down**: Services sleep after 15 minutes of inactivity
- **Cold Start**: First request after sleep takes ~30 seconds
- **APScheduler**: Birthday scheduler stops when service sleeps
  - Solution: Use external cron service (see below) or accept that checks only run when service is active

### Database:
- SQLite database is stored in the container
- Data persists during uptime but may be lost on redeploys
- For production, consider upgrading to PostgreSQL

---

## 🕐 Optional: External Cron for Birthday Checks

If you want guaranteed daily birthday checks:

### Option 1: cron-job.org (Recommended)
1. Go to [cron-job.org](https://cron-job.org) (free)
2. Create account
3. Add new cron job:
   - **URL**: `https://your-app-url.onrender.com/api/cron/birthday-check`
   - **Schedule**: Daily at 9:00 AM (or preferred time)
   - **Method**: GET
4. This will wake up your service and trigger birthday checks

### Option 2: UptimeRobot
1. Go to [uptimerobot.com](https://uptimerobot.com) (free)
2. Add monitor:
   - **URL**: `https://your-app-url.onrender.com/ping`
   - **Interval**: Every 5 minutes
3. This keeps your service awake (prevents spin down)

---

## 🐛 Troubleshooting

### Service Won't Start
- **Check Logs**: Dashboard → Logs tab
- **Verify Environment Variables**: Ensure `SENDGRID_API_KEY` and `SENDER_EMAIL` are set
- **Build Errors**: Check if all dependencies in `requirements.txt` are valid

### Emails Not Sending
- **Verify SendGrid API Key**: Test in SendGrid dashboard
- **Check Sender Email**: Must be verified in SendGrid
- **Review Logs**: Look for SendGrid errors in application logs

### Database Errors
- **Check Logs**: SQLite initialization errors
- **Restart Service**: Dashboard → Manual Deploy

### 502 Bad Gateway
- **Service is starting**: Wait 30-60 seconds after deploy
- **Health check failing**: Ensure `/ping` endpoint works

---

## 📈 Monitoring & Maintenance

### View Logs:
```bash
# In Render Dashboard
Dashboard → Your Service → Logs
```

### Restart Service:
```bash
# In Render Dashboard
Dashboard → Your Service → Manual Deploy → Deploy Latest Commit
```

### Check Service Status:
Visit your app's `/ping` endpoint anytime

---

## 🔒 Security Best Practices

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Rotate API keys** regularly in SendGrid
3. **Use strong SECRET_KEY** - Render auto-generates this
4. **Monitor logs** for suspicious activity
5. **Enable HTTPS only** - Render provides this by default

---

## 📞 Support

- **Render Docs**: [render.com/docs](https://render.com/docs)
- **Render Community**: [community.render.com](https://community.render.com)
- **SendGrid Support**: [support.sendgrid.com](https://support.sendgrid.com)

---

## 🎉 Next Steps

1. Share your deployed URL with your team
2. Update any frontend applications to use the new API URL
3. Set up external cron if needed for birthday checks
4. Monitor logs for the first few days
5. Consider upgrading to paid tier if you need:
   - No spin down
   - More resources
   - PostgreSQL database

---

**Congratulations! Your email automation system is now live! 🚀**
