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

# Platform Stats (Real-time)
class PlatformStatsService:
    """Fetches real-time platform statistics from Supabase"""

    @staticmethod
    def get_stats() -> Dict[str, Any]:
        """Get real-time platform stats for About / marketing pages."""
        stats = {
            'total_users': 0,
            'total_queries': 0,
            'total_tools': 6,          # calculators (Tax, HRA, GST, SIP, EMI, Regime)
            'satisfaction_rate': 0,
            'total_cas': 0,
            'total_services': 6,       # financial service pages
        }
        try:
            sb = supabase_db.get_client()

            # Total registered users
            users_resp = sb.table('profiles').select('id', count='exact').execute()
            stats['total_users'] = users_resp.count if hasattr(users_resp, 'count') and users_resp.count else len(users_resp.data or [])

            # Total AI queries
            queries_resp = sb.table('chat_queries').select('id', count='exact').execute()
            stats['total_queries'] = queries_resp.count if hasattr(queries_resp, 'count') and queries_resp.count else len(queries_resp.data or [])

            # Average satisfaction (from user_feedback ratings 1-5)
            try:
                fb_resp = sb.table('user_feedback').select('rating').not_.is_('rating', 'null').execute()
                if fb_resp.data:
                    ratings = [r['rating'] for r in fb_resp.data if r.get('rating')]
                    if ratings:
                        stats['satisfaction_rate'] = round(sum(ratings) / len(ratings) / 5 * 100, 1)
            except Exception:
                pass

            # Total approved CAs
            try:
                ca_resp = sb.table('profiles').select('id', count='exact').eq('role', 'ca').execute()
                stats['total_cas'] = ca_resp.count if hasattr(ca_resp, 'count') and ca_resp.count else len(ca_resp.data or [])
            except Exception:
                pass

        except Exception as e:
            try:
                current_app.logger.error(f"Error fetching platform stats: {e}")
            except Exception:
                print(f"Error fetching platform stats: {e}")
        return stats


# Blog Operations
class BlogService:
    """Blog post management via Supabase"""

    @staticmethod
    def get_published(limit: int = 20) -> List[Dict]:
        """Get all published blog posts, newest first."""
        try:
            sb = supabase_db.get_client()
            result = sb.table('blog_posts') \
                .select('*') \
                .eq('status', 'published') \
                .order('published_at', desc=True) \
                .limit(limit) \
                .execute()
            return result.data if result.data else []
        except Exception:
            return []

    @staticmethod
    def get_featured() -> Optional[Dict]:
        """Get the featured blog post."""
        try:
            sb = supabase_db.get_client()
            result = sb.table('blog_posts') \
                .select('*') \
                .eq('status', 'published') \
                .eq('is_featured', True) \
                .order('published_at', desc=True) \
                .limit(1) \
                .execute()
            return result.data[0] if result.data else None
        except Exception:
            return None

    @staticmethod
    def get_by_category(category: str, limit: int = 10) -> List[Dict]:
        """Get posts by category."""
        try:
            sb = supabase_db.get_client()
            result = sb.table('blog_posts') \
                .select('*') \
                .eq('status', 'published') \
                .eq('category', category) \
                .order('published_at', desc=True) \
                .limit(limit) \
                .execute()
            return result.data if result.data else []
        except Exception:
            return []


