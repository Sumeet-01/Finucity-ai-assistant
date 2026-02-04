"""
Centralized route handlers for the Finucity AI application. 
Author: Sumeet Sangwan
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, abort, send_from_directory, current_app
from flask_login import login_required, current_user, login_user, logout_user
import uuid
import re
from datetime import datetime
import os
import jwt
import html

from .models import User
from .database import UserService, ChatService, FeedbackService, get_supabase

# Dummy limiter decorator (rate limiting handled at app level)
class DummyLimiter:
    def limit(self, *args, **kwargs):
        def decorator(f):
            return f
        return decorator

limiter = DummyLimiter()

try:
    from .ai import get_ai_response
except ImportError: 
    print("Warning: AI module not found. Some features may be limited.")
    get_ai_response = None

main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
api_bp = Blueprint('api', __name__, url_prefix='/api')


# ==================== SECURITY HELPERS ====================

def sanitize_input(text):
    """Sanitize user input to prevent XSS attacks."""
    if isinstance(text, str):
        return html.escape(text)
    return text

def validate_file_upload(file):
    """Validate file upload for security."""
    allowed_extensions = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg'}
    allowed_mimetypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'image/png',
        'image/jpeg'
    ]
    
    # Check file extension
    if '.' not in file.filename:
        return False, "No file extension"
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in allowed_extensions:
        return False, f"Invalid file extension: {ext}"
    
    # Check MIME type
    if file.content_type not in allowed_mimetypes:
        return False, f"Invalid file type: {file.content_type}"
    
    # Check file size (5MB max)
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to start
    
    if size > 5 * 1024 * 1024:
        return False, "File too large (max 5MB)"
    
    return True, "Valid"


# ==================== HELPERS ====================

def decode_supabase_jwt(token: str):
    """Decode and validate Supabase JWT token."""
    supabase_url = os.getenv('SUPABASE_URL', '').rstrip('/')
    legacy_secret = os.getenv('SUPABASE_JWT_SECRET')

    if supabase_url: 
        jwks_url = f"{supabase_url}/auth/v1/jwks"
        try:
            from jwt import PyJWKClient
            jwk_client = PyJWKClient(jwks_url)
            signing_key = jwk_client.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=None,
                options={"verify_aud": False},
                leeway=600,
            )
            return claims, None
        except Exception as e:
            rs_error = str(e)
    else:
        rs_error = "no_supabase_url"

    if not legacy_secret: 
        return None, f"server misconfigured: missing SUPABASE_JWT_SECRET (RS error: {rs_error})"
    try:
        claims = jwt.decode(
            token,
            legacy_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
            leeway=600,
        )
        return claims, None
    except Exception as e:
        return None, f"invalid token (RS error: {rs_error}); HS error: {e}"


def ensure_local_user_from_claims(claims, role='user'):
    """Find or create a local User based on Supabase claims."""
    email = claims.get("email") or claims.get("user_metadata", {}).get("email")
    first_name = claims.get("user_metadata", {}).get("full_name", "") or claims.get("name", "") or ""
    last_name = ""
    if first_name and " " in first_name:
        parts = first_name.split(" ", 1)
        first_name, last_name = parts[0], parts[1]
    if not email:
        raise ValueError("No email found in token")

    # Check if user exists in Supabase
    user_data = UserService.get_by_email(email.lower())
    
    if not user_data:
        # Create new user profile in Supabase
        base_username = email.split("@")[0]
        candidate = base_username
        i = 1
        # Check for username uniqueness
        sb = get_supabase()
        while True:
            existing = sb.table('profiles').select('id').eq('username', candidate.lower()).limit(1).execute()
            if not existing.data:
                break
            i += 1
            candidate = f"{base_username}{i}"
        
        # Create profile data
        profile_data = {
            'id': claims.get('sub'),  # Use Supabase auth user ID
            'email': email.lower(),
            'username': candidate.lower(),
            'first_name': first_name.title() if first_name else "",
            'last_name': last_name.title() if last_name else "",
            'role': role
        }
        
        user_data = UserService.create(profile_data)
        if not user_data:
            raise Exception("Failed to create user profile")
    else:
        # Update existing user if needed
        updates = {}
        if first_name and not user_data.get('first_name'):
            updates['first_name'] = first_name.title()
        if last_name and not user_data.get('last_name'):
            updates['last_name'] = last_name.title()
        
        if updates:
            user_data = UserService.update(user_data['id'], updates)
    
    return User(user_data)


def check_ca_access():
    """Helper function to check if current user has CA access."""
    if not current_user. is_authenticated: 
        return False
    user_role = getattr(current_user, 'role', 'user')
    return user_role in ['ca', 'admin']


def check_admin_access():
    """Helper function to check if current user has admin access."""
    if not current_user. is_authenticated: 
        return False
    user_role = getattr(current_user, 'role', 'user')
    return user_role == 'admin'


def get_user_role():
    """Get the current user's role."""
    if not current_user.is_authenticated:
        return None
    return getattr(current_user, 'role', 'user')


# ==================== MAIN & STATIC PAGE ROUTES ====================

@main_bp. route('/', endpoint='home')
def index():
    """Renders the homepage."""
    return render_template('index.html')


@main_bp.route('/profile', endpoint='profile')
@login_required
def profile():
    """Displays the current user's profile page with real-time stats."""
    try:
        sb = get_supabase()
        user_id = current_user.id
        
        # Get user's recent queries
        recent_response = sb.table('chat_queries').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(5).execute()
        recent_queries = recent_response.data if recent_response.data else []
        
        # Get user statistics
        total_queries_response = sb.table('chat_queries').select('id', count='exact').eq('user_id', user_id).execute()
        total_queries = total_queries_response.count if hasattr(total_queries_response, 'count') else 0
        
        helpful_response = sb.table('chat_queries').select('id', count='exact').eq('user_id', user_id).eq('is_helpful', True).execute()
        total_feedback = helpful_response.count if hasattr(helpful_response, 'count') else 0
        
        # Calculate satisfaction rate
        satisfaction_rate = round((total_feedback / total_queries * 100), 1) if total_queries > 0 else 0
        
        user_stats = {
            'total_queries': total_queries,
            'total_feedback': total_feedback,
            'days_active': 1,  # Can be enhanced with actual login tracking
            'satisfaction_rate': satisfaction_rate
        }
        
        return render_template('profile.html', user=current_user, user_stats=user_stats, recent_queries=recent_queries)
    except Exception as e:
        print(f"Profile page error: {e}")
        # Fallback to empty stats
        return render_template('profile.html', user=current_user, user_stats=None, recent_queries=[])


@main_bp.route('/about', endpoint='about')
def about():
    """Renders the about page."""
    try:
        return render_template('about.html')
    except:
        return render_template('Errors/404.html'), 404
    return render_template('about.html')


@main_bp. route('/faq', endpoint='faq')
def faq():
    """Renders the FAQ page."""
    try:
        return render_template('faq.html')
    except:
        return render_template('Errors/404.html'), 404


@main_bp.route('/security', endpoint='security')
def security():
    """Renders the security information page."""
    try:
        return render_template('Support/security.html')
    except: 
        try:
            return render_template('security.html')
        except:
            return render_template('Errors/404.html'), 404


@main_bp.route('/contact', endpoint='contact')
def contact():
    """Renders the contact page."""
    try:
        return render_template('contact.html')
    except:
        try:
            return render_template('Support/contact.html')
        except: 
            return render_template('Errors/404.html'), 404


@main_bp.route('/pricing', endpoint='pricing')
def pricing():
    """Renders the pricing page."""
    try:
        return render_template('pricing.html')
    except:
        return render_template('Errors/404.html'), 404


@main_bp.route('/careers', endpoint='careers')
def careers():
    """Renders the careers page."""
    try:
        return render_template('careers.html')
    except:
        try:
            return render_template('Support/careers.html')
        except: 
            return render_template('Errors/404.html'), 404


# ==================== FINANCIAL SERVICES ROUTES ====================

@main_bp. route('/tax-planning', endpoint='tax_planning')
def tax_planning():
    """Renders the tax planning page."""
    try:
        return render_template('financial-services/tax-planning.html')
    except:
        try:
            return render_template('tax_planning.html')
        except:
            return render_template('Errors/404.html'), 404


@main_bp. route('/investment-advisory', endpoint='investment_advisory')
def investment_advisory():
    """Renders the investment advisory page."""
    try:
        return render_template('financial-services/investment-advisory.html')
    except:
        try:
            return render_template('investment_advisory.html')
        except: 
            return render_template('Errors/404.html'), 404


@main_bp.route('/gst-compliance', endpoint='gst_compliance')
def gst_compliance():
    """Renders the GST compliance page."""
    try:
        return render_template('financial-services/gst-compliance.html')
    except:
        try:
            return render_template('gst_compliance.html')
        except: 
            return render_template('Errors/404.html'), 404


@main_bp.route('/business-finance', endpoint='business_finance')
def business_finance():
    """Renders the business finance page."""
    try:
        return render_template('financial-services/bussiness-finance.html')
    except:
        try: 
            return render_template('bussiness_finance.html')
        except:
            return render_template('Errors/404.html'), 404


@main_bp.route('/insurance-planning', endpoint='insurance_planning')
def insurance_planning():
    """Renders the insurance planning page."""
    try:
        return render_template('financial-services/insurance-planning.html')
    except:
        try:
            return render_template('insurance_planning.html')
        except: 
            return render_template('Errors/404.html'), 404


@main_bp.route('/audit-services', endpoint='audit_services')
def audit_services():
    """Renders the audit services page."""
    try:
        return render_template('financial-services/audit-services.html')
    except:
        try:
            return render_template('audit_services.html')
        except: 
            return render_template('Errors/404.html'), 404


@main_bp.route('/startup-advisory', endpoint='startup_advisory')
def startup_advisory():
    """Renders the startup advisory page."""
    try:
        return render_template('financial-services/startup-advisory.html')
    except:
        try:
            return render_template('startup_advisory.html')
        except: 
            return render_template('Errors/404.html'), 404


@main_bp.route('/nri-taxation', endpoint='nri_taxation')
def nri_taxation():
    """Renders the NRI taxation page."""
    try:
        return render_template('financial-services/nri-taxation.html')
    except:
        try:
            return render_template('nri_taxation.html')
        except: 
            return render_template('Errors/404.html'), 404


@main_bp.route('/company-registration', endpoint='company_registration')
def company_registration():
    """Renders the company registration page."""
    try:
        return render_template('financial-services/company-registration.html')
    except:
        try:
            return render_template('company_registration.html')
        except: 
            return render_template('Errors/404.html'), 404


# ==================== RESOURCE ROUTES ====================

@main_bp. route('/financial-blog', endpoint='financial_blog')
def financial_blog():
    """Renders the financial blog page."""
    try:
        return render_template('Resources/financial_blog.html')
    except Exception as e:
        print(f"Error loading financial blog: {e}")
        try:
            return render_template('financial_blog.html')
        except: 
            return render_template('Errors/404.html'), 404


@main_bp.route('/learning-centre', endpoint='learning_centre')
def learning_centre():
    """Renders the learning center page."""
    try:
        return render_template('Resources/learning_center.html')
    except Exception as e: 
        print(f"Error loading learning center: {e}")
        try:
            return render_template('learning_centre.html')
        except:
            return render_template('Errors/404.html'), 404


@main_bp.route('/tax-calculator', endpoint='tax_calculator')
def tax_calculator():
    """Renders the tax calculator page."""
    try: 
        return render_template('Resources/tax_calculator.html')
    except Exception as e:
        print(f"Error loading tax calculator: {e}")
        try: 
            return render_template('tax_calculator.html')
        except:
            return render_template('Errors/404.html'), 404


@main_bp.route('/investment-tools', endpoint='investment_tools')
def investment_tools():
    """Renders the investment tools page."""
    try:
        return render_template('Resources/investment_tools.html')
    except Exception as e: 
        print(f"Error loading investment tools:  {e}")
        try:
            return render_template('investment_tools.html')
        except: 
            return render_template('Errors/404.html'), 404


@main_bp.route('/retirement-planning', endpoint='retirement_planning')
def retirement_planning():
    """Renders the retirement planning page."""
    try: 
        return render_template('Resources/retirement-planning.html')
    except Exception as e:
        print(f"Error loading retirement planning: {e}")
        try: 
            return render_template('retirement_planning.html')
        except:
            return render_template('Errors/404.html'), 404


@main_bp.route('/gst-calculator', endpoint='gst_calculator')
def gst_calculator():
    """Renders the GST calculator page."""
    try:
        return render_template('Resources/gst_calculator.html')
    except: 
        try: 
            return render_template('gst_calculator.html')
        except:
            return render_template('Errors/404.html'), 404


@main_bp.route('/emi-calculator', endpoint='emi_calculator')
def emi_calculator():
    """Renders the EMI calculator page."""
    try:
        return render_template('Resources/emi_calculator.html')
    except:
        try:
            return render_template('emi_calculator.html')
        except: 
            return render_template('Errors/404.html'), 404


@main_bp.route('/sip-calculator', endpoint='sip_calculator')
def sip_calculator():
    """Renders the SIP calculator page."""
    try:
        return render_template('Resources/sip_calculator.html')
    except:
        try:
            return render_template('sip_calculator.html')
        except: 
            return render_template('Errors/404.html'), 404


@main_bp.route('/financial-glossary', endpoint='financial_glossary')
def financial_glossary():
    """Renders the financial glossary page."""
    try:
        return render_template('Resources/financial_glossary.html')
    except: 
        try: 
            return render_template('financial_glossary.html')
        except:
            return render_template('Errors/404.html'), 404


# ==================== SUPPORT ROUTES ====================

@main_bp. route('/privacy-policy', endpoint='privacy_policy')
def privacy_policy():
    """Renders the privacy policy page."""
    try: 
        return render_template('Support/privacy_policy.html')
    except:
        try:
            return render_template('privacy_policy.html')
        except: 
            return render_template('Errors/404.html'), 404


@main_bp.route('/terms-of-service', endpoint='terms_of_service')
def terms_of_service():
    """Renders the terms of service page."""
    try:
        return render_template('Support/terms-of-services.html')
    except:
        try:
            return render_template('terms_of_service.html')
        except:
            return render_template('Errors/404.html'), 404


@main_bp.route('/refund-policy', endpoint='refund_policy')
def refund_policy():
    """Renders the refund policy page."""
    try:
        return render_template('Support/refund_policy.html')
    except:
        try:
            return render_template('refund_policy.html')
        except:
            return render_template('Errors/404.html'), 404


@main_bp.route('/help-center', endpoint='help_center')
def help_center():
    """Renders the help center page."""
    try: 
        return render_template('Support/help_center.html')
    except:
        try:
            return render_template('help_center.html')
        except: 
            return render_template('Errors/404.html'), 404


@main_bp.route('/sitemap.xml', endpoint='sitemap')
def sitemap():
    """Generate sitemap.xml."""
    try: 
        static_folder = os.path.join(os. path.dirname(os.path.abspath(__file__)), 'static')
        return send_from_directory(static_folder, 'sitemap.xml')
    except Exception as e:
        print(f"Error serving sitemap: {e}")
        abort(404)


