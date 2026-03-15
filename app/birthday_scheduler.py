"""
Birthday Scheduler Module

Automatically checks for recipients with birthdays today and sends birthday emails.
Prevents duplicate sends by tracking the last year a birthday email was sent.
"""

from datetime import datetime, date
from .models import db, Recipient, TrackingEvent
from .sender import send_birthday_email
import os

def check_and_send_birthday_emails():
    """
    Main function to check for today's birthdays and send birthday emails.
    
    This function:
    1. Queries all recipients with a birthday today (month and day match)
    2. Filters out recipients who already received a birthday email this year
    3. Sends birthday emails to eligible recipients
    4. Logs the send event to prevent duplicates
    
    Should be called daily by the scheduler.
    Note: Requires Flask app context (handled by wrapper function)
    """
    try:
        today = date.today()
        current_year = today.year
        
        # Get default sender credentials from environment or config
        sender_email = os.environ.get('BIRTHDAY_SENDER_EMAIL')
        sender_password = os.environ.get('BIRTHDAY_SENDER_PASSWORD')
        
        if not sender_email or not sender_password:
            print("⚠️  Birthday sender credentials not configured. Skipping birthday check.")
            return
        
        # Find all recipients whose birthday is today (month and day match)
        # Filter recipients who have a DOB set
        recipients_with_birthdays = Recipient.query.filter(
            Recipient.dob.isnot(None)
        ).all()
        
        # Filter to only those with birthday today
        birthday_recipients = []
        for recipient in recipients_with_birthdays:
            if recipient.dob.month == today.month and recipient.dob.day == today.day:
                birthday_recipients.append(recipient)
        
        if not birthday_recipients:
            print(f"ℹ️  No birthdays today ({today.strftime('%B %d, %Y')})")
            return
        
        print(f"🎂 Found {len(birthday_recipients)} birthday(s) today!")
        
        sent_count = 0
        skipped_count = 0
        
        for recipient in birthday_recipients:
            # Check if birthday email was already sent this year to this EMAIL
            if already_sent_this_year_to_email(recipient.email, current_year):
                print(f"⏭️  Skipped {recipient.email} - already sent this year")
                skipped_count += 1
                continue
            
            # Send birthday email
            success = send_birthday_email(recipient, sender_email, sender_password)
            
            if success:
                # Log the birthday_sent event for this email
                log_birthday_sent_for_email(recipient.id, recipient.email, current_year)
                sent_count += 1
                print(f"✅ Sent birthday email to {recipient.email} ({recipient.name or 'Friend'})")
            else:
                print(f"❌ Failed to send birthday email to {recipient.email}")
        
        print(f"📊 Summary: {sent_count} sent, {skipped_count} skipped")
        
    except Exception as e:
        # Don't crash the app if birthday checking fails
        print(f"❌ Error in birthday check: {e}")
        import traceback
        traceback.print_exc()

def already_sent_this_year_to_email(email, year):
    """
    Check if a birthday email was already sent to this EMAIL ADDRESS this year.
    This prevents duplicate sends when the same email exists in multiple campaigns.
    
    Args:
        email: Email address to check
        year: Year to check for
        
    Returns:
        True if already sent this year, False otherwise
    """
    # Check for a birthday_sent event this year for ANY recipient with this email
    year_start = datetime(year, 1, 1)
    year_end = datetime(year, 12, 31, 23, 59, 59)
    
    # Join TrackingEvent with Recipient to check by email
    event = db.session.query(TrackingEvent).join(Recipient).filter(
        Recipient.email == email,
        TrackingEvent.type == 'birthday_sent',
        TrackingEvent.timestamp >= year_start,
        TrackingEvent.timestamp <= year_end
    ).first()
    
    return event is not None

def log_birthday_sent_for_email(recipient_id, email, year):
    """
    Log that a birthday email was sent to prevent duplicate sends.
    Records the event for the recipient_id, but the check uses email.
    
    Args:
        recipient_id: ID of the recipient (for the foreign key)
        email: Email address that received the birthday wish
        year: Year the email was sent
    """
    event = TrackingEvent(
        recipient_id=recipient_id,
        type='birthday_sent',
        timestamp=datetime.now()
    )
    db.session.add(event)
    db.session.commit()
