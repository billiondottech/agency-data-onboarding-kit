-- =====================================================
-- Seed Data: Do Not Contact List
-- =====================================================
--
-- This file seeds the do_not_contact table with common
-- test/generic emails that should never be contacted
--
-- Run this AFTER running schema.sql
--
-- =====================================================

-- Insert common test and generic email patterns
INSERT INTO do_not_contact (email, reason) VALUES
    -- Test emails
    ('test@example.com', 'test_email'),
    ('test@test.com', 'test_email'),
    ('testing@example.com', 'test_email'),
    ('demo@example.com', 'test_email'),
    
    -- Generic company emails (low value for outreach)
    ('info@example.com', 'generic_email'),
    ('contact@example.com', 'generic_email'),
    ('hello@example.com', 'generic_email'),
    ('support@example.com', 'generic_email'),
    ('sales@example.com', 'generic_email'),
    ('admin@example.com', 'generic_email'),
    ('noreply@example.com', 'generic_email'),
    ('no-reply@example.com', 'generic_email'),
    
    -- Common role-based emails (replace with actual domains if needed)
    ('webmaster@example.com', 'generic_email'),
    ('postmaster@example.com', 'generic_email'),
    ('hostmaster@example.com', 'generic_email')
ON CONFLICT (email) DO NOTHING;

-- =====================================================
-- Add your own do-not-contact emails here
-- =====================================================

/*
-- Example: Add specific emails that have unsubscribed
INSERT INTO do_not_contact (email, reason) VALUES
    ('john.doe@company.com', 'unsubscribe'),
    ('jane.smith@company.com', 'bounce_hard')
ON CONFLICT (email) DO NOTHING;

-- Example: Bulk insert from a list
INSERT INTO do_not_contact (email, reason)
SELECT 
    unnest(ARRAY[
        'email1@domain.com',
        'email2@domain.com',
        'email3@domain.com'
    ]) AS email,
    'unsubscribe' AS reason
ON CONFLICT (email) DO NOTHING;
*/

-- =====================================================
-- Verification: Check do_not_contact entries
-- =====================================================

SELECT 
    reason,
    COUNT(*) AS count
FROM do_not_contact
GROUP BY reason
ORDER BY count DESC;

-- Show all entries
SELECT * FROM do_not_contact ORDER BY added_at DESC LIMIT 20;

-- =====================================================
-- SEED COMPLETE!
-- =====================================================