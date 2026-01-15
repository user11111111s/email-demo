"""
Temporarily change scheduler to run in 2 minutes for testing
"""

from datetime import datetime

# Get current time
now = datetime.now()
current_hour = now.hour
current_minute = now.minute

# Calculate 2 minutes from now
test_minute = (current_minute + 2) % 60
test_hour = current_hour if (current_minute + 2) < 60 else (current_hour + 1) % 24

print(f"📍 Current time: {now.strftime('%H:%M:%S')}")
print(f"\n🎯 To test the scheduler automatically:")
print(f"   Change line 85-86 in app/__init__.py to:")
print(f"   hour={test_hour},")
print(f"   minute={test_minute},")
print(f"\n⏰ This will make the scheduler run at {test_hour:02d}:{test_minute:02d}")
print(f"   (approximately 2 minutes from now)")
print(f"\n📝 Steps:")
print(f"   1. Stop the current app (Ctrl+C in the terminal)")
print(f"   2. Edit app/__init__.py lines 85-86")  
print(f"   3. Restart: python run.py")
print(f"   4. Wait until {test_hour:02d}:{test_minute:02d} - scheduler will run automatically!")
print(f"\n✅ You'll see birthday emails sent automatically in the console")
