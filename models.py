from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    embedding = db.Column(db.Text, nullable=True)  # Store as JSON string
    photo_path = db.Column(db.String(255), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    otp_hash = db.Column(db.String(255), nullable=True)
    otp_expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship with login history
    login_history = db.relationship('LoginHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_embedding(self, embedding_array):
        """Convert numpy array to JSON string for storage"""
        if embedding_array is not None:
            self.embedding = json.dumps(embedding_array.tolist())
    
    def get_embedding(self):
        """Convert JSON string back to numpy array"""
        if self.embedding:
            import numpy as np
            return np.array(json.loads(self.embedding))
        return None
    
    def set_otp_expiry(self, minutes=10):
        """Set OTP expiry time"""
        self.otp_expires_at = datetime.utcnow() + timedelta(minutes=minutes)
    
    def is_otp_valid(self):
        """Check if OTP is still valid"""
        if not self.otp_expires_at:
            return False
        return datetime.utcnow() < self.otp_expires_at
    
    def clear_otp(self):
        """Clear OTP data after successful verification"""
        self.otp_hash = None
        self.otp_expires_at = None
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<User {self.email}>'


class LoginHistory(db.Model):
    __tablename__ = 'login_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    face_confidence = db.Column(db.Float, nullable=True)  # Face matching confidence score
    ip_address = db.Column(db.String(45), nullable=True)  # Support IPv6
    user_agent = db.Column(db.String(255), nullable=True)
    success = db.Column(db.Boolean, default=True, nullable=False)
    failure_reason = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f'<LoginHistory {self.user_id} at {self.login_time}>'