-- =====================================================================
-- FINUCITY COMPLETE DATABASE SETUP SCRIPT
-- Run this in Supabase SQL Editor
-- Author: Sumeet Sangwan
-- Date: February 4, 2026
-- =====================================================================

-- =====================================================================
-- PART 1: CORE TABLES (Existing + Extensions)
-- =====================================================================

-- Create profiles table (extends auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    profession TEXT,
    city TEXT,
    state TEXT,
    role TEXT DEFAULT 'user' CHECK (role IN ('user', 'ca', 'ca_pending', 'admin')),
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    last_seen TIMESTAMP WITH TIME ZONE
);

-- Create chat_queries table
CREATE TABLE IF NOT EXISTS public.chat_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    session_id TEXT,
    conversation_id TEXT,
    question TEXT NOT NULL,
    response TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    confidence_score FLOAT,
    response_time FLOAT,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    is_helpful BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address TEXT,
    user_agent TEXT
);

-- Create CA applications table
CREATE TABLE IF NOT EXISTS public.ca_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    icai_membership_number TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    years_of_experience INTEGER NOT NULL CHECK (years_of_experience >= 0),
    specialization TEXT[],
    practice_areas TEXT[],
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    linkedin_url TEXT,
    portfolio_url TEXT,
    membership_certificate_url TEXT,
    identity_proof_url TEXT,
    address_proof_url TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'under_review', 'approved', 'rejected')),
    admin_notes TEXT,
    reviewed_by UUID REFERENCES public.profiles(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create consultations table
CREATE TABLE IF NOT EXISTS public.consultations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    ca_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('tax_planning', 'itr_filing', 'gst', 'company_formation', 'audit', 'other')),
    urgency TEXT DEFAULT 'normal' CHECK (urgency IN ('low', 'normal', 'high', 'urgent')),
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'assigned', 'in_progress', 'resolved', 'closed', 'cancelled')),
    budget_min NUMERIC(10, 2),
    budget_max NUMERIC(10, 2),
    final_price NUMERIC(10, 2),
    assigned_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create consultation_messages table
CREATE TABLE IF NOT EXISTS public.consultation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consultation_id UUID REFERENCES public.consultations(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================
-- PART 2: COMPREHENSIVE TAX SERVICES TABLES
-- =====================================================================

-- 1. Service Catalog
CREATE TABLE IF NOT EXISTS public.service_catalog (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_code TEXT UNIQUE NOT NULL,
    service_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('income_tax', 'gst', 'business_compliance', 'tax_planning', 'advisory', 'other')),
    sub_category TEXT,
    short_description TEXT,
    detailed_description TEXT,
    features JSONB DEFAULT '[]'::jsonb,
    deliverables JSONB DEFAULT '[]'::jsonb,
    requirements JSONB DEFAULT '[]'::jsonb,
    base_price NUMERIC(10, 2) NOT NULL,
    currency TEXT DEFAULT 'INR',
    pricing_type TEXT DEFAULT 'fixed' CHECK (pricing_type IN ('fixed', 'starting_from', 'custom')),
    discount_percentage INTEGER DEFAULT 0 CHECK (discount_percentage BETWEEN 0 AND 100),
    is_diy_enabled BOOLEAN DEFAULT FALSE,
    is_ca_assisted BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 0,
    estimated_days INTEGER DEFAULT 3,
    tags TEXT[],
    created_by UUID REFERENCES public.profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Service Bookings
CREATE TABLE IF NOT EXISTS public.service_bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_number TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    service_id UUID REFERENCES public.service_catalog(id) ON DELETE RESTRICT,
    service_code TEXT NOT NULL,
    service_name TEXT NOT NULL,
    assigned_ca_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'assigned', 'in_progress', 'completed', 'cancelled', 'disputed')),
    payment_status TEXT DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'partially_paid', 'refunded', 'failed')),
    total_amount NUMERIC(10, 2) NOT NULL,
    paid_amount NUMERIC(10, 2) DEFAULT 0,
    discount_amount NUMERIC(10, 2) DEFAULT 0,
    tax_amount NUMERIC(10, 2) DEFAULT 0,
    refund_amount NUMERIC(10, 2) DEFAULT 0,
    user_requirements JSONB,
    admin_notes TEXT,
    internal_notes TEXT,
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    is_diy BOOLEAN DEFAULT FALSE,
    assigned_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    rated_at TIMESTAMP WITH TIME ZONE,
    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
    user_feedback TEXT,
    last_message_at TIMESTAMP WITH TIME ZONE,
    unread_user_count INTEGER DEFAULT 0,
    unread_ca_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Document Vault
