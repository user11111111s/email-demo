from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask import current_app as app
from . import db
from .models import Campaign, Recipient, TrackingEvent
from .utils import parse_recipient_file, get_file_headers
import os

@app.route('/api/get-columns', methods=['POST'])
def get_columns():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    try:
        columns, error = get_file_headers(file)
        if error:
            return jsonify({'error': error}), 400
            
        return jsonify({'columns': columns})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        
    campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
    # In a real app we might want pagination or limiting
    return render_template('dashboard.html', campaigns=[c for c in campaigns]) # Pass object directly to use property methods

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
    
    # Check both inputs (Select for CSV, Text for Excel)
    email_column = request.form.get('email_column_select') or request.form.get('email_column_text')
    
    file = request.files.get('recipient_file')
    
    if not file or not email_column:
        flash('Please upload a file and specify the email column.', 'danger')
        return redirect(url_for('new_campaign'))

    # Parse File
    emails, error = parse_recipient_file(file, email_column)
    
    if error:
        flash(f'Error parsing file: {error}', 'danger')
        return redirect(url_for('new_campaign'))
        
    if not emails:
        flash('No valid emails found in the selected column.', 'warning')
        return redirect(url_for('new_campaign'))

    # Create Campaign
    campaign = Campaign(name=name, subject=subject, body_content=body_content, status='Draft')
    db.session.add(campaign)
    db.session.commit()
    
    # Create Recipients
    recipients = [Recipient(campaign_id=campaign.id, email=email) for email in emails]
    db.session.add_all(recipients)
    db.session.commit()
    
    return redirect(url_for('review_campaign', campaign_id=campaign.id))

@app.route('/campaign/<int:campaign_id>/review')
def review_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    return render_template('campaign_review.html', campaign=campaign)

@app.route('/campaign/<int:campaign_id>/start', methods=['POST'])
def start_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    sender_email = session.get('sender_email')
    sender_password = session.get('sender_password')
    
    if not sender_email or not sender_password:
        flash('Session expired. Please login again.', 'danger')
        return redirect(url_for('login'))

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
        'clicked': sum(1 for r in campaign.recipients if any(e.type == 'click' for e in r.events))
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

@app.route('/track/click/<int:recipient_id>')
def track_click(recipient_id):
    recipient = Recipient.query.get(recipient_id)
    if recipient:
        # Log Click Event
        exists = TrackingEvent.query.filter_by(recipient_id=recipient_id, type='click').first()
        if not exists:
            event = TrackingEvent(recipient_id=recipient_id, type='click')
            db.session.add(event)
            db.session.commit()
            
    return render_template('tracking_success.html')
