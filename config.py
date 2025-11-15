"""
Enhanced configuration module for Finucity AI
Handles all environment settings and application configuration
Author: Sumeet Sangwan
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    
    # ===== Core Flask Settings =====
    SECRET_KEY = os.getenv('SECRET_KEY', 'finucity-super-secret-key-change-in-production-sumeet-2025')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() in ['true', '1', 'yes']
    
    # ===== Database Configuration =====
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'pool_timeout': 30,
    }
    
    # ===== AI Configuration =====
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    AI_MODEL_NAME = os.getenv('AI_MODEL_NAME', 'llama-3.1-8b-instant')
    AI_MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', '1500'))
    AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', '0.7'))
    
    # ===== Supabase Configuration =====
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
    USE_SUPABASE = os.getenv('USE_SUPABASE', 'false').lower() in ['true', '1', 'yes']
    SUPABASE_DATABASE_URL = os.getenv('SUPABASE_DATABASE_URL')
    
    # ===== Email Configuration =====
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', '1', 'yes']
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@finucity.com')
    
    # ===== Application Features =====
    ENABLE_REGISTRATION = os.getenv('ENABLE_REGISTRATION', 'true').lower() in ['true', '1', 'yes']
    ENABLE_EMAIL_VERIFICATION = os.getenv('ENABLE_EMAIL_VERIFICATION', 'false').lower() in ['true', '1', 'yes']
    ENABLE_TWO_FACTOR_AUTH = os.getenv('ENABLE_TWO_FACTOR_AUTH', 'false').lower() in ['true', '1', 'yes']
    ENABLE_ANALYTICS = os.getenv('ENABLE_ANALYTICS', 'true').lower() in ['true', '1', 'yes']
    ENABLE_CONVERSATION_MODE = os.getenv('ENABLE_CONVERSATION_MODE', 'true').lower() in ['true', '1', 'yes']
    ENABLE_ADMIN_DASHBOARD = os.getenv('ENABLE_ADMIN_DASHBOARD', 'true').lower() in ['true', '1', 'yes']
    
    # ===== Chat & Conversation Limits =====
    FREE_MESSAGES_LIMIT = int(os.getenv('FREE_MESSAGES_LIMIT', '50'))
    MAX_CONVERSATIONS_PER_USER = int(os.getenv('MAX_CONVERSATIONS_PER_USER', '100'))
    MAX_MESSAGES_PER_CONVERSATION = int(os.getenv('MAX_MESSAGES_PER_CONVERSATION', '500'))
    
    # ===== Security Configuration =====
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'finucity-jwt-secret-sumeet-2025')
    WTF_CSRF_ENABLED = os.getenv('WTF_CSRF_ENABLED', 'false').lower() in ['true', '1', 'yes']
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() in ['true', '1', 'yes']
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'true').lower() in ['true', '1', 'yes']
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # ===== Rate Limiting =====
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '1000 per hour')
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    
    # ===== File Upload Configuration =====
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '16777216'))  # 16MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'txt,pdf,png,jpg,jpeg,gif,doc,docx,xls,xlsx').split(','))
    
    # ===== Logging Configuration =====
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/finucity.log')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '10485760'))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # ===== Application Metadata =====
    APP_NAME = os.getenv('APP_NAME', 'Finucity')
    APP_VERSION = os.getenv('APP_VERSION', '2.0.0')
    APP_DESCRIPTION = os.getenv('APP_DESCRIPTION', 'Your Trusted AI Chartered Accountant')
    APP_AUTHOR = os.getenv('APP_AUTHOR', 'Sumeet Sangwan')
    APP_EMAIL = os.getenv('APP_EMAIL', 'contact@finucity.com')
    APP_URL = os.getenv('APP_URL', 'https://finucity.com')
    GITHUB_URL = os.getenv('GITHUB_URL', 'https://github.com/Sumeet-01')
    
    # ===== Cache Configuration =====
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))
    
    # ===== External APIs =====
    STOCK_API_KEY = os.getenv('STOCK_API_KEY')
    CURRENCY_API_KEY = os.getenv('CURRENCY_API_KEY')
    
    # Government API URLs
    INCOME_TAX_API_URL = os.getenv('INCOME_TAX_API_URL', 'https://www.incometax.gov.in/iec/foportal')
    GST_API_URL = os.getenv('GST_API_URL', 'https://services.gst.gov.in/services')
    RBI_API_URL = os.getenv('RBI_API_URL', 'https://api.rbi.org.in')
    SEBI_API_URL = os.getenv('SEBI_API_URL', 'https://www.sebi.gov.in')
    EPFO_API_URL = os.getenv('EPFO_API_URL', 'https://www.epfindia.gov.in')
    
    # ===== Development & Testing =====
    TESTING = os.getenv('TESTING', 'false').lower() in ['true', '1', 'yes']
    DEBUG_TOOLBAR = os.getenv('DEBUG_TOOLBAR', 'true').lower() in ['true', '1', 'yes']
    
    # ===== Analytics & Monitoring =====
    ENABLE_USER_ANALYTICS = os.getenv('ENABLE_USER_ANALYTICS', 'true').lower() in ['true', '1', 'yes']
    ENABLE_PERFORMANCE_MONITORING = os.getenv('ENABLE_PERFORMANCE_MONITORING', 'true').lower() in ['true', '1', 'yes']
    ENABLE_ERROR_TRACKING = os.getenv('ENABLE_ERROR_TRACKING', 'true').lower() in ['true', '1', 'yes']
    
    # ===== Feature Flags =====
    ENABLE_CONVERSATION_EXPORT = os.getenv('ENABLE_CONVERSATION_EXPORT', 'true').lower() in ['true', '1', 'yes']
    ENABLE_CONVERSATION_SHARING = os.getenv('ENABLE_CONVERSATION_SHARING', 'true').lower() in ['true', '1', 'yes']
    ENABLE_DARK_MODE = os.getenv('ENABLE_DARK_MODE', 'true').lower() in ['true', '1', 'yes']
    ENABLE_MOBILE_APP_API = os.getenv('ENABLE_MOBILE_APP_API', 'true').lower() in ['true', '1', 'yes']
    ENABLE_BULK_OPERATIONS = os.getenv('ENABLE_BULK_OPERATIONS', 'true').lower() in ['true', '1', 'yes']
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        pass

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Database - Use SQLite for development
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL', 'sqlite:///finucity_dev.db')
    
    # Relaxed security for development
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    
    # Enhanced logging for development
    LOG_LEVEL = 'DEBUG'
    
    # Enable development tools
    DEBUG_TOOLBAR = True
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Development-specific initialization
        print("🚀 Finucity AI - Development Mode")
        print(f"📊 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"🤖 AI Model: {app.config['AI_MODEL_NAME']}")
        print(f"🔑 Groq API: {'✅ Configured' if app.config['GROQ_API_KEY'] else '❌ Missing'}")

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # Use in-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False
    
    # Fast password hashing for tests
    BCRYPT_LOG_ROUNDS = 4
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        print("🧪 Finucity AI - Testing Mode")

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Database - Use PostgreSQL/Supabase for production
    SQLALCHEMY_DATABASE_URI = (
        os.getenv('SUPABASE_DATABASE_URL') if Config.USE_SUPABASE 
        else os.getenv('DATABASE_URL', 'postgresql://localhost/finucity_prod')
    )
    
    # Enhanced security for production
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # Production logging
    LOG_LEVEL = 'INFO'
    
    # Disable debug toolbar
    DEBUG_TOOLBAR = False
    
    # Stricter rate limiting
    RATELIMIT_DEFAULT = '500 per hour'
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Production-specific initialization
        print("🏭 Finucity AI - Production Mode")
        
        # Ensure critical config is set
        critical_settings = ['SECRET_KEY', 'GROQ_API_KEY']
        missing_settings = [setting for setting in critical_settings if not os.getenv(setting)]
        
        if missing_settings:
            print(f"❌ Critical settings missing: {', '.join(missing_settings)}")
            raise RuntimeError(f"Missing critical production settings: {missing_settings}")
        
        # Import logging for production
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Setup file handler
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Finucity AI Production Startup')

class StagingConfig(ProductionConfig):
    """Staging configuration - similar to production but with debug info"""
    DEBUG = True
    
    # Use staging database
    SQLALCHEMY_DATABASE_URI = os.getenv('STAGING_DATABASE_URL', 
                                       'postgresql://localhost/finucity_staging')
    
    # Less strict rate limiting for staging
    RATELIMIT_DEFAULT = '1000 per hour'
    
    @staticmethod
    def init_app(app):
        ProductionConfig.init_app(app)
        print("🎭 Finucity AI - Staging Mode")

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Helper functions for configuration management

def get_config_class():
    """Get configuration class based on environment"""
    env = os.getenv('FLASK_ENV', 'development').lower()
    return config.get(env, config['default'])

def validate_config():
    """Validate current configuration"""
    issues = []
    
    # Check critical environment variables
    critical_vars = ['SECRET_KEY', 'GROQ_API_KEY']
    for var in critical_vars:
        if not os.getenv(var):
            issues.append(f"Missing environment variable: {var}")
    
    # Check database URL format
    db_url = os.getenv('SQLALCHEMY_DATABASE_URI') or os.getenv('DATABASE_URL')
    if db_url and not any(db_url.startswith(prefix) for prefix in ['sqlite://', 'postgresql://', 'mysql://']):
        issues.append("Invalid database URL format")
    
    # Check AI configuration
    try:
        ai_temp = float(os.getenv('AI_TEMPERATURE', '0.7'))
        if not (0.0 <= ai_temp <= 2.0):
            issues.append("AI_TEMPERATURE should be between 0.0 and 2.0")
    except ValueError:
        issues.append("AI_TEMPERATURE should be a valid float")
    
    try:
        max_tokens = int(os.getenv('AI_MAX_TOKENS', '1500'))
        if not (100 <= max_tokens <= 4000):
            issues.append("AI_MAX_TOKENS should be between 100 and 4000")
    except ValueError:
        issues.append("AI_MAX_TOKENS should be a valid integer")
    
    return issues

def print_config_summary():
    """Print configuration summary for debugging"""
    config_class = get_config_class()
    
    print("\n" + "="*50)
    print("📋 FINUCITY AI CONFIGURATION SUMMARY")
    print("="*50)
    
    print(f"🌍 Environment: {os.getenv('FLASK_ENV', 'development').upper()}")
    print(f"📦 Configuration: {config_class.__name__}")
    print(f"🔒 Debug Mode: {config_class.DEBUG}")
    print(f"🧪 Testing Mode: {config_class.TESTING}")
    
    print("\n🤖 AI Configuration:")
    print(f"   Model: {config_class.AI_MODEL_NAME}")
    print(f"   Max Tokens: {config_class.AI_MAX_TOKENS}")
    print(f"   Temperature: {config_class.AI_TEMPERATURE}")
    print(f"   API Key: {'✅ Set' if config_class.GROQ_API_KEY else '❌ Missing'}")
    
    print(f"\n🗄️ Database:")
    db_url = getattr(config_class, 'SQLALCHEMY_DATABASE_URI', 'Not set')
    if 'sqlite' in db_url:
        print(f"   Type: SQLite")
        print(f"   Path: {db_url.replace('sqlite:///', '')}")
    elif 'postgresql' in db_url:
        print(f"   Type: PostgreSQL")
        print(f"   URL: {db_url.split('@')[1] if '@' in db_url else 'Not configured'}")
    else:
        print(f"   URL: {db_url}")
    
    print(f"\n🔧 Features:")
    print(f"   Registration: {'✅' if config_class.ENABLE_REGISTRATION else '❌'}")
    print(f"   Email Verification: {'✅' if config_class.ENABLE_EMAIL_VERIFICATION else '❌'}")
    print(f"   Analytics: {'✅' if config_class.ENABLE_ANALYTICS else '❌'}")
    print(f"   Admin Dashboard: {'✅' if config_class.ENABLE_ADMIN_DASHBOARD else '❌'}")
    
    print(f"\n📊 Limits:")
    print(f"   Free Messages: {config_class.FREE_MESSAGES_LIMIT}")
    print(f"   Max Conversations: {config_class.MAX_CONVERSATIONS_PER_USER}")
    print(f"   Rate Limit: {config_class.RATELIMIT_DEFAULT}")
    
    print(f"\n🔐 Security:")
    print(f"   CSRF Protection: {'✅' if config_class.WTF_CSRF_ENABLED else '❌'}")
    print(f"   Secure Cookies: {'✅' if config_class.SESSION_COOKIE_SECURE else '❌'}")
    print(f"   HTTP Only Cookies: {'✅' if config_class.SESSION_COOKIE_HTTPONLY else '❌'}")
    
    # Validate configuration
    issues = validate_config()
    if issues:
        print(f"\n⚠️ Configuration Issues:")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print(f"\n✅ Configuration validated successfully!")
    
    print("=" * 50 + "\n")

def create_env_template():
    """Create a template .env file with all available options"""
    template = """# ==========================================
