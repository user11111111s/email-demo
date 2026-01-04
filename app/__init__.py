from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

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
        except Exception:
            # If anything goes wrong, skip silently; app can still run.
            pass

    return app
