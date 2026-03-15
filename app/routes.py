from flask import render_template, request, redirect, url_for, flash, session, Blueprint, current_app
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from .models import User, Campaign, Recipient, TrackingEvent, SenderAccount
from .utils import parse_recipient_file, parse_manual_emails, encrypt_password, decrypt_password
import os
import pandas as pd
import io
import smtplib
from flask import send_file

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('main.login'))
    return redirect(url_for('main.dashboard'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('email') # Using email field as username for now
        password = request.form.get('password')

        if not username or not password:
            flash('Username and Password are required.', 'danger')
            return redirect(url_for('main.login'))

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('main.login'))

    return render_template('login.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    
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

@main_bp.route('/campaign/new', methods=['GET', 'POST'])
@login_required
def new_campaign():
    accounts = SenderAccount.query.filter_by(user_id=current_user.id, is_active=True).all()
    if not accounts:
        flash('Please add at least one email account before creating a campaign.', 'warning')
        return redirect(url_for('main.manage_accounts'))
    return render_template('campaign_setup.html', accounts=accounts)

@main_bp.route('/campaign/create', methods=['POST'])
@login_required
def create_campaign():

    name = request.form.get('campaign_name')
    subject = request.form.get('subject')
    body_content = request.form.get('body_content')
    scheduled_at_str = request.form.get('scheduled_at')
    
    # Get batch config
    try:
        batch_size = int(request.form.get('batch_size', 50))
    except (ValueError, TypeError):
        batch_size = 50
        
    try:
        batch_delay = int(request.form.get('batch_delay', 5))
    except (ValueError, TypeError):
        batch_delay = 5
    
    # Check both inputs (Select for CSV, Text for Excel)
    email_column = request.form.get('email_column_select') or request.form.get('email_column_text')
    
    # Optional: Get name and DOB column names
    name_column = request.form.get('name_column_select') or request.form.get('name_column_text')
    dob_column = request.form.get('dob_column_select') or request.form.get('dob_column_text')
    
    file = request.files.get('recipient_file')
    manual_emails_input = request.form.get('manual_emails', '').strip()
    
    if not file and not manual_emails_input:
        flash('Please upload a file or enter emails manually.', 'danger')
        return redirect(url_for('main.new_campaign'))

    recipients_data = []
    
    # 1. Parse File if provided
    if file and file.filename:
        if not email_column:
            flash('Please specify the email column for the uploaded file.', 'danger')
            return redirect(url_for('main.new_campaign'))
            
        file_recipients, error = parse_recipient_file(file, email_column, name_column, dob_column)
        if error:
            flash(f'Error parsing file: {error}', 'danger')
            return redirect(url_for('main.new_campaign'))
        recipients_data.extend(file_recipients)
        
    # 2. Parse Manual Emails if provided
    if manual_emails_input:
        manual_recipients = parse_manual_emails(manual_emails_input)
        # Deduplicate against file recipients
        seen_emails = {r['email'] for r in recipients_data}
        for mr in manual_recipients:
            if mr['email'] not in seen_emails:
                recipients_data.append(mr)
                seen_emails.add(mr['email'])
        
    if not recipients_data:
        flash('No valid emails found.', 'warning')
        return redirect(url_for('main.new_campaign'))

    # Parse scheduled_at if provided
    scheduled_at = None
    if scheduled_at_str:
        try:
            from datetime import datetime
            # The form sends UTC datetime in ISO format (after JavaScript conversion)
            scheduled_at = datetime.fromisoformat(scheduled_at_str)
        except ValueError:
            flash('Invalid scheduled time format.', 'danger')
            return redirect(url_for('main.new_campaign'))

    # Selected accounts
    selected_account_ids = request.form.getlist('selected_accounts')
    if not selected_account_ids:
        flash('Please select at least one email account to send from.', 'danger')
        return redirect(url_for('main.new_campaign'))
    
    selected_account_ids = [int(aid) for aid in selected_account_ids]

    # Create Campaign
    campaign = Campaign(
        user_id=current_user.id,
        name=name, 
        subject=subject, 
        body_content=body_content, 
        status='Draft', 
        scheduled_at=scheduled_at,
        batch_size=batch_size,
        batch_delay=batch_delay
    )
    campaign.selected_account_ids = selected_account_ids
    db.session.add(campaign)
    db.session.commit()
    
    # Handle Attachments
    attachments = request.files.getlist('attachments')
    if attachments:
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', str(campaign.id))
        os.makedirs(upload_folder, exist_ok=True)
        
        for att in attachments:
            if att and att.filename:
                from werkzeug.utils import secure_filename
                filename = secure_filename(att.filename)
                file_path = os.path.join(upload_folder, filename)
                att.save(file_path)
                
                attachment_rec = Attachment(
                    campaign_id=campaign.id,
                    filename=filename,
                    file_path=file_path,
                    mime_type=att.content_type
                )
                db.session.add(attachment_rec)
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
    
    return redirect(url_for('main.review_campaign', campaign_id=campaign.id))

@main_bp.route('/campaign/<int:campaign_id>/review')
@login_required
def review_campaign(campaign_id):
    campaign = Campaign.query.filter_by(id=campaign_id, user_id=current_user.id).first_or_404()
    return render_template('campaign_review.html', campaign=campaign)

@main_bp.route('/campaign/<int:campaign_id>/start', methods=['POST'])
@login_required
def start_campaign(campaign_id):
    from datetime import datetime
    campaign = Campaign.query.filter_by(id=campaign_id, user_id=current_user.id).first_or_404()

    # Get current local time
    now = datetime.now()
    
    # Check if campaign is scheduled for future
    if campaign.scheduled_at and campaign.scheduled_at > now:
        campaign.status = 'Scheduled'
        db.session.commit()
        scheduled_time = campaign.scheduled_at.strftime('%Y-%m-%d %H:%M:%S')
        flash(f'Campaign scheduled to send at {scheduled_time}', 'success')
        return redirect(url_for('main.dashboard'))
    
    # If scheduled_at is in the past or not set, send immediately
    campaign.status = 'Sending'
    db.session.commit()
    
    # Start Background Sending
    from .sender import start_sending_thread
    try:
        start_sending_thread(current_app._get_current_object(), campaign_id)
        flash('Campaign started! Emails are being dispatched in the background.', 'success')
    except Exception as e:
        flash(f'Error starting campaign: {e}', 'danger')
        campaign.status = 'Draft'
        db.session.commit()
    
    return redirect(url_for('main.dashboard'))

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
                    start_sending_thread(current_app._get_current_object(), campaign.id, campaign.sender_email, campaign.sender_password)
            except Exception as e:
                print(f"Error starting scheduled campaign {campaign.id}: {e}")
    except Exception as e:
        # Silently fail if there's an issue (e.g., scheduled_at column doesn't exist yet)
        print(f"Scheduled campaigns check skipped: {e}")

@main_bp.route('/campaign/<int:campaign_id>/delete')
def delete_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    db.session.delete(campaign)
    db.session.commit()
    flash('Campaign discarded.', 'info')
    return redirect(url_for('main.dashboard'))

@main_bp.route('/campaign/<int:campaign_id>')
@login_required
def campaign_detail(campaign_id):
    campaign = Campaign.query.filter_by(id=campaign_id, user_id=current_user.id).first_or_404()
    
    # Calculate stats for the specific campaign view
    stats = {
        'total': len(campaign.recipients),
        'sent': sum(1 for r in campaign.recipients if r.status == 'Sent'),
        'opened': sum(1 for r in campaign.recipients if any(e.type == 'open' for e in r.events)),
        'replied': sum(1 for r in campaign.recipients if any(e.type == 'replied' for e in r.events))
    }
    
    return render_template('campaign_detail.html', campaign=campaign, recipients=campaign.recipients, stats=stats)

# --- Tracking Routes ---

@main_bp.route('/track/open/<int:recipient_id>')
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

@main_bp.route('/track/replied/<int:recipient_id>')
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

@main_bp.route('/campaign/<int:campaign_id>/replied')
def campaign_replied(campaign_id):
    if 'sender_email' not in session:
        return redirect(url_for('main.login'))
        
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Get all recipients who have replied
    replied_recipients = [
        r for r in campaign.recipients 
        if any(e.type == 'replied' for e in r.events)
    ]
    
    return render_template('campaign_replied.html', campaign=campaign, replied_recipients=replied_recipients)

@main_bp.route('/export/report')
def export_report():
    if 'sender_email' not in session:
        return redirect(url_for('main.login'))
        
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
        return redirect(url_for('main.dashboard'))
        
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

# --- Account Management Routes ---

@main_bp.route('/accounts')
@login_required
def manage_accounts():
    accounts = SenderAccount.query.filter_by(user_id=current_user.id).all()
    return render_template('manage_accounts.html', accounts=accounts)

@main_bp.route('/accounts/add', methods=['POST'])
@login_required
def add_account():
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        flash('Email and App Password are required.', 'danger')
        return redirect(url_for('main.manage_accounts'))
    
    encrypted_pw = encrypt_password(password)
    
    new_account = SenderAccount(
        user_id=current_user.id,
        email=email,
        encrypted_password=encrypted_pw
    )
    db.session.add(new_account)
    db.session.commit()
    
    flash(f'Account {email} added successfully!', 'success')
    return redirect(url_for('main.manage_accounts'))

@main_bp.route('/accounts/<int:account_id>/delete')
@login_required
def delete_account(account_id):
    account = SenderAccount.query.filter_by(id=account_id, user_id=current_user.id).first_or_404()
    db.session.delete(account)
    db.session.commit()
    flash('Account deleted.', 'info')
    return redirect(url_for('main.manage_accounts'))

@main_bp.route('/accounts/<int:account_id>/test')
@login_required
def test_account_connection(account_id):
    account = SenderAccount.query.filter_by(id=account_id, user_id=current_user.id).first_or_404()
    password = decrypt_password(account.encrypted_password)
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(account.email, password)
        server.quit()
        flash(f'Connection test for {account.email} successful!', 'success')
    except Exception as e:
        flash(f'Connection test for {account.email} failed: {e}', 'danger')
        
    return redirect(url_for('main.manage_accounts'))