CREATE TABLE IF NOT EXISTS public.document_vault (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    booking_id UUID REFERENCES public.service_bookings(id) ON DELETE SET NULL,
    document_type TEXT NOT NULL,
    document_category TEXT CHECK (document_category IN ('pan', 'aadhaar', 'form16', 'bank_statement', 'invoice', 'certificate', 'other')),
    file_name TEXT NOT NULL,
    file_size INTEGER,
    file_url TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    mime_type TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    encryption_status TEXT DEFAULT 'encrypted' CHECK (encryption_status IN ('encrypted', 'pending', 'failed')),
    uploaded_by UUID REFERENCES public.profiles(id),
    verified_by UUID REFERENCES public.profiles(id),
    verified_at TIMESTAMP WITH TIME ZONE,
    expiry_date DATE,
    tags TEXT[],
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Calculator History
CREATE TABLE IF NOT EXISTS public.calculator_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    session_id TEXT,
    calculator_type TEXT NOT NULL CHECK (calculator_type IN ('income_tax', 'hra', 'capital_gains', 'sip', 'gst', 'tds', 'gratuity', 'home_loan', 'retirement', 'tax_regime')),
    input_data JSONB NOT NULL,
    result_data JSONB NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. AI Interactions
CREATE TABLE IF NOT EXISTS public.ai_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    booking_id UUID REFERENCES public.service_bookings(id) ON DELETE SET NULL,
    interaction_type TEXT NOT NULL CHECK (interaction_type IN ('form16_parse', 'deduction_discovery', 'compliance_check', 'tax_tips', 'general_query')),
    input_data JSONB NOT NULL,
    output_data JSONB NOT NULL,
    ai_model TEXT DEFAULT 'llama-3.1-8b-instant',
    processing_time FLOAT,
    confidence_score FLOAT,
    tokens_used INTEGER,
    cost NUMERIC(10, 4),
    is_successful BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. CA Ratings
CREATE TABLE IF NOT EXISTS public.ca_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ca_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    booking_id UUID REFERENCES public.service_bookings(id) ON DELETE SET NULL,
    overall_rating INTEGER NOT NULL CHECK (overall_rating BETWEEN 1 AND 5),
    communication_rating INTEGER CHECK (communication_rating BETWEEN 1 AND 5),
    expertise_rating INTEGER CHECK (expertise_rating BETWEEN 1 AND 5),
    timeliness_rating INTEGER CHECK (timeliness_rating BETWEEN 1 AND 5),
    value_rating INTEGER CHECK (value_rating BETWEEN 1 AND 5),
    review_title TEXT,
    review_text TEXT,
    pros TEXT,
    cons TEXT,
    is_verified_purchase BOOLEAN DEFAULT FALSE,
    is_published BOOLEAN DEFAULT TRUE,
    is_flagged BOOLEAN DEFAULT FALSE,
    flag_reason TEXT,
    ca_response TEXT,
    ca_responded_at TIMESTAMP WITH TIME ZONE,
    helpful_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(booking_id, user_id)
);

