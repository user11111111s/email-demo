import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
from .models import db, Campaign, Recipient
from datetime import datetime
import time

def send_async(app, campaign_id, sender_email, sender_password):
    """
    Background worker to send emails.
    """
    with app.app_context():
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return

        recipients = Recipient.query.filter_by(campaign_id=campaign_id, status='Pending').all()
        
        try:
            # Connect to SMTP
            # Assuming Gmail for now as per requirements, but could be configurable
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            
            base_url = "http://127.0.0.1:5000"  # Hardcoded for local dev

            for r in recipients:
                try:
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = campaign.subject
                    msg['From'] = sender_email
                    msg['To'] = r.email

                    # Construct Body with Tracking
                    # 1. Open Pixel
                    tracking_pixel = f'<img src="{base_url}/track/open/{r.id}" width="1" height="1" style="display:none;" />'
                    
                    # 2. Reply Link Replacement
                    # We look for the placeholder or [VERIFY_BUTTON] we inserted in JS
                    # A better way is to wrap the whole body and replacing a known token
                    
                    click_link = f"{base_url}/track/replied/{r.id}"
                    
                    # Replace [VERIFY_BUTTON] or similar constructions
                    # For V1: We will REPLACE the specific text "[VERIFY_BUTTON]" with the button HTML
                    # And also append the pixel at the end.
                    
                    body = campaign.body_content
                    
                    btn_html = f'''
                    <a href="{click_link}" style="display: inline-block; padding: 12px 24px; background-color: #6366f1; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; font-family: sans-serif;">
                        Verify Email
                    </a>
                    '''
                    
                    if '[VERIFY_BUTTON]' in body:
                        body = body.replace('[VERIFY_BUTTON]', btn_html)
                    
                    # Also look for {{ tracking_link }} just in case
                    body = body.replace('{{ tracking_link }}', click_link)
                    
                    final_html = f"<html><body>{body}<br>{tracking_pixel}</body></html>"

                    msg.attach(MIMEText(final_html, 'html'))

                    server.sendmail(sender_email, r.email, msg.as_string())
                    
                    r.status = 'Sent'
                    r.sent_at = datetime.now()
                    db.session.commit()
                    
                    # Small delay to avoid aggressive rate limits
                    time.sleep(1) 

                except Exception as e:
                    print(f"Failed to send to {r.email}: {e}")
                    r.status = 'Failed'
                    db.session.commit()

            campaign.status = 'Completed'
            db.session.commit()
            server.quit()
            
        except Exception as e:
            print(f"SMTP Error: {e}")
            campaign.status = 'Failed'  # Mark campaign as failed if logic breaks
            db.session.commit()

def start_sending_thread(app, campaign_id, sender_email, sender_password):
    thread = threading.Thread(target=send_async, args=(app, campaign_id, sender_email, sender_password))
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

