"""
Enhanced Admin Dashboard Routes
Service management, pricing control, analytics, dispute handling
Author: Sumeet Sangwan
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from functools import wraps
from finucity.database import get_supabase

admin_enhanced_bp = Blueprint('admin_enhanced', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access admin panel', 'error')
            return redirect(url_for('auth.login'))
        if current_user.role != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# =====================================================
# ADMIN DASHBOARD HOME
# =====================================================

@admin_enhanced_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard home - redirect to analytics"""
    return redirect(url_for('admin_enhanced.analytics'))

# =====================================================
# SERVICE CATALOG MANAGEMENT
# =====================================================

@admin_enhanced_bp.route('/services')
@login_required
@admin_required
def manage_services():
    """Manage service catalog"""
    try:
        supabase = get_supabase()
        result = supabase.table('service_catalog')\
            .select('*')\
            .order('category', 'display_order')\
            .execute()
        
        services = result.data if result.data else []
        
        # Group by category
        categorized = {}
        for service in services:
            cat = service['category']
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(service)
        
        return render_template('admin/manage_services.html',
                             services=services,
                             categorized=categorized,
                             page_title='Manage Services')
    except Exception as e:
        flash(f'Error loading services: {str(e)}', 'error')
        return redirect(url_for('admin_enhanced.dashboard'))

