"""
Finucity Test Suite
Comprehensive tests for auth, API, chat, and security
"""

import pytest
import os
import json
from unittest.mock import patch, MagicMock

# Set test environment BEFORE importing app
os.environ.setdefault('FLASK_ENV', 'testing')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-testing-only')
os.environ.setdefault('SUPABASE_URL', 'https://test.supabase.co')
os.environ.setdefault('SUPABASE_ANON_KEY', 'test-anon-key')
os.environ.setdefault('SUPABASE_SERVICE_KEY', 'test-service-key')
os.environ.setdefault('SUPABASE_JWT_SECRET', 'test-jwt-secret')
os.environ.setdefault('GROQ_API_KEY', 'gsk_test_key_placeholder_for_testing')
os.environ.setdefault('MAIL_USERNAME', 'test@test.com')
os.environ.setdefault('MAIL_PASSWORD', 'test-password')
os.environ.setdefault('GITHUB_TOKEN', 'test-github-token')
os.environ.setdefault('WTF_CSRF_ENABLED', 'false')


@pytest.fixture
def app():
    """Create and configure test Flask application"""
    with patch('finucity.database.create_client') as mock_supabase:
        mock_client = MagicMock()
        mock_supabase.return_value = mock_client
        
        from app import app as flask_app
        flask_app.config['TESTING'] = True
        flask_app.config['WTF_CSRF_ENABLED'] = False
        flask_app.config['SERVER_NAME'] = 'localhost:5000'
        yield flask_app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create CLI test runner"""
    return app.test_cli_runner()


# =====================================================================
# HEALTH & BASIC ROUTES
# =====================================================================

class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_endpoint(self, client):
        """Health check should return 200 with status"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'finucity'
    
    def test_home_page(self, client):
        """Homepage should return 200"""
        response = client.get('/')
        assert response.status_code == 200


class TestErrorHandlers:
    """Test error handling"""
    
    def test_404_handler(self, client):
        """Non-existent route should return 404"""
        response = client.get('/nonexistent-page-xyz')
        assert response.status_code == 404
    
    def test_405_method_not_allowed(self, client):
        """Wrong method should return 405"""
        response = client.delete('/')
        assert response.status_code == 405


# =====================================================================
# SECURITY HEADERS
# =====================================================================

class TestSecurityHeaders:
    """Verify security headers are set correctly"""
    
    def test_x_content_type_options(self, client):
        """Should have X-Content-Type-Options: nosniff"""
        response = client.get('/health')
        assert response.headers.get('X-Content-Type-Options') == 'nosniff'
    
    def test_x_frame_options(self, client):
        """Should have X-Frame-Options: SAMEORIGIN"""
        response = client.get('/health')
        assert response.headers.get('X-Frame-Options') == 'SAMEORIGIN'
    
    def test_x_xss_protection(self, client):
        """Should have XSS protection header"""
        response = client.get('/health')
        assert response.headers.get('X-XSS-Protection') == '1; mode=block'
    
    def test_referrer_policy(self, client):
        """Should have strict referrer policy"""
        response = client.get('/health')
        assert response.headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'
    
    def test_no_server_header(self, client):
        """Server header should be removed"""
        response = client.get('/health')
        assert response.headers.get('Server') is None


# =====================================================================
# AUTH FLOW TESTS
# =====================================================================

