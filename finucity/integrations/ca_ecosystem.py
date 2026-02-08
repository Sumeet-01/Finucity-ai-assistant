"""
Finucity CA Ecosystem - Integration Setup
Production-grade CA lifecycle management system
Author: Sumeet Sangwan (Fintech-grade implementation)
"""

import os
from flask import Flask
from finucity.database import supabase_db
from finucity.routes.ca_ecosystem import ca_ecosystem_bp

def register_ca_ecosystem_routes(app):
    """Register CA ecosystem routes with Flask app"""
    
    # Register the CA ecosystem blueprint
    app.register_blueprint(ca_ecosystem_bp)
    
    # Register admin dashboard route
    @app.route('/admin')
    @login_required
    def admin_dashboard():
        """Admin dashboard route"""
        if not current_user.is_admin:
            return render_template('errors/403.html'), 403
        return render_template('admin_dashboard.html')
    
    # Register CA application route
    @app.route('/ca-application')
    @login_required
    def ca_application():
        """CA application route"""
        # Check if user already has an application
        from finucity.services.ca_ecosystem import CAEcosystemService
        
        try:
            applications = CAEcosystemService.get_ca_applications(limit=1)
            user_applications = [app for app in applications if app.get('user_id') == current_user.id]
            
            if user_applications:
                latest_app = user_applications[0]
                if latest_app['status'] in ['pending', 'under_review']:
                    return render_template('ca_application_status.html', application=latest_app)
                elif latest_app['status'] == 'approved':
                    return redirect(url_for('main.user_dashboard'))
        except Exception as e:
            app.logger.error(f"Error checking existing application: {e}")
        
        from datetime import datetime
        return render_template('ca_application.html', current_year=datetime.now().year)
    
    # Register CA application status route
    @app.route('/ca-application-status')
    @login_required
    def ca_application_status():
        """CA application status route"""
        from finucity.services.ca_ecosystem import CAEcosystemService
        
        try:
            applications = CAEcosystemService.get_ca_applications(limit=1)
            user_applications = [app for app in applications if app.get('user_id') == current_user.id]
            
            if not user_applications:
                return redirect(url_for('main.ca_application'))
            
            return render_template('ca_application_status.html', application=user_applications[0])
        except Exception as e:
            app.logger.error(f"Error loading application status: {e}")
            return render_template('ca_application.html'), 500

def setup_ca_ecosystem_middleware(app):
    """Setup middleware for CA ecosystem"""
    
    @app.before_request
    def log_admin_activity():
        """Log admin activity for audit trail"""
        if request.endpoint and request.endpoint.startswith('ca_ecosystem.'):
            # Log API access
            if current_user.is_authenticated and current_user.is_admin:
                from finucity.services.ca_ecosystem import CAEcosystemService
                
                CAEcosystemService.log_admin_action(
                    admin_id=current_user.id,
                    action_type='api_access',
                    target_user_id=None,
                    target_type='api',
                    target_id=request.endpoint,
                    description=f"API access: {request.method} {request.endpoint}",
                    metadata={
                        'ip_address': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
                        'user_agent': request.headers.get('User-Agent'),
                        'method': request.method
                    }
                )
    
    @app.after_request
    def add_security_headers(response):
        """Add security headers for CA ecosystem"""
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add CA ecosystem specific headers for admin routes
        if request.endpoint and request.endpoint.startswith('admin'):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        return response

def initialize_ca_ecosystem(app):
    """Initialize CA ecosystem with Flask app"""
    
    # Register routes
    register_ca_ecosystem_routes(app)
    
    # Setup middleware
    setup_ca_ecosystem_middleware(app)
    
    # Add template context processors
    @app.context_processor
    def inject_ca_ecosystem_vars():
        """Inject CA ecosystem variables into templates"""
        return {
            'ca_ecosystem_enabled': True,
            'current_year': __import__('datetime').datetime.now().year
        }
    
    # Add error handlers for CA ecosystem
    @app.errorhandler(403)
    def ca_ecosystem_forbidden(error):
        """Handle forbidden errors for CA ecosystem"""
        if request.endpoint and request.endpoint.startswith('admin'):
            return render_template('errors/403_admin.html'), 403
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(429)
    def ca_ecosystem_rate_limit(error):
        """Handle rate limiting errors"""
        return render_template('errors/429.html'), 429
    
    app.logger.info("CA Ecosystem initialized successfully")

# Export for use in main app
__all__ = ['initialize_ca_ecosystem']
