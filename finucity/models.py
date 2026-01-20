"""
Supabase Database Schema Documentation
Finucity uses ONLY Supabase for all data persistence
Author: Sumeet Sangwan (Refactored for production)
"""

from flask_login import UserMixin
from werkzeug.security import check_password_hash
from typing import Optional, Dict, Any

# =====================================================================
# SUPABASE SCHEMA DOCUMENTATION
# =====================================================================
# This file documents the Supabase tables used by Finucity.
# All database operations use the Supabase client via database.py
# NO SQLAlchemy or local database is used.
# =====================================================================

"""
SUPABASE TABLES:

1. profiles (extends auth.users)
   - id: UUID (primary key, references auth.users)
   - email: TEXT (unique, not null)
   - username: TEXT (unique)
   - first_name: TEXT
   - last_name: TEXT
   - phone: TEXT
   - profession: TEXT
   - city: TEXT
   - state: TEXT
   - role: TEXT (user|ca|ca_pending|admin)
   - is_active: BOOLEAN (default true)
   - email_verified: BOOLEAN (default false)
   - created_at: TIMESTAMP (default now())
   - last_login: TIMESTAMP
   - last_seen: TIMESTAMP
   
2. chat_queries
   - id: UUID (primary key)
   - user_id: UUID (references profiles)
   - session_id: TEXT
   - conversation_id: TEXT
   - question: TEXT (not null)
   - response: TEXT (not null)
   - category: TEXT (default 'general')
   - confidence_score: FLOAT
   - response_time: FLOAT
   - rating: INTEGER
   - is_helpful: BOOLEAN
   - feedback_text: TEXT
   - created_at: TIMESTAMP (default now())
   
3. user_feedback
   - id: UUID (primary key)
   - user_id: UUID (references profiles)
   - admin_user_id: UUID (references profiles, nullable)
   - subject: TEXT (not null)
   - message: TEXT (not null)
   - rating: INTEGER
   - created_at: TIMESTAMP (default now())
   
4. ca_applications
   - id: UUID (primary key)
   - user_id: UUID (references profiles)
   - full_name: TEXT (not null)
   - email: TEXT (not null)
   - phone: TEXT (not null)
   - city: TEXT
   - state: TEXT
   - icai_number: TEXT (not null)
   - registration_year: INTEGER
   - ca_type: TEXT
   - experience_years: INTEGER
   - firm_name: TEXT
   - practice_address: TEXT
   - services: JSONB
   - client_types: JSONB
   - status: TEXT (pending|approved|rejected)
   - reviewed_by: UUID (references profiles, nullable)
   - rejection_reason: TEXT
   - created_at: TIMESTAMP (default now())
   - updated_at: TIMESTAMP

5. conversations (optional - for grouping chat messages)
   - id: UUID (primary key)
   - user_id: UUID (references profiles)
   - session_id: TEXT (unique)
   - title: TEXT
   - category: TEXT
   - created_at: TIMESTAMP (default now())
   - updated_at: TIMESTAMP
"""

# =====================================================================
# USER ADAPTER FOR FLASK-LOGIN
# =====================================================================

class User(UserMixin):
    """
    User adapter class for Flask-Login compatibility
    Wraps Supabase user data to work with Flask-Login's session management
    This is NOT a database model - just an adapter
    """
    
    def __init__(self, user_data: Dict[str, Any]):
        """Initialize from Supabase profile data"""
        self.id = user_data.get('id')
        self.email = user_data.get('email')
        self.username = user_data.get('username', '')
        self.first_name = user_data.get('first_name', '')
        self.last_name = user_data.get('last_name', '')
        self.phone = user_data.get('phone')
        self.profession = user_data.get('profession')
        self.city = user_data.get('city')
        self.state = user_data.get('state')
        self.role = user_data.get('role', 'user')
        self._is_active = user_data.get('is_active', True)
        self.email_verified = user_data.get('email_verified', False)
        self.created_at = user_data.get('created_at')
        self.last_login = user_data.get('last_login')
        self.last_seen = user_data.get('last_seen')
        
        # Store original data
        self._data = user_data
    
    @property
    def is_active(self) -> bool:
        """Override Flask-Login's is_active property"""
        return self._is_active
    
    @is_active.setter
    def is_active(self, value: bool):
        """Allow setting is_active"""
        self._is_active = value
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip() or self.username or 'User'
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == 'admin'
    
    @property
    def is_ca(self) -> bool:
        """Check if user is CA"""
        return self.role in ('ca', 'admin')
    
    def get_id(self) -> str:
        """Required by Flask-Login"""
        return str(self.id)
    
    @staticmethod
    def check_password(password: str) -> bool:
        """
        Password checking is handled by Supabase Auth
        This method is here for compatibility but should not be used
        """
        raise NotImplementedError(
            "Password authentication is handled by Supabase Auth. "
            "Use supabase.auth.sign_in_with_password() instead."
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self._data

# =====================================================================
# MIGRATION NOTES
# =====================================================================
"""
IMPORTANT:

1. All database queries must use the Supabase client from database.py
2. User authentication is handled by Supabase Auth (not Flask-Login passwords)
3. The User class above is ONLY for Flask-Login session management
4. DO NOT create SQLAlchemy models or use db.session anywhere
5. All data persistence goes through Supabase REST API

Example usage:

    from finucity.database import UserService, ChatService
    
    # Get user
    user_data = UserService.get_by_email('user@example.com')
    if user_data:
        user = User(user_data)  # Wrap for Flask-Login
    
    # Store chat query
    ChatService.create_query(
        user_id=user.id,
        question='How to save tax?',
        response='Use Section 80C...'
    )
"""