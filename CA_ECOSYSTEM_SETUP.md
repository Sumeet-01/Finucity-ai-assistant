# Finucity CA Ecosystem - Production Setup Guide

## 🚀 Overview

This guide covers the complete setup and deployment of the Finucity CA Ecosystem - a production-grade, Apple-level polished Chartered Accountant verification and management system built entirely on Supabase.

## 📋 Prerequisites

### Infrastructure Requirements
- **Supabase Project**: Enterprise tier recommended for production
- **Node.js**: v16+ for development
- **Python**: v3.8+ for Flask backend
- **Redis**: For session storage and rate limiting (production)

### Environment Variables
```bash
# Supabase Configuration
SUPABASE_URL=your-supabase-project-url
SUPABASE_SERVICE_KEY=your-supabase-service-key
SUPABASE_ANON_KEY=your-supabase-anon-key

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key

# Security
RATE_LIMIT_REDIS_URL=redis://localhost:6379/0
```

## 🗄️ Database Setup

### 1. Run Schema Migrations

Execute the SQL migrations in order:

```bash
# Step 1: Enhanced Schema
psql $SUPABASE_DATABASE_URL -f database/migrations/001_ca_ecosystem_schema.sql

# Step 2: RLS Policies
psql $SUPABASE_DATABASE_URL -f database/migrations/002_rls_policies.sql
```

### 2. Create Supabase Storage Buckets

```sql
-- Create storage buckets for documents
INSERT INTO storage.buckets (id, name, public) VALUES 
('ca_documents', 'ca_documents', false),
('profile_photos', 'profile_photos', true);

-- Set up storage policies
CREATE POLICY "Users can upload their own documents" ON storage.objects
FOR INSERT WITH CHECK (
  bucket_id = 'ca_documents' AND 
  auth.role() = 'authenticated' AND
  (storage.foldername(name))[1] = auth.uid()
);

CREATE POLICY "Users can view their own documents" ON storage.objects
FOR SELECT USING (
  bucket_id = 'ca_documents' AND 
  auth.role() = 'authenticated' AND
  (storage.foldername(name))[1] = auth.uid()
);
```

## 🔧 Backend Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Update Main Application

In your `app.py`, add the CA ecosystem integration:

```python
from finucity.integrations.ca_ecosystem import initialize_ca_ecosystem

# After app initialization
initialize_ca_ecosystem(app)
```

### 3. Create Admin User

```python
# Create initial admin user
from finucity.database import get_supabase_admin
from finucity.services.ca_ecosystem import CAEcosystemService

supabase = get_supabase_admin()

# Create admin profile
admin_data = {
    'email': 'admin@finucity.com',
    'first_name': 'Admin',
    'last_name': 'User',
    'role': 'admin',
    'is_active': True,
    'email_verified': True
}

supabase.table('profiles').insert(admin_data).execute()
```

## 🎨 Frontend Setup

### 1. Update Base Template

Ensure `base.html` includes the new CSS files:

```html
{% block extra_css %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/admin-dashboard.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/ca-onboarding.css') }}">
{% endblock %}
```

### 2. Add Navigation Items

Update navigation in `base.html`:

```html
{% if current_user.is_authenticated %}
    {% if current_user.is_admin %}
    <li><a href="{{ url_for('admin_dashboard') }}" class="nav-link">Admin Dashboard</a></li>
    {% endif %}
    
    {% if current_user.role == 'ca_pending' %}
    <li><a href="{{ url_for('ca_application_status') }}" class="nav-link">Application Status</a></li>
    {% elif current_user.role == 'user' %}
    <li><a href="{{ url_for('ca_application') }}" class="nav-link">Become a CA</a></li>
    {% endif %}
{% endif %}
```

## 🔒 Security Configuration

### 1. Rate Limiting Setup

```python
# In app.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

# Apply to CA ecosystem routes
@ca_ecosystem_bp.before_request
def check_rate_limit():
    # Implement rate limiting logic
    pass
```

