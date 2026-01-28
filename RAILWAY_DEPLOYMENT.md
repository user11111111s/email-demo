# Railway.app Deployment Guide

Complete guide for deploying the Email Automation System to Railway.app with SMTP support.

---

## Why Railway?

✅ **SMTP Support**: Ports 587 and 465 are **not blocked** (unlike Render)  
✅ **Gmail SMTP Works**: Your current code works without changes  
✅ **Free Credits**: $5/month free tier  
✅ **Easy Deployment**: Git-based deployment like Render  
✅ **No Cold Starts**: Better than serverless platforms

---

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Code pushed to GitHub
3. **Gmail Credentials**: Email and App Password

---

## Deployment Steps

### Step 1: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Click **"Start a New Project"**
3. Sign in with GitHub (recommended)

### Step 2: Deploy from GitHub

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your `email-demo-2` repository
4. Select branch: `deploy/railway-setup` (for testing) or `main` (for production)

### Step 3: Configure Build

Railway auto-detects Python projects. It will:
- Install dependencies from `requirements.txt`
- Use configuration from `railway.toml`
- Start with: `gunicorn --bind 0.0.0.0:$PORT run:app`

### Step 4: Set Environment Variables

Click on your service → **"Variables"** tab

Add these variables:

| Variable | Value | Required |
|----------|-------|----------|
| `FLASK_ENV` | `production` | ✅ Yes |
| `SECRET_KEY` | Generate a random string | ✅ Yes |
| `SENDER_EMAIL` | Your Gmail address | ✅ Yes |
| `SENDER_PASSWORD` | Gmail App Password | ✅ Yes |

**Important**: Use Gmail **App Password**, not your regular password!

#### How to Generate Gmail App Password:

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Security → 2-Step Verification (enable if not already)
3. App passwords → Create new
4. Copy the 16-character password
5. Use this in `SENDER_PASSWORD`

### Step 5: Deploy

1. Railway automatically deploys on push
2. Wait 2-3 minutes for deployment
3. Railway will provide a public URL: `https://your-app.up.railway.app`

---

## Testing SMTP

Once deployed:

### 1. Health Check
```bash
curl https://your-app.up.railway.app/ping
```

Expected:
```json
{"message": "Server is running!"}
```

### 2. Test Email Campaign

1. Visit your Railway URL
2. Login with Gmail credentials
3. Create campaign with 3-5 test emails
4. Click "Start Campaign"
5. **Watch**: Request should complete in ~15-30 seconds
6. **Verify**: All emails should be "Sent"
7. **Check inbox**: Emails should arrive!

---

## Environment Variables Reference

### Required Variables

```bash
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
SENDER_EMAIL=youremail@gmail.com
SENDER_PASSWORD=your-gmail-app-password
```

### Optional Variables

```bash
# Database (Railway provides PostgreSQL if needed)
DATABASE_URL=postgresql://...

# Custom domain
RAILWAY_STATIC_URL=https://yourdomain.com
```

---

## Differences from Render

| Feature | Render | Railway |
|---------|--------|---------|
| **SMTP Support** | ❌ Blocked | ✅ Works |
| **Free Tier** | 750 hrs/month | $5 credits/month |
| **Cold Starts** | Yes (15min) | No |
| **Configuration** | `render.yaml` | `railway.toml` |
| **Deployment** | Git push | Git push |

---

## Configuration Files

### `railway.toml`
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "gunicorn --bind 0.0.0.0:$PORT run:app"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### No Other Changes Needed!
Your existing code works as-is on Railway.

---

## Cost Estimate

### Free Tier ($5/month credits):
- **Web Service**: ~$5/month
- **Bandwidth**: Included
- **Enough for**: Development and small-scale testing

### After Free Credits:
- Pay-as-you-go: ~$5-10/month for small apps
- Much cheaper than dedicated hosting

---

## Troubleshooting

### Emails Still Not Sending?

**Check Environment Variables:**
```bash
# In Railway dashboard → Variables tab
FLASK_ENV = "production" ✅
SENDER_EMAIL = "your@gmail.com" ✅
SENDER_PASSWORD = "app-password" ✅ (16 chars)
```

**Check Logs:**
- Railway Dashboard → Your Service → "Deployments" → View Logs
- Look for SMTP errors

**Common Issues:**

1. **"Authentication failed"**
   - Use Gmail App Password, not regular password
   - Enable 2FA on Google account first

2. **"Connection timeout"**
   - Should NOT happen on Railway (SMTP ports open)
   - If it does, contact Railway support

3. **"Campaign stays pending"**
   - Check `FLASK_ENV=production` is set
   - Review application logs

---

## Monitoring

### View Logs:
Railway Dashboard → Your Service → "Deployments" → Latest deploy → "View Logs"

### Check Metrics:
Railway Dashboard → Your Service → "Metrics"
- CPU usage
- Memory usage
- Network traffic

### Check Service Status:
Railway Dashboard → Your Service → Status indicator (green = healthy)

---

## Updating Your App

### Push Updates:
```bash
git add .
git commit -m "Update email feature"
git push origin deploy/railway-setup
```

Railway auto-deploys on push!

---

## Migration from Render

If you want to move completely from Render to Railway:

1. Deploy to Railway using this guide
2. Test thoroughly (especially email sending)
3. Update any external services to use Railway URL
4. Once confirmed working, update `main` branch
5. Optionally: Delete Render service

---

## Support Resources

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: Active community support
- **Railway Status**: [status.railway.app](https://status.railway.app)

---

## Next Steps

1. ✅ Create Railway account
2. ✅ Connect GitHub repository  
3. ✅ Set environment variables
4. ✅ Deploy and test
5. ✅ Verify email sending works
6. ✅ If successful, merge to main

---

**Railway solves the SMTP blocking issue completely!** 🚀

Your emails will send reliably without any code changes.