# Finucity AI - Environment Configuration
# Created by: Sumeet Sangwan (@Sumeet-01)
# AI Chartered Accountant Platform
# ==========================================

# Flask Environment
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-super-secret-key-here

# Database Configuration
DATABASE_URL=sqlite:///finucity.db
DEV_DATABASE_URL=sqlite:///finucity_dev.db

# Supabase Configuration (Optional)
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key
USE_SUPABASE=false
SUPABASE_DATABASE_URL=postgresql://postgres.your-supabase-project:[PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres

# ==========================================
# AI Configuration - GROQ LLaMA
# ==========================================
GROQ_API_KEY=your-groq-api-key-here
AI_MODEL_NAME=llama-3.1-8b-instant
AI_MAX_TOKENS=1500
AI_TEMPERATURE=0.7

# ==========================================
# Email Configuration
# ==========================================
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_DEFAULT_SENDER=noreply@finucity.com

# ==========================================
# Application Features
# ==========================================
ENABLE_REGISTRATION=true
ENABLE_EMAIL_VERIFICATION=false
ENABLE_TWO_FACTOR_AUTH=false
ENABLE_ANALYTICS=true
ENABLE_CONVERSATION_MODE=true
ENABLE_ADMIN_DASHBOARD=true

# ==========================================
# Chat & Conversation Limits
# ==========================================
FREE_MESSAGES_LIMIT=50
MAX_CONVERSATIONS_PER_USER=100
MAX_MESSAGES_PER_CONVERSATION=500

