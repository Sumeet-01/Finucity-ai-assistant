"""
Supabase Database Layer - Single Source of Truth
Finucity uses ONLY Supabase for all data storage
Author: Sumeet Sangwan (Refactored for production)
"""

import os
from typing import Optional, Dict, List, Any
from supabase import create_client, Client
from functools import wraps
from flask import g, current_app

class SupabaseDB:
    """
    Centralized Supabase database client
    This is the ONLY database interface for Finucity
    """
    
    def __init__(self, app=None):
        self.client: Optional[Client] = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize Supabase client with Flask app"""
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_service_key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set. "
                "Finucity requires Supabase as the database."
            )
        
        # Service role client for backend operations (bypasses RLS)
        self.client = create_client(supabase_url, supabase_service_key)
        
        app.config['SUPABASE_CLIENT'] = self.client
        app.teardown_appcontext(self.teardown)
    
    def teardown(self, exception):
        """Cleanup on request end"""
        pass
    
    def get_client(self) -> Client:
        """Get Supabase client instance"""
        if not self.client:
            raise RuntimeError("Supabase client not initialized")
        return self.client

# Global instance
supabase_db = SupabaseDB()

def get_supabase() -> Client:
    """Get Supabase client for current request"""
    if not hasattr(g, 'supabase'):
        g.supabase = supabase_db.get_client()
    return g.supabase

# User Operations
class UserService:
    """User management via Supabase"""
    
    @staticmethod
    def get_by_id(user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        try:
            sb = supabase_db.get_client()
            result = sb.table('profiles').select('*').eq('id', user_id).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            current_app.logger.error(f"Error getting user by ID: {e}")
            # Try reconnecting on connection error
            try:
                supabase_url = os.getenv('SUPABASE_URL')
                supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
                if supabase_url and supabase_service_key:
                    supabase_db.client = create_client(supabase_url, supabase_service_key)
                    result = supabase_db.client.table('profiles').select('*').eq('id', user_id).limit(1).execute()
                    return result.data[0] if result.data else None
            except Exception as retry_error:
                current_app.logger.error(f"Retry failed: {retry_error}")
            return None
    
    @staticmethod
    def get_by_email(email: str) -> Optional[Dict]:
        """Get user by email"""
        try:
            sb = get_supabase()
            result = sb.table('profiles').select('*').eq('email', email.lower()).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            current_app.logger.error(f"Error getting user by email: {e}")
            return None
    
    @staticmethod
    def create(user_data: Dict) -> Optional[Dict]:
        """Create new user profile"""
        try:
            sb = get_supabase()
            result = sb.table('profiles').insert(user_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            current_app.logger.error(f"Error creating user: {e}")
            return None
    
    @staticmethod
    def update(user_id: str, updates: Dict) -> Optional[Dict]:
        """Update user profile"""
        try:
            sb = get_supabase()
            result = sb.table('profiles').update(updates).eq('id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            current_app.logger.error(f"Error updating user: {e}")
            return None
    
    @staticmethod
    def get_all(limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all users (admin only)"""
        try:
            sb = get_supabase()
            result = sb.table('profiles').select('*').range(offset, offset + limit - 1).execute()
            return result.data if result.data else []
        except Exception as e:
            current_app.logger.error(f"Error getting all users: {e}")
            return []

