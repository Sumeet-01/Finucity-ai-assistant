"""
Middleware & Decorators for Finucity
Centralized auth checks, input validation, and request processing
"""

import html
import re
from functools import wraps
from flask import request, jsonify, abort, current_app
from flask_login import current_user


# =====================================================================
# AUTH DECORATORS
# =====================================================================

def admin_required(f):
    """Require admin role for access"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            abort(401)
        if getattr(current_user, 'role', 'user') != 'admin':
            if request.is_json:
                return jsonify({'error': 'Admin access required'}), 403
            abort(403)
        return f(*args, **kwargs)
    return decorated


def ca_required(f):
    """Require CA or admin role for access"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            abort(401)
        if getattr(current_user, 'role', 'user') not in ('ca', 'admin'):
            if request.is_json:
                return jsonify({'error': 'CA access required'}), 403
            abort(403)
        return f(*args, **kwargs)
    return decorated


def api_auth_required(f):
    """Require valid auth for API endpoints (token or session)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        if not getattr(current_user, 'is_active', True):
            return jsonify({
                'success': False,
                'error': 'Account is deactivated'
            }), 403
        return f(*args, **kwargs)
    return decorated


# =====================================================================
# INPUT VALIDATION
# =====================================================================

def sanitize_string(text, max_length=10000):
    """Sanitize string input — escape HTML, enforce length"""
    if not isinstance(text, str):
        return ''
    text = text.strip()
    if len(text) > max_length:
        text = text[:max_length]
    return html.escape(text)


def validate_email(email):
    """Validate email format"""
    if not email or not isinstance(email, str):
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def validate_phone(phone):
    """Validate Indian phone number"""
    if not phone or not isinstance(phone, str):
        return False
    # Remove spaces, dashes, and country code prefix
    cleaned = re.sub(r'[\s\-+]', '', phone)
    if cleaned.startswith('91') and len(cleaned) == 12:
        cleaned = cleaned[2:]
    return bool(re.match(r'^[6-9]\d{9}$', cleaned))


def validate_password_strength(password):
    """Check password meets minimum security requirements"""
    issues = []
    if len(password) < 8:
        issues.append('Password must be at least 8 characters')
    if not re.search(r'[A-Z]', password):
        issues.append('Password must contain at least one uppercase letter')
    if not re.search(r'[a-z]', password):
        issues.append('Password must contain at least one lowercase letter')
    if not re.search(r'\d', password):
        issues.append('Password must contain at least one number')
    return issues


def validate_json_request(*required_fields):
    """Decorator to validate JSON request body has required fields"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'error': 'Content-Type must be application/json'
                }), 400
            
            data = request.get_json(silent=True)
            if data is None:
                return jsonify({
                    'success': False,
                    'error': 'Invalid JSON body'
                }), 400
            
            missing = [f for f in required_fields if not data.get(f)]
            if missing:
                return jsonify({
                    'success': False,
                    'error': f'Missing required fields: {", ".join(missing)}'
                }), 400
            
            return f(*args, **kwargs)
        return decorated
    return decorator


# =====================================================================
# RESPONSE HELPERS
# =====================================================================

def api_success(data=None, message=None, status=200):
    """Standardized success response"""
    response = {'success': True}
    if message:
        response['message'] = message
    if data:
        response['data'] = data
    return jsonify(response), status


def api_error(message, status=400, details=None):
    """Standardized error response"""
    response = {
        'success': False,
        'error': message
    }
    if details and current_app.debug:
        response['details'] = str(details)
    return jsonify(response), status
