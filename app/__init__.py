from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
import atexit

db = SQLAlchemy()
login_manager = LoginManager()

# Global scheduler instance
scheduler = None

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
    
    # Handle Render PostgreSQL URI (which starts with postgres:// but SQLAlchemy needs postgresql://)
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        # Import parts of our application
        from . import routes, models
        from .routes import main_bp
        app.register_blueprint(main_bp)

        # Create database tables
        db.create_all()

        # Database migration logic
        try:
            engine_name = db.engine.name
            
            if engine_name == 'sqlite':
                with db.engine.begin() as conn:
                    # Campaign columns
                    result = conn.execute(db.text("PRAGMA table_info(campaign)"))
                    cols = [row[1] for row in result.fetchall()]
                    
                    for col_name, col_type in [
                        ('scheduled_at', 'DATETIME'),
                        ('user_id', 'INTEGER'),
                        ('selected_account_ids', 'TEXT'),
                        ('batch_size', 'INTEGER DEFAULT 50'),
                        ('batch_delay', 'INTEGER DEFAULT 5')
                    ]:
                        if col_name not in cols:
                            conn.execute(db.text(f"ALTER TABLE campaign ADD COLUMN {col_name} {col_type}"))
                    
                    # Recipient columns
                    result = conn.execute(db.text("PRAGMA table_info(recipient)"))
                    recipient_cols = [row[1] for row in result.fetchall()]
                    if 'name' not in recipient_cols:
                        conn.execute(db.text("ALTER TABLE recipient ADD COLUMN name VARCHAR(100)"))
                    if 'dob' not in recipient_cols:
                        conn.execute(db.text("ALTER TABLE recipient ADD COLUMN dob DATE"))
                    if 'sender_account_id' not in recipient_cols:
                        conn.execute(db.text("ALTER TABLE recipient ADD COLUMN sender_account_id INTEGER"))
            else:
                with db.engine.begin() as conn:
                    # Campaign columns
                    for col_name, col_type in [
                        ('scheduled_at', 'TIMESTAMP'),
                        ('user_id', 'INTEGER'),
                        ('selected_account_ids', 'TEXT'),
                        ('batch_size', 'INTEGER DEFAULT 50'),
                        ('batch_delay', 'INTEGER DEFAULT 5')
                    ]:
                        try:
                            conn.execute(db.text(f"ALTER TABLE campaign ADD COLUMN {col_name} {col_type}"))
                        except Exception: pass
                            
                    # Recipient columns
                    for col_name, col_type in [
                        ('name', 'VARCHAR(100)'),
                        ('dob', 'DATE'),
                        ('sender_account_id', 'INTEGER')
                    ]:
                        try:
                            conn.execute(db.text(f"ALTER TABLE recipient ADD COLUMN {col_name} {col_type}"))
                        except Exception: pass
        except Exception as e:
            print(f"⚠️  Database migration skipped: {e}")
    
    # Setup APScheduler for automatic birthday wishes
    setup_scheduler(app)

    return app

def setup_scheduler(app):
    """
    Set up APScheduler to run daily birthday checks.
    """
    global scheduler
    
    if scheduler is not None:
        return
    
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        
        # PREVENT DOUBLE RUN:
        # 1. In development (Flask reloader), only start in the reloader process.
        # 2. In production (Gunicorn), we start it. Note: If using multiple workers, 
        #    you'd usually use a separate process for the scheduler.
        
        is_dev = os.environ.get('FLASK_ENV') != 'production'
        is_reloader = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
        
        if is_dev and not is_reloader:
            return

        scheduler = BackgroundScheduler(daemon=True)
        
        # Schedule daily birthday check
        scheduler.add_job(
            func=lambda: check_and_send_birthday_emails_wrapper(app),
            trigger='cron',
            hour=9,   # Run at 9:00 AM
            minute=0,
            id='birthday_check',
            name='Daily Birthday Check',
            replace_existing=True
        )
        
        scheduler.start()
        print(f"✅ Birthday scheduler started - daily checks at 09:00 AM")
        
        atexit.register(lambda: scheduler.shutdown() if scheduler else None)
        
    except Exception as e:
        print(f"⚠️  Failed to start birthday scheduler: {e}")

def check_and_send_birthday_emails_wrapper(app):
    """
    Wrapper function to ensure Flask app context is available.
    """
    with app.app_context():
        from .birthday_scheduler import check_and_send_birthday_emails
        check_and_send_birthday_emails()


