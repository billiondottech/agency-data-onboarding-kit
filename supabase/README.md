# Supabase Database Schema

This folder contains SQL files for setting up your Supabase database.

## Files

- **`schema.sql`** - Main database schema (tables, indexes, functions, views)
- **`seed_do_not_contact.sql`** - Seed data for the do_not_contact table

---

## Quick Setup

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Click "New Project"
3. Choose organization and name your project (e.g., "agency-data-prod")
4. Set a strong database password (save this!)
5. Choose a region close to you
6. Click "Create new project" and wait ~2 minutes

### 2. Run the Schema

1. In your Supabase dashboard, go to **SQL Editor**
2. Click "New Query"
3. Copy the entire contents of `schema.sql`
4. Paste into the editor
5. Click "Run" (or press Cmd/Ctrl + Enter)
6. Wait for success message

### 3. Run the Seed Data (Optional)

1. Still in SQL Editor, click "New Query"
2. Copy the contents of `seed_do_not_contact.sql`
3. Paste and click "Run"

### 4. Get Your Credentials

1. Go to **Settings → API**
2. Copy your:
   - **Project URL** (e.g., `https://abc123.supabase.co`)
   - **Anon/Public Key** (starts with `eyJ...`)
3. Add these to your `.env` file

---

## Database Schema Overview

### Tables

#### **accounts** (Companies/Organizations)
```
id               UUID PRIMARY KEY
name             TEXT (required)
website          TEXT
domain           TEXT (unique) - Used for deduplication
industry         TEXT
employee_count   INTEGER
billing_country  TEXT
status           TEXT (prospect/lead/customer/active/inactive/churned)
source           TEXT (sheet/hubspot/salesforce/manual/api)
created_at       TIMESTAMPTZ
updated_at       TIMESTAMPTZ (auto-updates)
```

**Key Features:**
- ✅ Unique constraint on `domain` prevents duplicates
- ✅ Auto-updating `updated_at` timestamp
- ✅ Full-text search index on `name`
- ✅ Indexes on `status`, `country`, `created_at`

#### **contacts** (People)
```
id               UUID PRIMARY KEY
account_id       UUID (foreign key to accounts)
full_name        TEXT
email            TEXT (unique) - Used for deduplication
title            TEXT
phone            TEXT
linkedin_url     TEXT
country          TEXT
source           TEXT (sheet/hubspot/salesforce/manual/api)
created_at       TIMESTAMPTZ
updated_at       TIMESTAMPTZ (auto-updates)
```

**Key Features:**
- ✅ Unique constraint on `email` prevents duplicates
- ✅ Foreign key to `accounts` table
- ✅ Cascade delete (if account deleted, contacts deleted)
- ✅ Full-text search index on `full_name`
- ✅ Indexes on `email`, `account_id`, `country`

#### **do_not_contact** (Compliance)
```
email       TEXT PRIMARY KEY
reason      TEXT
added_at    TIMESTAMPTZ
```

**Purpose:**
- Legal compliance (GDPR, CAN-SPAM)
- Track unsubscribes, bounces, complaints
- Prevent accidental re-contact

---

## Views for Reporting

### **accounts_with_contact_counts**
Shows all accounts with how many contacts each has

```sql
SELECT * FROM accounts_with_contact_counts
WHERE contact_count > 0
ORDER BY contact_count DESC;
```

### **contacts_with_accounts**
Shows all contacts with their account information denormalized

```sql
SELECT * FROM contacts_with_accounts
WHERE account_industry = 'Software'
ORDER BY full_name;
```

### **data_quality_summary**
Summary statistics for monitoring data completeness

```sql
SELECT * FROM data_quality_summary;
```

---

## Helper Functions

### **upsert_account()**
Idempotent function to insert or update accounts by domain

```sql
SELECT upsert_account(
    p_name := 'Acme Corporation',
    p_domain := 'acme-corp.com',
    p_industry := 'Software',
    p_employee_count := 250,
    p_billing_country := 'United States',
    p_status := 'customer'
);
```

### **upsert_contact()**
Idempotent function to insert or update contacts by email

```sql
SELECT upsert_contact(
    p_full_name := 'Sarah Johnson',
    p_email := 'sarah.johnson@acme-corp.com',
    p_title := 'VP of Sales',
    p_phone := '+15551234567',
    p_account_domain := 'acme-corp.com'
);
```

**Why use these functions?**
- Automatically links contacts to accounts by domain
- Safe for repeated calls (idempotent)
- Preserves existing data when updating

---

## Row Level Security (RLS)

**Current Status:** RLS is DISABLED for simplicity

**For Production:** Uncomment the RLS policies in `schema.sql`

