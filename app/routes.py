from flask import render_template, request, redirect, url_for, flash, session
from flask import current_app as app
from . import db
from .models import Campaign, Recipient, TrackingEvent
from .utils import parse_recipient_file
import os
import pandas as pd
import io
from flask import send_file

@app.route('/')
def home():
    if 'sender_email' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        save_creds = request.form.get('save_creds')

        if not email or not password:
            flash('Email and App Password are required.', 'danger')
            return redirect(url_for('login'))

        # In a real app, we would Validate SMTP connection here before saving.
        session['sender_email'] = email
        session['sender_password'] = password 
        
        flash('Configuration saved successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html', saved_email=session.get('sender_email'), saved_password=session.get('sender_password'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'sender_email' not in session:
        return redirect(url_for('login'))
    
    # Check and start any scheduled campaigns that are due
    check_and_start_scheduled_campaigns()
        
    query = request.args.get('q', '').strip()
    
    if query:
        # Search by Name, Subject, or Recipient Email
        search_filter = f"%{query}%"
        campaigns = Campaign.query.outerjoin(Recipient).filter(
            (Campaign.name.ilike(search_filter)) | 
            (Campaign.subject.ilike(search_filter)) |
            (Recipient.email.ilike(search_filter))
        ).distinct().order_by(Campaign.created_at.desc()).all()
    else:
        campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()

    # In a real app we might want pagination or limiting
    return render_template('dashboard.html', campaigns=[c for c in campaigns], query=query) # Pass object directly to use property methods

@app.route('/campaign/new', methods=['GET', 'POST'])
def new_campaign():
    if 'sender_email' not in session:
        return redirect(url_for('login'))
        
    return render_template('campaign_setup.html')

@app.route('/campaign/create', methods=['POST'])
def create_campaign():
    if 'sender_email' not in session:
        return redirect(url_for('login'))

    name = request.form.get('campaign_name')
    subject = request.form.get('subject')
    body_content = request.form.get('body_content')
    scheduled_at_str = request.form.get('scheduled_at')
    
    # Check both inputs (Select for CSV, Text for Excel)
    email_column = request.form.get('email_column_select') or request.form.get('email_column_text')
    
    # Optional: Get name and DOB column names
    name_column = request.form.get('name_column_select') or request.form.get('name_column_text')
    dob_column = request.form.get('dob_column_select') or request.form.get('dob_column_text')
    
    file = request.files.get('recipient_file')
    
    if not file or not email_column:
        flash('Please upload a file and specify the email column.', 'danger')
        return redirect(url_for('new_campaign'))

    # Parse File with optional name and DOB columns
    recipients_data, error = parse_recipient_file(file, email_column, name_column, dob_column)
    
    if error:
        flash(f'Error parsing file: {error}', 'danger')
        return redirect(url_for('new_campaign'))
        
    if not recipients_data:
        flash('No valid emails found in the selected column.', 'warning')
        return redirect(url_for('new_campaign'))

    # Parse scheduled_at if provided
    scheduled_at = None
    if scheduled_at_str:
        try:
            from datetime import datetime
            # The form sends UTC datetime in ISO format (after JavaScript conversion)
            scheduled_at = datetime.fromisoformat(scheduled_at_str)
        except ValueError:
            flash('Invalid scheduled time format.', 'danger')
            return redirect(url_for('new_campaign'))

    # Create Campaign
    campaign = Campaign(name=name, subject=subject, body_content=body_content, status='Draft', scheduled_at=scheduled_at)
    campaign.sender_email = session.get('sender_email')
    campaign.sender_password = session.get('sender_password')
    db.session.add(campaign)
    db.session.commit()
    
    # Create Recipients with email, name, and dob (if available)
    recipients = []
    for recipient_data in recipients_data:
        recipient = Recipient(
            campaign_id=campaign.id,
            email=recipient_data['email'],
            name=recipient_data.get('name'),
            dob=recipient_data.get('dob')
        )
        recipients.append(recipient)
    
    db.session.add_all(recipients)
    db.session.commit()
    
    return redirect(url_for('review_campaign', campaign_id=campaign.id))

@app.route('/campaign/<int:campaign_id>/review')
def review_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    return render_template('campaign_review.html', campaign=campaign)

@app.route('/campaign/<int:campaign_id>/start', methods=['POST'])
def start_campaign(campaign_id):
    from datetime import datetime
    campaign = Campaign.query.get_or_404(campaign_id)
    
    sender_email = session.get('sender_email')
    sender_password = session.get('sender_password')
    
    if not sender_email or not sender_password:
        flash('Session expired. Please login again.', 'danger')
        return redirect(url_for('login'))

    # Get current local time
    now = datetime.now()
    
    # Check if campaign is scheduled for future
    if campaign.scheduled_at and campaign.scheduled_at > now:
        campaign.status = 'Scheduled'
        db.session.commit()
        scheduled_time = campaign.scheduled_at.strftime('%Y-%m-%d %H:%M:%S')
        flash(f'Campaign scheduled to send at {scheduled_time}', 'success')
        return redirect(url_for('dashboard'))
    
    # If scheduled_at is in the past or not set, send immediately
    campaign.status = 'Sending'
    db.session.commit()
    
    # Start Background Sending
    from .sender import start_sending_thread
    try:
        # Using current_app._get_current_object() to pass real app object to thread if needed
        # But our sender just needs app factory or app_context. 
        # Standard way: Pass app to thread.
        start_sending_thread(app._get_current_object(), campaign_id, sender_email, sender_password)
        flash('Campaign started! Emails are being dispatched in the background.', 'success')
    except Exception as e:
        flash(f'Error starting campaign: {e}', 'danger')
        campaign.status = 'Draft'
        db.session.commit()
    
    return redirect(url_for('dashboard'))

def check_and_start_scheduled_campaigns():
    """Check for campaigns scheduled to send and start them if due."""
    try:
        from datetime import datetime
        from .sender import start_sending_thread
        
        # Get current local time
        now = datetime.now()
        
        # Find all scheduled campaigns that are due
        due_campaigns = Campaign.query.filter(
            Campaign.status == 'Scheduled',
            Campaign.scheduled_at <= now
        ).all()
        
        for campaign in due_campaigns:
            try:
                # We can't access session here, so we'll need to get sender info differently
                # For now, we'll just mark it as sending - in production, you'd store this in the campaign
                campaign.status = 'Sending'
                db.session.commit()
                print(f"Starting scheduled campaign {campaign.id}")
                # Start the background thread with stored credentials
                if campaign.sender_email and campaign.sender_password:
                    start_sending_thread(app._get_current_object(), campaign.id, campaign.sender_email, campaign.sender_password)
            except Exception as e:
                print(f"Error starting scheduled campaign {campaign.id}: {e}")
    except Exception as e:
        # Silently fail if there's an issue (e.g., scheduled_at column doesn't exist yet)
        print(f"Scheduled campaigns check skipped: {e}")

@app.route('/campaign/<int:campaign_id>/delete')
def delete_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    db.session.delete(campaign)
    db.session.commit()
    flash('Campaign discarded.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/campaign/<int:campaign_id>')
def campaign_detail(campaign_id):
    if 'sender_email' not in session:
        return redirect(url_for('login'))
        
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Calculate stats for the specific campaign view
    stats = {
        'total': len(campaign.recipients),
        'sent': sum(1 for r in campaign.recipients if r.status == 'Sent'),
        'opened': sum(1 for r in campaign.recipients if any(e.type == 'open' for e in r.events)),
        'replied': sum(1 for r in campaign.recipients if any(e.type == 'replied' for e in r.events))
    }
    
    return render_template('campaign_detail.html', campaign=campaign, recipients=campaign.recipients, stats=stats)

# --- Tracking Routes ---

@app.route('/track/open/<int:recipient_id>')
def track_open(recipient_id):
    recipient = Recipient.query.get(recipient_id)
    if recipient:
        # Log Open Event if not already logged (or log every time)
        # For unique opens check existence
        exists = TrackingEvent.query.filter_by(recipient_id=recipient_id, type='open').first()
        if not exists:
            event = TrackingEvent(recipient_id=recipient_id, type='open')
            db.session.add(event)
            db.session.commit()
            
    # Return 1x1 transparent pixel
    # Base64 of a 1x1 transparent gif
    pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    return app.response_class(pixel, mimetype='image/gif')

@app.route('/track/replied/<int:recipient_id>')
def track_replied(recipient_id):
    recipient = Recipient.query.get(recipient_id)
    if recipient:
        # Log Reply Event
        exists = TrackingEvent.query.filter_by(recipient_id=recipient_id, type='replied').first()
        if not exists:
            event = TrackingEvent(recipient_id=recipient_id, type='replied')
            db.session.add(event)
            db.session.commit()
            
    return render_template('tracking_success.html')

@app.route('/campaign/<int:campaign_id>/replied')
def campaign_replied(campaign_id):
    if 'sender_email' not in session:
        return redirect(url_for('login'))
        
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Get all recipients who have replied
    replied_recipients = [
        r for r in campaign.recipients 
        if any(e.type == 'replied' for e in r.events)
    ]
    
    return render_template('campaign_replied.html', campaign=campaign, replied_recipients=replied_recipients)

@app.route('/export/report')
def export_report():
    if 'sender_email' not in session:
        return redirect(url_for('login'))
        
    campaign_id = request.args.get('campaign_id', type=int)
    
    if campaign_id:
        campaigns = [Campaign.query.get_or_404(campaign_id)]
        filename = f"report_campaign_{campaign_id}.xlsx"
    else:
        campaigns = Campaign.query.all()
        filename = "all_campaigns_report.xlsx"
        
    data = []
    for c in campaigns:
        for r in c.recipients:
            data.append({
                'Campaign Name': c.name,
                'Subject': c.subject,
                'Recipient Email': r.email,
                'Status': r.status,
                'Sent At': r.sent_at.strftime('%Y-%m-%d %H:%M:%S') if r.sent_at else 'N/A',
                'Opens': sum(1 for e in r.events if e.type == 'open'),
                'Replies': sum(1 for e in r.events if e.type == 'replied'),
                'Created At': c.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
            
    if not data:
        flash('No data available to export.', 'warning')
        return redirect(url_for('dashboard'))
        
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Email Report')
        
        # Add a summary sheet if exporting all
        if not campaign_id:
            summary_data = [c.to_dict() for c in campaigns]
            summary_df = pd.DataFrame(summary_data)
            # Clean up dict for excel
            if not summary_df.empty:
                cols_to_keep = ['name', 'subject', 'status', 'created_at', 'total_recipients', 'sent_count', 'open_count', 'replied_count']
                summary_df = summary_df[cols_to_keep]
                summary_df.columns = ['Campaign', 'Subject', 'Status', 'Date', 'Recipients', 'Sent', 'Opens', 'Replies']
                summary_df.to_excel(writer, index=False, sheet_name='Campaign Summary')
                
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

# --- Cron Endpoint for Birthday Automation ---

@app.route('/cron/birthday-check')
def cron_birthday_check():
    """
    Cron endpoint for external services to trigger birthday checks.
    
    This endpoint allows external cron services (cron-job.org, GitHub Actions, Render cron, etc.)
    to trigger birthday email automation without requiring APScheduler to run 24/7.
    
    Security: Requires CRON_SECRET environment variable as query parameter 'key'.
    
    Usage:
        curl "https://yourapp.com/cron/birthday-check?key=YOUR_CRON_SECRET"
    
    Returns:
        JSON with status and message
    """
    # Validate secret key for security
    provided_key = request.args.get('key')
    expected_secret = os.environ.get('CRON_SECRET')
    
    if not expected_secret:
        return {'error': 'CRON_SECRET not configured on server'}, 500
    
    if not provided_key or provided_key != expected_secret:
        return {'error': 'unauthorized'}, 403
    
    # Execute birthday logic (app context is already available in Flask request)
    from .birthday_scheduler import check_and_send_birthday_emails
    
    try:
        check_and_send_birthday_emails()
        return {
            'status': 'ok',
            'message': 'Birthday check executed successfully'
        }, 200
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Birthday check failed: {str(e)}'
        }, 500

