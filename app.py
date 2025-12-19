import os, jwt
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from dotenv import load_dotenv
from flask_migrate import Migrate
from supabase import create_client

# Load .env
env_path = r"D:\Moto Edge 50\Projects\Software engineering projects\Finucity\.env"
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✅ Loaded .env file from: {env_path}")
else:
    print(f"❌ ERROR: .env file not found at: {env_path}")

# Supabase config
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
SUPABASE_JWT_SECRET = os.environ["SUPABASE_JWT_SECRET"]

def get_supabase_admin():
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Flask app
app = Flask(__name__, template_folder='finucity/templates', static_folder='finucity/static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'finucity-secret-key-2025-sumeet-sangwan')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finucity_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# DB / Migrate
from finucity.models import db, User, ChatQuery
db.init_app(app)
migrate = Migrate(app, db)

# Blueprints
from finucity.routes import main_bp, auth_bp, api_bp
from finucity.chat_routes import chat_bp
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)
app.register_blueprint(chat_bp)

# Login manager (legacy; Supabase is primary auth for new flow)
from flask_login import LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
    db.session.rollback()
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

# Demo data (legacy)
def create_demo_data():
    try:
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', first_name='Admin', last_name='User', email='admin@finucity.com',
                         profession='System Administrator', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
        if not User.query.filter_by(username='demo').first():
            demo = User(username='demo', first_name='Demo', last_name='User', email='demo@example.com',
                        profession='Software Engineer', city='Bangalore')
            demo.set_password('demo123')
            db.session.add(demo)
        if not User.query.filter_by(username='sumeet').first():
            sumeet = User(username='sumeet', first_name='Sumeet', last_name='Sangwan',
                          email='sumeet@example.com', profession='AI/ML Engineer & Full Stack Developer',
                          city='Pune', state='Maharashtra', is_admin=True)
            sumeet.set_password('sumeet123')
            db.session.add(sumeet)
        db.session.commit()
        print("✅ Demo users created successfully!")
    except Exception as e:
        print(f"Demo data creation error: {e}")
        db.session.rollback()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_demo_data()

        print("🚀 Finucity AI Assistant Starting...")
        print("🌐 URL: http://localhost:3000")
        print("✨ Enhanced with advanced chat features")
        print("👨‍💻 Created by Sumeet Sangwan")
        print("🔗 GitHub: https://github.com/Sumeet-01")

    port = int(os.environ.get('PORT', 3000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)