import os
import jwt
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from dotenv import load_dotenv
from supabase import create_client

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

# Initialize Supabase database layer
from finucity.database import supabase_db
from finucity.models import User
supabase_db.init_app(app)

# Blueprints
from finucity.routes import main_bp, auth_bp, api_bp
from finucity.chat_routes import chat_bp
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)
app.register_blueprint(chat_bp)

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

# Supabase helpers
def decode_supabase_jwt(auth_header: str):
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.replace("Bearer ", "")
    try:
        return jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], options={"verify_aud": False})
    except Exception:
        return None

def get_role(user_id: str):
    sb = get_supabase_admin()
    res = sb.table("profiles").select("role").eq("id", user_id).limit(1).execute()
    if res.data:
        return res.data[0].get("role")
    return None

# API: who am I?
@app.route("/api/me", methods=["GET"])
def api_me():
    payload = decode_supabase_jwt(request.headers.get("Authorization", ""))
    if not payload:
        return {"error": "unauthorized"}, 401
    role = get_role(payload["sub"])
    if not role:
        return {"error": "profile not found"}, 404
    return {"id": payload["sub"], "email": payload.get("email"), "role": role}

# Login page (Supabase-driven)
@app.route("/login")
def login_page():
    return render_template("login.html", SUPABASE_URL=SUPABASE_URL, SUPABASE_ANON_KEY=SUPABASE_ANON_KEY)

# OAuth callback page (frontend JS will handle)
@app.route("/auth/callback")
def auth_callback():
    # The page is handled entirely client-side; just render a tiny template
    return render_template("auth_callback.html", SUPABASE_URL=SUPABASE_URL, SUPABASE_ANON_KEY=SUPABASE_ANON_KEY)

# CA dashboard guard (simple token check)
@app.route("/ca/dashboard")
def ca_dashboard():
    payload = decode_supabase_jwt(request.headers.get("Authorization", ""))
    if not payload:
        return redirect("/login")
    role = get_role(payload["sub"])
    if role not in ("ca", "admin"):
        return "Forbidden", 403
    return render_template("ca_dashboard.html")

if __name__ == '__main__':
    print("🚀 Finucity AI Assistant Starting...")
    print("💾 Database: Supabase (PostgreSQL)")
    print("🌐 URL: http://localhost:3000")
    print("✨ Enhanced with advanced chat features")
    print("👨‍💻 Created by Sumeet Sangwan")
    print("🔗 GitHub: https://github.com/Sumeet-01")
    print("")
    
    # Verify Supabase configuration
    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_SERVICE_KEY'):
        print("❌ ERROR: Supabase configuration missing")
        print("   Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env")
        exit(1)
    
    port = int(os.environ.get('PORT', 3000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)