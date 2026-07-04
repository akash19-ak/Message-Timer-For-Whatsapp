from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Schedule(db.Model):
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    scheduled_datetime = db.Column(db.DateTime, nullable=False)
    send_method = db.Column(db.String(10), default='app', nullable=False)  # 'app' | 'web' | 'link'
    sent = db.Column(db.Boolean, default=False)
    image_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'message': self.message,
            'scheduled_datetime': self.scheduled_datetime.isoformat(),
            'send_method': self.send_method,
            'sent': self.sent,
            'image_filename': self.image_filename,
            'created_at': self.created_at.isoformat()
        }
