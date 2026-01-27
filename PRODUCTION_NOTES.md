# Production Email Sending - Important Notes

## Email Sending Behavior

### Local Development (FLASK_ENV != 'production')
- ✅ Uses **threaded sending** via `start_sending_thread()`
- ✅ Emails send in background
- ✅ User sees "Campaign started!" message immediately
- ✅ Can continue working while emails send

### Production (FLASK_ENV = 'production')
- ✅ Uses **synchronous sending** via `send_campaign_sync()`
- ⏳ HTTP request blocks until all emails are sent
- ✅ User sees "Campaign completed!" message when finished
- ⏳ User must wait ~1-2 seconds per email

---

## Why This Change Was Needed

**Problem**: Background threading doesn't work with Gunicorn (Render's web server)
- Daemon threads are killed when HTTP request completes
- Emails would start sending but never finish
- All recipients remained "Pending" forever

**Solution**: Synchronous sending in production
- Emails send reliably
- Guaranteed delivery
- Works on any platform (Render, Railway, Heroku, etc.)

---

## Performance Expectations

### Small Campaigns (1-50 emails)
- **Time**: 1-2 minutes total
- **User Experience**: Wait a moment, see completion message
- **Status**: ✅ Acceptable

### Medium Campaigns (50-200 emails)
- **Time**: 3-7 minutes
- **User Experience**: Wait, but HTTP request may timeout
- **Status**: ⚠️ May need optimization

### Large Campaigns (200+ emails)
- **Time**: 10+ minutes
- **User Experience**: HTTP timeout likely
- **Status**: ❌ Need task queue (Celery) or batch processing

---

## Recommendations

For your current use case (email automation demo):
1. ✅ Keep small batches (≤50 recipients per campaign)
2. ✅ Use batch delays to avoid rate limits
3. ✅ Monitor campaign status in dashboard

For production scale:
1. Consider upgrading to task queue (Celery + Redis)
2. Or use batch API endpoint with external cron scheduler
3. Or split large campaigns into multiple smaller ones

---

## Environment Variables

Make sure these are set in Render dashboard:
- `FLASK_ENV=production` - Enables synchronous sending
- `RENDER_EXTERNAL_URL` - Your app URL (for tracking links)

---

## Testing

### Before deploying:
```bash
# Test locally first
python run.py
# Create campaign with 3-5 test emails
# Verify they send in background (threaded)
```

### After deploying to Render:
1. Create campaign with 3-5 test emails
2. Start campaign
3. Wait for "Campaign completed!" message
4. Check dashboard - all should be "Sent"
5. Verify actual emails arrived

---

## Troubleshooting

### Emails still pending on Render?
- Check environment variable: `FLASK_ENV` should be `production`
- Check logs for SMTP errors
- Verify Gmail credentials are correct

### Request timeout?
- Campaign too large (>100 emails)
- Reduce batch size or split campaign
- Consider external task queue

### Works locally but not on Render?
- Verify environment variables are set
- Check SMTP credentials in Render dashboard
- Review application logs
