"""
Finucity - AI-Powered Indian Tax & Financial Platform
Main Application Entry Point
Author: Sumeet Sangwan
"""

import os
from flask import Flask, render_template
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from supabase import create_client
import html

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

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

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
# SECURITY: INPUT SANITIZATION
# =====================================================================
def sanitize_input(text):
    """Sanitize user input to prevent XSS attacks"""
    if isinstance(text, str):
        return html.escape(text)
    return text

app.jinja_env.globals.update(sanitize=sanitize_input)

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
if __name__ == '__main__':
    print("")
    print("=" * 70)
    print("🚀 FINUCITY - AI-POWERED TAX & FINANCIAL PLATFORM")
    print("=" * 70)
    print("")
    print("💾 Database: Supabase (PostgreSQL)")
    print("🤖 AI Provider: Groq (llama-3.1-8b-instant)")
    print("✨ Features:")
    print("   • Income Tax Filing (ITR)")
    print("   • GST Registration & Filing")
    print("   • Business Compliance")
    print("   • Tax Planning & Advisory")
    print("   • 10+ Financial Calculators")
    print("   • AI-Powered Tax Intelligence")
    print("   • Verified CA Network")
    print("")
    print("🌐 Server starting on http://localhost:5000")
    print("📚 Admin Panel: http://localhost:5000/admin/dashboard")
    print("🧮 Calculators: http://localhost:5000/calculators/")
    print("💼 Services: http://localhost:5000/services/")
    print("")
    print("=" * 70)
    print("")
    
    # Run development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )

    print("")
    print("🌐 Server running on: http://localhost:3000")
    print("📡 Ready to accept connections...")
    print("")
    
    port = int(os.environ.get('PORT', 3000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)