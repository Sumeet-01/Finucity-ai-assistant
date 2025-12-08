"""
Centralized route handlers for the Finucity AI application.
This file defines all web pages and API endpoints.
Author: Sumeet Sangwan
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, abort, send_from_directory
from flask_login import login_required, current_user, login_user, logout_user
import uuid
import re
from datetime import datetime
import os

# Use relative imports to prevent circular dependencies.
from . import db, limiter
from .models import User, ChatQuery, UserFeedback

# Note: Chat routes are now in a separate file (chat_routes.py)
# Import ai module for any API endpoints that might still need it
try:
    from .ai import get_ai_response
except ImportError:
    print("Warning: AI module not found. Some features may be limited.")
    get_ai_response = None

# ==================== BLUEPRINT CREATION ====================
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Note: chat_bp is defined in chat_routes.py and imported in __init__.py

# ==================== MAIN & STATIC PAGE ROUTES ====================

@main_bp.route('/', endpoint='home')
def index():
    """Renders the homepage - accessible to both authenticated and non-authenticated users"""
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

@main_bp.route('/faq', endpoint='faq')
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

# ==================== FINANCIAL SERVICES ROUTES ====================

@main_bp.route('/tax-planning', endpoint='tax_planning')
def tax_planning():
    """Renders the tax planning page."""
    try:
        return render_template('financial-services/tax-planning.html')
    except:
        try:
            return render_template('tax_planning.html')
        except:
            return render_template('Errors/404.html'), 404

@main_bp.route('/investment-advisory', endpoint='investment_advisory')
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

# ==================== RESOURCE ROUTES ====================

@main_bp.route('/financial-blog', endpoint='financial_blog')
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
        print(f"Error loading investment tools: {e}")
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

# ==================== SUPPORT ROUTES ====================

@main_bp.route('/privacy-policy', endpoint='privacy_policy')
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

@main_bp.route('/sitemap.xml', endpoint='sitemap')
def sitemap():
    """Generate sitemap.xml."""
    try:
        static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        return send_from_directory(static_folder, 'sitemap.xml')
    except Exception as e:
        print(f"Error serving sitemap: {e}")
        abort(404)

@main_bp.route('/robots.txt', endpoint='robots')
def robots():
    """Generate robots.txt."""
    try:
        static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        return send_from_directory(static_folder, 'robots.txt')
    except Exception as e:
        print(f"Error serving robots.txt: {e}")
        abort(404)

# ==================== AUTHENTICATION ROUTES ====================

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handles new user registration."""
    if current_user.is_authenticated:
        flash('You are already logged in!', 'info')
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        first_name = request.form.get('first_name', '').strip().title()
        last_name = request.form.get('last_name', '').strip().title()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not all([username, email, first_name, last_name, password]):
            flash('All fields are required.', 'error')
        elif len(username) < 3:
            flash('Username must be at least 3 characters long.', 'error')
        elif len(password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
        elif password != confirm_password:
            flash('Passwords do not match.', 'error')
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Please enter a valid email address.', 'error')
        elif User.query.filter_by(username=username).first():
            flash('Username is already taken. Please choose another.', 'error')
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
                db.session.add(new_user)
                db.session.commit()
                flash(f'Welcome aboard, {first_name}! Your account has been created successfully. Please log in.', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                print(f"Registration error: {e}")
                flash('An error occurred during registration. Please try again.', 'error')
        
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    if current_user.is_authenticated:
        flash('You are already logged in!', 'info')
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip().lower()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me', False)
        
        if not username_or_email or not password:
            flash('Please enter both username/email and password.', 'error')
        else:
            user = User.query.filter(
                (User.username == username_or_email) | 
                (User.email == username_or_email)
            ).first()

            if user and user.check_password(password):
                login_user(user, remember=bool(remember_me))
                
                # Update last login time if you have that field
                try:
                    if hasattr(user, 'last_login'):
                        user.last_login = datetime.utcnow()
                        db.session.commit()
                except:
                    pass
                
                flash(f'Welcome back, {user.first_name}!', 'success')
                
                # Redirect to next page or chat interface
                next_page = request.args.get('next')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(url_for('chat.chat_interface'))
            else:
                flash('Invalid username/email or password. Please try again.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handles user logout."""
    user_name = current_user.first_name
    logout_user()
    flash(f'Goodbye, {user_name}! You have been successfully logged out.', 'info')
    return redirect(url_for('main.home'))

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    """Handle password reset request."""
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address.', 'error')
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Please enter a valid email address.', 'error')
        else:
            user = User.query.filter_by(email=email).first()
            
            if user:
                # TODO: Generate token and send reset email
                # For now, just show a message
                flash('If an account exists with that email, you will receive password reset instructions shortly.', 'info')
                return redirect(url_for('auth.login'))
            else:
                # Don't reveal if email exists or not (security best practice)
                flash('If an account exists with that email, you will receive password reset instructions shortly.', 'info')
                return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html')

# ==================== API ENDPOINTS (Legacy - for backward compatibility) ====================
# Note: Main chat API endpoints are now in chat_routes.py

@api_bp.route('/feedback', methods=['POST'])
@login_required
def api_feedback():
    """API endpoint for handling user feedback on responses."""
    try:
        data = request.get_json()
        query_id = data.get('query_id')
        is_helpful = data.get('is_helpful')
        feedback_text = data.get('feedback_text', '')
        rating = data.get('rating')
        
        if not query_id:
            return jsonify({'success': False, 'error': 'Query ID is required.'}), 400
            
        chat_query = ChatQuery.query.get(query_id)
        if not chat_query or chat_query.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Query not found.'}), 404
        
        # Update query with feedback
        try:
            if hasattr(chat_query, 'rating') and rating:
                chat_query.rating = rating
            if hasattr(chat_query, 'is_helpful') and is_helpful is not None:
                chat_query.is_helpful = is_helpful
            if hasattr(chat_query, 'feedback_text') and feedback_text:
                chat_query.feedback_text = feedback_text
        except Exception as e:
            print(f"Warning: Could not update all feedback fields: {e}")
        
        # Try to create UserFeedback entry if table exists
        try:
            user_feedback = UserFeedback(
                user_id=current_user.id,
                query_id=query_id,
                is_helpful=is_helpful if is_helpful is not None else (rating >= 4 if rating else None),
                feedback_text=feedback_text
            )
            db.session.add(user_feedback)
        except Exception as e:
            print(f"Warning: Could not create UserFeedback entry: {e}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Thank you for your feedback!'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Feedback API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to submit feedback'
        }), 500

@api_bp.route('/newsletter-signup', methods=['POST'])
def newsletter_signup():
    """API endpoint for newsletter signups."""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required.'}), 400
            
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({'success': False, 'error': 'Valid email is required.'}), 400
        
        # TODO: Add to newsletter database
        # For now, just return success
        
        return jsonify({
            'success': True, 
            'message': 'Thank you for subscribing to our newsletter!'
        })
        
    except Exception as e:
        print(f"Newsletter signup error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to process subscription'
        }), 500

@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """API endpoint to get platform statistics."""
    try:
        # In production, fetch these from database
        # For now, return static values
        stats = {
            'users': 18500,  # Updated count
            'queries': 325000,  # Updated count
            'accuracy': 98.5,
            'satisfaction': 96.8,
            'popular_topics': [
                {'topic': 'Tax Planning', 'count': 46000, 'icon': 'fa-calculator'},
                {'topic': 'Investment', 'count': 39000, 'icon': 'fa-chart-line'},
                {'topic': 'GST', 'count': 30000, 'icon': 'fa-file-invoice'},
                {'topic': 'Retirement', 'count': 16000, 'icon': 'fa-umbrella-beach'}
            ],
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True, 
            'data': stats
        })
        
    except Exception as e:
        print(f"Stats API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch statistics'
        }), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Check database connection
        db.session.execute(db.text('SELECT 1'))
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': 'v2.0.0'
        })
    except Exception as e:
        print(f"Health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 503

# ==================== ERROR HANDLERS ====================

@main_bp.app_errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    try:
        return render_template('Errors/404.html'), 404
    except:
        return """
        <html>
            <head><title>404 - Page Not Found</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>404 - Page Not Found</h1>
                <p>The page you're looking for doesn't exist.</p>
                <a href="/" style="color: #FBA002;">Go to Homepage</a>
            </body>
        </html>
        """, 404

@main_bp.app_errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors."""
    try:
        return render_template('Errors/500.html'), 500
    except:
        return """
        <html>
            <head><title>500 - Server Error</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>500 - Internal Server Error</h1>
                <p>Something went wrong on our end. Please try again later.</p>
                <a href="/" style="color: #FBA002;">Go to Homepage</a>
            </body>
        </html>
        """, 500

@main_bp.app_errorhandler(403)
def forbidden(e):
    """Handle 403 errors."""
    return jsonify({
        'success': False,
        'error': 'Access forbidden',
        'message': 'You do not have permission to access this resource.'
    }), 403

@main_bp.app_errorhandler(429)
def rate_limit_exceeded(e):
    """Handle rate limit errors."""
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.'
    }), 429

# ==================== TEMPLATE CONTEXT PROCESSORS ====================

@main_bp.context_processor
def inject_current_year():
    """Inject current year into all templates."""
    return {
        'current_year': datetime.now().year,
        'current_date': datetime.now().strftime('%B %d, %Y')
    }

@main_bp.context_processor
def inject_user_data():
    """Inject common user data into templates."""
    user_data = {
        'is_logged_in': current_user.is_authenticated,
        'has_notifications': False,
        'site_version': 'v2.0.0',
        'site_name': 'Finucity',
        'support_email': 'support@finucity.com'
    }
    
    if current_user.is_authenticated:
        # Check for notifications (implement your logic here)
        user_data['has_notifications'] = False
        user_data['user_initial'] = current_user.first_name[0].upper() if current_user.first_name else 'U'
    
    return {'user_data': user_data}

@main_bp.context_processor
def inject_navigation_data():
    """Inject navigation-related data."""
    return {
        'nav_items': {
            'services': [
                {'name': 'Tax Planning', 'endpoint': 'main.tax_planning', 'icon': 'fa-calculator'},
                {'name': 'Investment Advisory', 'endpoint': 'main.investment_advisory', 'icon': 'fa-chart-line'},
                {'name': 'GST Compliance', 'endpoint': 'main.gst_compliance', 'icon': 'fa-file-invoice'},
                {'name': 'Business Finance', 'endpoint': 'main.business_finance', 'icon': 'fa-building'},
            ],
            'resources': [
                {'name': 'Financial Blog', 'endpoint': 'main.financial_blog', 'icon': 'fa-book'},
                {'name': 'Learning Center', 'endpoint': 'main.learning_centre', 'icon': 'fa-graduation-cap'},
                {'name': 'Tax Calculator', 'endpoint': 'main.tax_calculator', 'icon': 'fa-calculator'},
                {'name': 'Retirement Planning', 'endpoint': 'main.retirement_planning', 'icon': 'fa-umbrella-beach'},
            ]
        }
    }

# ==================== UTILITY FUNCTIONS ====================

def format_currency(amount):
    """Format amount as Indian currency."""
    try:
        return f"₹{amount:,.2f}"
    except:
        return f"₹{amount}"

def format_date(date_obj):
    """Format date in a user-friendly way."""
    try:
        if isinstance(date_obj, str):
            date_obj = datetime.fromisoformat(date_obj)
        return date_obj.strftime('%B %d, %Y')
    except:
        return str(date_obj)

# Register template filters
@main_bp.app_template_filter('currency')
def currency_filter(amount):
    return format_currency(amount)

@main_bp.app_template_filter('date')
def date_filter(date_obj):
    return format_date(date_obj)