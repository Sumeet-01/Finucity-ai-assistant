"""
Enhanced CA Ecosystem Services
Production-grade CA lifecycle management with Supabase
Author: Sumeet Sangwan (Fintech-grade implementation)
"""

import os
import json
import hashlib
import uuid
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
from supabase import Client
from flask import current_app, g
import re

class CAEcosystemService:
    """Production-grade CA ecosystem management service"""
    
    @staticmethod
    def get_supabase_admin() -> Client:
        """Get admin Supabase client (bypasses RLS)"""
        from finucity.database import get_supabase
        return get_supabase()
    
    @staticmethod
    def create_ca_application(user_id: str, application_data: Dict) -> Optional[Dict]:
        """Create new CA application with validation"""
        try:
            sb = CAEcosystemService.get_supabase_admin()
            
            # Validate ICAI number format
            icai_number = application_data.get('icai_number', '').upper().strip()
            if not re.match(r'^[A-Z]{3}[0-9]{6}$', icai_number):
                raise ValueError("Invalid ICAI number format. Expected format: ABC123456")
            
            # Check for existing ICAI number
            existing = sb.table('ca_applications').select('id').eq('icai_number', icai_number).execute()
            if existing.data:
                raise ValueError("ICAI number already registered")
            
            # Check for existing application
            existing_app = sb.table('ca_applications').select('id, status').eq('user_id', user_id).execute()
            if existing_app.data:
                app = existing_app.data[0]
                if app['status'] in ['pending', 'under_review']:
                    raise ValueError("Application already in progress")
                elif app['status'] == 'approved':
                    raise ValueError("Already a verified CA")
            
            # Prepare application data
            app_data = {
                'user_id': user_id,
                'full_name': application_data.get('full_name', '').strip(),
                'email': application_data.get('email', '').strip().lower(),
                'phone': application_data.get('phone', '').strip(),
                'icai_number': icai_number,
                'registration_year': application_data.get('registration_year'),
                'experience_years': application_data.get('experience_years', 0),
                'ca_type': application_data.get('ca_type', 'practicing'),
                'firm_name': application_data.get('firm_name', '').strip(),
                'practice_address': application_data.get('practice_address', '').strip(),
                'office_address': application_data.get('office_address', '').strip(),
                'specializations': application_data.get('specializations', []),
                'services': application_data.get('services', []),
                'client_types': application_data.get('client_types', []),
                'documents': application_data.get('documents', {}),
                'status': 'pending',
                'review_deadline': (datetime.now() + timedelta(days=7)).isoformat()
            }
            
            # Validate required fields
            required_fields = ['full_name', 'email', 'phone', 'icai_number', 'practice_address']
            for field in required_fields:
                if not app_data.get(field):
                    raise ValueError(f"Field {field} is required")
            
            # Insert application
            result = sb.table('ca_applications').insert(app_data).execute()
            
            if result.data:
                # Update user role to ca_pending
                sb.table('profiles').update({'role': 'ca_pending'}).eq('id', user_id).execute()
                
                # Log admin action
                CAEcosystemService.log_admin_action(
                    admin_id=user_id,  # Self-application
                    action_type='ca_application_submitted',
                    target_user_id=user_id,
                    target_type='application',
                    target_id=result.data[0]['id'],
                    description=f"CA application submitted for ICAI: {icai_number}"
                )
                
                return result.data[0]
            
            return None
            
        except Exception as e:
            current_app.logger.error(f"Error creating CA application: {e}")
            raise
    
    @staticmethod
    def get_ca_applications(status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get CA applications with filtering"""
        try:
            sb = CAEcosystemService.get_supabase_admin()
            
            query = sb.table('ca_applications').select(
                '*, profiles!ca_applications_user_id_fkey(first_name, last_name, email, phone)'
            ).order('created_at', desc=True)
            
            if status:
                query = query.eq('status', status)
            
            result = query.range(offset, offset + limit - 1).execute()
            return result.data if result.data else []
            
        except Exception as e:
            current_app.logger.error(f"Error getting CA applications: {e}")
            return []
    
    @staticmethod
    def get_ca_application(application_id: str) -> Optional[Dict]:
        """Get specific CA application with user details"""
        try:
            sb = CAEcosystemService.get_supabase_admin()
            
            result = sb.table('ca_applications').select(
                '''*, 
                profiles!ca_applications_user_id_fkey(
                    first_name, last_name, email, phone, created_at
                )'''
            ).eq('id', application_id).limit(1).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            current_app.logger.error(f"Error getting CA application: {e}")
            return None
    
    @staticmethod
    def approve_ca_application(application_id: str, admin_id: str, notes: Optional[str] = None) -> bool:
        """Approve CA application and update user role"""
        try:
            sb = CAEcosystemService.get_supabase_admin()
            
            # Get application
            app = CAEcosystemService.get_ca_application(application_id)
            if not app:
                raise ValueError("Application not found")
            
            if app['status'] != 'pending':
                raise ValueError("Application cannot be approved")
            
            # Update application
            update_data = {
                'status': 'approved',
                'reviewed_by': admin_id,
                'reviewed_at': datetime.now().isoformat(),
                'admin_notes': notes
            }
            
            sb.table('ca_applications').update(update_data).eq('id', application_id).execute()
            
            # Update user profile
            user_update = {
                'role': 'ca',
                'verification_status': 'verified',
                'trust_score': 85,  # Starting trust score
                'profile_completion': 100
            }
            
            sb.table('profiles').update(user_update).eq('id', app['user_id']).execute()
            
            # Log admin action
            CAEcosystemService.log_admin_action(
                admin_id=admin_id,
                action_type='ca_approve',
                target_user_id=app['user_id'],
                target_type='application',
                target_id=application_id,
                description=f"CA application approved for ICAI: {app['icai_number']}",
                reason=notes
            )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error approving CA application: {e}")
            return False
    
    @staticmethod
    def reject_ca_application(application_id: str, admin_id: str, reason: str) -> bool:
        """Reject CA application"""
        try:
            sb = CAEcosystemService.get_supabase_admin()
            
            # Get application
            app = CAEcosystemService.get_ca_application(application_id)
            if not app:
                raise ValueError("Application not found")
            
            if app['status'] not in ['pending', 'under_review']:
                raise ValueError("Application cannot be rejected")
            
            # Update application
            update_data = {
                'status': 'rejected',
                'reviewed_by': admin_id,
                'reviewed_at': datetime.now().isoformat(),
                'rejection_reason': reason
            }
            
            sb.table('ca_applications').update(update_data).eq('id', application_id).execute()
            
            # Update user role back to user
            sb.table('profiles').update({'role': 'user'}).eq('id', app['user_id']).execute()
            
            # Log admin action
            CAEcosystemService.log_admin_action(
                admin_id=admin_id,
                action_type='ca_reject',
                target_user_id=app['user_id'],
                target_type='application',
                target_id=application_id,
                description=f"CA application rejected for ICAI: {app['icai_number']}",
                reason=reason
            )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error rejecting CA application: {e}")
            return False
    
    @staticmethod
    def suspend_ca(ca_id: str, admin_id: str, reason: str) -> bool:
        """Suspend a verified CA"""
        try:
            sb = CAEcosystemService.get_supabase_admin()
            
            # Check if user is verified CA
            ca_user = sb.table('profiles').select('*').eq('id', ca_id).limit(1).execute()
            if not ca_user.data:
                raise ValueError("CA not found")
            
            ca_profile = ca_user.data[0]
            if ca_profile['role'] != 'ca' or ca_profile['verification_status'] != 'verified':
                raise ValueError("User is not a verified CA")
            
            # Update profile
            update_data = {
                'is_suspended': True,
                'suspension_reason': reason,
                'verification_status': 'suspended'
            }
            
            sb.table('profiles').update(update_data).eq('id', ca_id).execute()
            
            # Hold all pending withdrawals
            sb.table('withdrawal_requests').update({'status': 'held'}).eq('ca_id', ca_id).eq('status', 'pending').execute()
            
            # Log admin action
            CAEcosystemService.log_admin_action(
                admin_id=admin_id,
                action_type='ca_suspend',
                target_user_id=ca_id,
                target_type='user',
                target_id=ca_id,
                description=f"CA suspended: {ca_profile['first_name']} {ca_profile['last_name']}",
                reason=reason
            )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error suspending CA: {e}")
            return False
    
    @staticmethod
    def reinstate_ca(ca_id: str, admin_id: str, reason: str) -> bool:
        """Reinstate a suspended CA"""
        try:
            sb = CAEcosystemService.get_supabase_admin()
            
            # Check if user is suspended CA
            ca_user = sb.table('profiles').select('*').eq('id', ca_id).limit(1).execute()
            if not ca_user.data:
                raise ValueError("CA not found")
            
            ca_profile = ca_user.data[0]
            if ca_profile['role'] != 'ca' or not ca_profile['is_suspended']:
                raise ValueError("User is not a suspended CA")
            
            # Update profile
            update_data = {
                'is_suspended': False,
                'suspension_reason': None,
                'verification_status': 'verified'
            }
            
            sb.table('profiles').update(update_data).eq('id', ca_id).execute()
            
            # Release held withdrawals
            sb.table('withdrawal_requests').update({'status': 'pending'}).eq('ca_id', ca_id).eq('status', 'held').execute()
            
            # Log admin action
            CAEcosystemService.log_admin_action(
                admin_id=admin_id,
                action_type='ca_reinstate',
                target_user_id=ca_id,
                target_type='user',
                target_id=ca_id,
                description=f"CA reinstated: {ca_profile['first_name']} {ca_profile['last_name']}",
                reason=reason
            )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error reinstating CA: {e}")
            return False
    
    @staticmethod
    def blacklist_ca(ca_id: str, admin_id: str, reason: str) -> bool:
        """Blacklist a CA (permanent ban)"""
        try:
            sb = CAEcosystemService.get_supabase_admin()
            
            # Get CA profile
            ca_user = sb.table('profiles').select('*').eq('id', ca_id).limit(1).execute()
            if not ca_user.data:
                raise ValueError("CA not found")
            
            ca_profile = ca_user.data[0]
            
            # Update profile
            update_data = {
                'is_suspended': True,
                'suspension_reason': reason,
                'blacklisted_reason': reason,
                'verification_status': 'blacklisted',
                'role': 'user'  # Remove CA role
            }
            
            sb.table('profiles').update(update_data).eq('id', ca_id).execute()
            
            # Reject all pending withdrawals
            sb.table('withdrawal_requests').update({
                'status': 'rejected',
                'rejection_reason': 'Account blacklisted'
            }).eq('ca_id', ca_id).eq('status', 'pending').execute()
            
            # Log admin action
            CAEcosystemService.log_admin_action(
                admin_id=admin_id,
                action_type='ca_blacklist',
                target_user_id=ca_id,
                target_type='user',
                target_id=ca_id,
                description=f"CA blacklisted: {ca_profile['first_name']} {ca_profile['last_name']}",
                reason=reason
            )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error blacklisting CA: {e}")
            return False
    
    @staticmethod
    def get_verified_cas(limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get all verified CAs with statistics"""
        try:
            sb = CAEcosystemService.get_supabase_admin()
            
            result = sb.table('profiles').select('*').eq('role', 'ca').eq('verification_status', 'verified').order('created_at', desc=True).range(offset, offset + limit - 1).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            current_app.logger.error(f"Error getting verified CAs: {e}")
            return []
    
    @staticmethod
    def get_ca_statistics() -> Dict:
        """Get CA ecosystem statistics"""
        try:
            sb = CAEcosystemService.get_supabase_admin()
            
            # Total CAs by status
            total_cas = sb.table('profiles').select('id', count='exact').eq('role', 'ca').execute()
            verified_cas = sb.table('profiles').select('id', count='exact').eq('role', 'ca').eq('verification_status', 'verified').execute()
            suspended_cas = sb.table('profiles').select('id', count='exact').eq('role', 'ca').eq('is_suspended', True).execute()
            
            # Applications by status
            pending_apps = sb.table('ca_applications').select('id', count='exact').eq('status', 'pending').execute()
            approved_apps = sb.table('ca_applications').select('id', count='exact').eq('status', 'approved').execute()
            rejected_apps = sb.table('ca_applications').select('id', count='exact').eq('status', 'rejected').execute()
            
            # Recent activity
            recent_applications = sb.table('ca_applications').select('id, created_at, status').order('created_at', desc=True).limit(10).execute()
            
            return {
                'total_cas': total_cas.count or 0,
                'verified_cas': verified_cas.count or 0,
                'suspended_cas': suspended_cas.count or 0,
                'pending_applications': pending_apps.count or 0,
                'approved_applications': approved_apps.count or 0,
                'rejected_applications': rejected_apps.count or 0,
                'recent_applications': recent_applications.data or []
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting CA statistics: {e}")
            return {}
    
    @staticmethod
    def log_admin_action(admin_id: str, action_type: str, target_user_id: Optional[str], 
                         target_type: str, target_id: Optional[str], description: str,
                         reason: Optional[str] = None, old_values: Optional[Dict] = None,
                         new_values: Optional[Dict] = None) -> bool:
        """Log admin action for audit trail"""
        try:
            sb = CAEcosystemService.get_supabase_admin()
            
            log_data = {
                'admin_id': admin_id,
                'action_type': action_type,
                'target_user_id': target_user_id,
                'target_type': target_type,
                'target_id': target_id,
                'description': description,
                'reason': reason,
                'old_values': old_values or {},
                'new_values': new_values or {},
                'ip_address': getattr(g, 'client_ip', None),
                'user_agent': getattr(g, 'user_agent', None)
            }
            
            sb.table('admin_logs').insert(log_data).execute()
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error logging admin action: {e}")
            return False
    
    @staticmethod
    def get_admin_logs(limit: int = 100, offset: int = 0, admin_id: Optional[str] = None,
                      action_type: Optional[str] = None) -> List[Dict]:
        """Get admin logs with filtering"""
        try:
            sb = CAEcosystemService.get_supabase_admin()
            
            query = sb.table('admin_logs').select(
                '''*, 
                profiles!admin_logs_admin_id_fkey(first_name, last_name),
                target_profiles!admin_logs_target_user_id_fkey(first_name, last_name)'''
            ).order('created_at', desc=True)
            
            if admin_id:
                query = query.eq('admin_id', admin_id)
            
            if action_type:
                query = query.eq('action_type', action_type)
            
            result = query.range(offset, offset + limit - 1).execute()
            return result.data if result.data else []
            
        except Exception as e:
            current_app.logger.error(f"Error getting admin logs: {e}")
            return []

class ComplaintService:
    """Complaint management service"""
    
    @staticmethod
    def create_complaint(reporter_id: str, complaint_data: Dict) -> Optional[Dict]:
        """Create new complaint"""
        try:
            sb = CAEcosystemService.get_supabase_admin()
            
            # Validate complaint data
            required_fields = ['against_id', 'complaint_type', 'title', 'description']
            for field in required_fields:
                if not complaint_data.get(field):
                    raise ValueError(f"Field {field} is required")
            
            # Prevent self-complaint
            if reporter_id == complaint_data['against_id']:
                raise ValueError("Cannot file complaint against yourself")
            
            complaint = {
                'reporter_id': reporter_id,
                'against_id': complaint_data['against_id'],
                'complaint_type': complaint_data['complaint_type'],
                'title': complaint_data['title'].strip(),
                'description': complaint_data['description'].strip(),
                'evidence': complaint_data.get('evidence', []),
                'attachments': complaint_data.get('attachments', []),
                'priority': complaint_data.get('priority', 'medium')
            }
            
            result = sb.table('complaints').insert(complaint).execute()
            
            if result.data:
                # Log the complaint
                CAEcosystemService.log_admin_action(
                    admin_id=reporter_id,
                    action_type='complaint_review',
                    target_user_id=complaint_data['against_id'],
                    target_type='complaint',
                    target_id=result.data[0]['id'],
                    description=f"Complaint filed: {complaint['title']}"
                )
                
                return result.data[0]
            
            return None
            
        except Exception as e:
            current_app.logger.error(f"Error creating complaint: {e}")
            raise
    
    @staticmethod
    def get_complaints(status: Optional[str] = None, priority: Optional[str] = None,
                      limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get complaints with filtering"""
        try:
            sb = CAEcosystemService.get_supabase_admin()
            
            query = sb.table('complaints').select(
                '''*, 
                reporter:profiles!complaints_reporter_id_fkey(first_name, last_name),
                accused:profiles!complaints_against_id_fkey(first_name, last_name)'''
            ).order('created_at', desc=True)
            
            if status:
                query = query.eq('status', status)
            
            if priority:
                query = query.eq('priority', priority)
            
            result = query.range(offset, offset + limit - 1).execute()
            return result.data if result.data else []
            
        except Exception as e:
            current_app.logger.error(f"Error getting complaints: {e}")
            return []

class DocumentService:
    """Document management service for CA verification"""
    
    @staticmethod
    def upload_document(user_id: str, document_type: str, file_data: bytes, 
                       filename: str, mime_type: str) -> Optional[Dict]:
        """Upload document to Supabase Storage and create record"""
        try:
            sb = CAEcosystemService.get_supabase_admin()
            
            # Generate unique file path
            file_ext = filename.split('.')[-1] if '.' in filename else ''
            unique_filename = f"{user_id}_{document_type}_{uuid.uuid4().hex}.{file_ext}"
            file_path = f"ca_documents/{user_id}/{unique_filename}"
            
            # Calculate checksum
            checksum = hashlib.sha256(file_data).hexdigest()
            
            # Upload to Supabase Storage
            storage = sb.storage
            storage.from_('ca_documents').upload(file_path, file_data)
            
            # Create document record
            doc_data = {
                'user_id': user_id,
                'document_type': document_type,
                'document_name': filename,
                'file_path': file_path,
                'file_size': len(file_data),
                'mime_type': mime_type,
                'checksum': checksum
            }
            
            result = sb.table('ca_verification_documents').insert(doc_data).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            current_app.logger.error(f"Error uploading document: {e}")
            raise
    
    @staticmethod
    def get_user_documents(user_id: str) -> List[Dict]:
        """Get all documents for a user"""
        try:
            sb = CAEcosystemService.get_supabase_admin()
            
            result = sb.table('ca_verification_documents').select('*').eq('user_id', user_id).order('uploaded_at', desc=True).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            current_app.logger.error(f"Error getting user documents: {e}")
            return []
    
    @staticmethod
    def verify_document(document_id: str, admin_id: str, status: str, 
                       reason: Optional[str] = None) -> bool:
        """Verify or reject document"""
        try:
            sb = CAEcosystemService.get_supabase_admin()
            
            update_data = {
                'verification_status': status,
                'verified_by': admin_id,
                'verified_at': datetime.now().isoformat()
            }
            
            if status == 'rejected' and reason:
                update_data['rejection_reason'] = reason
            
            sb.table('ca_verification_documents').update(update_data).eq('id', document_id).execute()
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error verifying document: {e}")
            return False

# Export all services
__all__ = [
    'CAEcosystemService',
    'ComplaintService', 
    'DocumentService'
]
