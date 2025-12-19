"""
Centralized route handlers for the Finucity AI application. 
Author: Sumeet Sangwan
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, abort, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user
import uuid
import re
from datetime import datetime
import os
import jwt

from .  import db, limiter
from .models import User, ChatQuery, UserFeedback

try:
    from . ai import get_ai_response
except ImportError: 
    print("Warning: AI module not found. Some features may be limited.")
    get_ai_response = None

main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
api_bp = Blueprint('api', __name__, url_prefix='/api')


# ==================== HELPERS ====================

def decode_supabase_jwt(token:  str):
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
    first_name = claims. get("user_metadata", {}).get("full_name", "") or claims.get("name", "") or ""
    last_name = ""
    if first_name and " " in first_name:
        parts = first_name. split(" ", 1)
        first_name, last_name = parts[0], parts[1]
    if not email:
        raise ValueError("No email found in token")

    user = User.query.filter_by(email=email. lower()).first()
    if not user:
        base_username = email.split("@")[0]
        candidate = base_username
        i = 1
        while User.query. filter_by(username=candidate. lower()).first():
            i += 1
            candidate = f"{base_username}{i}"
        user = User(
            username=candidate. lower(),
            email=email. lower(),
            first_name=first_name. title() if first_name else "",
            last_name=last_name.title() if last_name else "",
        )
        if hasattr(user, 'role'):
            user.role = role
        try:
            random_pwd = uuid.uuid4().hex
            user.set_password(random_pwd)
        except Exception: 
            user.password_hash = uuid.uuid4().hex
        db.session.add(user)
        db.session.commit()
    else:
        updated = False
        if first_name and not user.first_name:
            user. first_name = first_name. title()
            updated = True
        if last_name and not user.last_name:
            user. last_name = last_name.title()
            updated = True
        if not getattr(user, "password_hash", None):
            try:
                user. set_password(uuid.uuid4().hex)
            except Exception:
                user.password_hash = uuid.uuid4().hex
            updated = True
        if updated:
            db. session.commit()
    return user


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
    """Displays the current user's profile page."""
    return render_template('profile.html', user=current_user)


@main_bp.route('/about', endpoint='about')
def about():
    """Renders the about page."""
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
        return render_template('contact. html')
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
            return render_template('bussiness_finance. html')
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
            return render_template('tax_calculator. html')
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
            return render_template('retirement_planning. html')
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
        return render_template('Resources/financial_glossary. html')
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
        queries = ChatQuery.query.filter_by(user_id=current_user.id).order_by(ChatQuery. created_at.desc()).limit(50).all()
        history = [{
            'id': q.id,
            'query': q. query,
            'response': q.response,
            'created_at': q. created_at.isoformat() if q.created_at else None
        } for q in queries]
        return jsonify({'success': True, 'data': history})
    except Exception as e: 
        print(f"Chat history error: {e}")
        return jsonify({'success': False, 'error':  'Failed to fetch chat history'}), 500


# ==================== CA DASHBOARD ROUTES ====================