# Default blog content (used when DB table doesn't exist yet)
DEFAULT_BLOG_POSTS = [
    {
        'id': 1,
        'title': 'Union Budget 2025-26: Complete Tax Impact Analysis',
        'description': 'A comprehensive breakdown of every tax change in the Union Budget — new slabs, revised deductions, capital gains updates, and what it means for salaried professionals, business owners, and investors.',
        'category': 'budget',
        'read_time': 15,
        'author': 'Finucity Research',
        'is_featured': True,
        'accent_color': '#667eea,#764ba2',
        'published_at': '2025-02-01',
    },
    {
        'id': 2,
        'title': 'Old vs New Tax Regime 2025: The Definitive Decision Framework',
        'description': 'A mathematical framework to determine which regime saves you more. Includes crossover analysis for different income levels and deduction profiles.',
        'category': 'tax',
        'read_time': 12,
        'author': 'Finucity Research',
        'is_featured': False,
        'accent_color': '#667eea,#764ba2',
        'published_at': '2025-01-20',
    },
    {
        'id': 3,
        'title': 'Index Funds vs Active Funds: 10-Year Performance Data Analysis',
        'description': 'Analyzing SPIVA India data showing 85% of large-cap active funds underperform Nifty 50 over 10 years. Why passive investing should be your core strategy.',
        'category': 'invest',
        'read_time': 10,
        'author': 'Finucity Research',
        'is_featured': False,
        'accent_color': '#fba002,#ff6b35',
        'published_at': '2025-01-15',
    },
    {
        'id': 4,
        'title': 'Section 80C: Beyond the Basics — Hidden Instruments Most Miss',
        'description': 'Everyone knows about PPF and ELSS, but few optimize SSA, NPS 80CCD(1B), VPF, and home loan principal. A complete 80C optimization strategy.',
        'category': 'tax',
        'read_time': 8,
        'author': 'Finucity Research',
        'is_featured': False,
        'accent_color': '#43e97b,#38f9d7',
        'published_at': '2025-01-10',
    },
    {
        'id': 5,
        'title': 'GST Compliance Calendar 2025-26: Every Deadline You Need',
        'description': 'Month-by-month GSTR-1, GSTR-3B, GSTR-9 filing deadlines with late fee calculations. Set up auto-reminders and avoid penalties.',
        'category': 'gst',
        'read_time': 7,
        'author': 'Finucity Research',
        'is_featured': False,
        'accent_color': '#ff6b6b,#ffa07a',
        'published_at': '2025-01-05',
    },
    {
        'id': 6,
        'title': 'Emergency Fund Playbook: How Much, Where, and How Fast',
        'description': 'The scientific approach to building a 6-month emergency fund. Liquid funds vs savings accounts vs FDs — where to park emergency money for maximum returns.',
        'category': 'savings',
        'read_time': 6,
        'author': 'Finucity Research',
        'is_featured': False,
        'accent_color': '#4facfe,#00f2fe',
        'published_at': '2024-12-28',
    },
    {
        'id': 7,
        'title': 'Sovereign Gold Bonds: The Most Tax-Efficient Way to Own Gold',
        'description': '2.5% guaranteed interest + gold price gains + ZERO tax on maturity. Why SGBs are mathematically superior to physical gold, Gold ETFs, and digital gold.',
        'category': 'invest',
        'read_time': 8,
        'author': 'Finucity Research',
        'is_featured': False,
        'accent_color': '#a18cd1,#fbc2eb',
        'published_at': '2024-12-20',
    },
    {
        'id': 8,
        'title': 'New Tax Slabs 2025-26: How Much Will You Save?',
        'description': 'Income-wise comparison of tax liability under the revised slabs. Includes salary breakdowns for ₹8L, ₹12L, ₹18L, ₹25L, and ₹50L incomes.',
        'category': 'budget',
        'read_time': 11,
        'author': 'Finucity Research',
        'is_featured': False,
        'accent_color': '#f093fb,#f5576c',
        'published_at': '2025-02-05',
    },
    {
        'id': 9,
        'title': 'The 50-30-20 Budget Rule: Indian Edition with Real Numbers',
        'description': 'Adapting the classic budgeting framework for Indian households. How to allocate salary across needs, wants, and savings — with city-wise adjustments.',
        'category': 'savings',
        'read_time': 9,
        'author': 'Finucity Research',
        'is_featured': False,
        'accent_color': '#0acffe,#495aff',
        'published_at': '2024-12-15',
    },
]


# Export all services
__all__ = [
    'supabase_db',
    'get_supabase',
    'UserService',
    'ChatService',
    'FeedbackService',
    'CAApplicationService',
    'PlatformStatsService',
    'BlogService',
    'DEFAULT_BLOG_POSTS',
]
