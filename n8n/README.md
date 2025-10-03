# n8n Workflow

This folder contains the n8n workflow that orchestrates the entire data cleaning pipeline.

## File

- **`workflow_onboarding.json`** - Importable n8n workflow

---

## What This Workflow Does

The workflow automates the complete client data onboarding process:

1. ✅ **Detect CSV files** in `/incoming/` folder
2. ✅ **Run Python cleaning scripts** (contacts or accounts)
3. ✅ **Validate cleaning** succeeded
4. ✅ **Load clean data** to Supabase (upsert by domain/email)
5. ✅ **Link contacts to accounts** by email domain
6. ✅ **Generate run report** with statistics
7. ✅ **Archive original file** to dated folder
8. ✅ **Complete!** Ready for next run

**Runtime:** ~30 seconds for typical CSV (1,000-10,000 rows)

---

## Setup Instructions

### Prerequisites

Before importing the workflow, make sure you have:

1. ✅ **n8n installed** and running
2. ✅ **Python scripts** set up in `/scripts/` folder
3. ✅ **Supabase** database created with schema
4. ✅ **Environment variable** `PROJECT_PATH` set

### Step 1: Start n8n

```bash
# Using Docker (recommended)
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  -e PROJECT_PATH=/path/to/agency-data-onboarding-kit \
  n8nio/n8n

# Or using npm
npm install n8n -g
export PROJECT_PATH=/path/to/agency-data-onboarding-kit
n8n start
```

### Step 2: Set Environment Variable

The workflow needs to know where your project is located.

**Option A: Set in n8n UI**
1. Go to Settings → Environment Variables
2. Add variable:
   - Name: `PROJECT_PATH`
   - Value: `/full/path/to/agency-data-onboarding-kit`

**Option B: Set in terminal**
```bash
export PROJECT_PATH=/path/to/agency-data-onboarding-kit
n8n start
```

### Step 3: Configure Supabase Credentials

1. In n8n, go to **Credentials** (left sidebar)
2. Click **Add Credential**
3. Search for "Supabase"
4. Add your credentials:
   - **Host:** `https://your-project.supabase.co`
   - **Service Role Secret:** Your Supabase **anon key** (from Settings → API)
5. Click **Save**
6. Name it: "Supabase account"

**Important:** Use the **anon/public key**, not the service_role key!

### Step 4: Import Workflow

1. Open n8n UI (`http://localhost:5678`)
2. Click **"+"** (new workflow)
3. Click **⋮** (three dots) → **Import from File**
4. Select `workflow_onboarding.json`
5. Click **Import**

### Step 5: Update Supabase Nodes

The workflow has 4 Supabase nodes that need credentials:

1. **Upsert to Accounts**
2. **Upsert to Contacts**
3. **Find Account by Domain**
4. **Link Contact to Account**

For each node:
1. Click on the node
2. Under "Credentials", select "Supabase account"
3. Click **Save**

### Step 6: Create Required Folders

```bash
cd /path/to/agency-data-onboarding-kit

# Create folders if they don't exist
mkdir -p incoming
mkdir -p runs
mkdir -p archive/$(date +%Y-%m-%d)
```

### Step 7: Test the Workflow

1. Copy a sample CSV to `/incoming/`:
   ```bash
   cp samples/contacts_messy.csv incoming/
   ```

2. In n8n, click **"Execute Workflow"**

3. Watch the nodes light up green as they execute

4. Check the results:
   - Clean CSV in `/incoming/contacts_messy_clean.csv`
   - Run report in `/runs/[timestamp]_contacts_messy_report.md`
   - Original file moved to `/archive/[date]/`
   - Data in Supabase Table Editor

---

## Workflow Nodes Explained

### 1. Manual Trigger
- **What it does:** Starts the workflow
- **Future enhancement:** Replace with file watcher or cron schedule

### 2. List CSV Files
- **What it does:** Scans `/incoming/` folder for files
- **Type:** Read Binary Files node
- **Path:** `{{$env.PROJECT_PATH}}/incoming`

### 3. Check CSV Files
- **What it does:** Filters for `.csv` extension only
- **Type:** IF node
- **Condition:** fileName ends with ".csv"

### 4. No Files Found
- **What it does:** Stops workflow if no CSVs found
- **Type:** Stop and Error node
- **Triggers:** When Check CSV Files = false

### 5. Prepare File Metadata
- **What it does:** Determines if file is contacts or accounts
- **Type:** Code node (JavaScript)
- **Logic:** Checks if filename contains "contact"

### 6. Run Python Cleaning Script
- **What it does:** Executes `clean_contacts.py` or `clean_accounts.py`
- **Type:** Execute Command node
- **Command:** 
  ```bash
  cd {{$env.PROJECT_PATH}}/scripts && \
  source venv/bin/activate && \
  python clean_{{fileType}}.py \
    --input ../{{inputPath}} \
    --output ../{{outputPath}}
  ```

### 7. Check Cleaning Success
- **What it does:** Verifies Python script exit code = 0
- **Type:** IF node
- **Condition:** `code` equals "0"