```sql
-- Enable RLS
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;

-- Add policies (examples in schema.sql)
```

**Why enable RLS:**
- Multi-tenant support (isolate client data)
- Fine-grained access control
- Additional security layer

---

## Common Queries

### Find accounts without contacts
```sql
SELECT a.name, a.domain
FROM accounts a
LEFT JOIN contacts c ON a.id = c.account_id
WHERE c.id IS NULL;
```

### Find contacts without accounts
```sql
SELECT full_name, email
FROM contacts
WHERE account_id IS NULL;
```

### Link contacts to accounts by email domain
```sql
UPDATE contacts c
SET account_id = a.id
FROM accounts a
WHERE c.account_id IS NULL
AND a.domain = (
    SELECT split_part(c.email, '@', 2)
);
```

### Check for emails in do_not_contact
```sql
SELECT c.email, c.full_name, dnc.reason
FROM contacts c
INNER JOIN do_not_contact dnc ON c.email = dnc.email;
```

### Data completeness report
```sql
SELECT 
    COUNT(*) AS total,
    COUNT(title) AS has_title,
    COUNT(phone) AS has_phone,
    COUNT(linkedin_url) AS has_linkedin,
    ROUND(100.0 * COUNT(title) / COUNT(*), 1) AS title_pct,
    ROUND(100.0 * COUNT(phone) / COUNT(*), 1) AS phone_pct,
    ROUND(100.0 * COUNT(linkedin_url) / COUNT(*), 1) AS linkedin_pct
FROM contacts;
```

---

## Maintenance

### Backup Your Database

**Option 1: Supabase Dashboard**
1. Go to **Database → Backups**
2. Create manual backup
3. Download if needed

**Option 2: pg_dump (Advanced)**
```bash
pg_dump "postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres" \
  --no-owner --no-acl \
  > backup_$(date +%Y%m%d).sql
```

### Reset Database (Careful!)

```sql
-- Drop all tables (destructive!)
DROP TABLE IF EXISTS contacts CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS do_not_contact CASCADE;
DROP VIEW IF EXISTS accounts_with_contact_counts CASCADE;
DROP VIEW IF EXISTS contacts_with_accounts CASCADE;
DROP VIEW IF EXISTS data_quality_summary CASCADE;

-- Then re-run schema.sql
```

### Update Schema

If you need to add columns:

```sql
-- Add column
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS middle_name TEXT;

-- Add index
CREATE INDEX IF NOT EXISTS idx_contacts_middle_name ON contacts(middle_name);
```

---

## Troubleshooting

### "relation already exists"
The table is already created. Either:
- Skip creation (it's fine!)
- Or drop and recreate (see Reset Database above)

### "permission denied"
You're using the wrong key. Use:
- ✅ **Anon/Public key** (for n8n, scripts)
- ❌ **Service role key** (only for server-side admin tasks)

### "insert or update violates foreign key constraint"
You're trying to link a contact to an account that doesn't exist.
- Solution: Insert account first, or set `account_id` to NULL

### "duplicate key value violates unique constraint"
You're trying to insert:
- An account with a domain that already exists
- A contact with an email that already exists

Solution: Use the `upsert_*` functions or update instead of insert

---

## Performance Tips

### Indexes are already optimized for:
- ✅ Lookups by domain/email (unique constraints)
- ✅ Filtering by status, country
- ✅ Full-text search on names
- ✅ Sorting by created_at

### For large datasets (100K+ rows):
```sql
-- Vacuum to reclaim space
VACUUM ANALYZE accounts;
VACUUM ANALYZE contacts;

-- Update statistics
ANALYZE accounts;
ANALYZE contacts;
```

### Monitor slow queries:
Go to **Database → Query Performance** in Supabase dashboard

---

## Integration with n8n

Your n8n workflow should:

1. **Use the Supabase node** (not raw SQL)
2. **Set operation to "Upsert"**
3. **Match on:** `domain` for accounts, `email` for contacts
4. **This ensures idempotency** - running twice doesn't create duplicates

Example n8n Supabase node config:
```
Operation: Upsert
Table: contacts
Match: email
```

---

## Next Steps

After setting up your database:

1. ✅ Verify tables exist (run verification queries at end of schema.sql)
2. ✅ Add your Supabase credentials to `.env`
3. ✅ Run the Python cleaning scripts
4. ✅ Set up n8n workflow to load clean data
5. ✅ View your data in **Table Editor**

---

## Support

Questions about Supabase schema?
- 📚 [Supabase SQL Docs](https://supabase.com/docs/guides/database)
- 💬 [Join our WhatsApp community](link)
- 📧 [Email us](mailto:hello@billion.community)

---

*Schema v1.0 - Built for Agency Data Onboarding Kit*