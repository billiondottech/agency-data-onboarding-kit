# Production Scripts

These are production-ready Python scripts for cleaning client data. They're designed to be called by n8n or run manually from the command line.

## Files

- **`utils.py`** - Shared utility functions for data cleaning
- **`clean_contacts.py`** - Cleans contact/people data
- **`clean_accounts.py`** - Cleans company/account data
- **`requirements.txt`** - Python dependencies

---

## Setup

### 1. Create Virtual Environment

```bash
cd scripts/
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Usage

### Clean Contacts

```bash
python clean_contacts.py --input ../incoming/contacts.csv --output ../incoming/contacts_clean.csv
```

**What it does:**
- ✅ Normalizes column names to snake_case
- ✅ Cleans and validates email addresses
- ✅ Extracts domains from emails
- ✅ Normalizes country names (UK → United Kingdom)
- ✅ Cleans phone numbers (removes formatting)
- ✅ Standardizes LinkedIn URLs
- ✅ Filters out invalid/test emails
- ✅ Deduplicates by email (keeps most complete record)
- ✅ Adds source metadata

**Output:** Clean CSV with deduplicated contacts

### Clean Accounts

```bash
python clean_accounts.py --input ../incoming/accounts.csv --output ../incoming/accounts_clean.csv
```

**What it does:**
- ✅ Normalizes column names
- ✅ Cleans company names
- ✅ Extracts domains from websites
- ✅ Normalizes country names
- ✅ Standardizes industry names
- ✅ Validates employee counts
- ✅ Filters out invalid records (missing name)
- ✅ Deduplicates by domain (or name if no domain)
- ✅ Adds source metadata

**Output:** Clean CSV with deduplicated accounts

---

## Command Line Options

Both scripts support:

- `--input, -i`: Input CSV file path (required)
- `--output, -o`: Output CSV file path (required)
- `--quiet, -q`: Suppress progress messages

**Examples:**

```bash
# Verbose output (default)
python clean_contacts.py -i data.csv -o clean.csv

# Quiet mode
python clean_contacts.py -i data.csv -o clean.csv --quiet
```

---

## Testing the Scripts

### Test with Sample Data

```bash
# Test contacts cleaning
python clean_contacts.py \
  --input ../samples/contacts_messy.csv \
  --output ../samples/contacts_clean_test.csv

# Test accounts cleaning
python clean_accounts.py \
  --input ../samples/accounts_messy.csv \
  --output ../samples/accounts_clean_test.csv
```

### Test Utility Functions

```bash
python utils.py
```

This runs the built-in tests for all utility functions and prints results.

---

## Integration with n8n

These scripts are designed to be called from n8n using the **Execute Command** node.

### n8n Configuration

**Node:** Execute Command

**Command:**
```bash
cd /path/to/agency-data-onboarding-kit/scripts && \
source venv/bin/activate && \
python clean_contacts.py \
  --input ../incoming/{{ $json.filename }} \
  --output ../incoming/{{ $json.filename.replace('.csv', '_clean.csv') }}
```

**Capture Output:** Yes (to get statistics in JSON)

---

## Cleaning Statistics

Both scripts return statistics in this format:

```python
{
    "original_count": 41,
    "invalid_filtered": 3,
    "duplicates_removed": 5,
    "final_count": 33,
    "data_retained_pct": 80.5
}
```

Use these stats in your n8n workflow to generate reports!

---

## Utility Functions Reference

### Domain Extraction

```python
from utils import extract_domain

extract_domain("https://www.acme-corp.com/about")
# Returns: "acme-corp.com"
```

### Country Normalization

```python
from utils import normalize_country

normalize_country("UK")  # Returns: "United Kingdom"
normalize_country("usa") # Returns: "United States"
```

### Phone Cleaning

```python
from utils import clean_phone

clean_phone("(555) 123-4567")    # Returns: "5551234567"
clean_phone("+1-555-234-5678")   # Returns: "+15552345678"
```

### Email Validation

```python
from utils import is_valid_email

is_valid_email("sarah@acme.com")      # Returns: True
is_valid_email("test@example.com")    # Returns: False (test email)
is_valid_email("info@company.com")    # Returns: False (generic)
```

### LinkedIn URL Cleaning

```python
from utils import clean_linkedin_url

clean_linkedin_url("linkedin.com/in/john")
# Returns: "https://linkedin.com/in/john"
```

---

## Customization

### Adding Custom Country Mappings

Edit `utils.py`:

```python
COUNTRY_MAP = {
    # ... existing mappings ...
    "de": "Germany",
    "deutschland": "Germany",
    "fr": "France",
    # Add your custom mappings here
}
```

### Adding Custom Column Name Variations

Edit `utils.py`:

```python
CONTACT_COLUMN_SCHEMA = {
    "email": ["email", "email address", "e-mail", "your_custom_column_name"],
    # ... other fields ...
}
```

### Changing Deduplication Logic

Edit `clean_contacts.py` or `clean_accounts.py`:

```python
# Current: keeps most complete record
df = df.sort("completeness_score", descending=True).unique(subset=["email"], keep="first")

# Alternative: keep most recent (if you have a date column)
df = df.sort("created_date", descending=True).unique(subset=["email"], keep="first")
```

---

## Error Handling

### Common Issues

**1. "Email column not found"**
- Your CSV doesn't have an email column
- Solution: Add `email` column or update `CONTACT_COLUMN_SCHEMA` in `utils.py`

**2. "ModuleNotFoundError: No module named 'polars'"**
- Virtual environment not activated or dependencies not installed
- Solution: Run `source venv/bin/activate` and `pip install -r requirements.txt`

**3. "Input file not found"**
- File path is incorrect
- Solution: Use absolute paths or check your current directory

**4. "Too many rows dropped"**
- Your data doesn't match expected schema
- Solution: Add debug logging to see which rows are being filtered

---

## Performance

These scripts are optimized for agency use cases:

- **1,000 rows:** ~1 second
- **10,000 rows:** ~3 seconds
- **100,000 rows:** ~15 seconds

Polars uses lazy evaluation and parallel processing, so it's much faster than Pandas.

---

## Next Steps

After running these scripts:

1. **Load to Supabase** - Use n8n's Supabase node to upsert the cleaned data
2. **Generate reports** - Use the statistics to create run reports
3. **Automate** - Set up n8n workflow to run on file uploads

See the main README for the complete pipeline setup!