# Chat/Message Operations
class ChatService:
    """Chat query management via Supabase"""
    
    @staticmethod
    def create_query(user_id: str, question: str, response: str, 
                    session_id: Optional[str] = None, 
                    category: str = 'general') -> Optional[Dict]:
        """Store chat query"""
        try:
            sb = get_supabase()
            data = {
                'user_id': user_id,
                'question': question,
                'response': response,
                'session_id': session_id,
                'category': category
            }
            result = sb.table('chat_queries').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            current_app.logger.error(f"Error creating chat query: {e}")
            return None
    
    @staticmethod
    def get_user_history(user_id: str, limit: int = 50) -> List[Dict]:
        """Get user's chat history"""
        try:
            sb = get_supabase()
            result = sb.table('chat_queries')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            current_app.logger.error(f"Error getting chat history: {e}")
            return []
    
    @staticmethod
    def get_user_queries(user_id: str, limit: int = 100) -> List[Dict]:
        """Get user's queries (alias for get_user_history)"""
        return ChatService.get_user_history(user_id, limit)
    
    @staticmethod
    def get_by_session(session_id: str) -> List[Dict]:
        """Get all messages in a session"""
        try:
            sb = get_supabase()
            result = sb.table('chat_queries')\
                .select('*')\
                .eq('session_id', session_id)\
                .order('created_at', asc=True)\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            current_app.logger.error(f"Error getting session messages: {e}")
            return []
    
    @staticmethod
    def get_query_by_id(query_id: int) -> Optional[Dict]:
        """Get a specific chat query by ID"""
        try:
            sb = get_supabase()
            result = sb.table('chat_queries')\
                .select('*')\
                .eq('id', query_id)\
                .limit(1)\
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            current_app.logger.error(f"Error getting query by ID: {e}")
            return None
    
    @staticmethod
    def get_queries_by_session(session_id: str, user_id: str) -> List[Dict]:
        """Get all queries in a session for a specific user"""
        try:
            sb = get_supabase()
            result = sb.table('chat_queries')\
                .select('*')\
                .eq('session_id', session_id)\
                .eq('user_id', user_id)\
                .order('created_at', desc=False)\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            current_app.logger.error(f"Error getting queries by session: {e}")
            return []
    
    @staticmethod
    def delete_by_session(session_id: str, user_id: str) -> bool:
        """Delete all queries in a session for a specific user"""
        try:
            sb = get_supabase()
            result = sb.table('chat_queries')\
                .delete()\
                .eq('session_id', session_id)\
                .eq('user_id', user_id)\
                .execute()
            return True
        except Exception as e:
            current_app.logger.error(f"Error deleting session: {e}")
            return False

# Feedback Operations
class FeedbackService:
    """User feedback management via Supabase"""
    
    @staticmethod
    def create(user_id: str, subject: str, message: str, 
              rating: Optional[int] = None) -> Optional[Dict]:
        """Create feedback entry"""
        try:
            sb = get_supabase()
            data = {
                'user_id': user_id,
                'subject': subject,
                'message': message,
                'rating': rating
            }
            result = sb.table('user_feedback').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            current_app.logger.error(f"Error creating feedback: {e}")
            return None
    
    @staticmethod
    def get_all(limit: int = 100) -> List[Dict]:
        """Get all feedback (admin only)"""
        try:
            sb = get_supabase()
            result = sb.table('user_feedback')\
                .select('*')\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            current_app.logger.error(f"Error getting feedback: {e}")
            return []

# CA Application Operations
class CAApplicationService:
    """CA application management via Supabase"""
    
    @staticmethod
    def create(application_data: Dict) -> Optional[Dict]:
        """Create CA application"""
        try:
            sb = get_supabase()
            result = sb.table('ca_applications').insert(application_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            current_app.logger.error(f"Error creating CA application: {e}")
            return None
    
    @staticmethod
    def get_pending() -> List[Dict]:
        """Get all pending applications"""
        try:
            sb = get_supabase()
            result = sb.table('ca_applications')\
                .select('*')\
                .eq('status', 'pending')\
                .order('created_at', desc=True)\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            current_app.logger.error(f"Error getting pending applications: {e}")
            return []
    
    @staticmethod
    def approve(application_id: str, admin_id: str) -> bool:
        """Approve CA application"""
        try:
            sb = get_supabase()
            sb.table('ca_applications')\
                .update({'status': 'approved', 'reviewed_by': admin_id})\
                .eq('id', application_id)\
                .execute()
            return True
        except Exception as e:
            current_app.logger.error(f"Error approving application: {e}")
            return False
    
    @staticmethod
    def reject(application_id: str, admin_id: str, reason: str) -> bool:
        """Reject CA application"""
        try:
            sb = get_supabase()
            sb.table('ca_applications')\
                .update({
                    'status': 'rejected', 
                    'reviewed_by': admin_id,
                    'rejection_reason': reason
                })\
                .eq('id', application_id)\
                .execute()
            return True
        except Exception as e:
            current_app.logger.error(f"Error rejecting application: {e}")
            return False

# Export all services
__all__ = [
    'supabase_db',
    'get_supabase',
    'UserService',
    'ChatService',
    'FeedbackService',
    'CAApplicationService'
]