-- 7. Tax Profiles
CREATE TABLE IF NOT EXISTS public.tax_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE UNIQUE,
    pan_number TEXT UNIQUE,
    aadhaar_number TEXT,
    employment_type TEXT CHECK (employment_type IN ('salaried', 'self_employed', 'business', 'professional', 'freelancer', 'other')),
    annual_income NUMERIC(15, 2),
    preferred_tax_regime TEXT CHECK (preferred_tax_regime IN ('old', 'new')),
    has_house_property BOOLEAN DEFAULT FALSE,
    has_capital_gains BOOLEAN DEFAULT FALSE,
    has_business_income BOOLEAN DEFAULT FALSE,
    has_foreign_income BOOLEAN DEFAULT FALSE,
    has_agricultural_income BOOLEAN DEFAULT FALSE,
    tax_deductions JSONB DEFAULT '[]'::jsonb,
    investment_details JSONB DEFAULT '[]'::jsonb,
    last_itr_filed_year INTEGER,
    last_itr_status TEXT,
    is_auditable BOOLEAN DEFAULT FALSE,
    risk_profile TEXT DEFAULT 'low' CHECK (risk_profile IN ('low', 'medium', 'high')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. Notifications
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    notification_type TEXT NOT NULL CHECK (notification_type IN ('booking_update', 'ca_assigned', 'message_received', 'payment_received', 'review_received', 'dispute_resolved', 'document_uploaded', 'system_alert')),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    action_url TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    booking_id UUID REFERENCES public.service_bookings(id) ON DELETE CASCADE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE
);

-- 9. Platform Analytics
CREATE TABLE IF NOT EXISTS public.platform_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_type TEXT NOT NULL CHECK (metric_type IN ('revenue', 'bookings', 'users', 'calculators', 'ai_usage', 'ca_performance')),
    metric_name TEXT NOT NULL,
    metric_value NUMERIC(15, 2),
    dimensions JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE
);

-- 10. Compliance Calendar
CREATE TABLE IF NOT EXISTS public.compliance_calendar (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    compliance_type TEXT NOT NULL CHECK (compliance_type IN ('itr_filing', 'gst_filing', 'tds_payment', 'advance_tax', 'roc_filing', 'audit_deadline', 'other')),
    title TEXT NOT NULL,
    description TEXT,
    due_date DATE NOT NULL,
    reminder_date DATE,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'missed', 'not_applicable')),
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'critical')),
    financial_year TEXT,
    assessment_year TEXT,
    penalty_if_missed TEXT,
    related_booking_id UUID REFERENCES public.service_bookings(id) ON DELETE SET NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================================
-- PART 3: INDEXES FOR PERFORMANCE
-- =====================================================================

-- Profiles indexes
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_role ON public.profiles(role);
CREATE INDEX IF NOT EXISTS idx_profiles_is_active ON public.profiles(is_active);