@main_bp.route('/robots.txt', endpoint='robots')
def robots():
    """Generate robots.txt."""
    try:
        static_folder = os.path. join(os.path.dirname(os. path.abspath(__file__)), 'static')
        return send_from_directory(static_folder, 'robots.txt')
    except Exception as e:
        print(f"Error serving robots. txt: {e}")
        abort(404)


# ==================== SHORTCUT/TEST ROUTES ====================

@main_bp.route('/test-ca-dashboard')
@login_required
def test_ca_dashboard():
    """Test route for CA dashboard - redirects to CA dashboard."""
    return redirect(url_for('ca_ecosystem.dashboard'))


@main_bp.route('/admin')
@login_required
def admin_shortcut():
    """Shortcut route for admin panel - redirects to admin dashboard."""
    if not check_admin_access():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.home'))
    return redirect(url_for('main.admin_dashboard'))


# ==================== AI CHAT ROUTES ====================

@main_bp. route('/chat', endpoint='chat')
@login_required
def chat():
    """Renders the AI chat interface."""
    return render_template('chat.html', user=current_user)


@main_bp.route('/chat/history', endpoint='chat_history')
@login_required
def chat_history():
    """Get user's chat history."""
    try:
        # Get chat history from Supabase
        queries = ChatService.get_user_history(current_user.id, limit=50)
        history = [{
            'id': q.get('id'),
            'query': q.get('question'),
            'response': q.get('response'),
            'created_at': q.get('created_at')
        } for q in queries] if queries else []
        return jsonify({'success': True, 'data': history})
    except Exception as e: 
        print(f"Chat history error: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch chat history'}), 500


# ==================== CA APPLICATION ROUTES ====================

@main_bp.route('/ca-application', endpoint='ca_application')
@login_required
def ca_application():
    """CA application form for users to become verified CAs"""
    from finucity.services.ca_ecosystem import CAEcosystemService
    
    try:
        applications = CAEcosystemService.get_ca_applications(limit=10) or []
        user_applications = [app for app in applications if app.get('user_id') == current_user.id]
        
        if user_applications:
            latest_app = user_applications[0]
            if latest_app['status'] in ['pending', 'under_review']:
                return redirect(url_for('main.ca_application_status'))
            elif latest_app['status'] == 'approved':
                return redirect(url_for('main.user_dashboard'))
    except Exception as e:
        print(f"Error checking existing application: {e}")
        # Continue to application form if there's an error
    
    return render_template('ca_application.html', current_year=2026)


@main_bp.route('/ca-application-status', endpoint='ca_application_status')
@login_required
def ca_application_status():
    """Check CA application status"""
    from finucity.services.ca_ecosystem import CAEcosystemService
    
    try:
        applications = CAEcosystemService.get_ca_applications(limit=1)
        user_applications = [app for app in applications if app.get('user_id') == current_user.id]
        
        if not user_applications:
            return redirect(url_for('main.ca_application'))
        
        return render_template('ca_application_status.html', application=user_applications[0])
    except Exception as e:
        print(f"Error loading application status: {e}")
        return render_template('ca_application.html'), 500


# ==================== CA DASHBOARD ROUTES ====================

@main_bp. route('/ca/dashboard', endpoint='ca_dashboard')
@login_required
def ca_dashboard():
    """CA Dashboard - Production-grade workspace for Chartered Accountants."""
    if not check_ca_access():
        flash('Access denied.  This area is for verified CAs only.', 'error')
        return redirect(url_for('main.home'))

    return render_template(
        'ca/dashboard.html',
        user=current_user,
        supabase_url=os.getenv('SUPABASE_URL'),
        supabase_anon_key=os.getenv('SUPABASE_ANON_KEY')
    )


@main_bp.route('/ca/profile', endpoint='ca_profile')
@login_required
def ca_profile():
    """CA Profile management page."""
    if not check_ca_access():
        flash('Access denied. ', 'error')
        return redirect(url_for('main.home'))

    return render_template(
        'ca/profile.html',
        user=current_user,
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.getenv('SUPABASE_ANON_KEY')
    )


@main_bp.route('/ca/clients', endpoint='ca_clients')
@login_required
def ca_clients():
    """CA Client requests page - Production version."""
    if not check_ca_access():
        flash('Access denied.', 'error')
        return redirect(url_for('main.home'))

    return render_template(
        'ca/clients.html',
        user=current_user,
        supabase_url=os.getenv('SUPABASE_URL'),
        supabase_anon_key=os.getenv('SUPABASE_ANON_KEY')
    )


@main_bp.route('/ca/documents', endpoint='ca_documents')
@login_required
def ca_documents():
    """CA Documents management page."""
    if not check_ca_access():
        flash('Access denied.', 'error')
        return redirect(url_for('main.home'))

    return render_template(
        'ca/documents.html',
        user=current_user,
        supabase_url=os.getenv('SUPABASE_URL'),
        supabase_key=os.getenv('SUPABASE_ANON_KEY')
    )


@main_bp.route('/ca/messages', endpoint='ca_messages')
@login_required
def ca_messages():
    """CA Messages and chat page."""
    if not check_ca_access():
        flash('Access denied.', 'error')
        return redirect(url_for('main.home'))

    return render_template(
        'ca/messages.html',
        user=current_user,
        supabase_url=os.getenv('SUPABASE_URL'),
        supabase_key=os.getenv('SUPABASE_ANON_KEY')
    )


@main_bp.route('/ca/services', endpoint='ca_services')
@login_required
def ca_services():
    """CA Services offered page."""
    if not check_ca_access():
        flash('Access denied.', 'error')
        return redirect(url_for('main.home'))

    return render_template(
        'ca/services.html',
        user=current_user,
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.getenv('SUPABASE_ANON_KEY')
    )


@main_bp.route('/ca/insights', endpoint='ca_insights')
@login_required
def ca_insights():
    """CA Insights and analytics page."""
    if not check_ca_access():
        flash('Access denied.', 'error')
        return redirect(url_for('main.home'))

    return render_template(
        'ca/insights.html',
        user=current_user,
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.getenv('SUPABASE_ANON_KEY')
    )


@main_bp.route('/ca/settings', endpoint='ca_settings')
@login_required
def ca_settings():
    """CA Settings page."""
    if not check_ca_access():
        flash('Access denied.', 'error')
        return redirect(url_for('main.home'))

    return render_template(
        'ca/settings.html',
        user=current_user,
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.getenv('SUPABASE_ANON_KEY')
    )


@main_bp.route('/ca/earnings', endpoint='ca_earnings')
@login_required
def ca_earnings():
    """CA Earnings and billing page."""
    if not check_ca_access():
        flash('Access denied.', 'error')
        return redirect(url_for('main.home'))

    return render_template(
        'ca/earnings.html',
        user=current_user,
        supabase_url=os.getenv('SUPABASE_URL'),
        supabase_key=os.getenv('SUPABASE_ANON_KEY')
    )


@main_bp. route('/ca/calendar', endpoint='ca_calendar')
@login_required
def ca_calendar():
    """CA Calendar and appointments page."""
    if not check_ca_access():
        flash('Access denied.', 'error')
        return redirect(url_for('main.home'))

    return render_template(
        'ca/calendar.html',
        user=current_user,
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.getenv('SUPABASE_ANON_KEY')
    )


@main_bp.route('/ca/reviews', endpoint='ca_reviews')
@login_required
def ca_reviews():
    """CA Reviews and ratings page."""
    if not check_ca_access():
        flash('Access denied.', 'error')
        return redirect(url_for('main.home'))

    return render_template(
        'ca/reviews.html',
        user=current_user,
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.getenv('SUPABASE_ANON_KEY')
    )


@main_bp.route('/ca/notifications', endpoint='ca_notifications')
@login_required
def ca_notifications():
    """CA Notifications page."""
    if not check_ca_access():
        flash('Access denied.', 'error')
        return redirect(url_for('main.home'))

    return render_template(
        'ca/notifications.html',
        user=current_user,
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.getenv('SUPABASE_ANON_KEY')
    )


# ==================== USER DASHBOARD ROUTES ====================

@main_bp. route('/user/dashboard', endpoint='user_dashboard')
@login_required
def user_dashboard():
    """User Dashboard - Main workspace for users."""
    user_role = getattr(current_user, 'role', 'user')
    if user_role in ['ca', 'admin']:
        return redirect(url_for('main.ca_dashboard'))

    return render_template('user/dashboard.html', user=current_user)


@main_bp.route('/user/find-ca', endpoint='find_ca')
@login_required
def find_ca():
    """Find a Chartered Accountant page."""
    return render_template('user/find_ca.html', user=current_user)


@main_bp.route('/user/consultations', endpoint='user_consultations')
@login_required
def user_consultations():
    """User's consultations page."""
    return render_template('user/consultations.html', user=current_user)


@main_bp.route('/user/messages', endpoint='user_messages')
@login_required
def user_messages():
    """User's messages page."""
    return render_template('user/messages.html', user=current_user)


@main_bp.route('/user/documents', endpoint='user_documents')
@login_required
def user_documents():
    """User's document vault page."""
    return render_template('user/documents.html', user=current_user)


@main_bp.route('/user/recommendations', endpoint='user_recommendations')
@login_required
def user_recommendations():
    """Personalized recommendations page."""
    return render_template('user/recommendations.html', user=current_user)


@main_bp.route('/user/settings', endpoint='user_settings')
@login_required
def user_settings():
    """User settings page."""
    return render_template('user/settings.html', user=current_user)


@main_bp.route('/user/notifications', endpoint='user_notifications')
@login_required
def user_notifications():
    """User notifications page."""
    return render_template('user/notifications.html', user=current_user)


@main_bp.route('/user/payments', endpoint='user_payments')
@login_required
def user_payments():
    """User payments history page."""
    return render_template('user/payments.html', user=current_user)


@main_bp.route('/user/consultation/<int:consultation_id>', endpoint='view_consultation')
@login_required
def view_consultation(consultation_id):
    """View a specific consultation."""
    # In a real app, fetch consultation from database
    return render_template('user/consultation_detail.html', consultation_id=consultation_id, user=current_user)


# ==================== ADMIN LOGIN & AUTH ====================

@main_bp.route('/admin/login', methods=['GET'])
def admin_login_page():
    """Separate admin login page - only for administrators."""
    if current_user.is_authenticated:
        if check_admin_access():
            return redirect(url_for('main.admin_dashboard'))
        else:
            flash('Admin access required.', 'error')
            return redirect(url_for('main.home'))
    return render_template('admin/admin_login.html')


@main_bp.route('/admin/auth/login', methods=['POST'])
def admin_auth_login():
    """Admin authentication endpoint - validates admin credentials."""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password required'}), 400

        sb = get_supabase()
        
        # Try Supabase Auth login first
        try:
            auth_response = sb.auth.sign_in_with_password({
                'email': email,
                'password': password
            })
            
            if auth_response and auth_response.user:
                user_id = auth_response.user.id
                
                # Get user profile and verify admin role
                profile_response = sb.table('profiles').select('*').eq('id', user_id).single().execute()
                
                if profile_response.data:
                    user_data = profile_response.data
                    
                    # CRITICAL: Check if user is admin
                    if user_data.get('role') != 'admin':
                        return jsonify({
                            'success': False, 
                            'error': 'Access denied. Admin privileges required.'
                        }), 403
                    
                    # Create Flask-Login user and login
                    user = User(user_data)
                    login_user(user, remember=True)
                    
                    return jsonify({
                        'success': True,
                        'message': 'Admin login successful',
                        'redirect': url_for('main.admin_dashboard')
                    })
                else:
                    return jsonify({'success': False, 'error': 'Admin profile not found'}), 404
                    
        except Exception as auth_error:
            print(f"Admin Supabase auth failed: {auth_error}")
            
            # Fallback: Check local password hash
            try:
                user_response = sb.table('profiles').select('*').eq('email', email).single().execute()
                
                if user_response.data:
                    user_data = user_response.data
                    
                    # Verify admin role
                    if user_data.get('role') != 'admin':
                        return jsonify({
                            'success': False,
                            'error': 'Access denied. Admin privileges required.'
                        }), 403
                    
                    # Check password hash
                    password_hash = user_data.get('password_hash')
                    if password_hash and check_password_hash(password_hash, password):
                        user = User(user_data)
                        login_user(user, remember=True)
                        
                        return jsonify({
                            'success': True,
                            'message': 'Admin login successful',
                            'redirect': url_for('main.admin_dashboard')
                        })
                    else:
                        return jsonify({'success': False, 'error': 'Invalid admin credentials'}), 401
                else:
                    return jsonify({'success': False, 'error': 'Admin account not found'}), 404
                    
            except Exception as db_error:
                print(f"Admin database check failed: {db_error}")
                return jsonify({'success': False, 'error': 'Authentication failed'}), 500

    except Exception as e:
        print(f"Admin login error: {e}")
        return jsonify({'success': False, 'error': 'Login system error'}), 500


# ==================== ADMIN DASHBOARD ROUTES ====================

@main_bp.route('/admin/dashboard', endpoint='admin_dashboard')
@login_required
def admin_dashboard():
    """Admin Dashboard - Manage platform and CA verifications."""
    if not check_admin_access():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.home'))
    
    return render_template(
        'admin/dashboard.html',
        user=current_user,
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.getenv('SUPABASE_ANON_KEY')
    )


@main_bp.route('/admin/ca-applications', endpoint='admin_ca_applications')
@login_required
def admin_ca_applications():
    """Admin CA Applications management page."""
    if not check_admin_access():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.home'))
    
    return render_template(
        'admin/ca_applications.html',
        user=current_user,
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.getenv('SUPABASE_ANON_KEY')
    )


@main_bp.route('/api/admin/ca-applications', endpoint='api_admin_ca_applications')
@login_required
def api_admin_ca_applications():
    """API endpoint to get CA applications for admin."""
    if not check_admin_access():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        sb = get_supabase()
        status = request.args.get('status', 'pending')
        
        # Fetch applications from database
        query = sb.table('ca_applications').select('*')
        
        if status and status != 'all':
            query = query.eq('status', status)
        
        response = query.order('created_at', desc=True).execute()
        applications = response.data if response.data else []
        
        return jsonify({
            'success': True,
            'data': applications,
            'count': len(applications)
        })
    except Exception as e:
        print(f"Error fetching CA applications: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': []
        }), 500


@main_bp.route('/api/admin/ca-application/<application_id>/approve', endpoint='api_admin_approve_ca', methods=['POST'])
@login_required
def api_admin_approve_ca(application_id):
    """Approve CA application."""
    if not check_admin_access():
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    try:
        sb = get_supabase()
        
        # Get application first
        app_response = sb.table('ca_applications').select('*').eq('id', application_id).single().execute()
        if not app_response.data:
            return jsonify({'success': False, 'error': 'Application not found'}), 404
        
        application = app_response.data
        user_id = application['user_id']
        
        # Update application status
        sb.table('ca_applications').update({
            'status': 'approved',
            'reviewed_by': current_user.id,
            'reviewed_at': 'now()',
            'admin_notes': request.get_json().get('notes', '') if request.get_json() else ''
        }).eq('id', application_id).execute()
        
        # Update user role to 'ca'
        sb.table('profiles').update({
            'role': 'ca'
        }).eq('id', user_id).execute()
        
        return jsonify({
            'success': True,
            'message': 'CA application approved! User is now a verified CA.'
        })
        
    except Exception as e:
        print(f"Error approving CA application: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to approve: {str(e)}'
        }), 500