# ==========================================
# Security Configuration
# ==========================================
JWT_SECRET_KEY=your-jwt-secret-key
WTF_CSRF_ENABLED=false
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_HTTPONLY=true

# ==========================================
# Rate Limiting
# ==========================================
RATELIMIT_DEFAULT=1000 per hour
RATELIMIT_STORAGE_URL=memory://

# ==========================================
# File Upload Configuration
# ==========================================
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=uploads
ALLOWED_EXTENSIONS=txt,pdf,png,jpg,jpeg,gif,doc,docx,xls,xlsx

# ==========================================
# Logging Configuration
# ==========================================
LOG_LEVEL=DEBUG
LOG_FILE=logs/finucity.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5

# ==========================================
# Application Metadata
# ==========================================
APP_NAME=Finucity
APP_VERSION=2.0.0
APP_DESCRIPTION=Your Trusted AI Chartered Accountant
APP_AUTHOR=Sumeet Sangwan
APP_EMAIL=contact@finucity.com
APP_URL=https://finucity.com
GITHUB_URL=https://github.com/Sumeet-01

# ==========================================
# Cache Configuration
# ==========================================
CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=300

# ==========================================
# External APIs (Optional)
# ==========================================
STOCK_API_KEY=your_alpha_vantage_key_here
CURRENCY_API_KEY=your_currency_api_key_here