-- Chat queries indexes
CREATE INDEX IF NOT EXISTS idx_chat_queries_user_id ON public.chat_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_queries_session_id ON public.chat_queries(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_queries_created_at ON public.chat_queries(created_at DESC);

-- CA applications indexes
CREATE INDEX IF NOT EXISTS idx_ca_applications_user_id ON public.ca_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_ca_applications_status ON public.ca_applications(status);

-- Consultations indexes
CREATE INDEX IF NOT EXISTS idx_consultations_user_id ON public.consultations(user_id);
CREATE INDEX IF NOT EXISTS idx_consultations_ca_id ON public.consultations(ca_id);
CREATE INDEX IF NOT EXISTS idx_consultations_status ON public.consultations(status);

-- Service catalog indexes
CREATE INDEX IF NOT EXISTS idx_service_catalog_category ON public.service_catalog(category);
CREATE INDEX IF NOT EXISTS idx_service_catalog_is_active ON public.service_catalog(is_active);
CREATE INDEX IF NOT EXISTS idx_service_catalog_is_featured ON public.service_catalog(is_featured);

-- Service bookings indexes
CREATE INDEX IF NOT EXISTS idx_service_bookings_user_id ON public.service_bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_service_bookings_ca_id ON public.service_bookings(assigned_ca_id);
CREATE INDEX IF NOT EXISTS idx_service_bookings_status ON public.service_bookings(status);
CREATE INDEX IF NOT EXISTS idx_service_bookings_payment_status ON public.service_bookings(payment_status);
CREATE INDEX IF NOT EXISTS idx_service_bookings_created_at ON public.service_bookings(created_at DESC);

-- Document vault indexes
CREATE INDEX IF NOT EXISTS idx_document_vault_user_id ON public.document_vault(user_id);
CREATE INDEX IF NOT EXISTS idx_document_vault_booking_id ON public.document_vault(booking_id);

-- Calculator history indexes
CREATE INDEX IF NOT EXISTS idx_calculator_history_user_id ON public.calculator_history(user_id);
CREATE INDEX IF NOT EXISTS idx_calculator_history_type ON public.calculator_history(calculator_type);
CREATE INDEX IF NOT EXISTS idx_calculator_history_date ON public.calculator_history(calculated_at DESC);

-- CA ratings indexes
CREATE INDEX IF NOT EXISTS idx_ca_ratings_ca_id ON public.ca_ratings(ca_id);
CREATE INDEX IF NOT EXISTS idx_ca_ratings_user_id ON public.ca_ratings(user_id);
CREATE INDEX IF NOT EXISTS idx_ca_ratings_published ON public.ca_ratings(is_published);

-- Notifications indexes
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON public.notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON public.notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON public.notifications(created_at DESC);

-- Compliance calendar indexes
CREATE INDEX IF NOT EXISTS idx_compliance_calendar_user_id ON public.compliance_calendar(user_id);
CREATE INDEX IF NOT EXISTS idx_compliance_calendar_due_date ON public.compliance_calendar(due_date);
CREATE INDEX IF NOT EXISTS idx_compliance_calendar_status ON public.compliance_calendar(status);

-- =====================================================================
-- PART 4: ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================================

-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_queries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ca_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.consultations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.consultation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.service_catalog ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.service_bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_vault ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.calculator_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ca_ratings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tax_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.platform_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.compliance_calendar ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Admins can view all profiles" ON public.profiles
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Chat queries policies
CREATE POLICY "Users can view own chat queries" ON public.chat_queries
    FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can insert own chat queries" ON public.chat_queries
    FOR INSERT WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

-- Service catalog policies
CREATE POLICY "Everyone can view active services" ON public.service_catalog
    FOR SELECT USING (is_active = TRUE);

CREATE POLICY "Admins can manage services" ON public.service_catalog
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Service bookings policies
CREATE POLICY "Users can view own bookings" ON public.service_bookings
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "CAs can view assigned bookings" ON public.service_bookings
    FOR SELECT USING (auth.uid() = assigned_ca_id);

CREATE POLICY "Admins can view all bookings" ON public.service_bookings
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

CREATE POLICY "Users can create bookings" ON public.service_bookings
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Document vault policies
CREATE POLICY "Users can view own documents" ON public.document_vault
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can upload own documents" ON public.document_vault
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "CAs can view documents for assigned bookings" ON public.document_vault
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.service_bookings
            WHERE id = booking_id AND assigned_ca_id = auth.uid()
        )
    );

-- Calculator history policies
CREATE POLICY "Users can view own calculator history" ON public.calculator_history
    FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Anyone can create calculator history" ON public.calculator_history
    FOR INSERT WITH CHECK (TRUE);

-- CA ratings policies
CREATE POLICY "Users can view published ratings" ON public.ca_ratings
    FOR SELECT USING (is_published = TRUE);

CREATE POLICY "Users can create ratings for completed bookings" ON public.ca_ratings
    FOR INSERT WITH CHECK (
        auth.uid() = user_id AND
        EXISTS (
            SELECT 1 FROM public.service_bookings
            WHERE id = booking_id AND user_id = auth.uid() AND status = 'completed'
        )
    );

CREATE POLICY "CAs can view own ratings" ON public.ca_ratings
    FOR SELECT USING (auth.uid() = ca_id);

