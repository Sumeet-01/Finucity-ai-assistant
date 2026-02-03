"""
CA Ecosystem API Routes
Production-grade endpoints for CA lifecycle management
Author: Sumeet Sangwan (Fintech-grade implementation)
"""

from flask import Blueprint, request, jsonify, current_app, g
from flask_login import login_required, current_user
from functools import wraps
import time
from datetime import datetime
from finucity.services.ca_ecosystem import CAEcosystemService, ComplaintService, DocumentService
from finucity.database import get_supabase

# Create blueprint
ca_ecosystem_bp = Blueprint('ca_ecosystem', __name__, url_prefix='/api/ca-ecosystem')

# =====================================================
# RATE LIMITING & SECURITY DECORATORS
# =====================================================

def rate_limit(max_requests=60, window=60):
    """Simple rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Store request timestamps in memory (for demo - use Redis in production)
            if not hasattr(current_app, 'rate_limit_store'):
                current_app.rate_limit_store = {}
            
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            now = time.time()
            
            # Clean old requests
            if client_ip in current_app.rate_limit_store:
                current_app.rate_limit_store[client_ip] = [
                    req_time for req_time in current_app.rate_limit_store[client_ip]
                    if now - req_time < window
                ]
            else:
                current_app.rate_limit_store[client_ip] = []
            
            # Check limit
            if len(current_app.rate_limit_store[client_ip]) >= max_requests:
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            # Add current request
            current_app.rate_limit_store[client_ip].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def verified_ca_required(f):
    """Decorator to require verified CA access"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'ca' or current_user.verification_status != 'verified':
            return jsonify({'error': 'Verified CA access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def log_client_info():
    """Log client information for audit"""
    g.client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    g.user_agent = request.headers.get('User-Agent', '')

# =====================================================
# CA APPLICATION ENDPOINTS
# =====================================================

@ca_ecosystem_bp.route('/applications', methods=['POST'])
@login_required
@rate_limit(max_requests=5, window=300)  # 5 applications per 5 minutes
def create_ca_application():
    """Create new CA application"""
    try:
        log_client_info()
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['full_name', 'email', 'phone', 'icai_number', 'practice_address']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        application = CAEcosystemService.create_ca_application(current_user.id, data)
        
        if application:
            return jsonify({
                'success': True,
                'application': application,
                'message': 'Application submitted successfully! We will review it within 48 hours.'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create application. Please try again or contact support.'
            }), 500
            
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Validation error: {str(e)}'
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error in create_ca_application: {e}")
        # Check if it's a database table missing error
        error_msg = str(e)
        if 'ca_applications' in error_msg and 'not find' in error_msg:
            return jsonify({
                'success': False,
                'error': 'Database setup incomplete. Please contact administrator to run database migrations.'
            }), 503
        return jsonify({
            'success': False,
            'error': 'Internal server error. Please try again later or contact support if the issue persists.'
        }), 500

@ca_ecosystem_bp.route('/applications', methods=['GET'])
@admin_required
@rate_limit(max_requests=100, window=60)
def get_ca_applications():
    """Get CA applications (admin only)"""
    try:
        log_client_info()
        
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        applications = CAEcosystemService.get_ca_applications(status, limit, offset)
        
        return jsonify({
            'success': True,
            'applications': applications,
            'count': len(applications)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in get_ca_applications: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@ca_ecosystem_bp.route('/applications/<application_id>', methods=['GET'])
@admin_required
def get_ca_application(application_id):
    """Get specific CA application (admin only)"""
    try:
        log_client_info()
        
        application = CAEcosystemService.get_ca_application(application_id)
        
        if application:
            return jsonify({
                'success': True,
                'application': application
            })
        else:
            return jsonify({'error': 'Application not found'}), 404
            
    except Exception as e:
        current_app.logger.error(f"Error in get_ca_application: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@ca_ecosystem_bp.route('/applications/<application_id>/approve', methods=['POST'])
@admin_required
@rate_limit(max_requests=20, window=60)
def approve_ca_application(application_id):
    """Approve CA application (admin only)"""
    try:
        log_client_info()
        
        data = request.get_json() or {}
        notes = data.get('notes', '')
        
        success = CAEcosystemService.approve_ca_application(application_id, current_user.id, notes)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Application approved successfully'
            })
        else:
            return jsonify({'error': 'Failed to approve application'}), 500
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error in approve_ca_application: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@ca_ecosystem_bp.route('/applications/<application_id>/reject', methods=['POST'])
@admin_required
@rate_limit(max_requests=20, window=60)
def reject_ca_application(application_id):
    """Reject CA application (admin only)"""
    try:
        log_client_info()
        
        data = request.get_json()
        if not data or not data.get('reason'):
            return jsonify({'error': 'Rejection reason is required'}), 400
        
        reason = data['reason']
        success = CAEcosystemService.reject_ca_application(application_id, current_user.id, reason)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Application rejected successfully'
            })
        else:
            return jsonify({'error': 'Failed to reject application'}), 500
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error in reject_ca_application: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# CA MANAGEMENT ENDPOINTS
# =====================================================

@ca_ecosystem_bp.route('/verified-cas', methods=['GET'])
@admin_required
def get_verified_cas():
    """Get all verified CAs (admin only)"""
    try:
        log_client_info()
        
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        cas = CAEcosystemService.get_verified_cas(limit, offset)
        
        return jsonify({
            'success': True,
            'cas': cas,
            'count': len(cas)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in get_verified_cas: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@ca_ecosystem_bp.route('/cas/<ca_id>/suspend', methods=['POST'])
@admin_required
@rate_limit(max_requests=10, window=60)
def suspend_ca(ca_id):
    """Suspend a CA (admin only)"""
    try:
        log_client_info()
        
        data = request.get_json()
        if not data or not data.get('reason'):
            return jsonify({'error': 'Suspension reason is required'}), 400
        
        reason = data['reason']
        success = CAEcosystemService.suspend_ca(ca_id, current_user.id, reason)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'CA suspended successfully'
            })
        else:
            return jsonify({'error': 'Failed to suspend CA'}), 500
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error in suspend_ca: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@ca_ecosystem_bp.route('/cas/<ca_id>/reinstate', methods=['POST'])
@admin_required
@rate_limit(max_requests=10, window=60)
def reinstate_ca(ca_id):
    """Reinstate a suspended CA (admin only)"""
    try:
        log_client_info()
        
        data = request.get_json()
        if not data or not data.get('reason'):
            return jsonify({'error': 'Reinstatement reason is required'}), 400
        
        reason = data['reason']
        success = CAEcosystemService.reinstate_ca(ca_id, current_user.id, reason)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'CA reinstated successfully'
            })
        else:
            return jsonify({'error': 'Failed to reinstate CA'}), 500
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error in reinstate_ca: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@ca_ecosystem_bp.route('/cas/<ca_id>/blacklist', methods=['POST'])
@admin_required
@rate_limit(max_requests=5, window=300)  # Very limited
def blacklist_ca(ca_id):
    """Blacklist a CA (admin only) - permanent action"""
    try:
        log_client_info()
        
        data = request.get_json()
        if not data or not data.get('reason'):
            return jsonify({'error': 'Blacklist reason is required'}), 400
        
        reason = data['reason']
        success = CAEcosystemService.blacklist_ca(ca_id, current_user.id, reason)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'CA blacklisted successfully'
            })
        else:
            return jsonify({'error': 'Failed to blacklist CA'}), 500
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error in blacklist_ca: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# STATISTICS ENDPOINTS
# =====================================================