@main_bp. route('/ca/dashboard', endpoint='ca_dashboard')
@login_required
def ca_dashboard():
    """CA Dashboard - Main workspace for Chartered Accountants."""
    if not check_ca_access():
        flash('Access denied.  This area is for verified CAs only.', 'error')
        return redirect(url_for('main.home'))

    return render_template(
        'ca/dashboard.html',
        user=current_user,
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.getenv('SUPABASE_ANON_KEY')
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
    """CA Client requests page."""
    if not check_ca_access():
        flash('Access denied.', 'error')
        return redirect(url_for('main. home'))

    return render_template(
        'ca/clients.html',
        user=current_user,
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.getenv('SUPABASE_ANON_KEY')
    )


@main_bp. route('/ca/messages', endpoint='ca_messages')
@login_required
def ca_messages():
    """CA Messages/Chat page."""
    if not check_ca_access():
        flash('Access denied.', 'error')
        return redirect(url_for('main.home'))

    return render_template(
        'ca/messages. html',
        user=current_user,
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.getenv('SUPABASE_ANON_KEY')
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
        SUPABASE_URL=os. getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os. getenv('SUPABASE_ANON_KEY')
    )


@main_bp.route('/ca/services', endpoint='ca_services')
@login_required
def ca_services():
    """CA Services offered page."""
    if not check_ca_access():
        flash('Access denied.', 'error')
        return redirect(url_for('main.home'))

    return render_template(
        'ca/services. html',
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
        return redirect(url_for('main. home'))

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
        'ca/settings. html',
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
        return redirect(url_for('main. home'))

    return render_template(
        'ca/earnings.html',
        user=current_user,
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.getenv('SUPABASE_ANON_KEY')
    )


@main_bp. route('/ca/calendar', endpoint='ca_calendar')
@login_required
def ca_calendar():
    """CA Calendar and appointments page."""
    if not check_ca_access():
        flash('Access denied.', 'error')
        return redirect(url_for('main. home'))

    return render_template(
        'ca/calendar.html',
        user=current_user,
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.getenv('SUPABASE_ANON_KEY')
    )


@main_bp. route('/ca/reviews', endpoint='ca_reviews')
@login_required
def ca_reviews():
    """CA Reviews and ratings page."""
    if not check_ca_access():
        flash('Access denied.', 'error')
        return redirect(url_for('main. home'))

    return render_template(
        'ca/reviews.html',
        user=current_user,
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_ANON_KEY=os.getenv('SUPABASE_ANON_KEY')
    )


@main_bp. route('/ca/notifications', endpoint='ca_notifications')
@login_required
def ca_notifications():
    """CA Notifications page."""
    if not check_ca_access():
        flash('Access denied.', 'error')
        return redirect(url_for('main.home'))

    return render_template(
        'ca/notifications. html',
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
    return render_template('user/consultations. html', user=current_user)


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
    return render_template('user/recommendations. html', user=current_user)


@main_bp.route('/user/settings', endpoint='user_settings')
@login_required
def user_settings():
    """User settings page."""
    return render_template('user/settings. html', user=current_user)


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


@main_bp.route('/user/ca/<int:ca_id>', endpoint='view_ca_profile')
@login_required
def view_ca_profile(ca_id):
    """View a specific CA's public profile."""
    # Fetch CA profile from database
    ca_user = User.query.filter_by(id=ca_id).first()
    if not ca_user or getattr(ca_user, 'role', 'user') != 'ca': 
        flash('CA profile not found.', 'error')
        return redirect(url_for('main.find_ca'))
    
    return render_template('user/ca_profile_view.html', ca=ca_user, user=current_user)


@main_bp.route('/user/consultation/<int:consultation_id>', endpoint='view_consultation')
@login_required
def view_consultation(consultation_id):
    """View a specific consultation."""
    # In a real app, fetch consultation from database
    return render_template('user/consultation_detail.html', consultation_id=consultation_id, user=current_user)


@main_bp.route('/user/request-consultation/<int:ca_id>', endpoint='request_consultation')
@login_required
def request_consultation(ca_id):
    """Request a consultation with a specific CA."""
    ca_user = User. query.filter_by(id=ca_id).first()
    if not ca_user or getattr(ca_user, 'role', 'user') != 'ca':
        flash('CA not found. ', 'error')
        return redirect(url_for('main.find_ca'))
    
    return render_template('user/request_consultation.html', ca=ca_user, user=current_user)


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
    auth_header = request. headers.get('Authorization', '')
    if not auth_header. startswith('Bearer '):
        return jsonify({'error': 'missing token'}), 401

    token = auth_header.split(' ', 1)[1]
    claims, err = decode_supabase_jwt(token)
    if err or not claims:
        return jsonify({'error': 'invalid token', 'detail': err}), 401

    role = claims.get('user_metadata', {}).get('role', 'user')

    try:
        user = ensure_local_user_from_claims(claims, role=role)
    except Exception as e: 
        return jsonify({'error': 'user mapping failed', 'detail': str(e)}), 400

    login_user(user, remember=True)

    user_role = getattr(user, 'role', 'user') if hasattr(user, 'role') else 'user'
    
    # Determine redirect URL
    if user_role in ['ca', 'admin']:
        redirect_url = url_for('main.ca_dashboard')
    elif user_role == 'ca_pending':
        redirect_url = url_for('auth. ca_pending')
    else:
        redirect_url = url_for('main. user_dashboard')
    
    return jsonify({
        'ok': True,
        'id': user.id,
        'email':  user.email,
        'role': user_role,
        'redirect_url':  redirect_url
    })


@auth_bp.route('/redirect-after-login')
@login_required
def redirect_after_login():
    """Redirect users to appropriate dashboard based on role."""
    return redirect_after_auth()


def redirect_after_auth():
    """Helper function to redirect user after authentication."""
    user_role = getattr(current_user, 'role', 'user')
    
    if user_role == 'ca': 
        return redirect(url_for('main. ca_dashboard'))
    elif user_role == 'admin': 
        return redirect(url_for('main.ca_dashboard'))  # or admin dashboard
    elif user_role == 'ca_pending': 
        return redirect(url_for('auth. ca_pending'))
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
        elif User.query.filter_by(username=username).first():
            flash('Username is already taken.  Please choose another.', 'error')
        elif User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'error')
        else:
            try:
                new_user = User(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )
                new_user.set_password(password)
                db.session. add(new_user)
                db. session.commit()
                flash(f'Welcome aboard, {first_name}!  Your account has been created successfully.  Please log in.', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
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

    user_id = claims. get('sub')
    email = claims.get('email') or claims.get('user_metadata', {}).get('email')

    local_user = User. query.filter_by(email=email. lower()).first() if email else None
    role = getattr(local_user, 'role', 'user') if local_user and hasattr(local_user, 'role') else 'user'

    return jsonify({
        'id': user_id,
        'role': role,
        'email': email
    })


@api_bp.route('/ca-application', methods=['POST'])
def submit_ca_application():
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


@api_bp.route('/ca/update-profile', methods=['POST'])
@login_required
def update_ca_profile():
    """Update CA profile information."""
    if not check_ca_access():
        return jsonify({'error':  'Access denied'}), 403

    try: 
        data = request. get_json()

        # Update user fields
        if 'first_name' in data:
            current_user.first_name = data['first_name']. strip().title()
        if 'last_name' in data:
            current_user.last_name = data['last_name'].strip().title()

        db.session.commit()

        return jsonify({
            'success':  True,
            'message': 'Profile updated successfully'
        })
    except Exception as e:
        db. session.rollback()
        print(f"CA profile update error: {e}")
        return jsonify({'error':  'Failed to update profile'}), 500


@api_bp.route('/ca/client-requests', methods=['GET'])
@login_required
def get_client_requests():
    """Get client requests for CA."""
    if not check_ca_access():
        return jsonify({'error': 'Access denied'}), 403

    # Mock data for now
    requests_data = [
        {
            'id': '1',
            'user_name': 'Rahul Sharma',
            'city': 'Delhi',
            'service': 'GST Compliance',
            'budget': '₹15,000 - ₹25,000',
            'urgency': 'high',
            'description': 'Need help with GST filing for my e-commerce business.',
            'created_at': datetime.utcnow().isoformat()
        },
        {
            'id': '2',
            'user_name': 'Priya Mehta',
            'city': 'Bangalore',
            'service': 'Tax Planning',
            'budget': '₹5,000 - ₹10,000',
            'urgency': 'medium',
            'description': 'Looking for tax planning consultation for FY 2024-25.',
            'created_at': datetime.utcnow().isoformat()
        }
    ]

    return jsonify({
        'success':  True,
        'data': requests_data
    })


@api_bp.route('/ca/accept-request', methods=['POST'])
@login_required
def accept_client_request():
    """Accept a client request."""
    if not check_ca_access():
        return jsonify({'error': 'Access denied'}), 403

    try:
        data = request.get_json()
        request_id = data.get('request_id')

        if not request_id:
            return jsonify({'error':  'Request ID is required'}), 400

        # Handle request acceptance logic here

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
    """Decline a client request."""
    if not check_ca_access():
        return jsonify({'error': 'Access denied'}), 403

    try:
        data = request.get_json()
        request_id = data.get('request_id')
        reason = data. get('reason', '')

        if not request_id: 
            return jsonify({'error': 'Request ID is required'}), 400

        # Handle request decline logic here

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
    """Get CA dashboard statistics."""
    if not check_ca_access():
        return jsonify({'error': 'Access denied'}), 403

    # Mock stats
    stats = {
        'total_clients': 127,
        'active_consultations': 8,
        'pending_requests': 3,
        'total_earnings': 485000,
        'this_month_earnings':  48500,
        'average_rating': 4.9,
        'total_reviews': 89,
        'response_rate': 98,
        'completion_rate': 95
    }

    return jsonify({'success': True, 'data': stats})


@api_bp.route('/ca/earnings-summary', methods=['GET'])
@login_required
def ca_earnings_summary():
    """Get CA earnings summary."""
    if not check_ca_access():
        return jsonify({'error': 'Access denied'}), 403

    # Mock data
    summary = {
        'available_balance': 124500,
        'pending_amount': 28000,
        'total_earned': 485000,
        'total_withdrawn': 332500,
        'transactions': [
            {
                'id': '1',
                'type': 'credit',
                'amount': 18000,
                'description': 'Payment from Rahul Sharma - GST Compliance',
                'date': datetime.utcnow().isoformat()
            },
            {
                'id': '2',
                'type': 'debit',
                'amount': 50000,
                'description': 'Withdrawal to HDFC Bank ****4521',
                'date': datetime.utcnow().isoformat()
            }
        ]
    }

    return jsonify({'success': True, 'data':  summary})


@api_bp.route('/user/dashboard-stats', methods=['GET'])
@login_required
def user_dashboard_stats():
    """Get user dashboard statistics."""
    stats = {
        'active_consultations': 3,
        'documents_count': 12,
        'unread_messages': 5,
        'completed_tasks': 8,
        'upcoming_deadlines': 2
    }

    return jsonify({'success':  True, 'data': stats})


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


@api_bp. route('/user/request-consultation', methods=['POST'])
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
    """Search for CAs with filters."""
    location = request.args. get('location', '')
    service = request.args.get('service', '')
    experience = request.args. get('experience', '')
    sort_by = request. args.get('sort', 'recommended')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Mock CA data
    cas = [
        {
            'id': 1,
            'name': 'CA Rajesh Sharma',
            'location': 'Mumbai, Maharashtra',
            'experience': 8,
            'rating': 4.9,
            'reviews_count': 89,
            'clients_count': 127,
            'services': ['Tax Planning', 'GST Compliance', 'Audit', 'ITR Filing'],
            'verified': True
        },
        {
            'id':  2,
            'name': 'CA Priya Mehta',
            'location': 'Delhi NCR',
            'experience': 12,
            'rating': 5.0,
            'reviews_count':  156,
            'clients_count': 215,
            'services': ['Tax Planning', 'Investment Advisory', 'NRI Taxation'],
            'verified':  True
        }
    ]

    return jsonify({
        'success': True,
        'data':  cas,
        'total':  len(cas),
        'page':  page,
        'per_page': per_page
    })


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
        rating = data. get('rating')

        if not query_id: 
            return jsonify({'success': False, 'error': 'Query ID is required. '}), 400

        chat_query = ChatQuery. query.get(query_id)
        if not chat_query or chat_query.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Query not found.'}), 404

        try:
            if hasattr(chat_query, 'rating') and rating: 
                chat_query.rating = rating
            if hasattr(chat_query, 'is_helpful') and is_helpful is not None:
                chat_query.is_helpful = is_helpful
            if hasattr(chat_query, 'feedback_text') and feedback_text:
                chat_query.feedback_text = feedback_text
        except Exception as e: 
            print(f"Warning: Could not update all feedback fields: {e}")

        try:
            user_feedback = UserFeedback(
                user_id=current_user. id,
                query_id=query_id,
                is_helpful=is_helpful if is_helpful is not None else (rating >= 4 if rating else None),
                feedback_text=feedback_text
            )
            db.session.add(user_feedback)
        except Exception as e: 
            print(f"Warning:  Could not create UserFeedback entry: {e}")

        db.session. commit()
        return jsonify({'success':  True, 'message': 'Thank you for your feedback!'})

    except Exception as e:
        db.session.rollback()
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
    """Get platform statistics."""
    try:
        stats = {
            'users': 18500,
            'queries': 325000,
            'accuracy': 98.5,
            'satisfaction': 96.8,
            'cas': 450,
            'consultations': 12500,
            'popular_topics': [
                {'topic': 'Tax Planning', 'count':  46000, 'icon': 'fa-calculator'},
                {'topic': 'Investment', 'count': 39000, 'icon': 'fa-chart-line'},
                {'topic': 'GST', 'count': 30000, 'icon': 'fa-file-invoice'},
                {'topic': 'Retirement', 'count':  16000, 'icon': 'fa-umbrella-beach'}
            ],
            'last_updated': datetime.utcnow().isoformat()
        }
        return jsonify({'success': True, 'data': stats})
    except Exception as e: 
        print(f"Stats API error: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch statistics'}), 500


@api_bp. route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({
            'success':  True,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version':  'v2.0.0'
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

        # Store in database
        try:
            chat_query = ChatQuery(
                user_id=current_user.id,
                query=user_query,
                response=response
            )
            db.session.add(chat_query)
            db.session. commit()
            query_id = chat_query.id
        except Exception as e: 
            print(f"Failed to store chat query:  {e}")
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
                'priority':  'high'
            },
            {
                'id':  '2',
                'type': 'deadline',
                'title':  'Advance Tax Due Date',
                'description': 'Third installment of advance tax is due by December 15th.',
                'priority': 'urgent'
            },
            {
                'id': '3',
                'type':  'tip',
                'title': 'Early ITR Filing Benefits',
                'description': 'Consider filing your ITR early for faster refund processing.',
                'priority': 'normal'
            }
        ]

        return jsonify({'success': True, 'data': suggestions})
    except Exception as e:
        print(f"AI suggestions error: {e}")
        return jsonify({'success': False, 'error': 'Failed to fetch suggestions'}), 500


# ==================== ADMIN ROUTES ====================

@main_bp.route('/admin/dashboard', endpoint='admin_dashboard')
@login_required
def admin_dashboard():
    """Admin Dashboard."""
    if not check_admin_access():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main. home'))

    return render_template('admin/dashboard.html', user=current_user)


@main_bp.route('/admin/users', endpoint='admin_users')
@login_required
def admin_users():
    """Admin Users management."""
    if not check_admin_access():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.home'))

    users = User.query. order_by(User. created_at.desc()).all()
    return render_template('admin/users.html', user=current_user, users=users)


@main_bp.route('/admin/ca-applications', endpoint='admin_ca_applications')
@login_required
def admin_ca_applications():
    """Admin CA Applications management."""
    if not check_admin_access():
        flash('Access denied. Admin only. ', 'error')
        return redirect(url_for('main.home'))

    return render_template('admin/ca_applications. html', user=current_user)


@main_bp.route('/admin/settings', endpoint='admin_settings')
@login_required
def admin_settings():
    """Admin Settings page."""
    if not check_admin_access():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('main.home'))

    return render_template('admin/settings. html', user=current_user)


@api_bp.route('/admin/users', methods=['GET'])
@login_required
def admin_get_users():
    """Get all users (admin only)."""
    if not check_admin_access():
        return jsonify({'error': 'Access denied'}), 403

    try:
        users = User.query.order_by(User. created_at.desc()).all()
        users_data = [{
            'id':  u.id,
            'username': u. username,
            'email': u.email,
            'first_name': u. first_name,
            'last_name': u.last_name,
            'role': getattr(u, 'role', 'user'),
            'created_at': u. created_at.isoformat() if u.created_at else None
        } for u in users]

        return jsonify({'success': True, 'data': users_data})
    except Exception as e: 
        print(f"Admin get users error:  {e}")
        return jsonify({'error': 'Failed to fetch users'}), 500


@api_bp.route('/admin/user/<int:user_id>/role', methods=['PUT'])
@login_required
def admin_update_user_role(user_id):
    """Update user role (admin only)."""
    if not check_admin_access():
        return jsonify({'error': 'Access denied'}), 403

    try: 
        data = request.get_json()
        new_role = data. get('role')

        if new_role not in ['user', 'ca', 'ca_pending', 'admin']: 
            return jsonify({'error': 'Invalid role'}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if hasattr(user, 'role'):
            user.role = new_role
            db.session.commit()

        return jsonify({'success': True, 'message': 'User role updated successfully'})
    except Exception as e:
        db.session.rollback()
        print(f"Admin update user role error: {e}")
        return jsonify({'error': 'Failed to update user role'}), 500


@api_bp.route('/admin/ca-applications', methods=['GET'])
@login_required
def admin_get_ca_applications():
    """Get all CA applications (admin only)."""
    if not check_admin_access():
        return jsonify({'error': 'Access denied'}), 403

    # Mock data - in real app, fetch from database
    applications = [
        {
            'id':  '1',
            'full_name': 'Rajesh Kumar',
            'email':  'rajesh@example.com',
            'icai_number': '123456',
            'city': 'Mumbai',
            'state':  'Maharashtra',
            'status': 'pending',
            'submitted_at': datetime.utcnow().isoformat()
        },
        {
            'id': '2',
            'full_name': 'Priya Singh',
            'email': 'priya@example.com',
            'icai_number': '234567',
            'city': 'Delhi',
            'state': 'Delhi',
            'status': 'pending',
            'submitted_at': datetime.utcnow().isoformat()
        }
    ]

    return jsonify({'success': True, 'data': applications})


@api_bp.route('/admin/ca-application/<application_id>/approve', methods=['POST'])
@login_required
def admin_approve_ca_application(application_id):
    """Approve a CA application (admin only)."""
    if not check_admin_access():
        return jsonify({'error':  'Access denied'}), 403

    try:
        # Handle approval logic
        # Update user role to 'ca', send email, etc. 

        return jsonify({'success': True, 'message': 'CA application approved successfully'})
    except Exception as e:
        print(f"Admin approve CA error: {e}")
        return jsonify({'error': 'Failed to approve application'}), 500


@api_bp. route('/admin/ca-application/<application_id>/reject', methods=['POST'])
@login_required
def admin_reject_ca_application(application_id):
    """Reject a CA application (admin only)."""
    if not check_admin_access():
        return jsonify({'error': 'Access denied'}), 403

    try: 
        data = request.get_json()
        reason = data.get('reason', '')

        # Handle rejection logic
        # Send email with rejection reason, etc.

        return jsonify({'success': True, 'message':  'CA application rejected'})
    except Exception as e:
        print(f"Admin reject CA error: {e}")
        return jsonify({'error':  'Failed to reject application'}), 500


@api_bp.route('/admin/stats', methods=['GET'])
@login_required
def admin_stats():
    """Get admin dashboard statistics."""
    if not check_admin_access():
        return jsonify({'error': 'Access denied'}), 403

    try: 
        total_users = User. query.count()
        ca_count = User.query. filter_by(role='ca').count() if hasattr(User, 'role') else 0
        pending_cas = User.query. filter_by(role='ca_pending').count() if hasattr(User, 'role') else 0

        stats = {
            'total_users': total_users,
            'total_cas': ca_count,
            'pending_ca_applications': pending_cas,
            'total_consultations': 12500,
            'total_revenue': 4850000,
            'active_users_today': 1250,
            'new_users_this_week': 320
        }

        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        print(f"Admin stats error: {e}")
        return jsonify({'error': 'Failed to fetch admin stats'}), 500


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
    return redirect(url_for('auth. login'))


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
                {'name':  'GST Compliance', 'endpoint': 'main. gst_compliance', 'icon': 'fa-file-invoice', 'description': 'GST filing and compliance'},
                {'name': 'Business Finance', 'endpoint':  'main.business_finance', 'icon': 'fa-building', 'description':  'Business financial management'},
                {'name': 'Audit Services', 'endpoint':  'main.audit_services', 'icon': 'fa-search-dollar', 'description':  'Statutory and internal audits'},
                {'name': 'Startup Advisory', 'endpoint':  'main.startup_advisory', 'icon': 'fa-rocket', 'description': 'Startup compliance and advisory'},
            ],
            'resources': [
                {'name': 'Financial Blog', 'endpoint':  'main.financial_blog', 'icon': 'fa-book', 'description':  'Latest financial insights'},
                {'name':  'Learning Center', 'endpoint':  'main.learning_centre', 'icon':  'fa-graduation-cap', 'description': 'Financial education resources'},
                {'name': 'Tax Calculator', 'endpoint':  'main.tax_calculator', 'icon': 'fa-calculator', 'description': 'Calculate your taxes'},
                {'name': 'Retirement Planning', 'endpoint': 'main. retirement_planning', 'icon': 'fa-umbrella-beach', 'description': 'Plan for your future'},
                {'name': 'Investment Tools', 'endpoint':  'main.investment_tools', 'icon': 'fa-tools', 'description':  'Investment analysis tools'},
            ],
            'support': [
                {'name': 'Help Center', 'endpoint': 'main. help_center', 'icon':  'fa-question-circle'},
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
                {'name': 'Settings', 'endpoint': 'main. ca_settings', 'icon': 'fa-cog'},
            ],
            'user_menu': [
                {'name': 'Dashboard', 'endpoint':  'main.user_dashboard', 'icon': 'fa-home'},
                {'name': 'Find CA', 'endpoint':  'main.find_ca', 'icon': 'fa-user-tie'},
                {'name': 'My Consultations', 'endpoint': 'main. user_consultations', 'icon': 'fa-folder-open'},
                {'name': 'Messages', 'endpoint':  'main.user_messages', 'icon': 'fa-comments'},
                {'name': 'Documents', 'endpoint': 'main. user_documents', 'icon': 'fa-file-alt'},
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