@main_bp.route('/api/admin/ca-application/<application_id>/reject', endpoint='api_admin_reject_ca', methods=['POST'])
@login_required
def api_admin_reject_ca(application_id):
    """Reject CA application."""
    if not check_admin_access():
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'No reason provided')
        
        if not reason or reason == 'No reason provided':
            return jsonify({'success': False, 'error': 'Rejection reason is required'}), 400
        
        sb = get_supabase()
        
        # Update application status
        sb.table('ca_applications').update({
            'status': 'rejected',
            'rejection_reason': reason,
            'reviewed_by': current_user.id,
            'reviewed_at': 'now()'
        }).eq('id', application_id).execute()
        
        return jsonify({
            'success': True,
            'message': 'Application rejected. Applicant will be notified.'
        })
        
    except Exception as e:
        print(f"Error rejecting CA application: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to reject: {str(e)}'
        }), 500


@main_bp.route('/admin/users', endpoint='admin_users')
@login_required
def admin_users():
    """Admin Users management page."""
    if not check_admin_access():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.home'))
    
    sb = get_supabase()
    try:
        users_response = sb.table('profiles').select('*').order('created_at', desc=True).limit(100).execute()
        users = users_response.data if users_response.data else []
    except Exception as e:
        print(f"Error fetching users: {e}")
        users = []
    
    return render_template('admin/users.html', user=current_user, users=users)


# ==================== AUTH ROUTES ====================

@auth_bp.route('/gateway', methods=['GET'])
def gateway():
    """Role selection gateway - entry point for auth."""
    if current_user.is_authenticated:
        return redirect_after_auth()
    return render_template(
        'auth/gateway.html',
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.getenv('SUPABASE_ANON_KEY')
    )


@auth_bp.route('/login', methods=['GET'])
def login():
    """Unified login/signup page."""
    if current_user.is_authenticated:
        return redirect_after_auth()
    return render_template(
        'auth/login.html',
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.getenv('SUPABASE_ANON_KEY')
    )


@auth_bp.route('/callback', methods=['GET'])
def auth_callback():
    """Supabase OAuth callback handler."""
    return render_template(
        'auth/auth_callback.html',
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.getenv('SUPABASE_ANON_KEY')
    )


@auth_bp.route('/ca-apply', methods=['GET'])
def ca_apply():
    """CA professional application form."""
    if current_user.is_authenticated:
        if hasattr(current_user, 'role') and current_user. role in ['ca', 'ca_pending']:
            return redirect(url_for('main.home'))
    return render_template(
        'auth/ca_apply.html',
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.getenv('SUPABASE_ANON_KEY')
    )


@auth_bp. route('/ca-pending', methods=['GET'])
@login_required
def ca_pending():
    """CA verification pending page."""
    return render_template('auth/ca_pending.html')


@auth_bp.route('/supabase-login', methods=['POST'])
def supabase_login():
    """Bridge Supabase auth to Flask session."""
    auth_header = request.headers. get('Authorization', '')
    if not auth_header. startswith('Bearer '):
        return jsonify({'error': 'missing token'}), 401

    token = auth_header.split(' ', 1)[1]
    claims, err = decode_supabase_jwt(token)
    if err or not claims:
        return jsonify({'error': 'invalid token', 'detail': err}), 401

    # Get role from request body or claims
    try:
        body_data = request.get_json() or {}
        requested_role = body_data.get('role', 'user')
    except: 
        requested_role = 'user'

    # Get role from claims if available
    claims_role = claims. get('user_metadata', {}).get('role', 'user')

    # Use claims role if it's a privileged role, otherwise use requested role for new users
    if claims_role in ['ca', 'admin', 'ca_pending']:
        role = claims_role
    else:
        role = 'user'  # Default to user, CA requires application

    try:
        user = ensure_local_user_from_claims(claims, role=role)
    except Exception as e: 
        return jsonify({'error': 'user mapping failed', 'detail': str(e)}), 400

    login_user(user, remember=True)

    user_role = getattr(user, 'role', 'user') if hasattr(user, 'role') else 'user'

    # Determine redirect URL based on role
    if user_role in ['ca', 'admin']:
        redirect_url = url_for('main.ca_dashboard')
    elif user_role == 'ca_pending': 
        redirect_url = url_for('auth.ca_pending')
    elif requested_role == 'ca' and user_role == 'user':
        # User selected CA but isn't verified - redirect to apply
        redirect_url = url_for('auth.ca_apply')
    else:
        redirect_url = url_for('main.user_dashboard')

    return jsonify({
        'ok': True,
        'success': True,
        'id': user.id,
        'email':  user.email,
        'role': user_role,
        'redirect_url': redirect_url
    })

# ==================== FLASK EMAIL/PASSWORD AUTH ====================

