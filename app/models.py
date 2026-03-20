from datetime import datetime, date
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import json

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # Relationships
    accounts = db.relationship('SenderAccount', backref='owner', lazy=True, cascade="all, delete-orphan")
    campaigns = db.relationship('Campaign', backref='owner', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class SenderAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    encrypted_password = db.Column(db.String(255), nullable=False)
    daily_quota_used = db.Column(db.Integer, default=0)
    last_used_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    def get_usage_percent(self):
        return (self.daily_quota_used / 495) * 100 if 495 > 0 else 0

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Initially nullable for legacy
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='Draft')  # Draft, Scheduled, Sending, Completed
    
    # Selection of accounts to use for this campaign (stored as JSON list of IDs)
    _selected_account_ids = db.Column('selected_account_ids', db.Text, default='[]')
    
    batch_size = db.Column(db.Integer, default=50)
    batch_delay = db.Column(db.Integer, default=5) # Delay in minutes
    
    # Relationships
    recipients = db.relationship('Recipient', backref='campaign', lazy=True, cascade="all, delete-orphan")
    attachments = db.relationship('Attachment', backref='campaign', lazy=True, cascade="all, delete-orphan")

    @property
    def selected_account_ids(self):
        try:
            return json.loads(self._selected_account_ids)
        except:
            return []

    @selected_account_ids.setter
    def selected_account_ids(self, value):
        self._selected_account_ids = json.dumps(value)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject': self.subject,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'total_recipients': len(self.recipients),
            'sent_count': sum(1 for r in self.recipients if r.status == 'Sent'),
            'open_count': sum(1 for r in self.recipients if any(e.type == 'open' for e in r.events)),
            'replied_count': sum(1 for r in self.recipients if any(e.type == 'replied' for e in r.events))
        }

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    mime_type = db.Column(db.String(100), nullable=True)

class Recipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='Pending')
    sent_at = db.Column(db.DateTime, nullable=True)
    
    # Track which account sent this email
    sender_account_id = db.Column(db.Integer, db.ForeignKey('sender_account.id'), nullable=True)
    
    events = db.relationship('TrackingEvent', backref='recipient', lazy=True, cascade="all, delete-orphan")

class TrackingEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('recipient.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
