"""
Flask application factory and extensions initialization.
Author: Sumeet Sangwan
"""
import os
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user, login_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize extensions globally
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)

# Configure login manager
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app(config_name=None):
    """Application factory pattern."""
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration
    config_name = os.environ.get('FLASK_ENV', 'development')
    from config import config
    app.config.from_object(config[config_name])

    # Initialize extensions with the application instance
    login_manager.init_app(app)
    limiter.init_app(app)
    
    # Initialize Supabase database layer
    from .database import supabase_db
    supabase_db.init_app(app)

    # Import models and define the user loader
    from .models import User
    from .database import UserService
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user from Supabase for Flask-Login session"""
        user_data = UserService.get_by_id(user_id)
        if user_data:
            return User(user_data)
        return None

    # Register blueprints for modular parts of the app
    from .routes import main_bp, auth_bp, api_bp
    from .chat_routes import chat_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(chat_bp)

    # Define global error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
        
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    # No database table creation needed - Supabase handles schema
    # Tables are managed via Supabase Dashboard or migrations

    return app

