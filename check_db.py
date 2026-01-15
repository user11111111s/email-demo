"""
Database Inspector - View all recipients and their details
"""

from app import create_app, db
from app.models import Recipient, Campaign
from datetime import date

app = create_app()

def show_all_recipients():
    """Display all recipients in the database"""
    with app.app_context():
        recipients = Recipient.query.all()
        
        print('\n' + '=' * 100)
        print(f'{"ID":<5} {"Campaign":<12} {"Email":<40} {"Name":<20} {"DOB"}')
        print('=' * 100)
        
        for r in recipients:
            campaign_id = f'Camp {r.campaign_id}'
            name = r.name or 'N/A'
            dob = str(r.dob) if r.dob else 'N/A'
            print(f'{r.id:<5} {campaign_id:<12} {r.email:<40} {name:<20} {dob}')
        
        print('=' * 100)
        print(f'Total recipients: {len(recipients)}\n')

def show_recipients_with_birthdays():
    """Display only recipients with DOB set"""
    with app.app_context():
        today = date.today()
        recipients = Recipient.query.filter(Recipient.dob.isnot(None)).all()
        
        print('\n' + '=' * 100)
        print(f'RECIPIENTS WITH BIRTHDAYS')
        print('=' * 100)
        print(f'{"ID":<5} {"Campaign":<12} {"Email":<40} {"Name":<20} {"DOB":<15} {"Status"}')
        print('=' * 100)
        
        for r in recipients:
            campaign_id = f'Camp {r.campaign_id}'
            name = r.name or 'N/A'
            dob_str = str(r.dob)
            
            # Check if birthday is today
            is_today = r.dob.month == today.month and r.dob.day == today.day
            status = '🎂 TODAY!' if is_today else ''
            
            print(f'{r.id:<5} {campaign_id:<12} {r.email:<40} {name:<20} {dob_str:<15} {status}')
        
        print('=' * 100)
        print(f'Total with DOB: {len(recipients)}\n')

def show_campaigns():
    """Display all campaigns"""
    with app.app_context():
        campaigns = Campaign.query.all()
        
        print('\n' + '=' * 100)
        print(f'ALL CAMPAIGNS')
        print('=' * 100)
        print(f'{"ID":<5} {"Name":<30} {"Status":<15} {"Recipients"}')
        print('=' * 100)
        
        for c in campaigns:
            recipient_count = len(c.recipients)
            print(f'{c.id:<5} {c.name:<30} {c.status:<15} {recipient_count}')
        
        print('=' * 100)
        print(f'Total campaigns: {len(campaigns)}\n')

if __name__ == '__main__':
    print('\n📊 DATABASE INSPECTOR')
    
    # Show all campaigns
    show_campaigns()
    
    # Show all recipients
    show_all_recipients()
    
    # Show recipients with birthdays
    show_recipients_with_birthdays()
