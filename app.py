import os
from flask import Flask, render_template
from flask_login import login_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from supabase import create_client
import html

# Load .env from current directory or parent
load_dotenv()
if os.getenv('SUPABASE_URL'):
    print("✅ Environment variables loaded successfully")
else:
    print("⚠️  WARNING: SUPABASE_URL not found in environment")

# Supabase config
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
SUPABASE_JWT_SECRET = os.environ["SUPABASE_JWT_SECRET"]

def get_supabase_admin():
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Flask app
app = Flask(__name__, template_folder='finucity/templates', static_folder='finucity/static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise RuntimeError("SECRET_KEY environment variable must be set")

# Security: Rate Limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Security: Input Sanitization Utility
def sanitize_input(text):
    """Sanitize user input to prevent XSS attacks."""
    if isinstance(text, str):
        return html.escape(text)
    return text

# Make sanitize available globally
app.jinja_env.globals.update(sanitize=sanitize_input)

# Flask app
app = Flask(__name__, template_folder='finucity/templates', static_folder='finucity/static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise RuntimeError("SECRET_KEY environment variable must be set")

# Initialize Supabase database layer
from finucity.database import supabase_db
from finucity.models import User
supabase_db.init_app(app)

# Blueprints
from finucity.routes import main_bp, auth_bp, api_bp
from finucity.chat_routes import chat_bp
from finucity.ca_ecosystem_routes import ca_ecosystem_bp
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(ca_ecosystem_bp)

# Login manager for session management
from flask_login import LoginManager
from finucity.database import UserService

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    """Load user from Supabase for Flask-Login session"""
    user_data = UserService.get_by_id(user_id)
    if user_data:
        return User(user_data)
    return None

# Utility for Jinja
@app.context_processor
def utility_processor():
    return dict(hasattr=hasattr, getattr=getattr, isinstance=isinstance, len=len, str=str, int=int, float=float, bool=bool)

app.jinja_env.globals.update(hasattr=hasattr, getattr=getattr, isinstance=isinstance, len=len, str=str, int=int, float=float, bool=bool)

# All routes are now handled by blueprints in finucity/routes.py
# No duplicate routes in app.py - keeps it clean and organized

# Errors
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

# All routes are now handled by blueprints in finucity/routes.py
# No duplicate routes in app.py - keeps it clean and organized

if __name__ == '__main__':
    print("")
    print("=" * 70)
    print("🚀 FINUCITY AI ASSISTANT - STARTING")
    print("=" * 70)
    print("")
    print("💾 Database: Supabase (PostgreSQL)")
    print("✨ AI Powered Financial Assistant")
    print("👨‍💻 Created by Sumeet Sangwan")
    print("🔗 GitHub: https://github.com/Sumeet-01")
    print("")
    print("-" * 70)
    print("📍 AVAILABLE URLS:")
    print("-" * 70)
    print("")
    print("🏠 Main Application:")
    print("   → http://localhost:3000")
    print("")
    print("🔐 Admin Panel:")
    print("   → http://localhost:3000/admin/dashboard")
    print("   → http://localhost:3000/admin/users")
    print("   → http://localhost:3000/admin/ca-applications")
    print("")
    print("👔 CA Dashboard:")
    print("   → http://localhost:3000/ca/dashboard")
    print("   → http://localhost:3000/ca-application (Apply as CA)")
    print("   → http://localhost:3000/ca-application-status")
    print("")
    print("👤 User Dashboard:")
    print("   → http://localhost:3000/user/dashboard")
    print("   → http://localhost:3000/user/find-ca")
    print("   → http://localhost:3000/profile")
    print("")
    print("💬 AI Chat:")
    print("   → http://localhost:3000/chat")
    print("")
    print("🔑 Authentication:")
    print("   → http://localhost:3000/auth/login")
    print("   → http://localhost:3000/auth/register")
    print("")
    print("-" * 70)
    print("🎯 QUICK ACTIONS:")
    print("-" * 70)
    print("")
    print("Test CA Dashboard:  http://localhost:3000/test-ca-dashboard")
    print("Apply as CA:        http://localhost:3000/ca-application")
    print("Admin Panel:        http://localhost:3000/admin")
    print("Main App:           http://localhost:3000")
    print("")
    print("=" * 70)
    
    # Verify Supabase configuration
    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_SERVICE_KEY'):
        print("❌ ERROR: Supabase configuration missing")
        print("   Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env")
        print("=" * 70)
        exit(1)
    
    print("✅ Configuration: OK")
    print("✅ Environment: " + os.environ.get('FLASK_ENV', 'development'))
    print("=" * 70)
    print("")
    print("🌐 Server running on: http://localhost:3000")
    print("📡 Ready to accept connections...")
    print("")
    
    port = int(os.environ.get('PORT', 3000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)