-- =====================================================
-- FINUCITY ALL-IN-ONE SETUP SCRIPT
-- Run this ONCE in Supabase SQL Editor
-- =====================================================

-- =====================================================
-- 1. CREATE CA APPLICATIONS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS public.ca_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    
    -- Basic Information
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    
    -- Professional Details
    icai_number TEXT NOT NULL UNIQUE,
    registration_year INTEGER NOT NULL,
    experience_years INTEGER NOT NULL,
    ca_type TEXT NOT NULL CHECK (ca_type IN ('practicing', 'industry', 'government', 'academia')),
    firm_name TEXT,
    practice_address TEXT NOT NULL,
    office_address TEXT,
    
    -- Services & Specializations
    specializations TEXT[] NOT NULL DEFAULT '{}',
    services JSONB NOT NULL DEFAULT '[]',
    client_types JSONB NOT NULL DEFAULT '[]',
    
    -- Documents
    documents JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Application Status
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'under_review', 'approved', 'rejected', 'more_info_required')),
    admin_notes TEXT,
    rejection_reason TEXT,
    
    -- Review Information
    reviewed_by UUID REFERENCES public.profiles(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_deadline TIMESTAMP WITH TIME ZONE,
    
    -- Verification
    icai_verified BOOLEAN DEFAULT false,
    background_check_passed BOOLEAN DEFAULT false,
    documents_verified BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- =====================================================
-- 2. CREATE INDEXES FOR PERFORMANCE
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_ca_applications_user_id ON public.ca_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_ca_applications_status ON public.ca_applications(status);
CREATE INDEX IF NOT EXISTS idx_ca_applications_icai_number ON public.ca_applications(icai_number);
CREATE INDEX IF NOT EXISTS idx_ca_applications_created_at ON public.ca_applications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ca_applications_email ON public.ca_applications(email);

-- =====================================================
-- 3. ENABLE ROW LEVEL SECURITY
-- =====================================================

ALTER TABLE public.ca_applications ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Users can view own CA applications" ON public.ca_applications;
DROP POLICY IF EXISTS "Users can create own CA applications" ON public.ca_applications;
DROP POLICY IF EXISTS "Users can update own pending CA applications" ON public.ca_applications;
DROP POLICY IF EXISTS "Admins can view all CA applications" ON public.ca_applications;
DROP POLICY IF EXISTS "Admins can update all CA applications" ON public.ca_applications;

-- Users can view their own applications
CREATE POLICY "Users can view own CA applications"
    ON public.ca_applications
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can create their own applications
CREATE POLICY "Users can create own CA applications"
    ON public.ca_applications
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own pending applications
CREATE POLICY "Users can update own pending CA applications"
    ON public.ca_applications
    FOR UPDATE
    USING (auth.uid() = user_id AND status = 'pending');

-- Admins can view all applications
CREATE POLICY "Admins can view all CA applications"
    ON public.ca_applications
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Admins can update all applications
CREATE POLICY "Admins can update all CA applications"
    ON public.ca_applications
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- =====================================================
-- 4. CREATE AUTO-UPDATE TRIGGER
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_ca_applications_updated_at ON public.ca_applications;

CREATE TRIGGER update_ca_applications_updated_at 
    BEFORE UPDATE ON public.ca_applications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 5. ADD VERIFICATION STATUS TO PROFILES (if not exists)
-- =====================================================

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'profiles' AND column_name = 'verification_status'
    ) THEN
        ALTER TABLE public.profiles 
        ADD COLUMN verification_status TEXT DEFAULT 'none' 
        CHECK (verification_status IN ('none', 'pending', 'verified', 'suspended', 'blacklisted'));
    END IF;
END $$;

-- =====================================================
-- 6. MAKE SPECIFIC USER ADMIN
-- =====================================================

-- Update the specific email to admin role
UPDATE public.profiles 
SET role = 'admin',
    verification_status = 'verified'
WHERE email = 'sumeetsangwan2006@gmail.com';

-- =====================================================
-- 7. CREATE ADMIN_LOGS TABLE (for audit trail)
-- =====================================================