@auth_bp.route('/flask-login', methods=['POST'])
def flask_login():
    """Handle email/password login via Flask."""
    try:
        from werkzeug.security import check_password_hash
        
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        requested_role = data.get('role', 'user')

        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password are required'}), 400

        # Try Supabase Auth first
        sb = get_supabase()
        try:
            auth_response = sb.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user:
                # Get or create profile
                user_data = UserService.get_by_email(email)
                if not user_data:
                    # Create profile for auth user
                    user_data = UserService.create({
                        'id': auth_response.user.id,
                        'email': email,
                        'username': email.split('@')[0],
                        'role': 'user'
                    })
                
                user = User(user_data)
                login_user(user, remember=True)
                
                user_role = getattr(user, 'role', 'user')
                if user_role == 'admin':
                    redirect_url = url_for('main.admin_dashboard')
                elif user_role in ['ca']:
                    redirect_url = url_for('main.ca_dashboard')
                elif user_role == 'ca_pending':
                    redirect_url = url_for('auth.ca_pending')
                else:
                    redirect_url = url_for('main.user_dashboard')
                
                return jsonify({
                    'success': True,
                    'ok': True,
                    'message': 'Login successful',
                    'id': user.id,
                    'email': user.email,
                    'role': user_role,
                    'redirect_url': redirect_url
                })
        except Exception as supabase_error:
            print(f"Supabase auth failed, trying password hash: {supabase_error}")
            # Fallback to password hash check for manually created users
            user_data = UserService.get_by_email(email)
            
            if not user_data:
                return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
            
            # Check password hash
            password_hash = user_data.get('password_hash')
            if not password_hash or not check_password_hash(password_hash, password):
                return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
            
            user = User(user_data)
            login_user(user, remember=True)
            
            user_role = getattr(user, 'role', 'user')
            if user_role == 'admin':
                redirect_url = url_for('main.admin_dashboard')
            elif user_role in ['ca']:
                redirect_url = url_for('main.ca_dashboard')
            elif user_role == 'ca_pending':
                redirect_url = url_for('auth.ca_pending')
            else:
                redirect_url = url_for('main.user_dashboard')
            
            return jsonify({
                'success': True,
                'ok': True,
                'message': 'Login successful',
                'id': user.id,
                'email': user.email,
                'role': user_role,
                'redirect_url': redirect_url
            })

    except Exception as e:
        print(f"Flask login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'An error occurred during login'}), 500


@auth_bp.route('/flask-signup', methods=['POST'])
def flask_signup():
    """Handle email/password signup via Flask."""
    try:
        from werkzeug.security import generate_password_hash
        
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip().title()
        last_name = data.get('last_name', '').strip().title()
        requested_role = data.get('role', 'user')

        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password are required'}), 400

        if len(password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({'success': False, 'error': 'Please enter a valid email address'}), 400

        # Check if user already exists
        existing_user = UserService.get_by_email(email)
        if existing_user:
            return jsonify({'success': False, 'error': 'An account with this email already exists'}), 400

        # Try to create user in Supabase Auth first
        sb = get_supabase()
        try:
            auth_response = sb.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "first_name": first_name,
                        "last_name": last_name
                    }
                }
            })
            
            if auth_response.user:
                user_id = auth_response.user.id
            else:
                raise Exception("Supabase signup failed")
        except Exception as auth_error:
            print(f"Supabase Auth signup error: {auth_error}")
            # Generate UUID for manual user creation
            user_id = str(uuid.uuid4())

        # Generate unique username
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while True:
            existing = sb.table('profiles').select('id').eq('username', username.lower()).limit(1).execute()
            if not existing.data:
                break
            username = f"{base_username}{counter}"
            counter += 1

        # Create profile in Supabase profiles table
        user_data = {
            'id': user_id,
            'email': email,
            'username': username.lower(),
            'first_name': first_name if first_name else username.title(),
            'last_name': last_name,
            'role': 'user',
            'password_hash': generate_password_hash(password),
            'email_verified': False
        }

        created_user = UserService.create(user_data)
        if not created_user:
            return jsonify({'success': False, 'error': 'Failed to create account'}), 500

        # Login the new user
        new_user = User(created_user)
        login_user(new_user, remember=True)

        # Determine redirect
        if requested_role == 'ca':
            redirect_url = url_for('auth.ca_apply')
        else:
            redirect_url = url_for('main.user_dashboard')

        return jsonify({
            'success': True,
            'ok': True,
            'message': 'Account created successfully',
            'id': new_user.id,
            'email': new_user.email,
            'role': 'user',
            'redirect_url': redirect_url
        })

    except Exception as e:
        print(f"Flask signup error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'An error occurred during registration'}), 500


def redirect_after_auth():
    """Helper function to redirect user after authentication."""
    user_role = getattr(current_user, 'role', 'user')
    
    if user_role == 'ca': 
        return redirect(url_for('main.ca_dashboard'))
    elif user_role == 'admin': 
        return redirect(url_for('main.ca_dashboard'))  # or admin dashboard
    elif user_role == 'ca_pending': 
        return redirect(url_for('auth.ca_pending'))
    else:
        return redirect(url_for('main.user_dashboard'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Legacy registration."""
    if current_user.is_authenticated:
        flash('You are already logged in! ', 'info')
        return redirect(url_for('main.home'))

    if request.method == 'POST': 
        username = request.form. get('username', '').strip().lower()
        email = request.form. get('email', '').strip().lower()
        first_name = request. form.get('first_name', '').strip().title()
        last_name = request.form.get('last_name', '').strip().title()
        password = request.form.get('password', '')
        confirm_password = request.form. get('confirm_password', '')

        if not all([username, email, first_name, last_name, password]):
            flash('All fields are required. ', 'error')
        elif len(username) < 3:
            flash('Username must be at least 3 characters long. ', 'error')
        elif len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
        elif password != confirm_password: 
            flash('Passwords do not match. ', 'error')
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Please enter a valid email address.', 'error')
        else:
            # Check username and email in Supabase
            sb = get_supabase()
            username_check = sb.table('profiles').select('id').eq('username', username).limit(1).execute()
            if username_check.data:
                flash('Username is already taken.  Please choose another.', 'error')
            elif UserService.get_by_email(email):
                flash('An account with that email already exists.', 'error')
            else:
                try:
                    from werkzeug.security import generate_password_hash
                    user_data = {
                        'username': username,
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'role': 'user',
                        'password_hash': generate_password_hash(password)
                    }
                    created = UserService.create(user_data)
                    if created:
                        flash(f'Welcome aboard, {first_name}!  Your account has been created successfully.  Please log in.', 'success')
                        return redirect(url_for('auth.login'))
                    else:
                        flash('An error occurred during registration. Please try again.', 'error')
                except Exception as e:
                    print(f"Registration error: {e}")
                    flash('An error occurred during registration. Please try again.', 'error')

    return render_template('auth/register.html')


@auth_bp. route('/logout')
@login_required
def logout():
    """Handles user logout."""
    user_name = current_user.first_name if current_user.first_name else 'User'
    logout_user()
    flash(f'Goodbye, {user_name}!  You have been successfully logged out.', 'info')
    return redirect(url_for('main.home'))


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    """Password reset request."""
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request. method == 'POST':
        email = request.form. get('email', '').strip().lower()

        if not email: 
            flash('Please enter your email address. ', 'error')
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Please enter a valid email address.', 'error')
        else:
            flash('If an account exists with that email, you will receive password reset instructions shortly.', 'info')
            return redirect(url_for('auth.login'))

    return render_template('auth/reset_password_request.html')


@auth_bp.route('/verify-email/<token>', methods=['GET'])
def verify_email(token):
    """Email verification endpoint."""
    try:
        # Implement email verification logic here
        flash('Email verified successfully!  You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    except Exception as e:
        print(f"Email verification error: {e}")
        flash('Invalid or expired verification link. ', 'error')
        return redirect(url_for('auth.login'))


# ==================== API ENDPOINTS ====================

@api_bp.route('/me', methods=['GET'])
def api_me():
    """Get current user info from Supabase token."""
    auth_header = request. headers.get('Authorization', '')
    if not auth_header. startswith('Bearer '):
        return jsonify({'error': 'missing token'}), 401

    token = auth_header. split(' ', 1)[1]
    claims, err = decode_supabase_jwt(token)
    if err or not claims:
        return jsonify({'error':  'invalid token', 'detail': err}), 401

    user_id = claims.get('sub')
    email = claims.get('email') or claims.get('user_metadata', {}).get('email')

    # Get user from Supabase
    user_data = UserService.get_by_email(email.lower()) if email else None
    role = user_data.get('role', 'user') if user_data else 'user'

    return jsonify({
        'id': user_id,
        'role': role,
        'email': email
    })

@api_bp.route('/homepage-stats', methods=['GET'])
def homepage_stats():
    """Get real-time homepage statistics."""
    try:
        supabase = get_supabase_admin()
        
        # Count active users (all registered users)
        users_response = supabase.table('profiles').select('id', count='exact').execute()
        active_users = users_response.count if users_response.count else 0
        
        # Count total chat queries
        queries_response = supabase.table('chat_queries').select('id', count='exact').execute()
        total_queries = queries_response.count if queries_response.count else 0
        
        # Count verified CAs (users with role='ca')
        ca_response = supabase.table('profiles').select('id', count='exact').eq('role', 'ca').execute()
        verified_cas = ca_response.count if ca_response.count else 0
        
        # Calculate accuracy rate (placeholder - can be enhanced with actual feedback data)
        # For now, if we have queries, use feedback data; otherwise default to 0
        accuracy_rate = 0
        if total_queries > 0:
            feedback_response = supabase.table('user_feedback').select('rating', count='exact').execute()
            if feedback_response.count and feedback_response.count > 0:
                # Calculate average rating and convert to percentage
                ratings = [item.get('rating', 0) for item in feedback_response.data]
                avg_rating = sum(ratings) / len(ratings) if ratings else 0
                accuracy_rate = round((avg_rating / 5) * 100, 1)
            else:
                # No feedback yet, default to 0
                accuracy_rate = 0
        
        return jsonify({
            'active_users': active_users,
            'total_queries': total_queries,
            'accuracy_rate': accuracy_rate,
            'verified_cas': verified_cas
        })
    except Exception as e:
        print(f"Error fetching homepage stats: {str(e)}")
        return jsonify({
            'active_users': 0,
            'total_queries': 0,
            'accuracy_rate': 0,
            'verified_cas': 0
        }), 500

    """Handle CA application submission."""
    try:
        full_name = request. form.get('full_name')
        email = request.form.get('email')
        phone = request.form. get('phone')
        city = request.form. get('city')
        state = request. form.get('state')
        icai_number = request.form. get('icai_number')
        registration_year = request.form. get('registration_year')
        ca_type = request.form. get('ca_type')
        experience_years = request.form. get('experience_years')
        firm_name = request.form. get('firm_name', '')
        practice_address = request.form. get('practice_address', '')
        services = request.form. getlist('services')
        client_types = request.form. getlist('client_types')

        if not all([full_name, email, phone, city, state, icai_number, registration_year, ca_type, experience_years]):
            return jsonify({'error':  'Missing required fields'}), 400

        icai_certificate = request.files.get('icai_certificate')
        gov_id = request.files.get('gov_id')
        photo = request.files. get('photo')

        application_id = str(uuid.uuid4())

        print(f"CA Application received: {application_id}")
        print(f"  Name: {full_name}")
        print(f"  Email:  {email}")
        print(f"  ICAI:  {icai_number}")
        print(f"  Services: {services}")

        return jsonify({
            'success': True,
            'message': 'Application submitted successfully',
            'application_id':  application_id
        })

    except Exception as e:
        print(f"CA application error: {e}")
        return jsonify({'error': 'Failed to submit application'}), 500


@api_bp.route('/admin/users/<user_id>/role', methods=['POST'])
@login_required
def update_user_role(user_id):
    """Admin endpoint to update user role (approve/reject CA applications)."""
    if not check_admin_access():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        new_role = data.get('role')
        
        if new_role not in ['user', 'ca', 'ca_pending', 'admin']:
            return jsonify({'error': 'Invalid role'}), 400
        
        # Update user role in Supabase
        updated = UserService.update(user_id, {'role': new_role})
        
        if updated:
            return jsonify({
                'success': True,
                'message': f'User role updated to {new_role}',
                'user_id': user_id,
                'new_role': new_role
            })
        else:
            return jsonify({'error': 'Failed to update user'}), 500
    
    except Exception as e:
        print(f"Update role error: {e}")
        return jsonify({'error': 'Failed to update role'}), 500


@api_bp.route('/admin/stats', methods=['GET'])
@login_required
def api_admin_stats():
    """Get admin dashboard statistics - REAL-TIME from Supabase."""
    if not check_admin_access():
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        sb = get_supabase()
        
        # Total users
        users_response = sb.table('profiles').select('id', count='exact').execute()
        total_users = users_response.count if hasattr(users_response, 'count') else 0
        
        # Total queries
        queries_response = sb.table('chat_queries').select('id', count='exact').execute()
        total_queries = queries_response.count if hasattr(queries_response, 'count') else 0
        
        # Active CAs
        cas_response = sb.table('profiles').select('id', count='exact').eq('role', 'ca').execute()
        active_cas = cas_response.count if hasattr(cas_response, 'count') else 0
        
        # Pending CA applications
        pending_response = sb.table('profiles').select('id', count='exact').eq('role', 'ca_pending').execute()
        pending_applications = pending_response.count if hasattr(pending_response, 'count') else 0
        
        stats = {
            'total_users': total_users,
            'total_queries': total_queries,
            'active_cas': active_cas,
            'pending_applications': pending_applications,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        print(f"Admin stats error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Failed to fetch stats'}), 500


@api_bp.route('/admin/ca-applications', methods=['GET'])
@login_required
def api_admin_ca_applications():
    """Get pending CA applications for admin review."""
    if not check_admin_access():
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        sb = get_supabase()
        
        # Get all users with ca_pending role
        response = sb.table('profiles').select('*').eq('role', 'ca_pending').order('created_at', desc=True).execute()
        
        applications = response.data if response.data else []
        
        return jsonify({'success': True, 'data': applications})
    except Exception as e:
        print(f"CA applications fetch error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Failed to fetch applications'}), 500


# =====================================================
# ADMIN CONTROL ENDPOINTS - CA Management
# =====================================================

@api_bp.route('/admin/ca/suspend', methods=['POST'])
@login_required
def admin_suspend_ca():
    """Suspend a CA account with audit trail."""
    if not check_admin_access():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        sb = get_supabase()
        data = request.get_json()
        ca_id = data.get('ca_id')
        reason = data.get('reason', 'No reason provided')
        
        if not ca_id:
            return jsonify({'error': 'CA ID required'}), 400
        
        # Update CA profile status
        update_response = sb.table('profiles').update({
            'ca_status': 'suspended',
            'suspension_reason': reason,
            'last_admin_action_at': datetime.utcnow().isoformat()
        }).eq('id', ca_id).eq('role', 'ca').execute()
        
        if not update_response.data:
            return jsonify({'error': 'Failed to suspend CA'}), 500
        
        # Log admin action
        sb.table('ca_admin_actions').insert({
            'admin_id': current_user.id,
            'ca_id': ca_id,
            'action_type': 'suspend',
            'reason': reason,
            'old_status': 'active',
            'new_status': 'suspended'
        }).execute()
        
        return jsonify({
            'success': True,
            'message': 'CA suspended successfully'
        })
    
    except Exception as e:
        print(f"Suspend CA error: {e}")
        return jsonify({'error': 'Failed to suspend CA'}), 500


@api_bp.route('/admin/ca/unsuspend', methods=['POST'])
@login_required
def admin_unsuspend_ca():
    """Restore suspended CA account."""
    if not check_admin_access():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        sb = get_supabase()
        data = request.get_json()
        ca_id = data.get('ca_id')
        notes = data.get('notes', '')
        
        if not ca_id:
            return jsonify({'error': 'CA ID required'}), 400
        
        # Update CA profile status
        update_response = sb.table('profiles').update({
            'ca_status': 'active',
            'suspension_reason': None,
            'last_admin_action_at': datetime.utcnow().isoformat()
        }).eq('id', ca_id).execute()
        
        if not update_response.data:
            return jsonify({'error': 'Failed to unsuspend CA'}), 500
        
        # Log admin action
        sb.table('ca_admin_actions').insert({
            'admin_id': current_user.id,
            'ca_id': ca_id,
            'action_type': 'unsuspend',
            'reason': 'Suspension lifted',
            'notes': notes,
            'old_status': 'suspended',
            'new_status': 'active'
        }).execute()
        
        return jsonify({
            'success': True,
            'message': 'CA account restored'
        })
    
    except Exception as e:
        print(f"Unsuspend CA error: {e}")
        return jsonify({'error': 'Failed to unsuspend CA'}), 500


@api_bp.route('/admin/ca/freeze-earnings', methods=['POST'])
@login_required
def admin_freeze_earnings():
    """Freeze CA earnings to prevent withdrawals."""
    if not check_admin_access():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        sb = get_supabase()
        data = request.get_json()
        ca_id = data.get('ca_id')
        reason = data.get('reason', 'Pending investigation')
        
        if not ca_id:
            return jsonify({'error': 'CA ID required'}), 400
        
        # Freeze earnings
        update_response = sb.table('profiles').update({
            'earnings_frozen': True,
            'last_admin_action_at': datetime.utcnow().isoformat()
        }).eq('id', ca_id).eq('role', 'ca').execute()
        
        if not update_response.data:
            return jsonify({'error': 'Failed to freeze earnings'}), 500
        
        # Log admin action
        sb.table('ca_admin_actions').insert({
            'admin_id': current_user.id,
            'ca_id': ca_id,
            'action_type': 'freeze_earnings',
            'reason': reason
        }).execute()
        
        return jsonify({
            'success': True,
            'message': 'Earnings frozen successfully'
        })
    
    except Exception as e:
        print(f"Freeze earnings error: {e}")
        return jsonify({'error': 'Failed to freeze earnings'}), 500


@api_bp.route('/admin/ca/unfreeze-earnings', methods=['POST'])
@login_required
def admin_unfreeze_earnings():
    """Unfreeze CA earnings."""
    if not check_admin_access():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        sb = get_supabase()
        data = request.get_json()
        ca_id = data.get('ca_id')
        notes = data.get('notes', '')
        
        if not ca_id:
            return jsonify({'error': 'CA ID required'}), 400
        
        # Unfreeze earnings
        update_response = sb.table('profiles').update({
            'earnings_frozen': False,
            'last_admin_action_at': datetime.utcnow().isoformat()
        }).eq('id', ca_id).execute()
        
        if not update_response.data:
            return jsonify({'error': 'Failed to unfreeze earnings'}), 500
        
        # Log admin action
        sb.table('ca_admin_actions').insert({
            'admin_id': current_user.id,
            'ca_id': ca_id,
            'action_type': 'unfreeze_earnings',
            'reason': 'Investigation cleared',
            'notes': notes
        }).execute()
        
        return jsonify({
            'success': True,
            'message': 'Earnings unfrozen'
        })
    
    except Exception as e:
        print(f"Unfreeze earnings error: {e}")
        return jsonify({'error': 'Failed to unfreeze earnings'}), 500


@api_bp.route('/admin/ca/revoke-verification', methods=['POST'])
@login_required
def admin_revoke_verification():
    """Revoke CA verification status."""
    if not check_admin_access():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        sb = get_supabase()
        data = request.get_json()
        ca_id = data.get('ca_id')
        reason = data.get('reason', 'Verification revoked by admin')
        
        if not ca_id:
            return jsonify({'error': 'CA ID required'}), 400
        
        # Revoke verification
        update_response = sb.table('profiles').update({
            'verification_revoked': True,
            'last_admin_action_at': datetime.utcnow().isoformat()
        }).eq('id', ca_id).eq('role', 'ca').execute()
        
        if not update_response.data:
            return jsonify({'error': 'Failed to revoke verification'}), 500
        
        # Log admin action
        sb.table('ca_admin_actions').insert({
            'admin_id': current_user.id,
            'ca_id': ca_id,
            'action_type': 'revoke_verification',
            'reason': reason
        }).execute()
        
        return jsonify({
            'success': True,
            'message': 'Verification revoked'
        })
    
    except Exception as e:
        print(f"Revoke verification error: {e}")
        return jsonify({'error': 'Failed to revoke verification'}), 500


@api_bp.route('/admin/ca/restore-verification', methods=['POST'])
@login_required
def admin_restore_verification():
    """Restore CA verification status."""
    if not check_admin_access():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        sb = get_supabase()
        data = request.get_json()
        ca_id = data.get('ca_id')
        notes = data.get('notes', '')
        
        if not ca_id:
            return jsonify({'error': 'CA ID required'}), 400
        
        # Restore verification
        update_response = sb.table('profiles').update({
            'verification_revoked': False,
            'last_admin_action_at': datetime.utcnow().isoformat()
        }).eq('id', ca_id).execute()
        
        if not update_response.data:
            return jsonify({'error': 'Failed to restore verification'}), 500
        
        # Log admin action
        sb.table('ca_admin_actions').insert({
            'admin_id': current_user.id,
            'ca_id': ca_id,
            'action_type': 'restore_verification',
            'reason': 'Verification restored',
            'notes': notes
        }).execute()
        
        return jsonify({
            'success': True,
            'message': 'Verification restored'
        })
    
    except Exception as e:
        print(f"Restore verification error: {e}")
        return jsonify({'error': 'Failed to restore verification'}), 500


@api_bp.route('/admin/ca/ban', methods=['POST'])
@login_required
def admin_ban_ca():
    """Permanently ban a CA account."""
    if not check_admin_access():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        sb = get_supabase()
        data = request.get_json()
        ca_id = data.get('ca_id')
        reason = data.get('reason', 'Terms of service violation')
        
        if not ca_id:
            return jsonify({'error': 'CA ID required'}), 400
        
        # Ban CA
        update_response = sb.table('profiles').update({
            'ca_status': 'banned',
            'suspension_reason': reason,
            'earnings_frozen': True,
            'verification_revoked': True,
            'last_admin_action_at': datetime.utcnow().isoformat()
        }).eq('id', ca_id).eq('role', 'ca').execute()
        
        if not update_response.data:
            return jsonify({'error': 'Failed to ban CA'}), 500
        
        # Log admin action
        sb.table('ca_admin_actions').insert({
            'admin_id': current_user.id,
            'ca_id': ca_id,
            'action_type': 'ban',
            'reason': reason,
            'old_status': 'active',
            'new_status': 'banned'
        }).execute()
        
        return jsonify({
            'success': True,
            'message': 'CA banned permanently'
        })
    
    except Exception as e:
        print(f"Ban CA error: {e}")
        return jsonify({'error': 'Failed to ban CA'}), 500


@api_bp.route('/admin/ca/approve-withdrawal', methods=['POST'])
@login_required
def admin_approve_withdrawal():
    """Approve CA withdrawal request."""
    if not check_admin_access():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        sb = get_supabase()
        data = request.get_json()
        transaction_id = data.get('transaction_id')
        notes = data.get('notes', '')
        
        if not transaction_id:
            return jsonify({'error': 'Transaction ID required'}), 400
        
        # Approve withdrawal
        update_response = sb.table('ca_earnings').update({
            'status': 'approved',
            'approved_by': current_user.id,
            'approved_at': datetime.utcnow().isoformat(),
            'admin_notes': notes
        }).eq('id', transaction_id).eq('transaction_type', 'debit').execute()
        
        if not update_response.data:
            return jsonify({'error': 'Failed to approve withdrawal'}), 500
        
        transaction = update_response.data[0]
        
        # Log admin action
        sb.table('ca_admin_actions').insert({
            'admin_id': current_user.id,
            'ca_id': transaction['ca_id'],
            'action_type': 'approve_withdrawal',
            'reason': 'Withdrawal approved',
            'notes': notes,
            'affected_amount': transaction['amount']
        }).execute()
        
        return jsonify({
            'success': True,
            'message': 'Withdrawal approved'
        })
    
    except Exception as e:
        print(f"Approve withdrawal error: {e}")
        return jsonify({'error': 'Failed to approve withdrawal'}), 500


@api_bp.route('/admin/ca/reject-withdrawal', methods=['POST'])
@login_required
def admin_reject_withdrawal():
    """Reject CA withdrawal request."""
    if not check_admin_access():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        sb = get_supabase()
        data = request.get_json()
        transaction_id = data.get('transaction_id')
        reason = data.get('reason', 'Requirements not met')
        
        if not transaction_id:
            return jsonify({'error': 'Transaction ID required'}), 400
        
        # Reject withdrawal
        update_response = sb.table('ca_earnings').update({
            'status': 'rejected',
            'approved_by': current_user.id,
            'approved_at': datetime.utcnow().isoformat(),
            'rejection_reason': reason
        }).eq('id', transaction_id).eq('transaction_type', 'debit').execute()
        
        if not update_response.data:
            return jsonify({'error': 'Failed to reject withdrawal'}), 500
        
        transaction = update_response.data[0]
        
        # Log admin action
        sb.table('ca_admin_actions').insert({
            'admin_id': current_user.id,
            'ca_id': transaction['ca_id'],
            'action_type': 'reject_withdrawal',
            'reason': reason,
            'affected_amount': transaction['amount']
        }).execute()
        
        return jsonify({
            'success': True,
            'message': 'Withdrawal rejected'
        })
    
    except Exception as e:
        print(f"Reject withdrawal error: {e}")
        return jsonify({'error': 'Failed to reject withdrawal'}), 500


@api_bp.route('/admin/ca/earnings-adjustment', methods=['POST'])
@login_required
def admin_earnings_adjustment():
    """Manual earnings adjustment for CA."""
    if not check_admin_access():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        sb = get_supabase()
        data = request.get_json()
        ca_id = data.get('ca_id')
        amount = data.get('amount')
        reason = data.get('reason', 'Admin adjustment')
        
        if not ca_id or amount is None:
            return jsonify({'error': 'CA ID and amount required'}), 400
        
        # Create adjustment transaction
        transaction_response = sb.table('ca_earnings').insert({
            'ca_id': ca_id,
            'transaction_type': 'adjustment',
            'amount': amount,
            'title': 'Admin Adjustment',
            'description': reason,
            'status': 'completed',
            'approved_by': current_user.id,
            'approved_at': datetime.utcnow().isoformat(),
            'processed_at': datetime.utcnow().isoformat()
        }).execute()
        
        if not transaction_response.data:
            return jsonify({'error': 'Failed to create adjustment'}), 500
        
        # Log admin action
        sb.table('ca_admin_actions').insert({
            'admin_id': current_user.id,
            'ca_id': ca_id,
            'action_type': 'adjust_earnings',
            'reason': reason,
            'affected_amount': amount
        }).execute()
        
        return jsonify({
            'success': True,
            'message': 'Earnings adjusted successfully'
        })
    
    except Exception as e:
        print(f"Earnings adjustment error: {e}")
        return jsonify({'error': 'Failed to adjust earnings'}), 500


@api_bp.route('/ca/consultations', methods=['GET'])
@login_required
def get_ca_consultations():
    """Get all consultations for CA with enriched client details."""
    if not check_ca_access():
        return jsonify({'error': 'CA access required'}), 403
    
    try:
        sb = get_supabase()
        ca_id = session.get('user_id')
        
        # Fetch all consultations for this CA with client profile data
        result = sb.table('consultations').select(
            '*, profiles!consultations_user_id_fkey(full_name, city, avatar_url)'
        ).eq('ca_id', ca_id).order('created_at', desc=True).execute()
        
        # Enrich consultation data with client info
        consultations = []
        for item in result.data:
            consultation = {
                'id': item['id'],
                'user_id': item['user_id'],
                'service_type': item['service_type'],
                'description': item['description'],
                'min_budget': item['min_budget'],
                'max_budget': item['max_budget'],
                'status': item['status'],
                'created_at': item['created_at'],
                'accepted_at': item.get('accepted_at'),
                'started_at': item.get('started_at'),
                'completed_at': item.get('completed_at'),
                'client_name': item['profiles']['full_name'] if item.get('profiles') else 'Unknown',
                'client_city': item['profiles']['city'] if item.get('profiles') else 'Unknown',
                'client_avatar': item['profiles']['avatar_url'] if item.get('profiles') else None
            }
            consultations.append(consultation)
        
        return jsonify(consultations)
    
    except Exception as e:
        print(f"Get consultations error: {e}")
        return jsonify([])


@api_bp.route('/ca/start-consultation', methods=['POST'])
@login_required
def start_consultation():
    """Update consultation status from accepted to in_progress."""
    if not check_ca_access():
        return jsonify({'error': 'CA access required'}), 403
    
    try:
        data = request.get_json()
        consultation_id = data.get('consultation_id')
        
        if not consultation_id:
            return jsonify({'error': 'Consultation ID required'}), 400
        
        sb = get_supabase()
        ca_id = session.get('user_id')
        
        # Verify ownership and update status
        result = sb.table('consultations').update({
            'status': 'in_progress',
            'started_at': 'now()'
        }).eq('id', consultation_id).eq('ca_id', ca_id).eq('status', 'accepted').execute()
        
        if not result.data:
            return jsonify({'error': 'Consultation not found or invalid status'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Consultation started successfully'
        })
    
    except Exception as e:
        print(f"Start consultation error: {e}")
        return jsonify({'error': 'Failed to start consultation'}), 500


@api_bp.route('/ca/complete-consultation', methods=['POST'])
@login_required
def complete_consultation():
    """Update consultation status from in_progress to completed."""
    if not check_ca_access():
        return jsonify({'error': 'CA access required'}), 403
    
    try:
        data = request.get_json()
        consultation_id = data.get('consultation_id')
        
        if not consultation_id:
            return jsonify({'error': 'Consultation ID required'}), 400
        
        sb = get_supabase()
        ca_id = session.get('user_id')
        
        # Verify ownership and update status
        result = sb.table('consultations').update({
            'status': 'completed',
            'completed_at': 'now()'
        }).eq('id', consultation_id).eq('ca_id', ca_id).eq('status', 'in_progress').execute()
        
        if not result.data:
            return jsonify({'error': 'Consultation not found or invalid status'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Consultation completed successfully'
        })
    
    except Exception as e:
        print(f"Complete consultation error: {e}")
        return jsonify({'error': 'Failed to complete consultation'}), 500


@api_bp.route('/ca/transactions', methods=['GET'])
@login_required
def get_ca_transactions():
    """Get all transactions for CA (earnings + withdrawals)."""
    if not check_ca_access():
        return jsonify({'error': 'CA access required'}), 403
    
    try:
        sb = get_supabase()
        ca_id = session.get('user_id')
        
        # Fetch all earnings transactions for this CA
        result = sb.table('ca_earnings').select('*').eq(
            'ca_id', ca_id
        ).order('created_at', desc=True).execute()
        
        return jsonify(result.data if result.data else [])
    
    except Exception as e:
        print(f"Get transactions error: {e}")
        return jsonify([])


@api_bp.route('/ca/request-withdrawal', methods=['POST'])
@login_required
def request_withdrawal():
    """Submit a withdrawal request for CA earnings."""
    if not check_ca_access():
        return jsonify({'error': 'CA access required'}), 403
    
    try:
        data = request.get_json()
        amount = data.get('amount')
        bank_account = data.get('bank_account')
        note = data.get('note', '')
        
        if not amount or amount < 500:
            return jsonify({'error': 'Minimum withdrawal amount is ₹500'}), 400
        
        sb = get_supabase()
        ca_id = session.get('user_id')
        
        # Check available balance
        balance_response = sb.table('ca_earnings').select('amount, transaction_type').eq(
            'ca_id', ca_id
        ).eq('status', 'completed').execute()
        
        total_earned = sum(t['amount'] for t in balance_response.data if t['transaction_type'] == 'credit')
        total_withdrawn = sum(t['amount'] for t in balance_response.data if t['transaction_type'] == 'debit')
        available = total_earned - total_withdrawn
        
        if amount > available:
            return jsonify({'error': f'Insufficient balance. Available: ₹{available}'}), 400
        
        # Create withdrawal record
        withdrawal_data = {
            'ca_id': ca_id,
            'amount': amount,
            'transaction_type': 'debit',
            'status': 'pending',
            'description': f'Withdrawal request - {note}' if note else 'Withdrawal request',
            'bank_account_details': bank_account,
            'created_at': 'now()'
        }
        
        result = sb.table('ca_earnings').insert(withdrawal_data).execute()
        
        return jsonify({
            'success': True,
            'message': 'Withdrawal request submitted for admin approval'
        })
    
    except Exception as e:
        print(f"Withdrawal request error: {e}")
        return jsonify({'error': 'Failed to submit withdrawal request'}), 500


@api_bp.route('/ca/documents', methods=['GET'])
@login_required
def get_ca_documents():
    """Get all documents uploaded by CA."""
    if not check_ca_access():
        return jsonify({'error': 'CA access required'}), 403
    
    try:
        sb = get_supabase()
        ca_id = session.get('user_id')
        
        result = sb.table('ca_documents').select('*').eq(
            'ca_id', ca_id
        ).order('created_at', desc=True).execute()
        
        return jsonify(result.data if result.data else [])
    
    except Exception as e:
        print(f"Get documents error: {e}")
        return jsonify([])


@api_bp.route('/ca/upload-document', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def upload_ca_document():
    """Upload a document to CA storage."""
    if not check_ca_access():
        return jsonify({'error': 'CA access required'}), 403
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Use security validation function
        is_valid, message = validate_file_upload(file)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Sanitize filename
        safe_filename = sanitize_input(file.filename)
        
        file_content = file.read()
        
        sb = get_supabase()
        ca_id = session.get('user_id')
        
        # Create document record (file storage would be added here in production)
        doc_data = {
            'ca_id': ca_id,
            'file_name': safe_filename,
            'file_type': file.content_type,
            'file_size': len(file_content),
            'storage_path': f'ca-documents/{ca_id}/{safe_filename}',
            'created_at': 'now()'
        }
        
        result = sb.table('ca_documents').insert(doc_data).execute()
        
        return jsonify({
            'success': True,
            'message': 'Document uploaded successfully'
        })
    
    except Exception as e:
        print(f"Upload document error: {e}")
        return jsonify({'error': 'Failed to upload document'}), 500


@api_bp.route('/ca/download-document/<doc_id>', methods=['GET'])
@login_required
def download_ca_document(doc_id):
    """Download a document."""
    if not check_ca_access():
        return jsonify({'error': 'CA access required'}), 403
    
    try:
        # In production, retrieve file from Supabase Storage
        # For now, return placeholder response
        return jsonify({'error': 'Document download not implemented'}), 501
    
    except Exception as e:
        print(f"Download document error: {e}")
        return jsonify({'error': 'Failed to download document'}), 500


@api_bp.route('/ca/delete-document/<doc_id>', methods=['DELETE'])
@login_required
def delete_ca_document(doc_id):
    """Delete a document."""
    if not check_ca_access():
        return jsonify({'error': 'CA access required'}), 403
    
    try:
        sb = get_supabase()
        ca_id = session.get('user_id')
        
        # Delete document record (and file from storage in production)
        result = sb.table('ca_documents').delete().eq(
            'id', doc_id
        ).eq('ca_id', ca_id).execute()
        
        if not result.data:
            return jsonify({'error': 'Document not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Document deleted successfully'
        })
    
    except Exception as e:
        print(f"Delete document error: {e}")
        return jsonify({'error': 'Failed to delete document'}), 500


@api_bp.route('/ca/conversations', methods=['GET'])
@login_required
def get_ca_conversations():
    """Get all conversations (consultations with messages)."""
    if not check_ca_access():
        return jsonify({'error': 'CA access required'}), 403
    
    try:
        sb = get_supabase()
        ca_id = session.get('user_id')
        
        # Get consultations with client profiles
        result = sb.table('consultations').select(
            '*, profiles!consultations_user_id_fkey(full_name, avatar_url)'
        ).eq('ca_id', ca_id).order('created_at', desc=True).execute()
        
        conversations = []
        for item in result.data:
            conv = {
                'consultation_id': item['id'],
                'client_name': item['profiles']['full_name'] if item.get('profiles') else 'Unknown',
                'client_avatar': item['profiles']['avatar_url'] if item.get('profiles') else None,
                'last_message': None,
                'last_message_at': item['created_at'],
                'unread_count': 0,
                'created_at': item['created_at']
            }
            conversations.append(conv)
        
        return jsonify(conversations)
    
    except Exception as e:
        print(f"Get conversations error: {e}")
        return jsonify([])


@api_bp.route('/ca/messages/<consultation_id>', methods=['GET'])
@login_required
def get_consultation_messages(consultation_id):
    """Get all messages for a consultation."""
    if not check_ca_access():
        return jsonify({'error': 'CA access required'}), 403
    
    try:
        sb = get_supabase()
        
        result = sb.table('consultation_messages').select('*').eq(
            'consultation_id', consultation_id
        ).order('created_at', desc=False).execute()
        
        return jsonify(result.data if result.data else [])
    
    except Exception as e:
        print(f"Get messages error: {e}")
        return jsonify([])


@api_bp.route('/ca/send-message', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def send_ca_message():
    """Send a message in a consultation."""
    if not check_ca_access():
        return jsonify({'error': 'CA access required'}), 403
    
    try:
        data = request.get_json()
        consultation_id = data.get('consultation_id')
        message_text = data.get('message_text')
        
        if not consultation_id or not message_text:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Sanitize message text
        safe_message = sanitize_input(message_text)
        
        # Validate message length
        if len(safe_message) > 5000:
            return jsonify({'error': 'Message too long (max 5000 characters)'}), 400
        
        sb = get_supabase()
        ca_id = session.get('user_id')
        
        # Insert message
        msg_data = {
            'consultation_id': consultation_id,
            'sender_id': ca_id,
            'sender_type': 'ca',
            'message_text': safe_message,
            'created_at': 'now()'
        }
        
        result = sb.table('consultation_messages').insert(msg_data).execute()
        
        return jsonify({
            'success': True,
            'message': 'Message sent successfully'
        })
    
    except Exception as e:
        print(f"Send message error: {e}")
        return jsonify({'error': 'Failed to send message'}), 500


@api_bp.route('/admin/ca/actions/<ca_id>', methods=['GET'])
@login_required
def admin_get_ca_actions(ca_id):
    """Get audit trail for a specific CA."""
    if not check_admin_access():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        sb = get_supabase()
        
        # Get all admin actions for this CA
        actions_response = sb.table('ca_admin_actions').select('''
            *,
            admin:admin_id(full_name, email)
        ''').eq('ca_id', ca_id).order('created_at', desc=True).execute()
        
        actions = actions_response.data if actions_response.data else []
        
        return jsonify({
            'success': True,
            'data': actions
        })
    
    except Exception as e:
        print(f"Get CA actions error: {e}")
        return jsonify({'error': 'Failed to fetch actions'}), 500


# =====================================================
# END ADMIN CONTROL ENDPOINTS
# =====================================================


@api_bp.route('/ca/update-profile', methods=['POST'])
@login_required
def update_ca_profile():
    """Update CA profile information."""
    if not check_ca_access():
        return jsonify({'error': 'Access denied'}), 403

    try: 
        data = request.get_json()

        # Update user fields in Supabase
        updates = {}
        if 'first_name' in data:
            updates['first_name'] = data['first_name'].strip().title()
        if 'last_name' in data:
            updates['last_name'] = data['last_name'].strip().title()

        if updates:
            UserService.update(current_user.id, updates)

        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        })
    except Exception as e:
        print(f"CA profile update error: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500


@api_bp.route('/ca/client-requests', methods=['GET'])
@login_required
def get_client_requests():
    """Get client requests for CA - REAL-TIME from Supabase."""
    if not check_ca_access():
        return jsonify({'error': 'Access denied'}), 403

    try:
        sb = get_supabase()
        ca_id = current_user.id
        
        # Get all pending consultations for this CA
        consultations_response = sb.table('consultations').select('''
            id,
            client_id,
            service_type,
            title,
            description,
            budget_min,
            budget_max,
            currency,
            status,
            created_at
        ''').eq('ca_id', ca_id).eq('status', 'pending').order('created_at', desc=True).execute()
        
        requests_data = []
        if consultations_response.data:
            # Get client profiles
            client_ids = [c['client_id'] for c in consultations_response.data]
            if client_ids:
                profiles_response = sb.table('profiles').select('id, full_name, city').in_('id', client_ids).execute()
                profiles_map = {p['id']: p for p in profiles_response.data} if profiles_response.data else {}
                
                for consultation in consultations_response.data:
                    client = profiles_map.get(consultation['client_id'], {})
                    
                    # Format budget
                    budget = f"₹{consultation['budget_min']:,} - ₹{consultation['budget_max']:,}" if consultation.get('budget_min') and consultation.get('budget_max') else "Negotiable"
                    
                    # Determine urgency based on time since creation
                    from datetime import datetime, timedelta
                    created = datetime.fromisoformat(consultation['created_at'].replace('Z', '+00:00'))
                    hours_old = (datetime.now(created.tzinfo) - created).total_seconds() / 3600
                    urgency = 'high' if hours_old < 24 else 'medium' if hours_old < 72 else 'low'
                    
                    requests_data.append({
                        'id': consultation['id'],
                        'user_name': client.get('full_name', 'Unknown'),
                        'city': client.get('city', 'Not specified'),
                        'service': consultation['service_type'].replace('_', ' ').title(),
                        'budget': budget,
                        'urgency': urgency,
                        'description': consultation['description'],
                        'created_at': consultation['created_at']
                    })

        return jsonify({
            'success': True,
            'data': requests_data
        })
    
    except Exception as e:
        print(f"Client requests error: {e}")
        return jsonify({
            'success': True,
            'data': []
        })


@api_bp.route('/ca/accept-request', methods=['POST'])
@login_required
def accept_client_request():
    """Accept a client request - REAL-TIME with Supabase."""
    if not check_ca_access():
        return jsonify({'error': 'Access denied'}), 403

    try:
        sb = get_supabase()
        ca_id = current_user.id
        data = request.get_json()
        request_id = data.get('request_id')

        if not request_id:
            return jsonify({'error':  'Request ID is required'}), 400

        # Update consultation status to accepted
        update_response = sb.table('consultations').update({
            'status': 'accepted',
            'started_at': datetime.utcnow().isoformat()
        }).eq('id', request_id).eq('ca_id', ca_id).execute()
        
        if not update_response.data:
            return jsonify({'error': 'Failed to accept request'}), 500

        return jsonify({
            'success':  True,
            'message': 'Request accepted successfully'
        })
    except Exception as e: 
        print(f"Accept request error:  {e}")
        return jsonify({'error': 'Failed to accept request'}), 500


@api_bp.route('/ca/decline-request', methods=['POST'])
@login_required
def decline_client_request():
    """Decline a client request - REAL-TIME with Supabase."""
    if not check_ca_access():
        return jsonify({'error': 'Access denied'}), 403

    try:
        sb = get_supabase()
        ca_id = current_user.id
        data = request.get_json()
        request_id = data.get('request_id')
        reason = data. get('reason', '')

        if not request_id: 
            return jsonify({'error': 'Request ID is required'}), 400

        # Update consultation status to cancelled
        update_response = sb.table('consultations').update({
            'status': 'cancelled',
            'cancelled_at': datetime.utcnow().isoformat(),
            'cancelled_by': ca_id,
            'cancellation_reason': reason or 'Declined by CA'
        }).eq('id', request_id).eq('ca_id', ca_id).execute()
        
        if not update_response.data:
            return jsonify({'error': 'Failed to decline request'}), 500

        return jsonify({
            'success': True,
            'message': 'Request declined'
        })
    except Exception as e: 
        print(f"Decline request error: {e}")
        return jsonify({'error': 'Failed to decline request'}), 500


@api_bp.route('/ca/dashboard-stats', methods=['GET'])
@login_required
def ca_dashboard_stats():
    """Get CA dashboard statistics - REAL-TIME from Supabase."""
    if not check_ca_access():
        return jsonify({'error': 'Access denied'}), 403

    try:
        sb = get_supabase()
        ca_id = current_user.id
        
        # Get total unique clients
        clients_response = sb.table('consultations').select('client_id', count='exact').eq('ca_id', ca_id).execute()
        unique_clients = set()
        if clients_response.data:
            unique_clients = {c['client_id'] for c in clients_response.data}
        total_clients = len(unique_clients)
        
        # Get active consultations count (in_progress + accepted)
        active_response = sb.table('consultations').select('id', count='exact').eq('ca_id', ca_id).in_('status', ['accepted', 'in_progress']).execute()
        active_consultations = active_response.count if hasattr(active_response, 'count') else 0
        
        # Get pending requests
        pending_response = sb.table('consultations').select('id', count='exact').eq('ca_id', ca_id).eq('status', 'pending').execute()
        pending_requests = pending_response.count if hasattr(pending_response, 'count') else 0
        
        # Get total earnings (all completed credits)
        earnings_response = sb.table('ca_earnings').select('amount').eq('ca_id', ca_id).eq('transaction_type', 'credit').eq('status', 'completed').execute()
        total_earnings = sum(e['amount'] for e in earnings_response.data) if earnings_response.data else 0
        
        # Get this month's earnings
        from datetime import datetime, timedelta
        first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month_response = sb.table('ca_earnings').select('amount').eq('ca_id', ca_id).eq('transaction_type', 'credit').gte('created_at', first_day_of_month.isoformat()).execute()
        this_month_earnings = sum(e['amount'] for e in this_month_response.data) if this_month_response.data else 0
        
        # Get average rating
        reviews_response = sb.table('ca_reviews').select('rating').eq('ca_id', ca_id).eq('is_published', True).execute()
        if reviews_response.data:
            average_rating = round(sum(r['rating'] for r in reviews_response.data) / len(reviews_response.data), 1)
            total_reviews = len(reviews_response.data)
        else:
            average_rating = 0.0
            total_reviews = 0
        
        # Calculate response rate (consultations responded to within 24 hours)
        all_consultations = sb.table('consultations').select('id, created_at, updated_at, status').eq('ca_id', ca_id).execute()
        responded = 0
        total_requests = 0
        if all_consultations.data:
            for c in all_consultations.data:
                if c['status'] != 'pending':
                    total_requests += 1
                    created = datetime.fromisoformat(c['created_at'].replace('Z', '+00:00'))
                    updated = datetime.fromisoformat(c['updated_at'].replace('Z', '+00:00'))
                    if (updated - created) <= timedelta(hours=24):
                        responded += 1
        response_rate = round((responded / total_requests * 100)) if total_requests > 0 else 100
        
        # Calculate completion rate
        completed_response = sb.table('consultations').select('id', count='exact').eq('ca_id', ca_id).eq('status', 'completed').execute()
        completed = completed_response.count if hasattr(completed_response, 'count') else 0
        total_accepted = sb.table('consultations').select('id', count='exact').eq('ca_id', ca_id).neq('status', 'pending').execute()
        total = total_accepted.count if hasattr(total_accepted, 'count') else 0
        completion_rate = round((completed / total * 100)) if total > 0 else 100

        stats = {
            'total_clients': total_clients,
            'active_consultations': active_consultations,
            'pending_requests': pending_requests,
            'total_earnings': total_earnings,
            'this_month_earnings': this_month_earnings,
            'average_rating': average_rating,
            'total_reviews': total_reviews,
            'response_rate': response_rate,
            'completion_rate': completion_rate
        }

        return jsonify({'success': True, 'data': stats})
    
    except Exception as e:
        print(f"CA dashboard stats error: {e}")
        # Return zeros instead of mock data on error
        return jsonify({
            'success': True,
            'data': {
                'total_clients': 0,
                'active_consultations': 0,
                'pending_requests': 0,
                'total_earnings': 0,
                'this_month_earnings': 0,
                'average_rating': 0.0,
                'total_reviews': 0,
                'response_rate': 0,
                'completion_rate': 0
            }
        })


@api_bp.route('/ca/earnings-summary', methods=['GET'])
@login_required
def ca_earnings_summary():
    """Get CA earnings summary - REAL-TIME from Supabase."""
    if not check_ca_access():
        return jsonify({'error': 'Access denied'}), 403

    try:
        sb = get_supabase()
        ca_id = current_user.id
        
        # Get all completed credits
        credits_response = sb.table('ca_earnings').select('amount').eq('ca_id', ca_id).eq('transaction_type', 'credit').eq('status', 'completed').execute()
        total_earned = sum(e['amount'] for e in credits_response.data) if credits_response.data else 0
        
        # Get all completed withdrawals
        withdrawals_response = sb.table('ca_earnings').select('amount').eq('ca_id', ca_id).eq('transaction_type', 'debit').eq('status', 'completed').execute()
        total_withdrawn = sum(e['amount'] for e in withdrawals_response.data) if withdrawals_response.data else 0
        
        # Get pending amounts (approved but not completed)
        pending_response = sb.table('ca_earnings').select('amount').eq('ca_id', ca_id).eq('transaction_type', 'credit').eq('status', 'approved').execute()
        pending_amount = sum(e['amount'] for e in pending_response.data) if pending_response.data else 0
        
        # Calculate available balance
        available_balance = total_earned - total_withdrawn - pending_amount
        
        # Get recent transactions (last 10)
        transactions_response = sb.table('ca_earnings').select('*').eq('ca_id', ca_id).order('created_at', desc=True).limit(10).execute()
        
        transactions = []
        if transactions_response.data:
            for t in transactions_response.data:
                transactions.append({
                    'id': t['id'],
                    'type': t['transaction_type'],
                    'amount': t['amount'],
                    'description': t['title'],
                    'status': t['status'],
                    'date': t['created_at']
                })
        
        summary = {
            'available_balance': available_balance,
            'pending_amount': pending_amount,
            'total_earned': total_earned,
            'total_withdrawn': total_withdrawn,
            'transactions': transactions
        }

        return jsonify({'success': True, 'data': summary})
    
    except Exception as e:
        print(f"CA earnings summary error: {e}")
        return jsonify({
            'success': True,
            'data': {
                'available_balance': 0,
                'pending_amount': 0,
                'total_earned': 0,
                'total_withdrawn': 0,
                'transactions': []
            }
        })


@api_bp.route('/user/dashboard-stats', methods=['GET'])
@login_required
def user_dashboard_stats():
    """Get user dashboard statistics - REAL-TIME from Supabase."""
    try:
        sb = get_supabase()
        user_id = current_user.id
        
        # Get total queries count for this user
        queries_response = sb.table('chat_queries').select('id', count='exact').eq('user_id', user_id).execute()
        total_queries = queries_response.count if hasattr(queries_response, 'count') else 0
        
        # Get helpful responses count
        helpful_response = sb.table('chat_queries').select('id', count='exact').eq('user_id', user_id).eq('is_helpful', True).execute()
        helpful_count = helpful_response.count if hasattr(helpful_response, 'count') else 0
        
        # Calculate accuracy rate
        accuracy_rate = round((helpful_count / total_queries * 100), 1) if total_queries > 0 else 0
        
        stats = {
            'total_queries': total_queries,
            'helpful_responses': helpful_count,
            'accuracy_rate': accuracy_rate,
            'active_consultations': 0,  # Will be implemented when consultations table exists
            'documents_count': 0,  # Will be implemented when documents table exists
            'last_updated': datetime.utcnow().isoformat()
        }

        return jsonify({'success': True, 'data': stats})
        
    except Exception as e:
        print(f"User dashboard stats error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Failed to fetch dashboard stats',
            'data': {
                'total_queries': 0,
                'helpful_responses': 0,
                'accuracy_rate': 0,
                'active_consultations': 0,
                'documents_count': 0
            }
        }), 500


@api_bp.route('/user/recent-queries', methods=['GET'])
@login_required
def get_user_recent_queries():
    """Get user's recent AI queries - REAL-TIME from Supabase."""
    try:
        limit = request.args.get('limit', 10, type=int)
        sb = get_supabase()
        user_id = current_user.id
        
        # Get recent queries from chat_queries table
        response = sb.table('chat_queries').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
        
        queries = response.data if response.data else []
        
        return jsonify({'success': True, 'data': queries})
        
    except Exception as e:
        print(f"Recent queries error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Failed to fetch recent queries', 'data': []}), 500


@api_bp.route('/user/consultations', methods=['GET'])
@login_required
def get_user_consultations():
    """Get user's consultations."""
    # Mock data
    consultations = [
        {
            'id': '1',
            'ca_name': 'CA Rajesh Sharma',
            'ca_id': 1,
            'service': 'GST Compliance',
            'status': 'in_progress',
            'created_at':  datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat()
        },
        {
            'id': '2',
            'ca_name': 'CA Priya Mehta',
            'ca_id':  2,
            'service': 'Tax Planning FY 2024-25',
            'status': 'waiting',
            'created_at': datetime.utcnow().isoformat(),
            'last_activity':  datetime.utcnow().isoformat()
        }
    ]

    return jsonify({'success':  True, 'data': consultations})


@api_bp.route('/user/request-consultation', methods=['POST'])
@login_required
def create_consultation_request():
    """Create a new consultation request."""
    try:
        data = request.get_json()
        ca_id = data.get('ca_id')
        service_type = data.get('service_type')
        description = data.get('description')
        budget = data.get('budget')
        urgency = data.get('urgency', 'normal')

        if not all([ca_id, service_type, description]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Create consultation request in database
        request_id = str(uuid.uuid4())

        return jsonify({
            'success': True,
            'message': 'Consultation request sent successfully',
            'request_id': request_id
        })
    except Exception as e: 
        print(f"Create consultation error: {e}")
        return jsonify({'error': 'Failed to create consultation request'}), 500


@api_bp.route('/search/cas', methods=['GET'])
@login_required
def search_cas():
    """Search for CAs with filters - REAL-TIME from Supabase."""
    location = request.args.get('location', '')
    service = request.args.get('service', '')
    experience = request.args.get('experience', '')
    sort_by = request.args.get('sort', 'recommended')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    try:
        sb = get_supabase()
        
        # Query real CAs from profiles table
        query = sb.table('profiles').select('*').eq('role', 'ca')
        
        # Apply filters if provided
        if location:
            query = query.ilike('city', f'%{location}%')
        
        # Execute query
        response = query.order('created_at', desc=True).execute()
        
        ca_profiles = response.data if response.data else []
        
        # Format CA data for response
        cas = []
        for profile in ca_profiles:
            ca_data = {
                'id': profile.get('id'),
                'name': f"CA {profile.get('first_name', '')} {profile.get('last_name', '')}".strip(),
                'location': f"{profile.get('city', 'India')}, {profile.get('state', '')}",
                'experience': profile.get('experience_years', 0),
                'rating': 4.5,  # Default rating until reviews system is implemented
                'reviews_count': 0,
                'clients_count': 0,
                'services': profile.get('services', []) if profile.get('services') else ['Tax Planning', 'GST Compliance'],
                'verified': True,
                'email': profile.get('email'),
                'phone': profile.get('phone'),
                'icai_number': profile.get('icai_number')
            }
            cas.append(ca_data)
        
        # Pagination
        total = len(cas)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_cas = cas[start:end]
        
        return jsonify({
            'success': True,
            'data': paginated_cas,
            'total': total,
            'page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        print(f"CA search error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Failed to fetch CAs',
            'data': [],
            'total': 0
        }), 500


@api_bp.route('/documents/upload', methods=['POST'])
@login_required
def upload_document():
    """Upload a document."""
    try: 
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        category = request.form.get('category', 'other')
        share_with = request. form.get('share_with', '')

        if file.filename == '': 
            return jsonify({'error': 'No file selected'}), 400

        # Handle file upload logic here
        document_id = str(uuid.uuid4())

        return jsonify({
            'success':  True,
            'message': 'Document uploaded successfully',
            'document_id':  document_id
        })
    except Exception as e: 
        print(f"Document upload error: {e}")
        return jsonify({'error': 'Failed to upload document'}), 500


@api_bp. route('/documents', methods=['GET'])
@login_required
def get_documents():
    """Get user's documents."""
    category = request.args. get('category', '')

    # Mock documents
    documents = [
        {
            'id': '1',
            'name':  'Form 16 - FY 2023-24.pdf',
            'category': 'Tax Documents',
            'size': '1.2 MB',
            'uploaded_at': datetime. utcnow().isoformat(),
            'shared_with': ['RS', 'PM']
        },
        {
            'id': '2',
            'name': 'GSTR-1 November 2024.pdf',
            'category': 'GST Files',
            'size': '856 KB',
            'uploaded_at':  datetime.utcnow().isoformat(),
            'shared_with': ['RS']
        }
    ]

    return jsonify({'success': True, 'data': documents})


@api_bp.route('/messages', methods=['GET'])
@login_required
def get_messages():
    """Get user's messages/conversations."""
    # Mock conversations
    conversations = [
        {
            'id': '1',
            'with_user': 'CA Rajesh Sharma',
            'with_user_id': 1,
            'last_message': "I've reviewed your GST documents. Everything looks good.. .",
            'last_message_time': datetime.utcnow().isoformat(),
            'unread_count':  2,
            'online':  True
        },
        {
            'id': '2',
            'with_user': 'CA Priya Mehta',
            'with_user_id': 2,
            'last_message': 'Thank you for sharing the Form 16. I\'ll prepare.. .',
            'last_message_time':  datetime.utcnow().isoformat(),
            'unread_count': 1,
            'online': False
        }
    ]

    return jsonify({'success': True, 'data':  conversations})


@api_bp.route('/messages/<conversation_id>', methods=['GET'])
@login_required
def get_conversation_messages(conversation_id):
    """Get messages in a conversation."""
    # Mock messages
    messages = [
        {
            'id': '1',
            'sender': 'ca',
            'text': 'Good morning! I\'ve received all your GST documents for November filing.',
            'time': datetime.utcnow().isoformat()
        },
        {
            'id': '2',
            'sender': 'user',
            'text': 'That\'s great to hear! When do you expect to complete the filing?',
            'time': datetime.utcnow().isoformat()
        }
    ]

    return jsonify({'success': True, 'data':  messages})


@api_bp.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    """Send a message."""
    try:
        data = request.get_json()
        conversation_id = data. get('conversation_id')
        recipient_id = data. get('recipient_id')
        message_text = data.get('message')

        if not message_text:
            return jsonify({'error': 'Message cannot be empty'}), 400

        message_id = str(uuid.uuid4())

        return jsonify({
            'success': True,
            'message_id': message_id
        })
    except Exception as e: 
        print(f"Send message error: {e}")
        return jsonify({'error': 'Failed to send message'}), 500


@api_bp. route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Get user's notifications."""
    # Mock notifications
    notifications = [
        {
            'id': '1',
            'type':  'reminder',
            'title': 'Tax Filing Reminder',
            'message': 'ITR filing deadline is approaching. Consider filing early.',
            'time': datetime.utcnow().isoformat(),
            'read': False
        },
        {
            'id': '2',
            'type': 'message',
            'title': 'New message from CA Sharma',
            'message': 'Your documents have been reviewed.. .',
            'time': datetime.utcnow().isoformat(),
            'read': False
        }
    ]

    return jsonify({'success': True, 'data': notifications})


@api_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    """Mark notifications as read."""
    try:
        data = request.get_json()
        notification_ids = data.get('notification_ids', [])
        mark_all = data.get('mark_all', False)

        # Handle marking logic

        return jsonify({'success': True, 'message': 'Notifications marked as read'})
    except Exception as e: 
        print(f"Mark notifications error: {e}")
        return jsonify({'error': 'Failed to mark notifications'}), 500


@api_bp.route('/feedback', methods=['POST'])
@login_required
def api_feedback():
    """Handle user feedback on responses."""
    try:
        data = request.get_json()
        query_id = data.get('query_id')
        is_helpful = data.get('is_helpful')
        feedback_text = data.get('feedback_text', '')
        rating = data.get('rating')

        if not query_id: 
            return jsonify({'success': False, 'error': 'Query ID is required.'}), 400

        # Submit feedback to Supabase
        feedback_data = {
            'user_id': current_user.id,
            'query_id': query_id,
            'rating': rating,
            'is_helpful': is_helpful,
            'feedback_text': feedback_text
        }
        
        saved = FeedbackService.create_feedback(**feedback_data)
        if not saved:
            return jsonify({'success': False, 'error': 'Failed to save feedback'}), 500

        return jsonify({'success': True, 'message': 'Thank you for your feedback!'})

    except Exception as e:
        print(f"Feedback API error: {e}")
        return jsonify({'success': False, 'error': 'Failed to submit feedback'}), 500


@api_bp.route('/review/submit', methods=['POST'])
@login_required
def submit_review():
    """Submit a review for a CA."""
    try:
        data = request.get_json()
        ca_id = data. get('ca_id')
        consultation_id = data. get('consultation_id')
        rating = data.get('rating')
        review_text = data. get('review_text', '')

        if not all([ca_id, consultation_id, rating]):
            return jsonify({'error': 'Missing required fields'}), 400

        if rating < 1 or rating > 5:
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400

        review_id = str(uuid.uuid4())

        return jsonify({
            'success': True,
            'message': 'Review submitted successfully',
            'review_id': review_id
        })
    except Exception as e:
        print(f"Submit review error: {e}")
        return jsonify({'error': 'Failed to submit review'}), 500


@api_bp.route('/newsletter-signup', methods=['POST'])
def newsletter_signup():
    """Newsletter signup endpoint."""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()

        if not email: 
            return jsonify({'success': False, 'error': 'Email is required. '}), 400
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({'success':  False, 'error': 'Valid email is required.'}), 400

        return jsonify({'success': True, 'message': 'Thank you for subscribing to our newsletter!'})

    except Exception as e:
        print(f"Newsletter signup error: {e}")
        return jsonify({'success': False, 'error': 'Failed to process subscription'}), 500


@api_bp. route('/contact-form', methods=['POST'])
def contact_form():
    """Handle contact form submission."""
    try: 
        data = request. get_json()
        name = data. get('name', '').strip()
        email = data. get('email', '').strip().lower()
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()

        if not all([name, email, message]):
            return jsonify({'success': False, 'error':  'Name, email, and message are required.'}), 400

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({'success': False, 'error': 'Valid email is required. '}), 400

        # Handle contact form logic (e.g., send email, store in database)
        print(f"Contact form received: {name}, {email}, {subject}")

        return jsonify({'success': True, 'message': 'Thank you for contacting us!  We will get back to you soon.'})
    except Exception as e:
        print(f"Contact form error: {e}")
        return jsonify({'success': False, 'error': 'Failed to submit contact form'}), 500


@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get platform statistics - REAL-TIME from Supabase."""
    try:
        sb = get_supabase()
        
        # Get real counts from Supabase
        # Total users count
        users_response = sb.table('profiles').select('id', count='exact').execute()
        total_users = users_response.count if hasattr(users_response, 'count') else 0
        
        # Total queries/questions answered
        queries_response = sb.table('chat_queries').select('id', count='exact').execute()
        total_queries = queries_response.count if hasattr(queries_response, 'count') else 0
        
        # Total CAs count
        cas_response = sb.table('profiles').select('id', count='exact').eq('role', 'ca').execute()
        total_cas = cas_response.count if hasattr(cas_response, 'count') else 0
        
        # Calculate accuracy rate from feedback
        # Get queries with helpful feedback
        helpful_response = sb.table('chat_queries').select('id', count='exact').eq('is_helpful', True).execute()
        helpful_count = helpful_response.count if hasattr(helpful_response, 'count') else 0
        
        # Get queries with ratings
        rated_response = sb.table('chat_queries').select('id', count='exact').not_.is_('rating', 'null').execute()
        rated_count = rated_response.count if hasattr(rated_response, 'count') else 0
        
        # Calculate accuracy (percentage of helpful responses)
        accuracy = round((helpful_count / rated_count * 100), 1) if rated_count > 0 else 95.0
        
        # Calculate satisfaction from average rating
        ratings_response = sb.table('chat_queries').select('rating').not_.is_('rating', 'null').execute()
        if ratings_response.data and len(ratings_response.data) > 0:
            ratings = [r['rating'] for r in ratings_response.data if r.get('rating')]
            avg_rating = sum(ratings) / len(ratings) if ratings else 4.5
            satisfaction = round((avg_rating / 5.0 * 100), 1)
        else:
            satisfaction = 90.0
        
        # Get popular topics from actual queries (group by category)
        topics_response = sb.table('chat_queries').select('category').execute()
        popular_topics = []
        
        if topics_response.data:
            from collections import Counter
            category_counts = Counter([q.get('category', 'general') for q in topics_response.data])
            
            # Map categories to display info
            category_map = {
                'tax': {'topic': 'Tax Planning', 'icon': 'fa-calculator'},
                'investment': {'topic': 'Investment', 'icon': 'fa-chart-line'},
                'gst': {'topic': 'GST', 'icon': 'fa-file-invoice'},
                'retirement': {'topic': 'Retirement', 'icon': 'fa-umbrella-beach'},
                'general': {'topic': 'General Finance', 'icon': 'fa-coins'}
            }
            
            for category, count in category_counts.most_common(4):
                cat_info = category_map.get(category, {'topic': category.title(), 'icon': 'fa-question'})
                popular_topics.append({
                    'topic': cat_info['topic'],
                    'count': count,
                    'icon': cat_info['icon']
                })
        
        # If no topics yet, show placeholder
        if not popular_topics:
            popular_topics = [
                {'topic': 'Tax Planning', 'count': 0, 'icon': 'fa-calculator'},
                {'topic': 'Investment', 'count': 0, 'icon': 'fa-chart-line'},
                {'topic': 'GST', 'count': 0, 'icon': 'fa-file-invoice'},
                {'topic': 'General Finance', 'count': 0, 'icon': 'fa-coins'}
            ]
        
        stats = {
            'users': total_users,
            'queries': total_queries,
            'accuracy': accuracy,
            'satisfaction': satisfaction,
            'cas': total_cas,
            'consultations': total_queries,  # Using queries count as consultations
            'popular_topics': popular_topics,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify({'success': True, 'data': stats})
    except Exception as e: 
        print(f"Stats API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Failed to fetch statistics'}), 500


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Test Supabase connection
        sb = get_supabase()
        sb.table('profiles').select('id').limit(1).execute()
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': 'v2.0.0',
            'database': 'Supabase'
        })
    except Exception as e: 
        print(f"Health check failed: {e}")
        return jsonify({'success': False, 'status': 'unhealthy', 'error': str(e)}), 503


@api_bp.route('/ai/chat', methods=['POST'])
@login_required
def ai_chat():
    """AI Chat endpoint."""
    try:
        data = request.get_json()
        user_query = data.get('query', '').strip()
        conversation_id = data.get('conversation_id')

        if not user_query:
            return jsonify({'success': False, 'error': 'Query cannot be empty'}), 400

        # Get AI response
        if get_ai_response: 
            response = get_ai_response(user_query)
        else:
            response = "I'm sorry, the AI service is currently unavailable. Please try again later."

        # Store in Supabase
        try:
            chat_data = {
                'user_id': current_user.id,
                'question': user_query,
                'response': response,
                'category': 'general'
            }
            saved = ChatService.create_query(**chat_data)
            query_id = saved.get('id') if saved else None
        except Exception as e: 
            print(f"Failed to store chat query: {e}")
            query_id = None

        return jsonify({
            'success':  True,
            'response': response,
            'query_id': query_id
        })

    except Exception as e:
        print(f"AI chat error: {e}")
        return jsonify({'success': False, 'error': 'Failed to process your request'}), 500


@api_bp.route('/ai/suggestions', methods=['GET'])
@login_required
def ai_suggestions():
    """Get AI-powered suggestions for the user."""
    try:
        suggestions = [
            {
                'id': '1',
                'type': 'tax_saving',
                'title': 'Maximize Your 80C Deductions',
                'description': 'You may be eligible for additional deductions under Section 80C.',
                'priority': 'high'
            },
            {
                'id': '2',
                'type': 'deadline',
                'title': 'Advance Tax Due Date',
                'description': 'Third installment of advance tax is due by December 15th.',
                'priority': 'urgent'
            },
            {
                'id': '3',
                'type': 'tip',
                'title': 'Early ITR Filing Benefits',
                'description': 'Consider filing your ITR early for faster refund processing.',
                'priority': 'normal'
            }
        ]

        return jsonify({'success': True, 'data': suggestions})
    except Exception as e:
        print(f"AI suggestions error: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch suggestions'}), 500


# ==================== ERROR HANDLERS ====================

@main_bp. app_errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    try:
        return render_template('Errors/404.html'), 404
    except:
        return """
        <html>
            <head><title>404 - Page Not Found</title></head>
            <body style="font-family:  'Inter', Arial, sans-serif; text-align: center; padding: 60px; background:  #0a0d0a; color: #f0f2f0;">
                <div style="max-width: 500px; margin: 0 auto;">
                    <h1 style="color: #FBA002; font-size: 72px; margin-bottom: 10px;">404</h1>
                    <h2 style="margin-bottom: 20px;">Page Not Found</h2>
                    <p style="color: #9ca89c; margin-bottom: 30px;">The page you're looking for doesn't exist or has been moved.</p>
                    <a href="/" style="display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #FBA002, #e69200); color: #0a0c0a; text-decoration:  none; border-radius: 10px; font-weight: 600;">Go to Homepage</a>
                </div>
            </body>
        </html>
        """, 404


@main_bp. app_errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors."""
    try:
        return render_template('Errors/500.html'), 500
    except:
        return """
        <html>
            <head><title>500 - Server Error</title></head>
            <body style="font-family: 'Inter', Arial, sans-serif; text-align:  center; padding: 60px; background:  #0a0d0a; color:  #f0f2f0;">
                <div style="max-width: 500px; margin: 0 auto;">
                    <h1 style="color:  #FBA002; font-size: 72px; margin-bottom: 10px;">500</h1>
                    <h2 style="margin-bottom: 20px;">Internal Server Error</h2>
                    <p style="color: #9ca89c; margin-bottom: 30px;">Something went wrong on our end. Please try again later.</p>
                    <a href="/" style="display:  inline-block; padding: 14px 28px; background:  linear-gradient(135deg, #FBA002, #e69200); color: #0a0c0a; text-decoration: none; border-radius: 10px; font-weight:  600;">Go to Homepage</a>
                </div>
            </body>
        </html>
        """, 500


@main_bp.app_errorhandler(403)
def forbidden(e):
    """Handle 403 errors."""
    if request.is_json or request.headers.get('Accept') == 'application/json':
        return jsonify({
            'success': False,
            'error': 'Access forbidden',
            'message': 'You do not have permission to access this resource.'
        }), 403
    
    try:
        return render_template('Errors/403.html'), 403
    except:
        return """
        <html>
            <head><title>403 - Access Forbidden</title></head>
            <body style="font-family: 'Inter', Arial, sans-serif; text-align: center; padding:  60px; background: #0a0d0a; color: #f0f2f0;">
                <div style="max-width: 500px; margin:  0 auto;">
                    <h1 style="color: #FBA002; font-size:  72px; margin-bottom: 10px;">403</h1>
                    <h2 style="margin-bottom:  20px;">Access Forbidden</h2>
                    <p style="color:  #9ca89c; margin-bottom:  30px;">You do not have permission to access this resource.</p>
                    <a href="/" style="display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #FBA002, #e69200); color: #0a0c0a; text-decoration: none; border-radius:  10px; font-weight: 600;">Go to Homepage</a>
                </div>
            </body>
        </html>
        """, 403


@main_bp.app_errorhandler(429)
def rate_limit_exceeded(e):
    """Handle rate limit errors."""
    if request.is_json or request.headers. get('Accept') == 'application/json':
        return jsonify({
            'success': False,
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.'
        }), 429
    
    try:
        return render_template('Errors/429.html'), 429
    except:
        return """
        <html>
            <head><title>429 - Too Many Requests</title></head>
            <body style="font-family: 'Inter', Arial, sans-serif; text-align: center; padding: 60px; background: #0a0d0a; color: #f0f2f0;">
                <div style="max-width: 500px; margin: 0 auto;">
                    <h1 style="color: #FBA002; font-size: 72px; margin-bottom:  10px;">429</h1>
                    <h2 style="margin-bottom: 20px;">Too Many Requests</h2>
                    <p style="color: #9ca89c; margin-bottom: 30px;">You've made too many requests. Please wait a moment and try again.</p>
                    <a href="/" style="display:  inline-block; padding: 14px 28px; background:  linear-gradient(135deg, #FBA002, #e69200); color: #0a0c0a; text-decoration: none; border-radius: 10px; font-weight:  600;">Go to Homepage</a>
                </div>
            </body>
        </html>
        """, 429


@main_bp.app_errorhandler(401)
def unauthorized(e):
    """Handle 401 errors."""
    if request.is_json or request.headers.get('Accept') == 'application/json': 
        return jsonify({
            'success': False,
            'error': 'Unauthorized',
            'message': 'Please log in to access this resource.'
        }), 401
    
    flash('Please log in to access this page.', 'error')
    return redirect(url_for('auth.login'))


# ==================== TEMPLATE CONTEXT PROCESSORS ====================

@main_bp. context_processor
def inject_current_year():
    """Inject current year into all templates."""
    return {
        'current_year': datetime.now().year,
        'current_date': datetime. now().strftime('%B %d, %Y')
    }


@main_bp.context_processor
def inject_user_data():
    """Inject common user data into templates."""
    user_data = {
        'is_logged_in': current_user.is_authenticated,
        'has_notifications': False,
        'site_version': 'v2.0.0',
        'site_name': 'Finucity',
        'support_email': 'support@finucity.com',
        'is_ca':  False,
        'is_admin': False
    }
    if current_user.is_authenticated:
        user_data['has_notifications'] = True  # Check actual notifications
        user_data['user_initial'] = current_user. first_name[0].upper() if current_user.first_name else 'U'
        user_data['user_role'] = getattr(current_user, 'role', 'user') if hasattr(current_user, 'role') else 'user'
        user_data['is_ca'] = check_ca_access()
        user_data['is_admin'] = check_admin_access()
        user_data['user_full_name'] = f"{current_user. first_name or ''} {current_user.last_name or ''}".strip() or 'User'
    return {'user_data': user_data}


@main_bp.context_processor
def inject_navigation_data():
    """Inject navigation-related data."""
    return {
        'nav_items': {
            'services': [
                {'name': 'Tax Planning', 'endpoint': 'main.tax_planning', 'icon': 'fa-calculator', 'description': 'Strategic tax planning and optimization'},
                {'name': 'Investment Advisory', 'endpoint':  'main.investment_advisory', 'icon': 'fa-chart-line', 'description': 'Expert investment guidance'},
                {'name':  'GST Compliance', 'endpoint': 'main.gst_compliance', 'icon': 'fa-file-invoice', 'description': 'GST filing and compliance'},
                {'name': 'Business Finance', 'endpoint':  'main.business_finance', 'icon': 'fa-building', 'description':  'Business financial management'},
                {'name': 'Audit Services', 'endpoint':  'main.audit_services', 'icon': 'fa-search-dollar', 'description':  'Statutory and internal audits'},
                {'name': 'Startup Advisory', 'endpoint':  'main.startup_advisory', 'icon': 'fa-rocket', 'description': 'Startup compliance and advisory'},
            ],
            'resources': [
                {'name': 'Financial Blog', 'endpoint':  'main.financial_blog', 'icon': 'fa-book', 'description':  'Latest financial insights'},
                {'name':  'Learning Center', 'endpoint':  'main.learning_centre', 'icon':  'fa-graduation-cap', 'description': 'Financial education resources'},
                {'name': 'Tax Calculator', 'endpoint':  'main.tax_calculator', 'icon': 'fa-calculator', 'description': 'Calculate your taxes'},
                {'name': 'Retirement Planning', 'endpoint': 'main.retirement_planning', 'icon': 'fa-umbrella-beach', 'description': 'Plan for your future'},
                {'name': 'Investment Tools', 'endpoint':  'main.investment_tools', 'icon': 'fa-tools', 'description':  'Investment analysis tools'},
            ],
            'support': [
                {'name': 'Help Center', 'endpoint': 'main.help_center', 'icon':  'fa-question-circle'},
                {'name':  'Contact Us', 'endpoint':  'main.contact', 'icon': 'fa-envelope'},
                {'name':  'FAQ', 'endpoint':  'main.faq', 'icon': 'fa-comments'},
            ],
            'ca_menu': [
                {'name': 'Dashboard', 'endpoint':  'main.ca_dashboard', 'icon': 'fa-home'},
                {'name': 'My Profile', 'endpoint':  'main.ca_profile', 'icon': 'fa-user'},
                {'name': 'Client Requests', 'endpoint':  'main.ca_clients', 'icon':  'fa-folder-open'},
                {'name': 'Messages', 'endpoint':  'main.ca_messages', 'icon': 'fa-comments'},
                {'name': 'Documents', 'endpoint':  'main.ca_documents', 'icon': 'fa-file-alt'},
                {'name': 'Services', 'endpoint':  'main.ca_services', 'icon': 'fa-tags'},
                {'name': 'Insights', 'endpoint':  'main.ca_insights', 'icon': 'fa-chart-bar'},
                {'name': 'Earnings', 'endpoint':  'main.ca_earnings', 'icon': 'fa-rupee-sign'},
                {'name': 'Calendar', 'endpoint':  'main.ca_calendar', 'icon': 'fa-calendar'},
                {'name': 'Reviews', 'endpoint':  'main.ca_reviews', 'icon': 'fa-star'},
                {'name': 'Settings', 'endpoint': 'main.ca_settings', 'icon': 'fa-cog'},
            ],
            'user_menu': [
                {'name': 'Dashboard', 'endpoint':  'main.user_dashboard', 'icon': 'fa-home'},
                {'name': 'Find CA', 'endpoint':  'main.find_ca', 'icon': 'fa-user-tie'},
                {'name': 'My Consultations', 'endpoint': 'main.user_consultations', 'icon': 'fa-folder-open'},
                {'name': 'Messages', 'endpoint':  'main.user_messages', 'icon': 'fa-comments'},
                {'name': 'Documents', 'endpoint': 'main.user_documents', 'icon': 'fa-file-alt'},
                {'name': 'Recommendations', 'endpoint':  'main.user_recommendations', 'icon': 'fa-lightbulb'},
                {'name': 'Settings', 'endpoint': 'main.user_settings', 'icon': 'fa-cog'},
            ]
        }
    }


@main_bp.context_processor
def inject_supabase_env():
    """Inject Supabase environment variables."""
    return {
        'SUPABASE_URL': os.getenv('SUPABASE_URL', ''),
        'SUPABASE_ANON_KEY':  os.getenv('SUPABASE_ANON_KEY', '')
    }


# ==================== UTILITY FUNCTIONS ====================

def format_currency(amount):
    """Format amount as Indian currency."""
    try:
        if amount >= 10000000:  # 1 crore
            return f"₹{amount / 10000000:.2f} Cr"
        elif amount >= 100000:  # 1 lakh
            return f"₹{amount / 100000:.2f} L"
        else:
            return f"₹{amount: ,.2f}"
    except:
        return f"₹{amount}"


def format_date(date_obj):
    """Format date in a user-friendly way."""
    try:
        if isinstance(date_obj, str):
            date_obj = datetime.fromisoformat(date_obj. replace('Z', '+00:00'))
        return date_obj.strftime('%B %d, %Y')
    except:
        return str(date_obj)


def format_datetime(date_obj):
    """Format datetime in a user-friendly way."""
    try:
        if isinstance(date_obj, str):
            date_obj = datetime. fromisoformat(date_obj.replace('Z', '+00:00'))
        return date_obj. strftime('%B %d, %Y at %I:%M %p')
    except:
        return str(date_obj)


def time_ago(date_obj):
    """Get relative time string."""
    try:
        if isinstance(date_obj, str):
            date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))

        now = datetime. utcnow()
        diff = now - date_obj

        seconds = diff.total_seconds()

        if seconds < 60:
            return 'Just now'
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f'{minutes} minute{"s" if minutes > 1 else ""} ago'
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f'{hours} hour{"s" if hours > 1 else ""} ago'
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f'{days} day{"s" if days > 1 else ""} ago'
        elif seconds < 2592000:
            weeks = int(seconds / 604800)
            return f'{weeks} week{"s" if weeks > 1 else ""} ago'
        elif seconds < 31536000:
            months = int(seconds / 2592000)
            return f'{months} month{"s" if months > 1 else ""} ago'
        else:
            years = int(seconds / 31536000)
            return f'{years} year{"s" if years > 1 else ""} ago'
    except: 
        return str(date_obj)


def truncate_text(text, length=100, suffix='...'):
    """Truncate text to specified length."""
    if not text:
        return ''
    if len(text) <= length:
        return text
    return text[:length]. rsplit(' ', 1)[0] + suffix


def sanitize_filename(filename):
    """Sanitize a filename for safe storage."""
    import re
    # Remove any path components
    filename = os.path.basename(filename)
    # Remove any non-alphanumeric characters except for dots, dashes, and underscores
    filename = re.sub(r'[^\w\-\.]', '_', filename)
    return filename


# ==================== TEMPLATE FILTERS ====================

@main_bp.app_template_filter('currency')
def currency_filter(amount):
    """Template filter for currency formatting."""
    return format_currency(amount)


@main_bp.app_template_filter('date')
def date_filter(date_obj):
    """Template filter for date formatting."""
    return format_date(date_obj)


@main_bp.app_template_filter('datetime')
def datetime_filter(date_obj):
    """Template filter for datetime formatting."""
    return format_datetime(date_obj)


@main_bp.app_template_filter('time_ago')
def time_ago_filter(date_obj):
    """Template filter for relative time."""
    return time_ago(date_obj)


@main_bp.app_template_filter('truncate')
def truncate_filter(text, length=100):
    """Template filter for text truncation."""
    return truncate_text(text, length)


@main_bp.app_template_filter('initials')
def initials_filter(name):
    """Template filter to get initials from a name."""
    if not name:
        return 'U'
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    elif len(parts) == 1:
        return parts[0][0].upper()
    return 'U'


@main_bp.app_template_filter('file_size')
def file_size_filter(size_bytes):
    """Template filter for human-readable file sizes."""
    try: 
        size_bytes = int(size_bytes)
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:. 1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else: 
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    except:
        return str(size_bytes)


@main_bp.app_template_filter('phone_format')
def phone_format_filter(phone):
    """Template filter to format phone numbers."""
    if not phone:
        return ''
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, str(phone)))
    if len(digits) == 10:
        return f"+91 {digits[: 5]} {digits[5:]}"
    elif len(digits) == 12 and digits. startswith('91'):
        return f"+{digits[: 2]} {digits[2:7]} {digits[7:]}"
    return phone


# ==================== JINJA2 GLOBALS ====================

@main_bp.app_context_processor
def utility_processor():
    """Add utility functions to Jinja2 context."""
    def get_status_color(status):
        """Get color class for status."""
        status_colors = {
            'active': 'success',
            'in_progress': 'warning',
            'pending': 'warning',
            'waiting': 'info',
            'completed': 'success',
            'done': 'success',
            'cancelled': 'error',
            'rejected': 'error',
            'overdue': 'error'
        }
        return status_colors. get(status. lower() if status else '', 'muted')

    def get_priority_color(priority):
        """Get color class for priority."""
        priority_colors = {
            'urgent': 'error',
            'high': 'warning',
            'medium':  'info',
            'normal': 'muted',
            'low': 'success'
        }
        return priority_colors.get(priority. lower() if priority else '', 'muted')

    def get_file_icon(filename):
        """Get icon class for file type."""
        if not filename:
            return 'fa-file'
        
        ext = filename. rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        icons = {
            'pdf': 'fa-file-pdf',
            'doc':  'fa-file-word',
            'docx': 'fa-file-word',
            'xls': 'fa-file-excel',
            'xlsx':  'fa-file-excel',
            'csv': 'fa-file-csv',
            'ppt': 'fa-file-powerpoint',
            'pptx': 'fa-file-powerpoint',
            'jpg': 'fa-file-image',
            'jpeg': 'fa-file-image',
            'png': 'fa-file-image',
            'gif': 'fa-file-image',
            'zip': 'fa-file-archive',
            'rar': 'fa-file-archive',
            'txt': 'fa-file-alt',
            'mp4': 'fa-file-video',
            'mp3':  'fa-file-audio'
        }
        
        return icons. get(ext, 'fa-file')

    return dict(
        get_status_color=get_status_color,
        get_priority_color=get_priority_color,
        get_file_icon=get_file_icon
    )