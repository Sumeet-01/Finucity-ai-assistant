"""
Flask application factory and extensions initialization.
Author: Sumeet Sangwan
"""
import os
from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user, login_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize extensions globally
db = SQLAlchemy()
migrate = Migrate()
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
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    limiter.init_app(app) # CORRECTED: Limiter is now initialized

    # Import models and define the user loader
    from . import models
    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    # Register blueprints for modular parts of the app
    from .routes import auth_bp, api_bp, chat_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(chat_bp)

    # Define main page routes directly on the app to solve BuildErrors
    @app.route('/', endpoint='home')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('chat.chat_home'))
        return render_template('index.html')

    @app.route('/profile', endpoint='profile')
    @login_required
    def profile():
        return render_template('profile.html', user=current_user)

    @app.route('/about', endpoint='about')
    def about():
        return render_template('about.html')

    # Define global error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
        
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Create database tables within the application context
    with app.app_context():
        db.create_all()
        if config_name == 'development' and not models.User.query.first():
            models.create_sample_data()

    return app

