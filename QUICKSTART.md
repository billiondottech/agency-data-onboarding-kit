# Agency Data Onboarding Kit

> **Turn messy client data into clean, actionable intelligence in under 30 minutes**

A complete toolkit for AI automation agencies to onboard client data without the manual headache. Built by the [Billion community](https://billion.community) for agency operators who want to ship fast and iterate publicly.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/billiondottech/agency-data-onboarding-kit/blob/main/notebooks/learn_polars_cleaning.ipynb)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 The Problem

Every AI agency faces this on day one with a new client:

**"Can you send us your contact data?"**

What arrives is chaos:
- Excel files with merged cells and color-coded columns
- Countries as "UK", "GB", "United Kingdom", "U.K."
- Phone numbers in 17 different formats
- Duplicate contacts (is Sarah Johnson the same as S. Johnson?)
- Generic emails mixed with decision-makers

Your team spends **hours (sometimes days)** cleaning this manually. Every. Single. Time.

## ✨ The Solution

This kit gives you a **reusable pipeline** that:
- ✅ Accepts any CSV export (Google Sheets, HubSpot, Excel)
- ✅ Automatically cleans, standardizes, and deduplicates
- ✅ Loads into a proper database (Supabase)
- ✅ Generates a human-readable report
- ✅ Runs in under 5 minutes per client

**Before**: 4 hours of manual Excel hell  
**After**: Drop CSV → Click Run → Clean data in 3 minutes

---

## 📦 What's Included

### 1. **Interactive Learning Notebook** 📓
Start here! A Google Colab notebook that teaches you Polars interactively.
- Upload your own messy CSV
- See each transformation step-by-step
- Understand the logic before automating
- **[👉 Open in Colab](link-to-notebook)**

### 2. **Production Scripts** 🐍
Ready-to-run Python scripts for automation:
- `clean_accounts.py` - Company data cleaning
- `clean_contacts.py` - Contact data cleaning
- `utils.py` - Reusable transformation functions

### 3. **n8n Workflow** 🔄
Visual automation that orchestrates everything:
- Watch folder for new CSVs
- Run cleaning scripts
- Load to Supabase
- Generate run reports
- **Importable JSON** - just drag and drop

### 4. **Supabase Schema** 🗄️
Production-ready database schema:
- `accounts` table (companies)
- `contacts` table (people)
- `do_not_contact` table (compliance)
- Proper indexes and foreign keys

### 5. **Sample Data** 📊
Realistic messy CSVs to practice with:
- `accounts_messy.csv` - 20 companies with chaos
- `contacts_messy.csv` - 41 contacts with duplicates
- `hubspot_contacts.csv` - HubSpot export format

### 6. **Complete Playbook** 📖
12-page guide covering:
- Why this stack (Polars + n8n + Supabase)
- Step-by-step setup instructions
- Troubleshooting common issues
- Security & compliance best practices

---

# Quick Start Guide

Get your first pipeline running in **30 minutes**.

---

## Prerequisites

Before you start, make sure you have:

- [ ] **Python 3.9+** installed (`python3 --version`)
- [ ] **Docker** installed (for n8n)
- [ ] **Supabase account** (free tier works)
- [ ] **10 minutes** of focused time

---

## Step 1: Clone the Repository (2 minutes)

```bash
git clone https://github.com/billion-community/agency-data-onboarding-kit.git
cd agency-data-onboarding-kit
```

---

## Step 2: Set Up Python Environment (3 minutes)

```bash
cd scripts/
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

**Test it works:**
```bash
python scripts/utils.py
# Should see "✅ All utility functions tested!"
```

---

## Step 3: Set Up Supabase (5 minutes)

### 3a. Create Project

1. Go to [supabase.com](https://supabase.com)
2. Click **New Project**
3. Name it: `agency-data-dev`
4. Choose region, set password
5. Wait 2 minutes for provisioning

### 3b. Run Schema

1. Go to **SQL Editor** in Supabase dashboard
2. Click **New Query**
3. Copy all contents from `supabase/schema.sql`
4. Paste and click **Run**
5. Wait for "Success" message

### 3c. Get Credentials

1. Go to **Settings → API**
2. Copy:
   - **Project URL**
   - **Anon/Public Key**

### 3d. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

---

## Step 4: Test Python Scripts (5 minutes)

```bash
# Test with sample contacts
python scripts/clean_contacts.py \
  --input samples/contacts_messy.csv \
  --output samples/contacts_clean_test.csv

# You should see:
# ✅ Cleaned 38 contacts
# 📊 CLEANING SUMMARY
# ...
```

Check the output:
```bash
head samples/contacts_clean_test.csv
```

---

## Step 5: Set Up n8n (10 minutes)

### 5a. Start n8n

```bash
# Set project path
export PROJECT_PATH=$(pwd)

# Start n8n with Docker
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  -e PROJECT_PATH=$PROJECT_PATH \
  n8nio/n8n
```

Open browser: `http://localhost:5678`

Create your account (stored locally).

### 5b. Add Supabase Credentials

1. Click **Credentials** (left sidebar)
2. Click **Add Credential**
3. Search "Supabase"
4. Enter:
   - **Host:** Your Supabase URL
   - **Service Role Secret:** Your anon key
5. Click **Save**, name it "Supabase account"

### 5c. Import Workflow

1. Click **+** (new workflow)
2. Click **⋮** (three dots) → **Import from File**
3. Select `n8n/workflow_onboarding.json`
4. Click **Import**

### 5d. Update Supabase Nodes

For these 4 nodes, set credentials to "Supabase account":
- Upsert to Accounts
- Upsert to Contacts  
- Find Account by Domain
- Link Contact to Account

Click **Save Workflow**.

---

## Step 6: Run Your First Pipeline! (5 minutes)

### 6a. Prepare Folders

```bash
mkdir -p incoming runs archive/$(date +%Y-%m-%d)
```

### 6b. Add Sample Data

```bash
cp samples/contacts_messy.csv incoming/
```

### 6c. Execute Workflow

In n8n:
1. Click **Execute Workflow** button
2. Watch nodes turn green (takes ~10 seconds)
3. See "Success" message

### 6d. Check Results

**In Terminal:**
```bash
# View run report
cat runs/*_contacts_messy_report.md

# Check clean CSV
head incoming/contacts_messy_clean.csv

# Verify archive
ls archive/$(date +%Y-%m-%d)/
```

**In Supabase:**
1. Go to **Table Editor**
2. Open `contacts` table
3. See your clean data! 🎉

---

## 🎉 Success!

You just:
- ✅ Cleaned 41 messy contacts → 38 clean records
- ✅ Removed duplicates and invalid emails
- ✅ Loaded to Supabase database
- ✅ Generated a run report

**What changed:**
- Mixed case emails → lowercase
- Phone formats → standardized
- Country variations → normalized
- Duplicates → removed
- Invalid emails → filtered

---

## Next Steps

### Learn Interactively

Open the Colab notebook:
```
https://colab.research.google.com/github/billion-community/agency-data-onboarding-kit/blob/main/notebooks/learn_polars_cleaning.ipynb
```

Run through it to understand **how** the cleaning works.

### Try Your Own Data

1. Export contacts from your CRM to CSV
2. Copy to `incoming/your_data.csv`
3. Run the n8n workflow
4. Check Supabase for results

### Customize for Your Needs

**Add custom country mappings:**
Edit `scripts/utils.py`:
```python
COUNTRY_MAP = {
    # ... existing mappings ...
    "de": "Germany",
    "your_code": "Your Country"
}
```

**Change deduplication logic:**
Edit `scripts/clean_contacts.py` - search for "deduplicate"

**Add email notifications:**
In n8n, add a Send Email node after "Generate Run Report"

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'polars'"
```bash
cd scripts/
source venv/bin/activate
pip install -r requirements.txt
```

### "Command not found: python"
Update n8n workflow node to use `python3` instead of `python`

### "Supabase authentication failed"
- Check you're using the **anon key**, not service_role key
- Verify URL starts with `https://`

### "No CSV files found"
```bash
# Check files are in the right place
ls incoming/

# Ensure PROJECT_PATH is set
echo $PROJECT_PATH
```

### Workflow stuck
- Check Python script didn't error: click "Run Python Cleaning Script" node
- View stdout/stderr in node output
- Verify CSV file isn't corrupted

---

## Get Help

**Something not working?**

1. 📖 Check the detailed READMEs in each folder:
   - `/scripts/README.md` - Python troubleshooting
   - `/supabase/README.md` - Database issues
   - `/n8n/README.md` - Workflow problems

2. 💬 Join the community:
   - [WhatsApp Group](link)
   - [GitHub Issues](https://github.com/billion-community/agency-data-onboarding-kit/issues)

3. 📧 Email us:
   - hello@billion.community

---

## What's Next?

Now that your pipeline works:

1. **Process real client data** - Start small, validate results
2. **Set up monitoring** - Add Slack/email notifications
3. **Automate triggers** - Replace manual trigger with webhooks
4. **Share with team** - Export workflow JSON, document customizations
5. **Join community** - Share your wins, help others

---

## Advanced Learning

**Want to go deeper?**

- 📖 **Read the detailed READMEs** in each folder
- 🎓 **Get the complete playbook** at [billion.community](https://billion.community)
- 🔬 **Experiment** - Modify the scripts, break things, learn
- 💬 **Share** - Show the community what you built

---

**You're now ready to onboard clients 10x faster!** 🚀

Questions? Stuck? Want to show off your results?

👉 [Join the Billion WhatsApp community](link)

---

*Quick Start v1.0 - Get running in 30 minutes*