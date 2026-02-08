"""
Finucity - AI-Powered Indian Tax & Financial Platform
Main Application Entry Point
Author: Sumeet Sangwan
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, jsonify, g
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from supabase import create_client
import html
import time

# =====================================================================
# ENVIRONMENT SETUP
# =====================================================================
load_dotenv()

# Verify critical environment variables
required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_SERVICE_KEY', 'SECRET_KEY']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print("❌ ERROR: Missing required environment variables:")
    for var in missing_vars:
        print(f"   - {var}")
    print("\nPlease set them in your .env file")
    exit(1)

print("✅ Environment variables loaded successfully")

# Supabase configuration
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")

def get_supabase_admin():
    """Get Supabase client with admin privileges"""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# =====================================================================
# FLASK APP INITIALIZATION
# =====================================================================
app = Flask(__name__, 
            template_folder='finucity/templates', 
            static_folder='finucity/static')

# Core config
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Environment-aware security settings
is_production = os.getenv('FLASK_ENV', 'development') == 'production'
app.config['SESSION_COOKIE_SECURE'] = is_production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_NAME'] = '__finucity_session'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB upload limit
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour CSRF token validity

# CSRF Protection
csrf = CSRFProtect(app)
# Note: Blueprint exemptions are applied after blueprint registration below

# =====================================================================
# SECURITY: RATE LIMITING
# =====================================================================
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# =====================================================================
# SECURITY: INPUT SANITIZATION & HEADERS
# =====================================================================
def sanitize_input(text):
    """Sanitize user input to prevent XSS attacks"""
    if isinstance(text, str):
        return html.escape(text)
    return text

app.jinja_env.globals.update(sanitize=sanitize_input)

@app.after_request
def set_security_headers(response):
    """Apply security headers to every response"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    if is_production:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    # Remove server header
    response.headers.pop('Server', None)
    return response

@app.before_request
def before_request_logging():
    """Log request timing and attach request ID"""
    g.request_start_time = time.time()
    g.request_id = os.urandom(8).hex()

@app.after_request
def after_request_logging(response):
    """Log request duration for performance monitoring"""
    if hasattr(g, 'request_start_time'):
        duration = (time.time() - g.request_start_time) * 1000
        if duration > 1000:  # Log slow requests (>1s)
            app.logger.warning(
                f"Slow request: {request.method} {request.path} "
                f"took {duration:.0f}ms [rid={getattr(g, 'request_id', 'unknown')}]"
            )
    return response

# =====================================================================
# DATABASE INITIALIZATION
# =====================================================================
from finucity.database import supabase_db, UserService
from finucity.models import User

supabase_db.init_app(app)

# =====================================================================
# FLASK-LOGIN SETUP
# =====================================================================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Load user from Supabase for Flask-Login session"""
    try:
        user_data = UserService.get_by_id(user_id)
        if user_data:
            return User(user_data)
    except Exception as e:
        app.logger.error(f"Error loading user {user_id}: {e}")
    return None

# =====================================================================
# BLUEPRINT REGISTRATION
# =====================================================================
try:
    # Core blueprints (required)
    from finucity.routes import main_bp, auth_bp, api_bp
    from finucity.chat_routes import chat_bp
    from finucity.ca_ecosystem_routes import ca_ecosystem_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(ca_ecosystem_bp)
    
    # Exempt auth & chat blueprints from CSRF (they use token/session auth)
    csrf.exempt(auth_bp)
    csrf.exempt(chat_bp)
    csrf.exempt(api_bp)
    
    print("✅ Core blueprints loaded")
    
except ImportError as e:
    print(f"❌ ERROR: Failed to import core blueprints: {e}")
    exit(1)

# Optional blueprints (new features - graceful degradation)
try:
    from finucity.services_routes import services_bp, calculators_bp
    app.register_blueprint(services_bp)
    app.register_blueprint(calculators_bp)
    print("✅ Services and Calculators blueprints loaded")
except ImportError as e:
    print(f"⚠️  Services/Calculators modules not found: {e}")

try:
    from finucity.admin_routes import admin_enhanced_bp
    app.register_blueprint(admin_enhanced_bp)
    print("✅ Admin Enhanced blueprint loaded")
except ImportError as e:
    print(f"⚠️  Admin Enhanced module not found: {e}")

try:
    from finucity.trust_routes import trust_bp
    app.register_blueprint(trust_bp)
    print("✅ Trust System blueprint loaded")
except ImportError as e:
    print(f"⚠️  Trust System module not found: {e}")

# =====================================================================
# JINJA TEMPLATE UTILITIES
# =====================================================================
@app.context_processor
def utility_processor():
    """Make Python built-ins available in templates"""
    return dict(
        hasattr=hasattr,
        getattr=getattr,
        isinstance=isinstance,
        len=len,
        str=str,
        int=int,
        float=float,
        bool=bool,
        list=list,
        dict=dict
    )

# =====================================================================
# ERROR HANDLERS
# =====================================================================
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('Errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    app.logger.error(f"Internal server error: {error}")
    return render_template('Errors/500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors"""
    return render_template('Errors/403.html'), 403

@app.errorhandler(429)
def ratelimit_handler(error):
    """Handle rate limit errors"""
    return render_template('Errors/429.html'), 429

from flask_wtf.csrf import CSRFError

@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    """Return JSON for CSRF errors on API requests instead of HTML"""
    if request.is_json or request.headers.get('Accept', '').startswith('application/json'):
        return jsonify({'success': False, 'error': 'CSRF token missing or invalid'}), 400
    return render_template('Errors/403.html'), 400

# =====================================================================
# HEALTH CHECK
# =====================================================================
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return {
        'status': 'healthy',
        'service': 'finucity',
        'database': 'supabase'
    }, 200

# =====================================================================
# APPLICATION STARTUP
# =====================================================================
# =====================================================================
# LOGGING SETUP
# =====================================================================
def setup_logging(app):
    """Configure production-grade logging"""
    log_level = logging.DEBUG if app.debug else logging.INFO
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    
    # File handler (rotating)
    os.makedirs('logs', exist_ok=True)
    file_handler = RotatingFileHandler(
        'logs/finucity.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s [%(name)s:%(lineno)d] %(message)s'
    ))
    
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)

setup_logging(app)

# =====================================================================
# APPLICATION STARTUP
# =====================================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    print("")
    print("=" * 70)
    print("  FINUCITY - AI-POWERED TAX & FINANCIAL PLATFORM")
    print("=" * 70)
    print(f"  Database: Supabase (PostgreSQL)")
    print(f"  Environment: {'Development' if debug else 'Production'}")
    print(f"  Server: http://localhost:{port}")
    print("=" * 70)
    print("")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=debug
    )