CREATE POLICY "CAs can respond to own ratings" ON public.ca_ratings
    FOR UPDATE USING (auth.uid() = ca_id);

-- Tax profiles policies
CREATE POLICY "Users can view own tax profile" ON public.tax_profiles
    FOR ALL USING (auth.uid() = user_id);

-- Notifications policies
CREATE POLICY "Users can view own notifications" ON public.notifications
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own notifications" ON public.notifications
    FOR UPDATE USING (auth.uid() = user_id);

-- Compliance calendar policies
CREATE POLICY "Users can manage own compliance items" ON public.compliance_calendar
    FOR ALL USING (auth.uid() = user_id);

-- Platform analytics policies
CREATE POLICY "Admins can view analytics" ON public.platform_analytics
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- =====================================================================
-- PART 5: FUNCTIONS AND TRIGGERS
-- =====================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_ca_applications_updated_at BEFORE UPDATE ON public.ca_applications
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_consultations_updated_at BEFORE UPDATE ON public.consultations
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_service_catalog_updated_at BEFORE UPDATE ON public.service_catalog
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_service_bookings_updated_at BEFORE UPDATE ON public.service_bookings
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_document_vault_updated_at BEFORE UPDATE ON public.document_vault
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_ca_ratings_updated_at BEFORE UPDATE ON public.ca_ratings
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_tax_profiles_updated_at BEFORE UPDATE ON public.tax_profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_compliance_calendar_updated_at BEFORE UPDATE ON public.compliance_calendar
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Function to generate booking numbers
CREATE OR REPLACE FUNCTION public.generate_booking_number()
RETURNS TEXT AS $$
DECLARE
    new_number TEXT;
    counter INTEGER;
BEGIN
    counter := (SELECT COUNT(*) FROM public.service_bookings) + 1;
    new_number := 'FIN' || TO_CHAR(NOW(), 'YYYYMMDD') || LPAD(counter::TEXT, 4, '0');
    RETURN new_number;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- PART 6: SEED DATA (OPTIONAL - FOR TESTING)
-- =====================================================================

-- Insert sample services (you can customize these)
INSERT INTO public.service_catalog (service_code, service_name, display_name, category, short_description, base_price, is_diy_enabled, is_ca_assisted, is_featured)
VALUES 
    ('ITR_SELF_FILE', 'ITR Self Filing', 'File Your ITR Yourself', 'income_tax', 'DIY income tax return filing with AI guidance', 499, TRUE, FALSE, TRUE),
    ('ITR_CA_ASSISTED', 'ITR CA Assisted', 'Expert CA-Assisted ITR Filing', 'income_tax', 'Professional CA will file your ITR', 1999, FALSE, TRUE, TRUE),
    ('GST_REGISTRATION', 'GST Registration', 'Register Your Business for GST', 'gst', 'Complete GST registration with expert support', 1999, FALSE, TRUE, TRUE),
    ('GST_FILING_MONTHLY', 'Monthly GST Filing', 'Monthly GST Return Filing', 'gst', 'File GSTR-1, GSTR-3B monthly', 999, FALSE, TRUE, FALSE),
    ('COMPANY_REGISTRATION', 'Company Registration', 'Private Limited Company Registration', 'business_compliance', 'End-to-end company incorporation', 9999, FALSE, TRUE, TRUE),
    ('TAX_PLANNING', 'Tax Planning Consultation', 'Expert Tax Planning Session', 'tax_planning', 'Personalized tax saving strategies', 2999, FALSE, TRUE, TRUE)
ON CONFLICT (service_code) DO NOTHING;

-- =====================================================================
-- VERIFICATION QUERIES
-- =====================================================================

-- Check all tables created
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Check RLS enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;

-- =====================================================================
-- SCRIPT COMPLETE
-- =====================================================================
-- All tables, indexes, RLS policies, and functions have been created
-- Run the verification queries above to confirm setup
-- =====================================================================