CREATE TABLE IF NOT EXISTS public.admin_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL REFERENCES public.profiles(id),
    action_type TEXT NOT NULL CHECK (action_type IN (
        'ca_approve', 'ca_reject', 'ca_suspend', 'ca_reinstate', 'ca_blacklist',
        'user_suspend', 'user_reinstate', 'user_delete',
        'complaint_review', 'complaint_resolve',
        'system_config', 'data_export', 'bulk_action'
    )),
    target_user_id UUID REFERENCES public.profiles(id),
    target_type TEXT CHECK (target_type IN ('user', 'ca', 'application', 'complaint', 'system')),
    target_id UUID,
    description TEXT NOT NULL,
    reason TEXT,
    metadata JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_admin_logs_admin_id ON public.admin_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_logs_action_type ON public.admin_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_admin_logs_created_at ON public.admin_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_logs_target_user_id ON public.admin_logs(target_user_id);

ALTER TABLE public.admin_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Admins can view all logs" ON public.admin_logs;
DROP POLICY IF EXISTS "Admins can create logs" ON public.admin_logs;

CREATE POLICY "Admins can view all logs"
    ON public.admin_logs
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

CREATE POLICY "Admins can create logs"
    ON public.admin_logs
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- =====================================================
-- 8. VERIFICATION QUERIES
-- =====================================================

-- Check if admin user was created successfully
DO $$
DECLARE
    admin_count INTEGER;
    app_table_exists BOOLEAN;
    admin_email TEXT := 'sumeetsangwan2006@gmail.com';
    admin_exists BOOLEAN;
BEGIN
    -- Check if admin exists
    SELECT EXISTS(SELECT 1 FROM public.profiles WHERE email = admin_email AND role = 'admin') INTO admin_exists;
    
    -- Count total admins
    SELECT COUNT(*) INTO admin_count FROM public.profiles WHERE role = 'admin';
    
    -- Check if ca_applications table exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'ca_applications'
    ) INTO app_table_exists;
    
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ FINUCITY SETUP COMPLETE!';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Setup Summary:';
    RAISE NOTICE '   ✓ CA Applications table: %', CASE WHEN app_table_exists THEN 'CREATED' ELSE 'FAILED' END;
    RAISE NOTICE '   ✓ Admin logs table: CREATED';
    RAISE NOTICE '   ✓ Indexes: CREATED (5 indexes)';
    RAISE NOTICE '   ✓ RLS Policies: ENABLED';
    RAISE NOTICE '   ✓ Auto-update triggers: ACTIVE';
    RAISE NOTICE '';
    RAISE NOTICE '👨‍💼 Admin Account:';
    RAISE NOTICE '   Email: %', admin_email;
    RAISE NOTICE '   Status: %', CASE WHEN admin_exists THEN '✅ ADMIN' ELSE '❌ NOT FOUND' END;
    RAISE NOTICE '   Total Admins: %', admin_count;
    RAISE NOTICE '';
    
    IF admin_exists THEN
        RAISE NOTICE '🎉 SUCCESS! You can now:';
        RAISE NOTICE '   1. Login with: %', admin_email;
        RAISE NOTICE '   2. Access: http://localhost:3000/admin/dashboard';
        RAISE NOTICE '   3. Review CA applications';
        RAISE NOTICE '   4. Manage users and platform';
    ELSE
        RAISE NOTICE '⚠️  WARNING: Admin account not created!';
        RAISE NOTICE '   Make sure you have a user with email: %', admin_email;
        RAISE NOTICE '   Sign up first, then run this script again.';
    END IF;
    
    RAISE NOTICE '';
    RAISE NOTICE '📋 Quick Test:';
    RAISE NOTICE '   Run: SELECT email, role FROM profiles WHERE role = ''admin'';';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Your database is ready!';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
END $$;

-- Show admin users
SELECT 
    email, 
    role, 
    verification_status,
    created_at,
    '✅ ADMIN USER' as status
FROM public.profiles 
WHERE role = 'admin'
ORDER BY created_at DESC;

-- Show table stats
SELECT 
    'ca_applications' as table_name,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE status = 'pending') as pending,
    COUNT(*) FILTER (WHERE status = 'approved') as approved,
    COUNT(*) FILTER (WHERE status = 'rejected') as rejected
FROM public.ca_applications;