@ca_ecosystem_bp.route('/statistics', methods=['GET'])
@admin_required
def get_ca_statistics():
    """Get CA ecosystem statistics (admin only)"""
    try:
        log_client_info()
        
        stats = CAEcosystemService.get_ca_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in get_ca_statistics: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# AUDIT LOG ENDPOINTS
# =====================================================

@ca_ecosystem_bp.route('/audit-logs', methods=['GET'])
@admin_required
def get_admin_logs():
    """Get admin audit logs (admin only)"""
    try:
        log_client_info()
        
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        admin_id = request.args.get('admin_id')
        action_type = request.args.get('action_type')
        
        logs = CAEcosystemService.get_admin_logs(limit, offset, admin_id, action_type)
        
        return jsonify({
            'success': True,
            'logs': logs,
            'count': len(logs)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in get_admin_logs: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# COMPLAINT ENDPOINTS
# =====================================================

@ca_ecosystem_bp.route('/complaints', methods=['POST'])
@login_required
@rate_limit(max_requests=3, window=300)  # 3 complaints per 5 minutes
def create_complaint():
    """Create new complaint"""
    try:
        log_client_info()
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['against_id', 'complaint_type', 'title', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Field {field} is required'}), 400
        
        complaint = ComplaintService.create_complaint(current_user.id, data)
        
        if complaint:
            return jsonify({
                'success': True,
                'complaint': complaint,
                'message': 'Complaint filed successfully'
            }), 201
        else:
            return jsonify({'error': 'Failed to create complaint'}), 500
            
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error in create_complaint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@ca_ecosystem_bp.route('/complaints', methods=['GET'])
@admin_required
def get_complaints():
    """Get complaints (admin only)"""
    try:
        log_client_info()
        
        status = request.args.get('status')
        priority = request.args.get('priority')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        complaints = ComplaintService.get_complaints(status, priority, limit, offset)
        
        return jsonify({
            'success': True,
            'complaints': complaints,
            'count': len(complaints)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in get_complaints: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# DOCUMENT ENDPOINTS
# =====================================================

@ca_ecosystem_bp.route('/documents/upload', methods=['POST'])
@login_required
@rate_limit(max_requests=10, window=300)
def upload_document():
    """Upload verification document"""
    try:
        log_client_info()
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        document_type = request.form.get('document_type')
        
        if not document_type:
            return jsonify({'error': 'Document type is required'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type and size
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']
        max_size = 10 * 1024 * 1024  # 10MB
        
        if file.content_type not in allowed_types:
            return jsonify({'error': 'Invalid file type. Only PDF, JPEG, PNG allowed'}), 400
        
        file_data = file.read()
        if len(file_data) > max_size:
            return jsonify({'error': 'File too large. Maximum size is 10MB'}), 400
        
        document = DocumentService.upload_document(
            current_user.id, 
            document_type, 
            file_data, 
            file.filename, 
            file.content_type
        )
        
        if document:
            return jsonify({
                'success': True,
                'document': document,
                'message': 'Document uploaded successfully'
            }), 201
        else:
            return jsonify({'error': 'Failed to upload document'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error in upload_document: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@ca_ecosystem_bp.route('/documents', methods=['GET'])
@login_required
def get_user_documents():
    """Get user's documents"""
    try:
        log_client_info()
        
        documents = DocumentService.get_user_documents(current_user.id)
        
        return jsonify({
            'success': True,
            'documents': documents,
            'count': len(documents)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in get_user_documents: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@ca_ecosystem_bp.route('/documents/<document_id>/verify', methods=['POST'])
@admin_required
@rate_limit(max_requests=20, window=60)
def verify_document(document_id):
    """Verify or reject document (admin only)"""
    try:
        log_client_info()
        
        data = request.get_json()
        if not data or not data.get('status'):
            return jsonify({'error': 'Status is required'}), 400
        
        status = data['status']
        reason = data.get('reason', '')
        
        if status not in ['verified', 'rejected']:
            return jsonify({'error': 'Invalid status'}), 400
        
        if status == 'rejected' and not reason:
            return jsonify({'error': 'Rejection reason is required'}), 400
        
        success = DocumentService.verify_document(document_id, current_user.id, status, reason)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Document {status} successfully'
            })
        else:
            return jsonify({'error': 'Failed to verify document'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error in verify_document: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# PLATFORM SETTINGS ENDPOINTS
# =====================================================

@ca_ecosystem_bp.route('/settings', methods=['GET'])
def get_platform_settings():
    """Get public platform settings"""
    try:
        log_client_info()
        
        sb = get_supabase()
        result = sb.table('platform_settings').select('*').eq('is_public', True).execute()
        
        settings = {}
        for item in result.data or []:
            settings[item['key']] = item['value']
        
        return jsonify({
            'success': True,
            'settings': settings
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in get_platform_settings: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@ca_ecosystem_bp.route('/settings', methods=['PUT'])
@admin_required
def update_platform_settings():
    """Update platform settings (admin only)"""
    try:
        log_client_info()
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        sb = get_supabase()
        
        updated_settings = {}
        for key, value in data.items():
            result = sb.table('platform_settings').update({
                'value': value,
                'updated_by': current_user.id,
                'updated_at': datetime.now().isoformat()
            }).eq('key', key).execute()
            
            if result.data:
                updated_settings[key] = value
        
        # Log admin action
        CAEcosystemService.log_admin_action(
            admin_id=current_user.id,
            action_type='system_config',
            target_user_id=None,
            target_type='system',
            target_id=None,
            description=f"Platform settings updated: {', '.join(updated_settings.keys())}"
        )
        
        return jsonify({
            'success': True,
            'updated_settings': updated_settings,
            'message': 'Settings updated successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in update_platform_settings: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# =====================================================
# ERROR HANDLERS
# =====================================================

@ca_ecosystem_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@ca_ecosystem_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@ca_ecosystem_bp.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({'error': 'Rate limit exceeded'}), 429
