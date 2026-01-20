-- ============================================
-- FINUCITY - FINAL SETUP SCRIPT
-- Run this in Supabase SQL Editor
-- ============================================

-- STEP 1: Clean everything (remove all dummy users)
-- ============================================
DELETE FROM public.user_feedback;
DELETE FROM public.chat_queries;
DELETE FROM public.profiles;
DELETE FROM auth.users;

-- Verify clean state
SELECT 'Profiles count:' as info, COUNT(*) as count FROM public.profiles
UNION ALL
SELECT 'Auth users count:' as info, COUNT(*) as count FROM auth.users;
-- Both should show 0


-- STEP 2: Create Admin User in auth.users
-- ============================================
DO $$
DECLARE
    admin_user_id uuid;
BEGIN
    -- Generate a new UUID for admin
    admin_user_id := gen_random_uuid();
    
    -- Insert into auth.users
    INSERT INTO auth.users (
        instance_id,
        id,
        aud,
        role,
        email,
        encrypted_password,
        email_confirmed_at,
        invited_at,
        confirmation_token,
        confirmation_sent_at,
        recovery_token,
        recovery_sent_at,
        email_change_token_new,
        email_change,
        email_change_sent_at,
        last_sign_in_at,
        raw_app_meta_data,
        raw_user_meta_data,
        is_super_admin,
        created_at,
        updated_at,
        phone,
        phone_confirmed_at,
        phone_change,
        phone_change_token,
        phone_change_sent_at,
        email_change_token_current,
        email_change_confirm_status,
        banned_until,
        reauthentication_token,
        reauthentication_sent_at,
        is_sso_user,
        deleted_at
    ) VALUES (
        '00000000-0000-0000-0000-000000000000',
        admin_user_id,
        'authenticated',
        'authenticated',
        'sumeetsangwan2006@gmail.com',
        crypt('Admin@123', gen_salt('bf')),  -- Password: Admin@123
        NOW(),
        NULL,
        '',
        NULL,
        '',
        NULL,
        '',
        '',
        NULL,
        NOW(),
        '{"provider":"email","providers":["email"]}',
        '{"first_name":"Sumeet","last_name":"Sangwan","role":"admin"}',
        NULL,
        NOW(),
        NOW(),
        NULL,
        NULL,
        '',
        '',
        NULL,
        '',
        0,
        NULL,
        '',
        NULL,
        false,
        NULL
    );
    
    -- Insert into profiles (this should happen via trigger, but we'll do it manually to be sure)
    INSERT INTO public.profiles (
        id,
        email,
        username,
        first_name,
        last_name,
        phone,
        profession,
        city,
        state,
        role,
        is_active,
        email_verified,
        password_hash,
        created_at,
        last_login,
        last_seen
    ) VALUES (
        admin_user_id,
        'sumeetsangwan2006@gmail.com',
        'admin',
        'Sumeet',
        'Sangwan',
        NULL,
        'Platform Administrator',
        NULL,
        NULL,
        'admin',  -- CRITICAL: This is the admin role
        true,
        true,
        crypt('Admin@123', gen_salt('bf')),  -- Store hash in profiles too for fallback
        NOW(),
        NOW(),
        NOW()
    )
    ON CONFLICT (id) DO UPDATE SET
        role = 'admin',
        is_active = true,
        email_verified = true,
        password_hash = crypt('Admin@123', gen_salt('bf'));
    
    RAISE NOTICE 'Admin user created with ID: %', admin_user_id;
END $$;


-- STEP 3: Verify Admin Creation
-- ============================================
SELECT 
    'ADMIN USER CREATED ✅' as status,
    p.id,
    p.email,
    p.username,
    p.first_name,
    p.last_name,
    p.role,
    p.is_active,
    p.email_verified,
    p.created_at
FROM public.profiles p
WHERE p.role = 'admin';

SELECT 
    'ADMIN AUTH USER ✅' as status,
    u.id,
    u.email,
    u.email_confirmed_at,
    u.created_at
FROM auth.users u
WHERE u.email = 'sumeetsangwan2006@gmail.com';


-- STEP 4: Verify Triggers are Working
-- ============================================
SELECT 
    'TRIGGER CHECK' as info,
    trigger_name,
    event_manipulation,
    event_object_table,
    action_statement
FROM information_schema.triggers
WHERE trigger_name = 'on_auth_user_created';


-- ============================================
-- SETUP COMPLETE!
-- ============================================
-- 
-- Admin Credentials:
-- Email: sumeetsangwan2006@gmail.com
-- Password: Admin@123
-- 
-- Admin Login URL: http://localhost:3000/admin/login
-- 
-- Next Steps:
-- 1. Go to Supabase Dashboard
-- 2. Authentication → Providers → Enable "Email" provider
-- 3. Restart your Flask app
-- 4. Visit http://localhost:3000/admin/login
-- 5. Login with the credentials above
-- 
-- ============================================
