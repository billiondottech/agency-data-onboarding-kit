-- =====================================================
-- Agency Data Onboarding Kit - Supabase Schema
-- =====================================================
-- 
-- This schema creates the core tables for storing clean
-- client data: accounts, contacts, and do_not_contact list
--
-- Run this in your Supabase SQL Editor:
-- 1. Go to https://supabase.com/dashboard
-- 2. Select your project
-- 3. Go to SQL Editor
-- 4. Copy and paste this entire file
-- 5. Click "Run"
--
-- =====================================================

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- TABLE: accounts
-- Stores company/organization data
-- =====================================================

CREATE TABLE IF NOT EXISTS accounts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    website TEXT,
    domain TEXT UNIQUE,
    industry TEXT,
    employee_count INTEGER,
    billing_country TEXT,
    status TEXT DEFAULT 'prospect' CHECK (status IN ('prospect', 'lead', 'customer', 'active', 'inactive', 'churned')),
    source TEXT DEFAULT 'sheet' CHECK (source IN ('sheet', 'hubspot', 'salesforce', 'manual', 'api')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add comment to table
COMMENT ON TABLE accounts IS 'Company/organization records with deduplication by domain';

-- Add comments to columns
COMMENT ON COLUMN accounts.domain IS 'Unique domain extracted from website or email, used for deduplication';
COMMENT ON COLUMN accounts.status IS 'Current relationship status: prospect, lead, customer, active, inactive, churned';
COMMENT ON COLUMN accounts.source IS 'Origin of the data: sheet (CSV), hubspot, salesforce, manual entry, or api';

-- =====================================================
-- TABLE: contacts
-- Stores people/contact data linked to accounts
-- =====================================================

CREATE TABLE IF NOT EXISTS contacts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
    full_name TEXT,
    email TEXT UNIQUE NOT NULL,
    title TEXT,
    phone TEXT,
    linkedin_url TEXT,
    country TEXT,
    source TEXT DEFAULT 'sheet' CHECK (source IN ('sheet', 'hubspot', 'salesforce', 'manual', 'api')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add comment to table
COMMENT ON TABLE contacts IS 'People/contact records with deduplication by email';

-- Add comments to columns
COMMENT ON COLUMN contacts.account_id IS 'Foreign key to accounts table, links contact to their company';
COMMENT ON COLUMN contacts.email IS 'Unique email address, used for deduplication';
COMMENT ON COLUMN contacts.source IS 'Origin of the data: sheet (CSV), hubspot, salesforce, manual entry, or api';

-- =====================================================
-- TABLE: do_not_contact
-- Stores emails that should never be contacted
-- Used for compliance (unsubscribes, bounces, complaints)
-- =====================================================

CREATE TABLE IF NOT EXISTS do_not_contact (
    email TEXT PRIMARY KEY,
    reason TEXT,
    added_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add comment to table
COMMENT ON TABLE do_not_contact IS 'Email addresses that must not be contacted (unsubscribes, bounces, legal requests)';

-- Add comments to columns
COMMENT ON COLUMN do_not_contact.reason IS 'Why this email is blocked: unsubscribe, bounce, complaint, legal_request, etc.';

-- =====================================================
-- INDEXES for Performance
-- =====================================================

-- Accounts indexes
CREATE INDEX IF NOT EXISTS idx_accounts_domain ON accounts(domain) WHERE domain IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status);
CREATE INDEX IF NOT EXISTS idx_accounts_country ON accounts(billing_country);
CREATE INDEX IF NOT EXISTS idx_accounts_created_at ON accounts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_accounts_name_search ON accounts USING gin(to_tsvector('english', name));

-- Contacts indexes
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_account_id ON contacts(account_id);
CREATE INDEX IF NOT EXISTS idx_contacts_country ON contacts(country);
CREATE INDEX IF NOT EXISTS idx_contacts_created_at ON contacts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_contacts_name_search ON contacts USING gin(to_tsvector('english', full_name));

-- Do not contact index
CREATE INDEX IF NOT EXISTS idx_dnc_email ON do_not_contact(email);

-- =====================================================
-- FUNCTIONS: Auto-update updated_at timestamp
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TRIGGERS: Auto-update timestamps on UPDATE
-- =====================================================

DROP TRIGGER IF EXISTS update_accounts_updated_at ON accounts;
CREATE TRIGGER update_accounts_updated_at
    BEFORE UPDATE ON accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_contacts_updated_at ON contacts;
CREATE TRIGGER update_contacts_updated_at
    BEFORE UPDATE ON contacts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- ROW LEVEL SECURITY (RLS)
-- 
-- IMPORTANT: RLS is DISABLED by default for simplicity
-- Enable these policies when deploying to production
-- =====================================================

-- Disable RLS (for development/testing)
ALTER TABLE accounts DISABLE ROW LEVEL SECURITY;
ALTER TABLE contacts DISABLE ROW LEVEL SECURITY;
ALTER TABLE do_not_contact DISABLE ROW LEVEL SECURITY;

-- =====================================================
-- EXAMPLE RLS POLICIES (commented out by default)
-- Uncomment and customize for production use
-- =====================================================

/*
-- Enable RLS on all tables
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE do_not_contact ENABLE ROW LEVEL SECURITY;

-- Policy: Allow authenticated users to read all accounts
CREATE POLICY "Allow authenticated read on accounts"
    ON accounts FOR SELECT
    TO authenticated
    USING (true);

-- Policy: Allow authenticated users to insert/update accounts
CREATE POLICY "Allow authenticated write on accounts"
    ON accounts FOR INSERT
    TO authenticated
    WITH CHECK (true);

CREATE POLICY "Allow authenticated update on accounts"
    ON accounts FOR UPDATE
    TO authenticated
    USING (true);

-- Policy: Allow authenticated users to read all contacts
CREATE POLICY "Allow authenticated read on contacts"
    ON contacts FOR SELECT
    TO authenticated
    USING (true);

-- Policy: Allow authenticated users to insert/update contacts
CREATE POLICY "Allow authenticated write on contacts"
    ON contacts FOR INSERT
    TO authenticated
    WITH CHECK (true);

CREATE POLICY "Allow authenticated update on contacts"
    ON contacts FOR UPDATE
    TO authenticated
    USING (true);

-- Policy: Allow authenticated users to read do_not_contact
CREATE POLICY "Allow authenticated read on do_not_contact"
    ON do_not_contact FOR SELECT
    TO authenticated
    USING (true);

-- Policy: Allow authenticated users to insert into do_not_contact
CREATE POLICY "Allow authenticated write on do_not_contact"
    ON do_not_contact FOR INSERT
    TO authenticated
    WITH CHECK (true);
*/

-- =====================================================
-- VIEWS: Useful queries for reporting
-- =====================================================

-- View: Accounts with contact counts
CREATE OR REPLACE VIEW accounts_with_contact_counts AS
SELECT 
    a.id,
    a.name,
    a.domain,
    a.industry,
    a.billing_country,
    a.status,
    a.source,
    COUNT(c.id) AS contact_count,
    a.created_at,
    a.updated_at
FROM accounts a
LEFT JOIN contacts c ON a.id = c.account_id
GROUP BY a.id, a.name, a.domain, a.industry, a.billing_country, a.status, a.source, a.created_at, a.updated_at;

COMMENT ON VIEW accounts_with_contact_counts IS 'Accounts with the number of contacts associated with each';

-- View: Contacts with account information
CREATE OR REPLACE VIEW contacts_with_accounts AS
SELECT 
    c.id,
    c.full_name,
    c.email,
    c.title,
    c.phone,
    c.linkedin_url,
    c.country,
    c.source AS contact_source,
    a.id AS account_id,
    a.name AS account_name,
    a.domain AS account_domain,
    a.industry AS account_industry,
    a.status AS account_status,
    c.created_at,
    c.updated_at
FROM contacts c
LEFT JOIN accounts a ON c.account_id = a.id;

COMMENT ON VIEW contacts_with_accounts IS 'Contacts with their associated account information';

-- View: Data quality summary
CREATE OR REPLACE VIEW data_quality_summary AS
SELECT 
    'accounts' AS table_name,
    COUNT(*) AS total_records,
    COUNT(domain) AS records_with_domain,
    COUNT(industry) AS records_with_industry,
    COUNT(employee_count) AS records_with_employee_count,
    COUNT(billing_country) AS records_with_country,
    ROUND(100.0 * COUNT(domain) / NULLIF(COUNT(*), 0), 1) AS domain_completeness_pct,
    COUNT(DISTINCT billing_country) AS unique_countries,
    COUNT(DISTINCT industry) AS unique_industries
FROM accounts
UNION ALL
SELECT 
    'contacts' AS table_name,
    COUNT(*) AS total_records,
    COUNT(title) AS records_with_title,
    COUNT(phone) AS records_with_phone,
    COUNT(linkedin_url) AS records_with_linkedin,
    COUNT(country) AS records_with_country,
    ROUND(100.0 * COUNT(title) / NULLIF(COUNT(*), 0), 1) AS title_completeness_pct,
    COUNT(DISTINCT country) AS unique_countries,
    COUNT(DISTINCT account_id) AS unique_accounts
FROM contacts;

COMMENT ON VIEW data_quality_summary IS 'Summary statistics for data quality monitoring';

-- =====================================================
-- SAMPLE DATA (optional - for testing)
-- Uncomment to insert sample records
-- =====================================================

/*
-- Sample accounts
INSERT INTO accounts (name, domain, industry, employee_count, billing_country, status, source) VALUES
    ('Acme Corporation', 'acme-corp.com', 'Software', 250, 'United States', 'customer', 'sheet'),
    ('TechFlow Solutions', 'techflow.io', 'Technology', 45, 'United Kingdom', 'prospect', 'sheet'),
    ('Global Ventures', 'globalventures.com', 'Consulting', 1200, 'United Kingdom', 'customer', 'sheet')
ON CONFLICT (domain) DO NOTHING;

-- Sample contacts
INSERT INTO contacts (full_name, email, title, phone, country, source) VALUES
    ('Sarah Johnson', 'sarah.johnson@acme-corp.com', 'VP of Sales', '+15551234567', 'United States', 'sheet'),
    ('Michael Chen', 'michael.chen@techflow.io', 'CTO', '+442071234567', 'United Kingdom', 'sheet'),
    ('Jennifer Williams', 'jennifer.williams@globalventures.com', 'Chief Marketing Officer', '+15552345678', 'United Kingdom', 'sheet')
ON CONFLICT (email) DO NOTHING;

-- Sample do_not_contact entries
INSERT INTO do_not_contact (email, reason) VALUES
    ('unsubscribed@example.com', 'unsubscribe'),
    ('bounced@example.com', 'hard_bounce'),
    ('complaint@example.com', 'spam_complaint')
ON CONFLICT (email) DO NOTHING;
*/

-- =====================================================
-- HELPER FUNCTIONS for n8n/API integration
-- =====================================================

-- Function: Upsert account by domain
CREATE OR REPLACE FUNCTION upsert_account(
    p_name TEXT,
    p_website TEXT DEFAULT NULL,
    p_domain TEXT DEFAULT NULL,
    p_industry TEXT DEFAULT NULL,
    p_employee_count INTEGER DEFAULT NULL,
    p_billing_country TEXT DEFAULT NULL,
    p_status TEXT DEFAULT 'prospect',
    p_source TEXT DEFAULT 'sheet'
)
RETURNS UUID AS $$
DECLARE
    v_account_id UUID;
BEGIN
    -- Insert or update account
    INSERT INTO accounts (name, website, domain, industry, employee_count, billing_country, status, source)
    VALUES (p_name, p_website, p_domain, p_industry, p_employee_count, p_billing_country, p_status, p_source)
    ON CONFLICT (domain) 
    DO UPDATE SET
        name = EXCLUDED.name,
        website = EXCLUDED.website,
        industry = COALESCE(EXCLUDED.industry, accounts.industry),
        employee_count = COALESCE(EXCLUDED.employee_count, accounts.employee_count),
        billing_country = COALESCE(EXCLUDED.billing_country, accounts.billing_country),
        status = EXCLUDED.status,
        updated_at = NOW()
    RETURNING id INTO v_account_id;
    
    RETURN v_account_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION upsert_account IS 'Insert or update account by domain (idempotent)';

-- Function: Upsert contact by email
CREATE OR REPLACE FUNCTION upsert_contact(
    p_full_name TEXT,
    p_email TEXT,
    p_title TEXT DEFAULT NULL,
    p_phone TEXT DEFAULT NULL,
    p_linkedin_url TEXT DEFAULT NULL,
    p_country TEXT DEFAULT NULL,
    p_account_domain TEXT DEFAULT NULL,
    p_source TEXT DEFAULT 'sheet'
)
RETURNS UUID AS $$
DECLARE
    v_contact_id UUID;
    v_account_id UUID;
BEGIN
    -- Find account by domain if provided
    IF p_account_domain IS NOT NULL THEN
        SELECT id INTO v_account_id FROM accounts WHERE domain = p_account_domain;
    END IF;
    
    -- Insert or update contact
    INSERT INTO contacts (account_id, full_name, email, title, phone, linkedin_url, country, source)
    VALUES (v_account_id, p_full_name, p_email, p_title, p_phone, p_linkedin_url, p_country, p_source)
    ON CONFLICT (email) 
    DO UPDATE SET
        full_name = COALESCE(EXCLUDED.full_name, contacts.full_name),
        title = COALESCE(EXCLUDED.title, contacts.title),
        phone = COALESCE(EXCLUDED.phone, contacts.phone),
        linkedin_url = COALESCE(EXCLUDED.linkedin_url, contacts.linkedin_url),
        country = COALESCE(EXCLUDED.country, contacts.country),
        account_id = COALESCE(v_account_id, contacts.account_id),
        updated_at = NOW()
    RETURNING id INTO v_contact_id;
    
    RETURN v_contact_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION upsert_contact IS 'Insert or update contact by email, optionally linking to account (idempotent)';

-- =====================================================
-- VERIFICATION QUERIES
-- Run these to verify your schema is set up correctly
-- =====================================================

-- Check tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Check indexes exist
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Check views exist
SELECT table_name 
FROM information_schema.views 
WHERE table_schema = 'public'
ORDER BY table_name;

-- =====================================================
-- SCHEMA COMPLETE!
-- =====================================================
-- 
-- Next steps:
-- 1. Check the output of verification queries above
-- 2. Test with sample data (uncomment sample data section)
-- 3. Configure your .env file with Supabase credentials
-- 4. Run the Python cleaning scripts
-- 5. Set up n8n workflow to load cleaned data
--
-- =====================================================