### 8. Cleaning Failed
- **What it does:** Stops if cleaning failed
- **Type:** Stop and Error node
- **Shows:** Error message from Python script

### 9. Read Clean CSV
- **What it does:** Loads the cleaned CSV file
- **Type:** Read Binary File node
- **Path:** `{{outputPath}}`

### 10. CSV to JSON
- **What it does:** Converts CSV to JSON for Supabase
- **Type:** Convert to File node
- **Mode:** CSV to JSON

### 11. Route By Type
- **What it does:** Routes to accounts or contacts table
- **Type:** IF node
- **Condition:** fileType equals "accounts"

### 12. Upsert to Accounts
- **What it does:** Inserts/updates accounts table
- **Type:** Supabase node
- **Operation:** Upsert
- **Table:** accounts
- **Match on:** domain (prevents duplicates)

### 13. Upsert to Contacts
- **What it does:** Inserts/updates contacts table
- **Type:** Supabase node
- **Operation:** Upsert
- **Table:** contacts
- **Match on:** email (prevents duplicates)

### 14. Find Account by Domain
- **What it does:** Looks up account by email domain
- **Type:** Supabase node
- **Operation:** Get All
- **Filter:** domain = email_domain

### 15. Link Contact to Account
- **What it does:** Updates contact with account_id
- **Type:** Supabase node
- **Operation:** Update
- **Sets:** account_id field

### 16. Generate Run Report
- **What it does:** Creates markdown summary
- **Type:** Code node (JavaScript)
- **Outputs:** Timestamp, stats, report text

### 17. Save Report to File
- **What it does:** Writes report to `/runs/` folder
- **Type:** Write Binary File node
- **Filename:** `runs/[timestamp]_[filename]_report.md`

### 18. Archive Original File
- **What it does:** Moves CSV to `/archive/[date]/`
- **Type:** Execute Command node
- **Command:** `mv incoming/file.csv archive/$(date +%Y-%m-%d)/`

### 19. Pipeline Complete
- **What it does:** Marks end of workflow
- **Type:** No Op node
- **Purpose:** Visual indicator of completion

---

## Customization

### Add Email Notification

After "Generate Run Report", add:

**Node:** Send Email (or Slack, etc.)
```
Subject: Pipeline Run Complete - {{$json.fileName}}
Body: {{$json.report}}
```

### Add Slack Notification

After "Pipeline Complete":

**Node:** Slack
```
Channel: #data-pipeline
Message: ✅ Processed {{$('Generate Run Report').item.json.fileName}}
- Uploaded: {{$('Generate Run Report').item.json.uploadedCount}} records
- Report: [link to file]
```

### Schedule Automatic Runs

Replace "Manual Trigger" with:

**Node:** Cron
```
Cron Expression: 0 */6 * * *  (every 6 hours)
```

Or use:

**Node:** Webhook
```
Method: POST
Path: /onboarding-trigger
Authentication: Basic Auth
```

Then trigger via:
```bash
curl -X POST http://localhost:5678/webhook/onboarding-trigger
```

### Add Error Handling

After "Cleaning Failed", add:

**Node:** Send Email
```
To: admin@yourcompany.com
Subject: ⚠️ Pipeline Failed
Body: {{$json.stderr}}
```

### Process Multiple Files

The workflow already processes multiple files! Just add more CSVs to `/incoming/` and they'll all be processed in sequence.

---

## Troubleshooting

### "Command not found: python"

**Problem:** Python not in PATH or venv not activated

**Solution:** Update the "Run Python Cleaning Script" node:
```bash
# Use full path to Python
/usr/bin/python3 clean_contacts.py ...

# Or specify full path to venv
{{$env.PROJECT_PATH}}/scripts/venv/bin/python clean_contacts.py ...
```

### "Module 'polars' not found"

**Problem:** Virtual environment not activated or dependencies not installed

**Solution:**
```bash
cd scripts/
source venv/bin/activate
pip install -r requirements.txt
```

### "Supabase authentication failed"

**Problem:** Wrong credentials or expired key

**Solution:**
1. Go to Supabase dashboard
2. Settings → API
3. Copy the **anon/public key** (not service_role)
4. Update credentials in n8n

### "No such file or directory"

**Problem:** PROJECT_PATH environment variable not set

**Solution:**
```bash
# Check if set
echo $PROJECT_PATH

# Set it
export PROJECT_PATH=/full/path/to/agency-data-onboarding-kit

# Or add to n8n environment variables in UI
```

### "Permission denied"

**Problem:** n8n doesn't have permission to execute commands

**Solution:**
```bash
# Make scripts executable
chmod +x scripts/clean_contacts.py
chmod +x scripts/clean_accounts.py

# Or run n8n with proper permissions
```

### Workflow gets stuck

**Problem:** Python script hanging or infinite loop

**Solution:**
1. Check Python script logs
2. Add timeout to Execute Command node:
   - Click node → Parameters → Options → Timeout (ms): 60000 (1 minute)

