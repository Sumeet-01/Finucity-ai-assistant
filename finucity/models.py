"""
Enhanced database models for Finucity AI
Optimized for chat functionality and user management
Author: Sumeet Sangwan
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

# Import the globally defined 'db' object
from . import db

class User(UserMixin, db.Model):
    """Enhanced User model with comprehensive fields"""
    __tablename__ = 'users'

    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)

    # Personal information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(15))
    profession = db.Column(db.String(100))
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))

    # Account status
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    chat_queries = db.relationship('ChatQuery', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    # =================================================================
    # DEFINITIVE FIX for AmbiguousForeignKeysError
    # We explicitly tell SQLAlchemy which foreign key to use for this relationship.
    # =================================================================
    feedback_entries = db.relationship(
        'UserFeedback', 
        foreign_keys='UserFeedback.user_id', 
        backref='user', 
        lazy='dynamic', 
        cascade='all, delete-orphan'
    )
    admin_responses = db.relationship(
        'UserFeedback',
        foreign_keys='UserFeedback.admin_user_id',
        backref='admin',
        lazy='dynamic'
    )
    # =================================================================

    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"

    def set_password(self, password: str) -> None:
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)


class Conversation(db.Model):
    """Model for organizing chat sessions."""
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    session_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    title = db.Column(db.String(200))
    category = db.Column(db.String(50), default='general')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatQuery(db.Model):
    """Model for storing chat messages and AI responses"""
    __tablename__ = 'chat_queries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    session_id = db.Column(db.String(100), index=True)
    conversation_id = db.Column(db.String(64), nullable=True, index=True)
    question = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50), default='general')
    
    # Additional fields for analytics
    confidence_score = db.Column(db.Float, default=0.9)
    response_time = db.Column(db.Float)
    rating = db.Column(db.Integer)
    is_helpful = db.Column(db.Boolean)
    feedback_text = db.Column(db.Text)


class UserFeedback(db.Model):
    """Model for tracking user feedback."""
    __tablename__ = 'user_feedback'
    id = db.Column(db.Integer, primary_key=True)
    # This is the foreign key for the user who SUBMITTED the feedback
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    # This is the foreign key for the user who RESPONDED to the feedback (if they are an admin)
    admin_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def create_sample_data():
    """Create sample data for development."""
    if User.query.first():
        return  # Data already exists

    # Create admin user
    admin_user = User(
        username='admin', email='admin@finucity.com',
        first_name='Admin', last_name='User', is_admin=True
    )
    admin_user.set_password('admin123')
    db.session.add(admin_user)

    # Create demo user
    demo_user = User(
        username='demo', email='demo@finucity.com',
        first_name='Demo', last_name='User'
    )
    demo_user.set_password('demo123')
    db.session.add(demo_user)
    
    db.session.commit()
    print("✅ Sample users (admin, demo) created successfully.")