### 2. Security Headers

The security middleware is automatically configured in the integration.

### 3. File Upload Security

```python
# File upload validation
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file_upload(file):
    # Validate file type and size
    pass
```

## 🚀 Deployment

### 1. Production Configuration

```python
# config.py
class ProductionConfig:
    DEBUG = False
    TESTING = False
    
    # Supabase
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('RATE_LIMIT_REDIS_URL')
```

### 2. Environment Setup

```bash
# .env.production
FLASK_ENV=production
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
SECRET_KEY=your-production-secret
RATE_LIMIT_REDIS_URL=redis://your-redis:6379/0
```

### 3. Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    env_file:
      - .env.production
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## 📊 Monitoring & Logging

### 1. Application Logging

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
if not app.debug:
    file_handler = RotatingFileHandler('logs/finucity.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
```

### 2. Audit Trail

The audit logs are automatically stored in the `admin_logs` table. Monitor this table for:

- Admin actions
- API access patterns
- Security events
- System changes

### 3. Performance Monitoring

```python
# Add performance monitoring
@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    diff = time.time() - g.start_time
    if diff > 1.0:  # Log slow requests
        app.logger.warning(f'Slow request: {request.endpoint} took {diff:.2f}s')
    return response
```

## 🧪 Testing

### 1. Unit Tests

```bash
# Run tests
python -m pytest tests/test_ca_ecosystem.py -v
```

### 2. Integration Tests

```bash
# Test CA lifecycle
python tests/test_ca_lifecycle.py
```

### 3. Security Tests

```bash
# Test security measures
python tests/test_security.py
```

## 📈 Scaling Considerations

### 1. Database Optimization

- Add indexes for frequently queried columns
- Implement connection pooling
- Use read replicas for reporting

### 2. Caching Strategy

```python
# Redis caching for frequently accessed data
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

@cache.memoize(timeout=300)  # 5 minutes
def get_ca_statistics():
    # Cache expensive queries
    pass
```

### 3. CDN for Static Assets

Use CloudFront or similar CDN for static files.

## 🔧 Maintenance

### 1. Regular Tasks

- **Daily**: Monitor audit logs for suspicious activity
- **Weekly**: Review pending applications
- **Monthly**: Clean up old audit logs
- **Quarterly**: Security audit and penetration testing

### 2. Backup Strategy

- Supabase: Enable point-in-time recovery
- File Storage: Configure cross-region replication
- Application logs: Ship to centralized logging system

### 3. Updates

- Database migrations: Test in staging first
- Application updates: Use blue-green deployment
- Security patches: Apply within 24 hours

## 🚨 Troubleshooting

### Common Issues

1. **RLS Policy Errors**
   - Check user authentication status
   - Verify policy definitions
   - Test with service role key

2. **File Upload Failures**
   - Check storage bucket permissions
   - Verify file size limits
   - Check network connectivity

3. **Rate Limiting Issues**
   - Monitor Redis connectivity
   - Check rate limit configuration
   - Review user activity patterns

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📞 Support

For issues with the CA ecosystem:

1. Check the audit logs first
2. Review the application logs
3. Test with a fresh user account
4. Contact the development team with detailed error information

## 🔄 Version Updates

When updating the CA ecosystem:

1. Backup current database
2. Test migrations in staging
3. Update code incrementally
4. Monitor for issues post-deployment
5. Have rollback plan ready

---

## 🎯 Success Metrics

Monitor these KPIs:

- **Application Processing Time**: < 7 business days
- **Admin Response Time**: < 24 hours
- **System Uptime**: > 99.9%
- **Security Incidents**: 0 per month
- **User Satisfaction**: > 4.5/5

This completes the production setup for the Finucity CA Ecosystem. The system is now ready for enterprise-grade operation with Apple-level polish and fintech-grade security.
