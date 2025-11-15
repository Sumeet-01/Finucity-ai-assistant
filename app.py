"""
Finucity AI Assistant - Entry point
Created by Sumeet Sangwan
GitHub: https://github.com/Sumeet-01
"""

import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from finucity.models import db, User, ChatQuery
from dotenv import load_dotenv
from flask_migrate import Migrate

# Load environment variables with explicit path
env_path = r"D:\Moto Edge 50\Projects\Software engineering projects\Finucity\.env"
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"✅ Loaded .env file from: {env_path}")
else:
    print(f"❌ ERROR: .env file not found at: {env_path}")

# Initialize Flask app
app = Flask(__name__,
            template_folder='finucity/templates',
            static_folder='finucity/static')
            
# Load configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'finucity-secret-key-2025-sumeet-sangwan')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finucity_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)

# Import and register blueprints
from finucity.routes import main_bp, auth_bp, api_bp
from finucity.chat_routes import chat_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)
app.register_blueprint(chat_bp)

# Setup login manager
from flask_login import LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Utility functions for Jinja templates
@app.context_processor
def utility_processor():
    return dict(
        hasattr=hasattr,
        getattr=getattr,
        isinstance=isinstance,
        len=len,
        str=str,
        int=int,
        float=float,
        bool=bool
    )

app.jinja_env.globals.update(
    hasattr=hasattr,
    getattr=getattr,
    isinstance=isinstance,
    len=len,
    str=str,
    int=int,
    float=float,
    bool=bool
)

# Error handlers
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

# Create demo data for development
def create_demo_data():
    """Create demo users and sample data"""
    try:
        # Create admin user
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                first_name='Admin',
                last_name='User',
                email='admin@finucity.com',
                profession='System Administrator',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)

        # Create demo user
        if not User.query.filter_by(username='demo').first():
            demo = User(
                username='demo',
                first_name='Demo',
                last_name='User',
                email='demo@example.com',
                profession='Software Engineer',
                city='Bangalore'
            )
            demo.set_password('demo123')
            db.session.add(demo)

        # Create developer user
        if not User.query.filter_by(username='sumeet').first():
            sumeet = User(
                username='sumeet',
                first_name='Sumeet',
                last_name='Sangwan',
                email='sumeet@example.com',
                profession='AI/ML Engineer & Full Stack Developer',
                city='Pune',
                state='Maharashtra',
                is_admin=True
            )
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
        print("🌐 URL: http://localhost:5000")
        print("✨ Enhanced with advanced chat features")
        print("👨‍💻 Created by Sumeet Sangwan")
        print("🔗 GitHub: https://github.com/Sumeet-01")
        print("\n📋 Demo Login Credentials:")
        print("   Admin: admin / admin123")
        print("   Demo: demo / demo123")
        print("   Developer: sumeet / sumeet123")

    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)