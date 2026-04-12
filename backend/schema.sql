-- ResumeAI Database Schema
-- Run this in Supabase SQL Editor

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT NOT NULL,
    full_name TEXT,
    plan TEXT DEFAULT 'free' CHECK (plan IN ('free', 'single', 'pro')),
    user_type TEXT DEFAULT 'student' CHECK (user_type IN ('student', 'recruiter')),
    analyses_used INTEGER DEFAULT 0,
    scans_used_this_week INTEGER DEFAULT 0,
    plan_expires_at TIMESTAMPTZ,
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Optimizations table
CREATE TABLE IF NOT EXISTS public.optimizations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id),
    optimization_id TEXT UNIQUE NOT NULL,
    original_score INTEGER,
    optimized_score INTEGER,
    original_text TEXT,
    optimized_text TEXT,
    jd_snippet TEXT,                    -- First 200 chars of JD for display
    filename TEXT,                      -- Original resume filename
    job_title TEXT,                     -- Job title from JD
    payment_type TEXT,                  -- 'single' or 'pro'
    stripe_session_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recruiter batch scans table
CREATE TABLE IF NOT EXISTS public.recruiter_scans (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    recruiter_id UUID REFERENCES public.profiles(id),
    batch_name TEXT,
    job_description TEXT,
    keywords TEXT[],
    candidates JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row level security
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.optimizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recruiter_scans ENABLE ROW LEVEL SECURITY;

-- Policies: users can only see their own data
CREATE POLICY "Users see own profile" ON public.profiles
    FOR ALL USING (auth.uid() = id);

CREATE POLICY "Users see own optimizations" ON public.optimizations
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Recruiters see own scans" ON public.recruiter_scans
    FOR ALL USING (auth.uid() = recruiter_id);

-- Auto-create profile on signup (captures user_type from metadata)
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, user_type)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name',
        COALESCE(NEW.raw_user_meta_data->>'user_type', 'student')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


-- =============================================
-- MIGRATION: Run these ALTER statements on existing databases
-- (Safe to run multiple times due to IF NOT EXISTS)
-- =============================================

-- profiles: add new columns
ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS user_type TEXT DEFAULT 'student'
    CHECK (user_type IN ('student', 'recruiter')),
  ADD COLUMN IF NOT EXISTS scans_used_this_week INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS plan_expires_at TIMESTAMPTZ;

-- optimizations: add columns that dashboard references
ALTER TABLE public.optimizations
  ADD COLUMN IF NOT EXISTS filename TEXT,
  ADD COLUMN IF NOT EXISTS job_title TEXT;