@admin_enhanced_bp.route('/services/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_service():
    """Create new service"""
    if request.method == 'POST':
        try:
            data = request.json
            supabase = get_supabase()
            
            service_data = {
                'service_code': data['service_code'],
                'service_name': data['service_name'],
                'display_name': data['display_name'],
                'category': data['category'],
                'sub_category': data.get('sub_category'),
                'short_description': data.get('short_description'),
                'detailed_description': data.get('detailed_description'),
                'features': data.get('features', []),
                'deliverables': data.get('deliverables', []),
                'requirements': data.get('requirements', []),
                'base_price': int(data['base_price']),
                'currency': data.get('currency', 'INR'),
                'pricing_type': data.get('pricing_type', 'fixed'),
                'discount_percentage': int(data.get('discount_percentage', 0)),
                'is_diy_enabled': data.get('is_diy_enabled', False),
                'is_ca_assisted': data.get('is_ca_assisted', True),
                'is_active': data.get('is_active', True),
                'is_featured': data.get('is_featured', False),
                'estimated_days': int(data.get('estimated_days', 3)),
                'created_by': current_user.id
            }
            
            result = supabase.table('service_catalog').insert(service_data).execute()
            
            if result.data:
                return jsonify({'success': True, 'service': result.data[0]})
            else:
                return jsonify({'error': 'Failed to create service'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return render_template('admin/create_service.html',
                         page_title='Create Service')

@admin_enhanced_bp.route('/services/<service_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_service(service_id):
    """Edit existing service"""
    supabase = get_supabase()
    
    if request.method == 'POST':
        try:
            data = request.json
            
            update_data = {
                'service_name': data['service_name'],
                'display_name': data['display_name'],
                'base_price': int(data['base_price']),
                'is_active': data.get('is_active', True),
                'is_featured': data.get('is_featured', False),
                'discount_percentage': int(data.get('discount_percentage', 0)),
                'estimated_days': int(data.get('estimated_days', 3)),
                'short_description': data.get('short_description'),
                'detailed_description': data.get('detailed_description'),
                'features': data.get('features', []),
                'updated_at': datetime.now().isoformat()
            }
            
            result = supabase.table('service_catalog')\
                .update(update_data)\
                .eq('id', service_id)\
                .execute()
            
            if result.data:
                return jsonify({'success': True, 'service': result.data[0]})
            else:
                return jsonify({'error': 'Failed to update service'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # GET request
    try:
        result = supabase.table('service_catalog')\
            .select('*')\
            .eq('id', service_id)\
            .single()\
            .execute()
        
        if result.data:
            return render_template('admin/edit_service.html',
                                 service=result.data,
                                 page_title='Edit Service')
        else:
            flash('Service not found', 'error')
            return redirect(url_for('admin_enhanced.manage_services'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin_enhanced.manage_services'))

@admin_enhanced_bp.route('/services/<service_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_service(service_id):
    """Toggle service active status"""
    try:
        supabase = get_supabase()
        
        # Get current status
        current = supabase.table('service_catalog')\
            .select('is_active')\
            .eq('id', service_id)\
            .single()\
            .execute()
        
        if current.data:
            new_status = not current.data['is_active']
            
            result = supabase.table('service_catalog')\
                .update({'is_active': new_status})\
                .eq('id', service_id)\
                .execute()
            
            return jsonify({
                'success': True,
                'is_active': new_status,
                'message': f'Service {"activated" if new_status else "deactivated"}'
            })
        else:
            return jsonify({'error': 'Service not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =====================================================
# BOOKING MANAGEMENT
# =====================================================

@admin_enhanced_bp.route('/bookings')
@login_required
@admin_required
def manage_bookings():
    """Manage all service bookings"""
    try:
        supabase = get_supabase()
        
        # Get filters from query params
        status = request.args.get('status', 'all')
        search = request.args.get('search', '')
        
        query = supabase.table('service_bookings')\
            .select('*, service_catalog(*), profiles!service_bookings_user_id_fkey(*)')
        
        if status != 'all':
            query = query.eq('status', status)
        
        if search:
            query = query.or_(f'booking_number.ilike.%{search}%')
        
        result = query.order('created_at', desc=True).limit(50).execute()
        
        bookings = result.data if result.data else []
        
        # Get statistics
        stats = supabase.rpc('get_booking_stats').execute()
        
        return render_template('admin/manage_bookings.html',
                             bookings=bookings,
                             stats=stats.data if stats.data else {},
                             current_status=status,
                             page_title='Manage Bookings')
    except Exception as e:
        flash(f'Error loading bookings: {str(e)}', 'error')
        return redirect(url_for('admin_enhanced.dashboard'))

@admin_enhanced_bp.route('/bookings/<booking_id>')
@login_required
@admin_required
def booking_detail(booking_id):
    """View booking details"""
    try:
        supabase = get_supabase()
        result = supabase.table('service_bookings')\
            .select('*, service_catalog(*), profiles!service_bookings_user_id_fkey(*)')\
            .eq('id', booking_id)\
            .single()\
            .execute()
        
        if result.data:
            return render_template('admin/booking_detail.html',
                                 booking=result.data,
                                 page_title=f'Booking {result.data["booking_number"]}')
        else:
            flash('Booking not found', 'error')
            return redirect(url_for('admin_enhanced.manage_bookings'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin_enhanced.manage_bookings'))

@admin_enhanced_bp.route('/bookings/<booking_id>/update-status', methods=['POST'])
@login_required
@admin_required
def update_booking_status(booking_id):
    """Update booking status"""
    try:
        data = request.json
        new_status = data.get('status')
        admin_notes = data.get('admin_notes', '')
        
        supabase = get_supabase()
        
        update_data = {
            'status': new_status,
            'admin_notes': admin_notes,
            'updated_at': datetime.now().isoformat()
        }
        
        # Set specific timestamps based on status
        if new_status == 'in_progress':
            update_data['started_at'] = datetime.now().isoformat()
        elif new_status == 'completed':
            update_data['completed_at'] = datetime.now().isoformat()
        elif new_status == 'cancelled':
            update_data['cancelled_at'] = datetime.now().isoformat()
        
        result = supabase.table('service_bookings')\
            .update(update_data)\
            .eq('id', booking_id)\
            .execute()
        
        if result.data:
            # Create notification for user
            booking = result.data[0]
            supabase.table('notifications').insert({
                'user_id': booking['user_id'],
                'notification_type': 'booking_update',
                'title': 'Booking Status Updated',
                'message': f'Your booking #{booking["booking_number"]} is now {new_status}',
                'booking_id': booking_id
            }).execute()
            
            return jsonify({'success': True, 'booking': booking})
        else:
            return jsonify({'error': 'Failed to update status'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_enhanced_bp.route('/bookings/<booking_id>/assign-ca', methods=['POST'])
@login_required
@admin_required
def assign_ca(booking_id):
    """Assign CA to booking"""
    try:
        data = request.json
        ca_id = data.get('ca_id')
        
        supabase = get_supabase()
        
        result = supabase.table('service_bookings')\
            .update({
                'assigned_ca_id': ca_id,
                'assigned_at': datetime.now().isoformat(),
                'status': 'assigned'
            })\
            .eq('id', booking_id)\
            .execute()
        
        if result.data:
            # Notify CA
            supabase.table('notifications').insert({
                'user_id': ca_id,
                'notification_type': 'ca_assigned',
                'title': 'New Service Assigned',
                'message': f'You have been assigned to booking #{result.data[0]["booking_number"]}',
                'booking_id': booking_id
            }).execute()
            
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to assign CA'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =====================================================
# ANALYTICS DASHBOARD
# =====================================================

@admin_enhanced_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Platform analytics dashboard"""
    try:
        supabase = get_supabase()
        
        # Date range
        days = int(request.args.get('days', 30))
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Revenue metrics
        revenue_result = supabase.table('service_bookings')\
            .select('total_amount, paid_amount, status, created_at')\
            .gte('created_at', start_date)\
            .execute()
        
        bookings = revenue_result.data if revenue_result.data else []
        
        total_revenue = sum(b['paid_amount'] for b in bookings if b['paid_amount'])
        pending_revenue = sum(b['total_amount'] - b['paid_amount'] 
                            for b in bookings if b['total_amount'] > b['paid_amount'])
        total_bookings = len(bookings)
        
        # Service popularity
        service_stats = {}
        for booking in bookings:
            service_name = booking.get('service_id', 'Unknown')
            service_stats[service_name] = service_stats.get(service_name, 0) + 1
        
        # User growth
        user_result = supabase.table('profiles')\
            .select('created_at')\
            .gte('created_at', start_date)\
            .execute()
        
        new_users = len(user_result.data) if user_result.data else 0
        
        # Calculator usage
        calc_result = supabase.table('calculator_history')\
            .select('calculator_type')\
            .gte('calculated_at', start_date)\
            .execute()
        
        calc_usage = {}
        for calc in (calc_result.data or []):
            calc_type = calc['calculator_type']
            calc_usage[calc_type] = calc_usage.get(calc_type, 0) + 1
        
        # CA performance
        ca_result = supabase.table('ca_ratings')\
            .select('ca_id, overall_rating')\
            .gte('created_at', start_date)\
            .execute()
        
        ca_ratings = ca_result.data if ca_result.data else []
        
        analytics_data = {
            'revenue': {
                'total': total_revenue,
                'pending': pending_revenue,
                'average_booking': total_revenue / total_bookings if total_bookings > 0 else 0
            },
            'bookings': {
                'total': total_bookings,
                'completed': len([b for b in bookings if b['status'] == 'completed']),
                'in_progress': len([b for b in bookings if b['status'] == 'in_progress']),
                'cancelled': len([b for b in bookings if b['status'] == 'cancelled'])
            },
            'users': {
                'new': new_users,
                'growth_rate': (new_users / days) * 30  # Monthly growth
            },
            'services': service_stats,
            'calculators': calc_usage,
            'ca_ratings': ca_ratings
        }
        
        return render_template('admin/analytics.html',
                             analytics=analytics_data,
                             days=days,
                             page_title='Platform Analytics')
    except Exception as e:
        flash(f'Error loading analytics: {str(e)}', 'error')
        return redirect(url_for('admin_enhanced.manage_services'))

@admin_enhanced_bp.route('/analytics/export')
@login_required
@admin_required
def export_analytics():
    """Export analytics data"""
    try:
        # Generate CSV or JSON export
        # Implementation for data export
        return jsonify({'success': True, 'message': 'Export feature coming soon'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =====================================================
# DISPUTE MANAGEMENT
# =====================================================

@admin_enhanced_bp.route('/disputes')
@login_required
@admin_required
def manage_disputes():
    """Manage disputes and complaints"""
    try:
        supabase = get_supabase()
        
        # Get bookings marked as disputed
        result = supabase.table('service_bookings')\
            .select('*, service_catalog(*), profiles!service_bookings_user_id_fkey(*)')\
            .eq('status', 'disputed')\
            .order('created_at', desc=True)\
            .execute()
        
        disputes = result.data if result.data else []
        
        return render_template('admin/manage_disputes.html',
                             disputes=disputes,
                             page_title='Manage Disputes')
    except Exception as e:
        flash(f'Error loading disputes: {str(e)}', 'error')
        return redirect(url_for('admin_enhanced.dashboard'))

@admin_enhanced_bp.route('/disputes/<booking_id>/resolve', methods=['POST'])
@login_required
@admin_required
def resolve_dispute(booking_id):
    """Resolve a dispute"""
    try:
        data = request.json
        resolution = data.get('resolution')
        refund_amount = float(data.get('refund_amount', 0))
        
        supabase = get_supabase()
        
        update_data = {
            'status': 'completed' if resolution == 'resolved' else 'cancelled',
            'admin_notes': data.get('admin_notes', ''),
            'refund_amount': refund_amount
        }
        
        result = supabase.table('service_bookings')\
            .update(update_data)\
            .eq('id', booking_id)\
            .execute()
        
        if result.data:
            # Notify user
            booking = result.data[0]
            supabase.table('notifications').insert({
                'user_id': booking['user_id'],
                'notification_type': 'dispute_resolved',
                'title': 'Dispute Resolved',
                'message': f'Your dispute for booking #{booking["booking_number"]} has been resolved',
                'booking_id': booking_id
            }).execute()
            
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to resolve dispute'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =====================================================
# PRICING MANAGEMENT
# =====================================================

@admin_enhanced_bp.route('/pricing')
@login_required
@admin_required
def manage_pricing():
    """Manage platform pricing"""
    try:
        supabase = get_supabase()
        result = supabase.table('service_catalog')\
            .select('id, service_code, service_name, category, base_price, discount_percentage, is_active')\
            .order('category', 'base_price')\
            .execute()
        
        services = result.data if result.data else []
        
        return render_template('admin/manage_pricing.html',
                             services=services,
                             page_title='Manage Pricing')
    except Exception as e:
        flash(f'Error loading pricing: {str(e)}', 'error')
        return redirect(url_for('admin_enhanced.dashboard'))

@admin_enhanced_bp.route('/pricing/bulk-update', methods=['POST'])
@login_required
@admin_required
def bulk_update_pricing():
    """Bulk update pricing"""
    try:
        data = request.json
        updates = data.get('updates', [])
        
        supabase = get_supabase()
        
        for update in updates:
            supabase.table('service_catalog')\
                .update({
                    'base_price': int(update['base_price']),
                    'discount_percentage': int(update.get('discount_percentage', 0))
                })\
                .eq('id', update['service_id'])\
                .execute()
        
        return jsonify({'success': True, 'updated': len(updates)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =====================================================
# PLATFORM SETTINGS
# =====================================================

@admin_enhanced_bp.route('/settings')
@login_required
@admin_required
def platform_settings():
    """Platform configuration settings"""
    return render_template('admin/settings.html',
                         page_title='Platform Settings')

@admin_enhanced_bp.route('/settings/update', methods=['POST'])
@login_required
@admin_required
def update_settings():
    """Update platform settings"""
    try:
        data = request.json
        # Store settings in database or config
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