class TestAuthRoutes:
    """Test authentication routes"""
    
    def test_login_page(self, client):
        """Login page should be accessible"""
        response = client.get('/auth/login')
        assert response.status_code == 200
    
    def test_gateway_page(self, client):
        """Gateway page should be accessible"""
        response = client.get('/auth/gateway')
        assert response.status_code == 200
    
    def test_supabase_login_no_token(self, client):
        """Supabase login without token should return 401"""
        response = client.post('/auth/supabase-login')
        assert response.status_code == 401
    
    def test_supabase_login_invalid_token(self, client):
        """Supabase login with invalid token should return 401"""
        response = client.post(
            '/auth/supabase-login',
            headers={'Authorization': 'Bearer invalidtoken123'}
        )
        assert response.status_code == 401
    
    def test_flask_login_missing_fields(self, client):
        """Flask login without email/password should return 400"""
        response = client.post(
            '/auth/flask-login',
            json={'email': '', 'password': ''},
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_protected_route_unauthorized(self, client):
        """Protected routes should redirect unauthenticated users"""
        response = client.get('/chat/')
        # Should redirect to login
        assert response.status_code in (302, 401)
    
    def test_logout_redirects(self, client):
        """Logout should redirect to home"""
        response = client.get('/auth/logout', follow_redirects=False)
        # Should redirect (302) since not logged in
        assert response.status_code in (302, 401)


# =====================================================================
# CHAT API TESTS
# =====================================================================

class TestChatAPI:
    """Test chat API endpoints"""
    
    def test_send_message_unauthenticated(self, client):
        """Chat API should reject unauthenticated requests"""
        response = client.post(
            '/chat/api/send-message',
            json={'message': 'Hello'},
            content_type='application/json'
        )
        assert response.status_code in (302, 401)
    
    def test_conversations_unauthenticated(self, client):
        """Conversations API should reject unauthenticated requests"""
        response = client.get('/chat/api/conversations')
        assert response.status_code in (302, 401)


# =====================================================================
# INPUT VALIDATION TESTS
# =====================================================================

class TestInputValidation:
    """Test input validation and sanitization"""
    
    def test_sanitize_string(self):
        """Test XSS prevention in sanitization"""
        from finucity.middleware import sanitize_string
        
        # XSS attempt should be escaped
        result = sanitize_string('<script>alert("xss")</script>')
        assert '<script>' not in result
        assert '&lt;script&gt;' in result
    
    def test_sanitize_max_length(self):
        """Test string length enforcement"""
        from finucity.middleware import sanitize_string
        
        long_string = 'a' * 20000
        result = sanitize_string(long_string, max_length=100)
        assert len(result) == 100
    
    def test_validate_email_valid(self):
        """Test valid email validation"""
        from finucity.middleware import validate_email
        
        assert validate_email('user@example.com') is True
        assert validate_email('test.user@domain.co.in') is True
    
    def test_validate_email_invalid(self):
        """Test invalid email rejection"""
        from finucity.middleware import validate_email
        
        assert validate_email('') is False
        assert validate_email('notanemail') is False
        assert validate_email('@domain.com') is False
        assert validate_email(None) is False
    
    def test_validate_phone_valid(self):
        """Test valid Indian phone number"""
        from finucity.middleware import validate_phone
        
        assert validate_phone('9876543210') is True
        assert validate_phone('+91 9876543210') is True
    
    def test_validate_phone_invalid(self):
        """Test invalid phone number rejection"""
        from finucity.middleware import validate_phone
        
        assert validate_phone('1234567890') is False  # Starts with 1
        assert validate_phone('123') is False
        assert validate_phone(None) is False
    
    def test_password_strength(self):
        """Test password strength validation"""
        from finucity.middleware import validate_password_strength
        
        # Weak password
        issues = validate_password_strength('abc')
        assert len(issues) > 0
        
        # Strong password
        issues = validate_password_strength('MyStr0ngP@ss')
        assert len(issues) == 0


# =====================================================================
# AI MODULE TESTS
# =====================================================================

class TestAIModule:
    """Test AI module behavior"""
    
    def test_ai_no_hardcoded_keys(self):
        """SECURITY: Verify no hardcoded API keys exist"""
        import finucity.ai as ai_module
        import finucity.ai_providers as ai_providers_module
        import inspect
        
        ai_source = inspect.getsource(ai_module)
        providers_source = inspect.getsource(ai_providers_module)
        
        # Check for hardcoded GitHub tokens
        assert 'ghp_' not in ai_source, "Hardcoded GitHub token found in ai.py!"
        assert 'ghp_' not in providers_source, "Hardcoded GitHub token found in ai_providers.py!"
    
    def test_ai_confidentiality_prompt(self):
        """Verify AI system prompt includes confidentiality policy"""
        from finucity.ai import finucity_ai
        
        prompt = finucity_ai._build_system_prompt('general', {})
        assert 'CONFIDENTIALITY' in prompt
        assert 'MUST NEVER' in prompt
    
    def test_ai_fallback_response(self):
        """Fallback response should work when API is unavailable"""
        from finucity.ai import finucity_ai
        
        response = finucity_ai._generate_fallback_response(
            'How to save tax?', 'income_tax'
        )
        assert response['success'] is True
        assert len(response['response']) > 50
    
    def test_ai_empty_question_handling(self):
        """Empty question should return error response"""
        from finucity.ai import finucity_ai
        
        response = finucity_ai.get_response('')
        assert response['success'] is False
    
    def test_ai_categories_exist(self):
        """All expected categories should be configured"""
        from finucity.ai import get_categories
        
        categories = get_categories()
        expected = ['income_tax', 'gst', 'investment', 'business', 'general']
        for cat in expected:
            assert cat in categories, f"Missing category: {cat}"


# =====================================================================
# DATABASE SERVICE TESTS
# =====================================================================

class TestDatabaseServices:
    """Test database service layer"""
    
    def test_user_model_properties(self):
        """Test User model adapter"""
        from finucity.models import User
        
        user_data = {
            'id': 'test-uuid',
            'email': 'test@example.com',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'user',
            'is_active': True
        }
        
        user = User(user_data)
        assert user.get_id() == 'test-uuid'
        assert user.email == 'test@example.com'
        assert user.is_active is True
        assert user.is_admin is False
        assert user.full_name == 'Test User'
    
    def test_admin_user_detection(self):
        """Test admin role detection"""
        from finucity.models import User
        
        admin_data = {
            'id': 'admin-uuid',
            'email': 'admin@example.com',
            'role': 'admin',
            'is_active': True
        }
        
        admin = User(admin_data)
        assert admin.is_admin is True
        assert admin.is_ca is True  # admin has CA access too
    
    def test_ca_user_detection(self):
        """Test CA role detection"""
        from finucity.models import User
        
        ca_data = {
            'id': 'ca-uuid',
            'email': 'ca@example.com',
            'role': 'ca',
            'is_active': True
        }
        
        ca = User(ca_data)
        assert ca.is_ca is True
        assert ca.is_admin is False


# =====================================================================
# MIDDLEWARE TESTS
# =====================================================================

class TestMiddleware:
    """Test middleware decorators"""
    
    def test_api_success_response(self):
        """api_success should return proper format"""
        from finucity.middleware import api_success
        
        # Need app context for jsonify
        from flask import Flask
        app = Flask(__name__)
        with app.app_context():
            response, status = api_success({'key': 'value'}, 'OK')
            data = response.get_json()
            assert data['success'] is True
            assert data['message'] == 'OK'
            assert status == 200
    
    def test_api_error_response(self):
        """api_error should return proper format"""
        from finucity.middleware import api_error
        
        from flask import Flask
        app = Flask(__name__)
        app.config['DEBUG'] = False
        with app.app_context():
            response, status = api_error('Something failed', 400)
            data = response.get_json()
            assert data['success'] is False
            assert data['error'] == 'Something failed'
            assert status == 400


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
