# Setting Up Cron Jobs for Birthday Automation

## Quick Reference

Your endpoint URL will be:
```
https://yourapp.com/cron/birthday-check?key=bd8f7e3a9c2d1f4e6b5a0872df3c5a91
```

Replace `yourapp.com` with your actual deployed domain.

---

## Option 1: cron-job.org (Easiest - Recommended)

**Pros:** Free, simple UI, reliable, no coding needed

### Steps:

1. **Sign Up**
   - Go to https://cron-job.org/en/
   - Click "Sign up for free"
   - Create account with email

2. **Create Cron Job**
   - Click "Create cronjob" button
   - Fill in the form:
     - **Title:** `Birthday Email Automation`
     - **Address:** `https://yourapp.com/cron/birthday-check?key=bd8f7e3a9c2d1f4e6b5a0872df3c5a91`
     - **Schedule:**
       - Every day
       - Time: `00:05` (5 minutes after midnight)
     - **Request method:** GET
     - **Enable:** Yes (check the box)

3. **Save and Test**
   - Click "Create cronjob"
   - Click "Execute now" to test
   - Check execution history

**That's it!** The service will now call your endpoint daily at 00:05.

---

## Option 2: GitHub Actions (For GitHub repos)

**Pros:** Free, integrated with GitHub, version controlled

### Steps:

1. **Create Workflow File**
   
   In your repository, create: `.github/workflows/birthday-cron.yml`

   ```yaml
   name: Daily Birthday Check

   on:
     schedule:
       # Runs at 00:05 UTC every day (adjust for your timezone)
       - cron: '5 0 * * *'
     
     # Allows manual trigger from Actions tab
     workflow_dispatch:

   jobs:
     birthday-check:
       runs-on: ubuntu-latest
       
       steps:
         - name: Trigger Birthday Automation
           run: |
             response=$(curl -s -w "\n%{http_code}" "https://yourapp.com/cron/birthday-check?key=${{ secrets.CRON_SECRET }}")
             http_code=$(echo "$response" | tail -n 1)
             body=$(echo "$response" | head -n -1)
             
             echo "Response: $body"
             echo "Status Code: $http_code"
             
             if [ "$http_code" != "200" ]; then
               echo "❌ Birthday check failed!"
               exit 1
             fi
             
             echo "✅ Birthday check successful!"
   ```

2. **Add Secret to GitHub**
   - Go to your repo → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `CRON_SECRET`
   - Value: `bd8f7e3a9c2d1f4e6b5a0872df3c5a91`
   - Click "Add secret"

3. **Test**
   - Go to Actions tab
   - Select "Daily Birthday Check" workflow
   - Click "Run workflow" → "Run workflow"
   - Check the output

**Timezone Note:** Cron uses UTC. If you want 00:05 IST (India), use `'35 18 * * *'` (18:35 UTC = 00:05 IST next day)

---

## Option 3: EasyCron (Alternative free service)

**Pros:** Free tier (up to 1 job), simple

### Steps:

1. Sign up at https://www.easycron.com/
2. Click "Add Cron Job"
3. Fill form:
   - **URL:** `https://yourapp.com/cron/birthday-check?key=bd8f7e3a9c2d1f4e6b5a0872df3c5a91`
   - **Cron Expression:** `5 0 * * *` (00:05 daily)
   - **Name:** `Birthday Automation`
4. Save and enable

---

## Option 4: Render Cron Jobs (If using Render for hosting)

**Pros:** Native integration if you deploy on Render

### Steps:

1. In Render Dashboard, create a new "Cron Job"
2. Configure:
   - **Command:** 
     ```bash
     curl "https://yourapp.com/cron/birthday-check?key=$CRON_SECRET"
     ```
   - **Schedule:** `5 0 * * *`
3. Add environment variable `CRON_SECRET` in Render settings

---

## Testing Your Cron Job

### Before Production:

1. **Deploy your app first** (Railway, Render, etc.)
2. **Test the endpoint manually:**
   ```bash
   curl "https://yourapp.com/cron/birthday-check?key=bd8f7e3a9c2d1f4e6b5a0872df3c5a91"
   ```
   Should return: `{"status": "ok", "message": "Birthday check executed successfully"}`

3. **Set up cron job** using one of the options above

4. **Monitor first few runs** to ensure it works

---

## Timezone Converter

Common cron expressions for 00:05 in different timezones:

| Timezone | Cron Expression | Notes |
|----------|----------------|-------|
| UTC | `5 0 * * *` | Midnight + 5 min UTC |
| IST (India) | `35 18 * * *` | 18:35 UTC = 00:05 IST (next day) |
| EST (US East) | `5 5 * * *` | 05:05 UTC = 00:05 EST |
| PST (US West) | `5 8 * * *` | 08:05 UTC = 00:05 PST |

Use https://crontab.guru/ to customize your schedule!

---

## Troubleshooting

**Cron job fails with 403 error:**
- Check that CRON_SECRET matches in both `.env` and cron URL

**Birthday emails not sending:**
- Check app logs for errors
- Verify `BIRTHDAY_SENDER_EMAIL` and `BIRTHDAY_SENDER_PASSWORD` are set
- Ensure recipients have birthdays today

**Cron job not triggering:**
- Verify cron schedule syntax
- Check service status/logs
- Ensure app is running (not scaled to zero)
