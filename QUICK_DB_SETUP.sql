-- =====================================================
-- QUICK DATABASE SETUP - Run this in Supabase SQL Editor
-- This creates the missing ca_applications table
-- =====================================================

-- Create CA Applications Table
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
    
    -- Documents (stored in Supabase Storage, references here)
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

-- Create Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ca_applications_user_id ON public.ca_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_ca_applications_status ON public.ca_applications(status);
CREATE INDEX IF NOT EXISTS idx_ca_applications_icai_number ON public.ca_applications(icai_number);
CREATE INDEX IF NOT EXISTS idx_ca_applications_created_at ON public.ca_applications(created_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE public.ca_applications ENABLE ROW LEVEL SECURITY;

-- RLS Policies
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

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_ca_applications_updated_at 
    BEFORE UPDATE ON public.ca_applications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- SUCCESS MESSAGE
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE '✅ CA Applications table created successfully!';
    RAISE NOTICE '✅ Indexes created for performance';
    RAISE NOTICE '✅ Row Level Security enabled';
    RAISE NOTICE '✅ RLS Policies configured';
    RAISE NOTICE '✅ Auto-update trigger added';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Your database is ready for CA applications!';
END $$;
