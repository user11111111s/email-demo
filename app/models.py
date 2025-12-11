from datetime import datetime
from app import db

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Draft')  # Draft, Sending, Completed
    
    # Relationships
    recipients = db.relationship('Recipient', backref='campaign', lazy=True, cascade="all, delete-orphan")

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
            'click_count': sum(1 for r in self.recipients if any(e.type == 'click' for e in r.events))
        }

class Recipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Sent, Failed, Bounced
    sent_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    events = db.relationship('TrackingEvent', backref='recipient', lazy=True, cascade="all, delete-orphan")

class TrackingEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('recipient.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # open, click
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
