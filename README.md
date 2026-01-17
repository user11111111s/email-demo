# Email Automation System

Email campaign management system with automated birthday wishes.

## Features

- 📧 Email campaign creation and management
- 📊 Campaign analytics (opens, replies)
- 🎂 Automated birthday wishes
- 📁 CSV/Excel recipient upload
- ⏰ Scheduled campaigns
- 📈 Export reports

## Deployment on Render

### Quick Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Manual Deployment

1. **Fork/Clone this repository**

2. **Sign up for Render**
   - Go to https://render.com
   - Sign up with GitHub

3. **Create New Web Service**
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name:** `email-demo` (or your preferred name)
     - **Environment:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn run:app`
     - **Instance Type:** Free

4. **Add Disk for Database**
   - In Advanced settings
   - Add Disk:
     - **Name:** `email-demo-db`
     - **Mount Path:** `/opt/render/project/src/instance`
     - **Size:** 1 GB

5. **Set Environment Variables**
   ```
   BIRTHDAY_SENDER_EMAIL=your_email@gmail.com
   BIRTHDAY_SENDER_PASSWORD=your_app_password
   CRON_SECRET=generate_random_secret
   USE_INTERNAL_SCHEDULER=false
   ```

6. **Deploy!**
   - Click "Create Web Service"
   - Wait for deployment (2-3 minutes)

### Set Up Cron Job

After deployment, set up external cron at https://cron-job.org:
- **URL:** `https://your-app.onrender.com/cron/birthday-check?key=YOUR_CRON_SECRET`
- **Schedule:** Daily at 00:05

## Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Run the app:**
   ```bash
   python run.py
   ```

4. **Access:** http://127.0.0.1:5000

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BIRTHDAY_SENDER_EMAIL` | Gmail address for sending | Yes |
| `BIRTHDAY_SENDER_PASSWORD` | Gmail app password | Yes |
| `CRON_SECRET` | Secret key for cron endpoint | Yes (production) |
| `USE_INTERNAL_SCHEDULER` | Use APScheduler (`true`/`false`) | No (default: `true`) |

## Tech Stack

- **Backend:** Flask, SQLAlchemy
- **Database:** SQLite
- **Email:** SMTP (Gmail)
- **Scheduler:** APScheduler (local) / External cron (production)
- **Frontend:** HTML, CSS, JavaScript

## License

MIT
