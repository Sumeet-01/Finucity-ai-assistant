"""
Update to auth routes - Add this to your existing auth routes
This ensures users are redirected to the correct dashboard after login
"""

# Update the postLoginRedirect in your login template or add this route handler

@auth_bp.route('/redirect-after-login')
@login_required
def redirect_after_login():
    """Redirect users to appropriate dashboard based on role."""
    user_role = getattr(current_user, 'role', 'user')
    
    if user_role == 'ca': 
        return redirect(url_for('main. ca_dashboard'))
    elif user_role == 'admin': 
        return redirect(url_for('main.ca_dashboard'))  # or admin dashboard
    elif user_role == 'ca_pending':
        return redirect(url_for('auth.ca_pending'))
    else:
        return redirect(url_for('main.user_dashboard'))


# Update supabase_login to redirect properly
@auth_bp.route('/supabase-login', methods=['POST'])
def supabase_login():
    """Bridge Supabase auth to Flask session."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header. startswith('Bearer '):
        return jsonify({'error':  'missing token'}), 401

    token = auth_header.split(' ', 1)[1]
    claims, err = decode_supabase_jwt(token)
    if err or not claims:
        return jsonify({'error': 'invalid token', 'detail': err}), 401

    role = claims.get('user_metadata', {}).get('role', 'user')

    try:
        user = ensure_local_user_from_claims(claims, role=role)
    except Exception as e: 
        return jsonify({'error': 'user mapping failed', 'detail': str(e)}), 400

    login_user(user, remember=True)

    user_role = getattr(user, 'role', 'user') if hasattr(user, 'role') else 'user'
    
    # Determine redirect URL based on role
    if user_role in ['ca', 'admin']:
        redirect_url = '/ca/dashboard'
    elif user_role == 'ca_pending': 
        redirect_url = '/auth/ca-pending'
    else:
        redirect_url = '/user/dashboard'
    
    return jsonify({
        'ok': True,
        'id': user.id,
        'email':  user.email,
        'role': user_role,
        'redirect_url':  redirect_url
    })