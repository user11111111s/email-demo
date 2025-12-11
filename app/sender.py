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
                    
                    # 2. Click Link Replacement
                    # We look for the placeholder or [VERIFY_BUTTON] we inserted in JS
                    # A better way is to wrap the whole body and replacing a known token
                    
                    click_link = f"{base_url}/track/click/{r.id}"
                    
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
                    r.sent_at = datetime.utcnow()
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
