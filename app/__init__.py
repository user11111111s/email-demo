from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import atexit

db = SQLAlchemy()

# Global scheduler instance
scheduler = None

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'dev-key-please-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)

    with app.app_context():
        # Import parts of our application
        from . import routes, models
        
        # Create database tables
        db.create_all()

        # Ensure database has expected columns for existing installations.
        # Older databases may lack new columns added to the Campaign model.
        try:
            # Get column names for campaign table
            with db.engine.begin() as conn:
                result = conn.execute(db.text("PRAGMA table_info(campaign)"))
                cols = [row[1] for row in result.fetchall()]
                
                # Check and add missing columns
                if 'scheduled_at' not in cols:
                    conn.execute(db.text("ALTER TABLE campaign ADD COLUMN scheduled_at DATETIME"))
                if 'sender_email' not in cols:
                    conn.execute(db.text("ALTER TABLE campaign ADD COLUMN sender_email VARCHAR(120)"))
                if 'sender_password' not in cols:
                    conn.execute(db.text("ALTER TABLE campaign ADD COLUMN sender_password VARCHAR(255)"))
                
                # Get column names for recipient table
                result = conn.execute(db.text("PRAGMA table_info(recipient)"))
                recipient_cols = [row[1] for row in result.fetchall()]
                
                # Check and add missing columns for birthday wishes feature
                if 'name' not in recipient_cols:
                    conn.execute(db.text("ALTER TABLE recipient ADD COLUMN name VARCHAR(100)"))
                if 'dob' not in recipient_cols:
                    conn.execute(db.text("ALTER TABLE recipient ADD COLUMN dob DATE"))
        except Exception:
            # If anything goes wrong, skip silently; app can still run.
            pass
    
    # Setup APScheduler for automatic birthday wishes
    setup_scheduler(app)

    return app

def setup_scheduler(app):
    """
    Set up APScheduler to run daily birthday checks.
    Scheduler runs in a background thread and doesn't block Flask requests.
    """
    global scheduler
    
    # Only set up scheduler once
    if scheduler is not None:
        return
    
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from .birthday_scheduler import check_and_send_birthday_emails
        
        # Create background scheduler
        scheduler = BackgroundScheduler(daemon=True)
        
        # Schedule daily birthday check at 00:05 (5 minutes after midnight)
        # TEMP: Changed to 22:45 for testing .env file (normally hour=0, minute=5)
        scheduler.add_job(
            func=lambda: check_and_send_birthday_emails_wrapper(app),
            trigger='cron',
            hour=22,
            minute=49,
            id='birthday_check',
            name='Daily Birthday Check',
            replace_existing=True
        )
        
        # Start the scheduler
        scheduler.start()
        
        print(f"✅ Birthday scheduler started - test mode: checks at 22:45 (normally 00:05)")
        
        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown() if scheduler else None)
        
    except ImportError:
        print("⚠️  APScheduler not installed. Birthday automation disabled.")
        print("   Run: pip install APScheduler")
    except Exception as e:
        print(f"⚠️  Failed to start birthday scheduler: {e}")

def check_and_send_birthday_emails_wrapper(app):
    """
    Wrapper function to ensure Flask app context is available.
    """
    with app.app_context():
        from .birthday_scheduler import check_and_send_birthday_emails
        check_and_send_birthday_emails()


