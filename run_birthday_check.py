import os
os.environ['BIRTHDAY_SENDER_EMAIL'] = 'tajaneabhishek5@gmail.com'
os.environ['BIRTHDAY_SENDER_PASSWORD'] = 'cgel xfjy wxkz rzun'

from app import create_app, db
from app.models import Recipient
from app.birthday_scheduler import check_and_send_birthday_emails
from datetime import date

app = create_app()
with app.app_context():
    # Check what's in the database
    today = date.today()
    print('\n📊 Database Check:')
    print('=' * 80)
    
    all_recipients = Recipient.query.filter(Recipient.dob.isnot(None)).all()
    print(f'Total recipients with DOB: {len(all_recipients)}\n')
    
    for i, r in enumerate(all_recipients, 1):
        is_today = r.dob.month == today.month and r.dob.day == today.day
        marker = '🎂 BIRTHDAY TODAY!' if is_today else ''
        print(f'{i}. Campaign {r.campaign_id} - {r.email}')
        print(f'   Name: {r.name}, DOB: {r.dob} {marker}')
    
    print('\n' + '=' * 80)
    
    # Run birthday check
    print('\n🎂 Running Birthday Check...\n')
    check_and_send_birthday_emails()
