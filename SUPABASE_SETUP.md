# Finucity Supabase Database Setup

**CRITICAL**: Finucity uses **ONLY Supabase** as its database. No local databases are used.

## Prerequisites

1. Create a Supabase project at https://supabase.com
2. Get your project credentials:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_KEY` (service_role key)
   - `SUPABASE_JWT_SECRET`

## Database Schema

Execute these SQL commands in your Supabase SQL Editor:

### 1. Profiles Table (extends auth.users)

```sql
-- Create profiles table that extends Supabase Auth
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
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    last_seen TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

-- Create indexes
CREATE INDEX idx_profiles_email ON public.profiles(email);
CREATE INDEX idx_profiles_username ON public.profiles(username);
CREATE INDEX idx_profiles_role ON public.profiles(role);

-- Enable Row Level Security
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Policies for profiles
CREATE POLICY "Users can view their own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Service role can do anything" ON public.profiles
    FOR ALL USING (true);

-- Function to create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, username, first_name, role)
    VALUES (
        NEW.id,
        NEW.email,
        SPLIT_PART(NEW.email, '@', 1),
        COALESCE(NEW.raw_user_meta_data->>'first_name', SPLIT_PART(NEW.email, '@', 1)),
        COALESCE(NEW.raw_user_meta_data->>'role', 'user')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to auto-create profile
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

### 2. Chat Queries Table

```sql
CREATE TABLE IF NOT EXISTS public.chat_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    session_id TEXT,
    conversation_id TEXT,
    question TEXT NOT NULL,
    response TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    confidence_score FLOAT DEFAULT 0.9,
    response_time FLOAT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    is_helpful BOOLEAN,
    feedback_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_chat_queries_user_id ON public.chat_queries(user_id);
CREATE INDEX idx_chat_queries_session_id ON public.chat_queries(session_id);
CREATE INDEX idx_chat_queries_created_at ON public.chat_queries(created_at DESC);

-- RLS
ALTER TABLE public.chat_queries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own queries" ON public.chat_queries
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own queries" ON public.chat_queries
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Service role full access" ON public.chat_queries
    FOR ALL USING (true);
```

### 3. User Feedback Table

```sql
CREATE TABLE IF NOT EXISTS public.user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    admin_user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'resolved')),
    admin_response TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_feedback_user_id ON public.user_feedback(user_id);
CREATE INDEX idx_feedback_status ON public.user_feedback(status);

-- RLS
ALTER TABLE public.user_feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own feedback" ON public.user_feedback
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create feedback" ON public.user_feedback
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Admins can view all feedback" ON public.user_feedback
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

CREATE POLICY "Service role full access feedback" ON public.user_feedback
    FOR ALL USING (true);
```

### 4. CA Applications Table

```sql
CREATE TABLE IF NOT EXISTS public.ca_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    icai_number TEXT NOT NULL UNIQUE,
    registration_year INTEGER NOT NULL,
    ca_type TEXT NOT NULL CHECK (ca_type IN ('practicing', 'non-practicing', 'firm')),
    experience_years INTEGER NOT NULL CHECK (experience_years >= 0),
    firm_name TEXT,
    practice_address TEXT,
    services JSONB DEFAULT '[]'::jsonb,
    client_types JSONB DEFAULT '[]'::jsonb,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewed_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    rejection_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_ca_applications_user_id ON public.ca_applications(user_id);
CREATE INDEX idx_ca_applications_status ON public.ca_applications(status);
CREATE INDEX idx_ca_applications_icai ON public.ca_applications(icai_number);

-- RLS
ALTER TABLE public.ca_applications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own applications" ON public.ca_applications
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create applications" ON public.ca_applications
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Admins can view all applications" ON public.ca_applications
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

CREATE POLICY "Admins can update applications" ON public.ca_applications
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

CREATE POLICY "Service role full access ca_applications" ON public.ca_applications
    FOR ALL USING (true);
```

### 5. Conversations Table (Optional)

```sql
CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    session_id TEXT UNIQUE NOT NULL,
    title TEXT,
    category TEXT DEFAULT 'general',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_conversations_user_id ON public.conversations(user_id);
CREATE INDEX idx_conversations_session_id ON public.conversations(session_id);

-- RLS
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own conversations" ON public.conversations
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Service role full access conversations" ON public.conversations
    FOR ALL USING (true);
```

## Storage Buckets (for file uploads)

```sql
-- Create storage bucket for user documents
INSERT INTO storage.buckets (id, name, public) 
VALUES ('user-documents', 'user-documents', false)
ON CONFLICT DO NOTHING;

-- Storage policies
CREATE POLICY "Users can upload their own documents"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'user-documents' 
    AND auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can view their own documents"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'user-documents' 
    AND auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can delete their own documents"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'user-documents' 
    AND auth.uid()::text = (storage.foldername(name))[1]
);
```

## Environment Configuration

Add these to your `.env` file:

```env
# Supabase Configuration (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret

# Flask
SECRET_KEY=generate-a-secure-random-key
FLASK_ENV=development

# AI
GROQ_API_KEY=your-groq-api-key
```

## Authentication Flow

Finucity uses **Supabase Auth** for authentication:

1. **Sign Up**: Users sign up via Supabase Auth (email/password or OAuth)
2. **Profile Creation**: Trigger automatically creates profile in `profiles` table
3. **Session**: Supabase JWT token used for authentication
4. **Flask-Login**: User adapter wraps Supabase profile for Flask sessions

## Backend Access

Use service role key on backend to:
- Bypass RLS when needed
- Perform admin operations
- Access all data

Frontend should use anon key with user JWT tokens.

## Migration from SQLAlchemy

If you have existing data in SQLite:

1. Export data from SQLite
2. Transform to Supabase format (UUID for IDs)
3. Import via Supabase API or SQL
4. Delete SQLite files after verification

## Verification

Test your setup:

```python
from finucity.database import UserService, get_supabase

# Test connection
sb = get_supabase()
result = sb.table('profiles').select('*').limit(1).execute()
print("✅ Supabase connected" if result else "❌ Connection failed")
```

## Important Notes

- **NO SQLite or SQLAlchemy** - Removed completely
- **NO local database files** - All data in Supabase
- **RLS enabled** - Users can only access their own data
- **Service role** - Backend uses service_role key to bypass RLS when needed
- **UUID IDs** - All primary keys are UUIDs, not integers

## Support

For issues:
- Check Supabase logs in dashboard
- Verify RLS policies
- Ensure service role key is used on backend
- Check that triggers are created