### "Cannot read property of undefined"

**Problem:** Node referencing data from failed previous node

**Solution:**
1. Check each node's output
2. Click "Execute Node" to test individually
3. Verify data structure matches expectations

---

## Monitoring & Logs

### View Execution History

1. n8n UI → Executions
2. See all past runs with status
3. Click any execution to see detailed flow

### Check Run Reports

```bash
# View latest report
cat runs/latest_report.md

# List all reports
ls -lht runs/

# Search for failed runs
grep -r "Error" runs/
```

### Monitor Python Script Output

The workflow captures Python stdout/stderr. To see it:

1. Click on "Run Python Cleaning Script" node
2. View "stdout" and "stderr" in output

### Database Monitoring

In Supabase:
1. Go to **Database → Query Performance**
2. See slow queries
3. Monitor table sizes

---

## Performance Optimization

### For Large Files (100K+ rows)

1. **Increase timeout:**
   ```
   Execute Command node → Options → Timeout: 300000 (5 minutes)
   ```

2. **Process in batches:**
   - Split large CSV into smaller files
   - Or modify Python script to use chunking

3. **Use Supabase batch operations:**
   - Current workflow processes row-by-row
   - For huge datasets, use bulk insert APIs

### For Multiple Files

Current workflow processes files sequentially. To parallelize:

1. **Split by file type:**
   - One workflow for contacts
   - Another for accounts
   - Run simultaneously

2. **Use n8n's Split in Batches node:**
   ```
   After "Check CSV Files", add:
   Split in Batches (batch size: 1)
   This processes files in parallel
   ```

---

## Advanced Features

### Add Data Validation Rules

Before "Upsert to Contacts", add:

**Node:** IF (validation)
```javascript
// Check email domain is not blacklisted
const email = $json.email;
const domain = email.split('@')[1];
const blacklist = ['spam.com', 'fake.com'];
return !blacklist.includes(domain);
```

### Add Custom Enrichment

After "Upsert to Accounts", add:

**Node:** HTTP Request (to Clearbit/Apollo API)
```
URL: https://api.clearbit.com/v2/companies/find?domain={{$json.domain}}
Method: GET
Authentication: Bearer Token
```

Then update account with enriched data.

### Add Duplicate Detection Alert

After "Generate Run Report", add:

**Node:** IF
```
Condition: duplicates_removed > 10
Then: Send Slack alert "⚠️ High duplicate rate"
```

### Create Dashboard

Use the run reports to populate a dashboard:

1. Parse report files
2. Extract statistics
3. Send to Grafana/Metabase
4. Visualize trends over time

---

## Integration Examples

### Trigger from Google Drive

Replace Manual Trigger with:

**Node:** Google Drive Trigger
```
Event: File Updated
Folder ID: [your incoming folder]
```

### Trigger from Dropbox

**Node:** Dropbox Trigger
```
Event: New File
Path: /incoming
```

### Trigger from Webhook

**Node:** Webhook Trigger
```
HTTP Method: POST
Path: data-upload
```

Client uploads via:
```bash
curl -X POST \
  -F "file=@contacts.csv" \
  https://your-n8n.com/webhook/data-upload
```

### Send Report to Notion

After "Generate Run Report":

**Node:** Notion
```
Operation: Append to Database
Database: Pipeline Runs
Properties:
  - Timestamp: {{$json.timestamp}}
  - File: {{$json.fileName}}
  - Stats: {{$json.stats}}
```

---

## Production Checklist

Before deploying to production:

- [ ] Set up n8n on a server (not localhost)
- [ ] Use webhook or cron trigger (not manual)
- [ ] Add error notifications (email/Slack)
- [ ] Enable n8n authentication
- [ ] Use HTTPS for n8n
- [ ] Back up workflow JSON regularly
- [ ] Set up monitoring/alerting
- [ ] Test with production data
- [ ] Document any custom modifications
- [ ] Train team on how to use it

---

## Export Workflow

To back up or share your workflow:

1. Open workflow in n8n
2. Click **⋮** (three dots)
3. Click **Download**
4. Save as `workflow_onboarding_v2.json`

---

## Version History

**v1.0** - Initial release
- Manual trigger
- Basic cleaning pipeline
- Supabase upsert
- Run reports

**Future enhancements:**
- Webhook trigger
- Error recovery
- Batch processing
- Real-time monitoring dashboard

---

## Resources

- 📚 [n8n Documentation](https://docs.n8n.io/)
- 📺 [n8n YouTube Tutorials](https://www.youtube.com/c/n8n-io)
- 💬 [n8n Community Forum](https://community.n8n.io/)
- 📧 [Get help from Billion community](mailto:hello@billion.community)

---

## Next Steps

After setting up your workflow:

1. ✅ Test with sample data
2. ✅ Run with real client CSV
3. ✅ Verify data in Supabase
4. ✅ Share workflow with team
5. ✅ Set up monitoring
6. ✅ Document any customizations

---

*Workflow v1.0 - Built for Agency Data Onboarding Kit*