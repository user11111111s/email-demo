"""
Test CSV Upload with Name and DOB Fields

This script simulates uploading a CSV file through the web interface
to verify that name and DOB fields are correctly parsed and stored.
"""

from app import create_app, db
from app.models import Campaign, Recipient
from werkzeug.datastructures import FileStorage
from io import BytesIO

app = create_app()

with app.app_context():
    # Read the CSV file
    with open('test_birthdays.csv', 'rb') as f:
        csv_content = f.read()
    
    # Create a FileStorage object (simulates web upload)
    file_storage = FileStorage(
        stream=BytesIO(csv_content),
        filename='test_birthdays.csv',
        content_type='text/csv'
    )
    
    # Parse the file
    from app.utils import parse_recipient_file
    recipients_data, error = parse_recipient_file(file_storage, 'email', 'name', 'dob')
    
    print('\n🎂 CSV Upload Test - Name & DOB Parsing\n')
    print('=' * 100)
    
    if error:
        print(f'❌ Error: {error}')
        exit(1)
    
    if not recipients_data:
        print('❌ No recipients found!')
        exit(1)
    
    print(f'✅ Successfully parsed {len(recipients_data)} recipients\n')
    print('=' * 100)
    print(f'{"#":<4} {"Email":<40} {"Name":<20} {"DOB"}')
    print('=' * 100)
    
    birthdays_today = []
    for i, r in enumerate(recipients_data, 1):
        email = r.get('email', 'N/A')
        name = r.get('name', 'N/A')
        dob = r.get('dob', None)
        dob_str = str(dob) if dob else 'N/A'
        
        # Check if birthday is today
        if dob and dob.month == 1 and dob.day == 15:
            birthdays_today.append((email, name))
            marker = '  🎂 BIRTHDAY TODAY!'
        else:
            marker = ''
        
        print(f'{i:<4} {email:<40} {name:<20} {dob_str}{marker}')
    
    print('=' * 100)
    
    # Summary
    print(f'\n📊 Summary:')
    print(f'   Total recipients: {len(recipients_data)}')
    print(f'   Birthdays today:  {len(birthdays_today)}')
    
    if birthdays_today:
        print(f'\n🎉 People with birthdays today (Jan 15):')
        for email, name in birthdays_today:
            print(f'   - {name} ({email})')
    
    # Verify all fields present
    all_have_name = all('name' in r and r['name'] for r in recipients_data)
    all_have_dob = all('dob' in r and r['dob'] for r in recipients_data)
    
    print(f'\n✅ Verification:')
    print(f'   All have names: {"✓ Yes" if all_have_name else "✗ No"}')
    print(f'   All have DOBs:  {"✓ Yes" if all_have_dob else "✗ No"}')
    
    if all_have_name and all_have_dob:
        print(f'\n🎉 SUCCESS! CSV parsing works correctly with name and DOB fields!')
    else:
        print(f'\n⚠️  Some recipients are missing name or DOB data')