# Government API URLs
INCOME_TAX_API_URL=https://www.incometax.gov.in/iec/foportal
GST_API_URL=https://services.gst.gov.in/services
RBI_API_URL=https://api.rbi.org.in
SEBI_API_URL=https://www.sebi.gov.in
EPFO_API_URL=https://www.epfindia.gov.in

# ==========================================
# Development & Testing
# ==========================================
TESTING=false
DEBUG_TOOLBAR=true

# ==========================================
# Analytics & Monitoring
# ==========================================
ENABLE_USER_ANALYTICS=true
ENABLE_PERFORMANCE_MONITORING=true
ENABLE_ERROR_TRACKING=true

# ==========================================
# Feature Flags
# ==========================================
ENABLE_CONVERSATION_EXPORT=true
ENABLE_CONVERSATION_SHARING=true
ENABLE_DARK_MODE=true
ENABLE_MOBILE_APP_API=true
ENABLE_BULK_OPERATIONS=true

# ==========================================
# Production Overrides (when FLASK_ENV=production)
# ==========================================
# DATABASE_URL=postgresql://finucity_user:secure_password@localhost/finucity_prod
# USE_SUPABASE=true
# SESSION_COOKIE_SECURE=true
# LOG_LEVEL=INFO
# DEBUG=false
# RATELIMIT_DEFAULT=500 per hour
"""
    
    return template

# Configuration validation and setup utilities
class ConfigValidator:
    """Utility class for configuration validation"""
    
    @staticmethod
    def validate_database_url(url):
        """Validate database URL format"""
        if not url:
            return False, "Database URL is required"
        
        valid_prefixes = ['sqlite://', 'postgresql://', 'mysql://']
        if not any(url.startswith(prefix) for prefix in valid_prefixes):
            return False, f"Database URL must start with one of: {', '.join(valid_prefixes)}"
        
        return True, "Database URL is valid"
    
    @staticmethod
    def validate_groq_api_key(api_key):
        """Validate Groq API key format"""
        if not api_key:
            return False, "Groq API key is required for AI functionality"
        
        if not api_key.startswith('gsk_'):
            return False, "Groq API key should start with 'gsk_'"
        
        if len(api_key) < 50:
            return False, "Groq API key appears to be too short"
        
        return True, "Groq API key format is valid"
    
    @staticmethod
    def validate_email_config(server, port, username, password):
        """Validate email configuration"""
        if not all([server, port, username, password]):
            return False, "All email configuration fields are required"
        
        try:
            port = int(port)
            if not (1 <= port <= 65535):
                return False, "Email port must be between 1 and 65535"
        except ValueError:
            return False, "Email port must be a valid integer"
        
        if '@' not in username:
            return False, "Email username should be a valid email address"
        
        return True, "Email configuration is valid"
    
    @classmethod
    def validate_all(cls, config_obj):
        """Validate all configuration settings"""
        results = []
        
        # Validate database
        db_url = getattr(config_obj, 'SQLALCHEMY_DATABASE_URI', None)
        valid, msg = cls.validate_database_url(db_url)
        results.append(('Database', valid, msg))
        
        # Validate Groq API
        api_key = getattr(config_obj, 'GROQ_API_KEY', None)
        valid, msg = cls.validate_groq_api_key(api_key)
        results.append(('Groq API', valid, msg))
        
        # Validate email (if configured)
        mail_server = getattr(config_obj, 'MAIL_SERVER', None)
        mail_port = getattr(config_obj, 'MAIL_PORT', None)
        mail_username = getattr(config_obj, 'MAIL_USERNAME', None)
        mail_password = getattr(config_obj, 'MAIL_PASSWORD', None)
        
        if any([mail_server, mail_port, mail_username, mail_password]):
            valid, msg = cls.validate_email_config(mail_server, mail_port, mail_username, mail_password)
            results.append(('Email', valid, msg))
        
        return results

# Entry point function for configuration management
def main():
    """Main function for configuration management CLI"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'validate':
            print("Validating configuration...")
            issues = validate_config()
            if issues:
                print("Configuration issues found:")
                for issue in issues:
                    print(f"  - {issue}")
                sys.exit(1)
            else:
                print("Configuration is valid!")
        
        elif command == 'summary':
            print_config_summary()
        
        elif command == 'template':
            template = create_env_template()
            with open('.env.template', 'w') as f:
                f.write(template)
            print("Created .env.template file")
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: validate, summary, template")
            sys.exit(1)
    else:
        print_config_summary()

if __name__ == '__main__':
    main()