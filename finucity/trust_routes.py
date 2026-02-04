"""
Trust and Verification System
CA ratings, reviews, secure messaging, verification badges
Author: Sumeet Sangwan
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from finucity.database import get_supabase

trust_bp = Blueprint('trust', __name__, url_prefix='/trust')

# =====================================================
# CA RATINGS & REVIEWS
# =====================================================

@trust_bp.route('/ca/<ca_id>/reviews')
def ca_reviews(ca_id):
    """View all reviews for a CA"""
    try:
        supabase = get_supabase()
        
        # Get CA profile
        ca_result = supabase.table('profiles')\
            .select('*')\
            .eq('id', ca_id)\
            .single()\
            .execute()
        
        if not ca_result.data:
            flash('CA not found', 'error')
            return redirect(url_for('main.contact'))
        
        ca = ca_result.data
        
        # Get reviews
        reviews_result = supabase.table('ca_ratings')\
            .select('*, profiles!ca_ratings_user_id_fkey(first_name, last_name), service_bookings(booking_number)')\
            .eq('ca_id', ca_id)\
            .eq('is_published', True)\
            .order('created_at', desc=True)\
            .execute()
        
        reviews = reviews_result.data if reviews_result.data else []
        
        # Calculate statistics
        if reviews:
            avg_overall = sum(r['overall_rating'] for r in reviews) / len(reviews)
            avg_communication = sum(r['communication_rating'] for r in reviews if r['communication_rating']) / len(reviews)
            avg_expertise = sum(r['expertise_rating'] for r in reviews if r['expertise_rating']) / len(reviews)
            avg_timeliness = sum(r['timeliness_rating'] for r in reviews if r['timeliness_rating']) / len(reviews)
            avg_value = sum(r['value_rating'] for r in reviews if r['value_rating']) / len(reviews)
            
            rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for review in reviews:
                rating_distribution[review['overall_rating']] += 1
        else:
            avg_overall = avg_communication = avg_expertise = avg_timeliness = avg_value = 0
            rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        stats = {
            'total_reviews': len(reviews),
            'average_rating': avg_overall,
            'communication': avg_communication,
            'expertise': avg_expertise,
            'timeliness': avg_timeliness,
            'value': avg_value,
            'distribution': rating_distribution
        }
        
        return render_template('trust/ca_reviews.html',
                             ca=ca,
                             reviews=reviews,
                             stats=stats,
                             page_title=f'{ca["first_name"]} {ca["last_name"]} - Reviews')
    except Exception as e:
        flash(f'Error loading reviews: {str(e)}', 'error')
        return redirect(url_for('main.contact'))

@trust_bp.route('/booking/<booking_id>/review', methods=['GET', 'POST'])
@login_required
def submit_review(booking_id):
    """Submit review for completed booking"""
    supabase = get_supabase()
    
    if request.method == 'POST':
        try:
            data = request.json
            
            # Verify booking belongs to user and is completed
            booking = supabase.table('service_bookings')\
                .select('*')\
                .eq('id', booking_id)\
                .eq('user_id', current_user.id)\
                .eq('status', 'completed')\
                .single()\
                .execute()
            
            if not booking.data:
                return jsonify({'error': 'Booking not found or not completed'}), 404
            
            # Check if already reviewed
            existing = supabase.table('ca_ratings')\
                .select('id')\
                .eq('booking_id', booking_id)\
                .execute()
            
            if existing.data:
                return jsonify({'error': 'Review already submitted'}), 400
            
            # Create review
            review_data = {
                'ca_id': booking.data['assigned_ca_id'],
                'user_id': current_user.id,
                'booking_id': booking_id,
                'overall_rating': int(data['overall_rating']),
                'communication_rating': int(data.get('communication_rating', data['overall_rating'])),
                'expertise_rating': int(data.get('expertise_rating', data['overall_rating'])),
                'timeliness_rating': int(data.get('timeliness_rating', data['overall_rating'])),
                'value_rating': int(data.get('value_rating', data['overall_rating'])),
                'review_title': data.get('review_title', ''),
                'review_text': data.get('review_text', ''),
                'pros': data.get('pros', ''),
                'cons': data.get('cons', ''),
                'is_verified_purchase': True,
                'is_published': True
            }
            
            result = supabase.table('ca_ratings').insert(review_data).execute()
            
            if result.data:
                # Update booking
                supabase.table('service_bookings')\
                    .update({
                        'user_rating': int(data['overall_rating']),
                        'user_feedback': data.get('review_text', ''),
                        'rated_at': datetime.now().isoformat()
                    })\
                    .eq('id', booking_id)\
                    .execute()
                
                # Notify CA
                supabase.table('notifications').insert({
                    'user_id': booking.data['assigned_ca_id'],
                    'notification_type': 'review_received',
                    'title': 'New Review Received',
                    'message': f'You received a {data["overall_rating"]}-star review',
                    'booking_id': booking_id
                }).execute()
                
                return jsonify({'success': True, 'review': result.data[0]})
            else:
                return jsonify({'error': 'Failed to submit review'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # GET request
    try:
        booking = supabase.table('service_bookings')\
            .select('*, service_catalog(*), profiles!service_bookings_assigned_ca_id_fkey(*)')\
            .eq('id', booking_id)\
            .eq('user_id', current_user.id)\
            .single()\
            .execute()
        
        if booking.data:
            return render_template('trust/submit_review.html',
                                 booking=booking.data,
                                 page_title='Submit Review')
        else:
            flash('Booking not found', 'error')
            return redirect(url_for('services.my_bookings'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('services.my_bookings'))

@trust_bp.route('/review/<review_id>/report', methods=['POST'])
@login_required
def report_review(review_id):
    """Report inappropriate review"""
    try:
        data = request.json
        supabase = get_supabase()
        
        result = supabase.table('ca_ratings')\
            .update({
                'is_flagged': True,
                'flag_reason': data.get('reason', 'Inappropriate content')
            })\
            .eq('id', review_id)\
            .execute()
        
        if result.data:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to report review'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trust_bp.route('/review/<review_id>/respond', methods=['POST'])
@login_required
def respond_to_review(review_id):
    """CA responds to review"""
    try:
        data = request.json
        supabase = get_supabase()
        
        # Verify CA owns the review
        review = supabase.table('ca_ratings')\
            .select('ca_id')\
            .eq('id', review_id)\
            .single()\
            .execute()
        
        if review.data and review.data['ca_id'] == current_user.id:
            result = supabase.table('ca_ratings')\
                .update({
                    'ca_response': data.get('response', ''),
                    'ca_responded_at': datetime.now().isoformat()
                })\
                .eq('id', review_id)\
                .execute()
            
            if result.data:
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Failed to post response'}), 500
        else:
            return jsonify({'error': 'Unauthorized'}), 403
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =====================================================
# SECURE MESSAGING
# =====================================================

@trust_bp.route('/messages')
@login_required
def messages():
    """View all messages"""
    try:
        supabase = get_supabase()
        
        # Get user's bookings with message counts
        result = supabase.table('service_bookings')\
            .select('*, service_catalog(*), profiles!service_bookings_assigned_ca_id_fkey(*)')\
            .or_(f'user_id.eq.{current_user.id},assigned_ca_id.eq.{current_user.id}')\
            .order('last_message_at', desc=True, nullsfirst=False)\
            .execute()
        
        bookings = result.data if result.data else []
        
        return render_template('trust/messages.html',
                             bookings=bookings,
                             page_title='Messages')
    except Exception as e:
        flash(f'Error loading messages: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@trust_bp.route('/messages/<booking_id>')
@login_required
def booking_messages(booking_id):
    """View messages for specific booking"""
    try:
        supabase = get_supabase()
        
        # Verify user access
        booking = supabase.table('service_bookings')\
            .select('*, service_catalog(*), profiles!service_bookings_user_id_fkey(first_name, last_name), profiles!service_bookings_assigned_ca_id_fkey(first_name, last_name)')\
            .eq('id', booking_id)\
            .or_(f'user_id.eq.{current_user.id},assigned_ca_id.eq.{current_user.id}')\
            .single()\
            .execute()
        
        if not booking.data:
            flash('Booking not found or access denied', 'error')
            return redirect(url_for('trust.messages'))
        
        # Get messages (stored in consultation_messages table from CA ecosystem)
        # For now, return empty messages
        messages = []
        
        # Mark messages as read
        if current_user.role == 'ca':
            supabase.table('service_bookings')\
                .update({'unread_ca_count': 0})\
                .eq('id', booking_id)\
                .execute()
        else:
            supabase.table('service_bookings')\
                .update({'unread_user_count': 0})\
                .eq('id', booking_id)\
                .execute()
        
        return render_template('trust/booking_messages.html',
                             booking=booking.data,
                             messages=messages,
                             page_title=f'Messages - {booking.data["booking_number"]}')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('trust.messages'))

@trust_bp.route('/messages/<booking_id>/send', methods=['POST'])
@login_required
def send_message(booking_id):
    """Send message in booking conversation"""
    try:
        data = request.json
        message_text = data.get('message', '').strip()
        
        if not message_text:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        supabase = get_supabase()
        
        # Verify access
        booking = supabase.table('service_bookings')\
            .select('user_id, assigned_ca_id')\
            .eq('id', booking_id)\
            .or_(f'user_id.eq.{current_user.id},assigned_ca_id.eq.{current_user.id}')\
            .single()\
            .execute()
        
        if not booking.data:
            return jsonify({'error': 'Access denied'}), 403
        
        # Store message (implementation depends on your message storage)
        # For now, just update booking
        is_ca = current_user.id == booking.data['assigned_ca_id']
        
        update_data = {
            'last_message_at': datetime.now().isoformat()
        }
        
        if is_ca:
            update_data['unread_user_count'] = supabase.table('service_bookings')\
                .select('unread_user_count')\
                .eq('id', booking_id)\
                .single()\
                .execute().data['unread_user_count'] + 1
        else:
            update_data['unread_ca_count'] = supabase.table('service_bookings')\
                .select('unread_ca_count')\
                .eq('id', booking_id)\
                .single()\
                .execute().data['unread_ca_count'] + 1
        
        supabase.table('service_bookings').update(update_data).eq('id', booking_id).execute()
        
        # Send notification
        recipient_id = booking.data['assigned_ca_id'] if not is_ca else booking.data['user_id']
        supabase.table('notifications').insert({
            'user_id': recipient_id,
            'notification_type': 'message_received',
            'title': 'New Message',
            'message': f'You have a new message in booking {booking_id}',
            'booking_id': booking_id
        }).execute()
        
        return jsonify({'success': True, 'message': 'Message sent'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =====================================================
# VERIFICATION SYSTEM
# =====================================================

@trust_bp.route('/verify/ca/<ca_id>')
def ca_verification_status(ca_id):
    """View CA verification status"""
    try:
        supabase = get_supabase()
        
        # Get CA profile
        ca = supabase.table('profiles')\
            .select('*')\
            .eq('id', ca_id)\
            .single()\
            .execute()
        
        if not ca.data:
            return jsonify({'error': 'CA not found'}), 404
        
        # Get CA application
        application = supabase.table('ca_applications')\
            .select('*')\
            .eq('user_id', ca_id)\
            .eq('status', 'approved')\
            .single()\
            .execute()
        
        # Calculate verification score
        verification = {
            'is_verified': ca.data.get('role') == 'ca',
            'icai_verified': bool(application.data) if application.data else False,
            'email_verified': ca.data.get('email_verified', False),
            'phone_verified': False,  # Implement phone verification
            'documents_verified': bool(application.data) if application.data else False,
            'rating': 0,  # Get from ratings table
            'total_reviews': 0,
            'completion_rate': 0,
            'response_time': 0
        }
        
        # Get ratings
        ratings = supabase.table('ca_ratings')\
            .select('overall_rating')\
            .eq('ca_id', ca_id)\
            .execute()
        
        if ratings.data:
            verification['rating'] = sum(r['overall_rating'] for r in ratings.data) / len(ratings.data)
            verification['total_reviews'] = len(ratings.data)
        
        # Get completion rate
        bookings = supabase.table('service_bookings')\
            .select('status')\
            .eq('assigned_ca_id', ca_id)\
            .execute()
        
        if bookings.data:
            completed = len([b for b in bookings.data if b['status'] == 'completed'])
            verification['completion_rate'] = (completed / len(bookings.data)) * 100
        
        # Calculate trust score (0-100)
        trust_score = 0
        trust_score += 30 if verification['icai_verified'] else 0
        trust_score += 20 if verification['email_verified'] else 0
        trust_score += 10 if verification['phone_verified'] else 0
        trust_score += min(20, verification['rating'] * 4)  # Max 20 for 5-star rating
        trust_score += min(20, verification['completion_rate'] * 0.2)  # Max 20 for 100% completion
        
        verification['trust_score'] = int(trust_score)
        
        return jsonify(verification)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =====================================================
# DATA SECURITY INDICATORS
# =====================================================

@trust_bp.route('/security/status')
@login_required
def security_status():
    """View user's data security status"""
    try:
        supabase = get_supabase()
        
        # Get user's documents
        docs = supabase.table('document_vault')\
            .select('encryption_status, is_verified')\
            .eq('user_id', current_user.id)\
            .execute()
        
        # Get security metrics
        security = {
            'two_factor_enabled': False,  # Implement 2FA
            'documents_encrypted': all(d['encryption_status'] == 'encrypted' for d in docs.data) if docs.data else True,
            'verified_documents': sum(1 for d in docs.data if d['is_verified']) if docs.data else 0,
            'total_documents': len(docs.data) if docs.data else 0,
            'last_login': current_user.last_login.isoformat() if hasattr(current_user, 'last_login') else None,
            'account_age_days': (datetime.now() - datetime.fromisoformat(current_user.created_at)).days if hasattr(current_user, 'created_at') else 0
        }
        
        return render_template('trust/security_status.html',
                             security=security,
                             page_title='Security Status')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))
