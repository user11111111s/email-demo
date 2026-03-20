import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
from .models import db, Campaign, Recipient
from datetime import datetime
import time

from email.mime.application import MIMEApplication
from .models import db, Campaign, Recipient, SenderAccount, Attachment
from .utils import decrypt_password

def send_async(app, campaign_id):
    """
    Background worker to send emails with smart routing.
    """
    with app.app_context():
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return

        recipients = Recipient.query.filter_by(campaign_id=campaign_id, status='Pending').all()
        if not recipients:
            campaign.status = 'Completed'
            db.session.commit()
            return

        # Load selected accounts and decrypt passwords
        sender_accounts = []
        for aid in campaign.selected_account_ids:
            acc = SenderAccount.query.get(aid)
            if acc and acc.is_active:
                password = decrypt_password(acc.encrypted_password)
                if password:
                    sender_accounts.append({
                        'model': acc,
                        'email': acc.email,
                        'password': password
                    })
        
        if not sender_accounts:
            campaign.status = 'Failed'  # No valid accounts to send from
            db.session.commit()
            return

        # Load attachments
        campaign_attachments = Attachment.query.filter_by(campaign_id=campaign_id).all()
        
        current_account_idx = 0
        server = None
        
        def get_smtp_server(account):
            s = smtplib.SMTP('smtp.gmail.com', 587)
            s.starttls()
            s.login(account['email'], account['password'])
            return s

        try:
            import os
            base_url = os.environ.get("BASE_URL", "http://127.0.0.1:5002").rstrip('/')

            sent_in_batch = 0
            for i, r in enumerate(recipients):
                # Check if ANY account has quota left
                available_accounts = [acc for acc in sender_accounts if acc['model'].daily_quota_used < 495]
                if not available_accounts:
                    print("All selected accounts have reached their daily quota.")
                    # Requirement says provide clear error handling if all hit quota.
                    campaign.status = 'Failed' # Or 'Partially Completed'?
                    db.session.commit()
                    break

                # Ensure current_account_idx points to a valid account
                acc_data = sender_accounts[current_account_idx]
                while acc_data['model'].daily_quota_used >= 495:
                    current_account_idx = (current_account_idx + 1) % len(sender_accounts)
                    acc_data = sender_accounts[current_account_idx]

                acc_data = sender_accounts[current_account_idx]
                
                # Ensure server is connected to current account
                if server is None or server.user != acc_data['email']:
                    if server: server.quit()
                    try:
                        server = get_smtp_server(acc_data)
                    except Exception as e:
                        print(f"Failed to connect to {acc_data['email']}: {e}")
                        current_account_idx += 1
                        continue # Try next account

                try:
                    msg = MIMEMultipart('mixed') # Use mixed for attachments
                    msg['Subject'] = campaign.subject
                    msg['From'] = acc_data['email']
                    msg['To'] = r.email

                    # HTML Body part
                    body_container = MIMEMultipart('alternative')
                    msg.attach(body_container)

                    tracking_pixel = f'<img src="{base_url}/track/open/{r.id}" width="1" height="1" style="display:none;" />'
                    click_link = f"{base_url}/track/replied/{r.id}"
                    
                    body = campaign.body_content
                    btn_html = f'''
                    <a href="{click_link}" style="display: inline-block; padding: 12px 24px; background-color: #6366f1; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; font-family: sans-serif;">
                        Verify Email
                    </a>
                    '''
                    
                    if '[VERIFY_BUTTON]' in body:
                        body = body.replace('[VERIFY_BUTTON]', btn_html)
                    body = body.replace('{{ tracking_link }}', click_link)
                    final_html = f"<html><body>{body}<br>{tracking_pixel}</body></html>"

                    body_container.attach(MIMEText(final_html, 'html'))

                    # Attachments
                    for att in campaign_attachments:
                        try:
                            with open(att.file_path, "rb") as f:
                                part = MIMEApplication(f.read(), Name=att.filename)
                                part['Content-Disposition'] = f'attachment; filename="{att.filename}"'
                                msg.attach(part)
                        except Exception as ae:
                            print(f"Failed to attach file {att.filename}: {ae}")

                    server.sendmail(acc_data['email'], r.email, msg.as_string())
                    
                    # Update Recipient and Account stats
                    r.status = 'Sent'
                    r.sent_at = datetime.now()
                    r.sender_account_id = acc_data['model'].id
                    
                    acc_data['model'].daily_quota_used += 1
                    acc_data['model'].last_used_at = datetime.now()
                    
                    db.session.commit()
                    
                    sent_in_batch += 1
                    time.sleep(1) 
                    
                    if sent_in_batch >= campaign.batch_size:
                        sent_in_batch = 0
                        # Rotate to next account if we have more than one
                        if len(sender_accounts) > 1:
                            print(f"Batch limit reached. Rotating to next account.")
                            current_account_idx = (current_account_idx + 1) % len(sender_accounts)
                            
                        # Respect the user's batch delay regardless of rotation
                        if campaign.batch_delay > 0 and (i + 1) < len(recipients):
                            print(f"Pausing for {campaign.batch_delay} minutes.")
                            time.sleep(campaign.batch_delay * 60)

                except Exception as e:
                    print(f"Failed to send to {r.email}: {e}")
                    r.status = 'Failed'
                    db.session.commit()

            if campaign.status != 'Failed':
                campaign.status = 'Completed'
            db.session.commit()
            if server: server.quit()
            
        except Exception as e:
            error_msg = f"Critical Error for campaign {campaign_id}: {e}"
            print(error_msg)
            campaign.status = 'Failed'
            db.session.commit()

def start_sending_thread(app, campaign_id, sender_email=None, sender_password=None):
    # Ignoring raw credentials as we now use stored accounts from campaign
    thread = threading.Thread(target=send_async, args=(app, campaign_id))
    thread.daemon = True
    thread.start()

def send_birthday_email(recipient, sender_email, sender_password):
    """
    Send a birthday email to a single recipient.
    Reuses SMTP logic from the existing campaign sender.
    
    Args:
        recipient: Recipient model instance with email, name, and dob
        sender_email: Email address to send from
        sender_password: Password for the sender email
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Load birthday email template
        import os
        from flask import current_app
        
        template_path = os.path.join(current_app.root_path, '..', 'templates', 'birthday_email.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Replace {{ name }} placeholder with recipient's name or "Friend" if no name
        recipient_name = recipient.name if recipient.name else "Friend"
        email_body = template_content.replace('{{ name }}', recipient_name)
        
        # Connect to SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🎉 Happy Birthday {recipient_name}!"
        msg['From'] = sender_email
        msg['To'] = recipient.email
        
        # Attach HTML body
        msg.attach(MIMEText(email_body, 'html'))
        
        # Send email
        server.sendmail(sender_email, recipient.email, msg.as_string())
        server.quit()
        
        return True
        
    except Exception as e:
        print(f"Failed to send birthday email to {recipient.email}: {e}")
        return False

