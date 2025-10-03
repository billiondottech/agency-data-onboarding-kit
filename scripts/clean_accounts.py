"""
Account data cleaning script
Cleans and deduplicates company/account data from CSV exports

Usage:
    python clean_accounts.py --input incoming/accounts.csv --output incoming/accounts_clean.csv
"""

import argparse
import sys
from pathlib import Path
import polars as pl
from utils import (
    extract_domain,
    normalize_country,
    normalize_column_name,
    ACCOUNT_COLUMN_SCHEMA,
)


def clean_accounts(input_path: str, output_path: str, verbose: bool = True) -> dict:
    """
    Clean account/company data from CSV
    
    Args:
        input_path: Path to input CSV file
        output_path: Path to save cleaned CSV
        verbose: Print progress messages
        
    Returns:
        Dict with cleaning statistics
    """
    
    if verbose:
        print(f"📂 Reading accounts from: {input_path}")
    
    # Load CSV
    try:
        df = pl.read_csv(input_path)
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        sys.exit(1)
    
    original_count = len(df)
    if verbose:
        print(f"📊 Loaded {original_count} rows")
        print(f"📋 Columns: {df.columns}")
    
    # Step 1: Normalize column names
    if verbose:
        print("\n🔧 Step 1: Normalizing column names...")
    
    df = df.rename({
        col: normalize_column_name(col)
        for col in df.columns
    })
    
    if verbose:
        print(f"   ✅ Normalized to: {df.columns}")
    
    # Step 2: Clean company name
    if verbose:
        print("\n🔧 Step 2: Cleaning company names...")
    
    # Check for name column variations
    name_col = None
    for possible in ["name", "company_name", "company", "account_name"]:
        if possible in df.columns:
            name_col = possible
            break
    
    if not name_col:
        print("❌ Error: Could not find company name column")
        sys.exit(1)
    
    # Standardize to 'name'
    if name_col != "name":
        df = df.rename({name_col: "name"})
    
    # Clean name field
    df = df.with_columns([
        pl.col("name").str.strip().alias("name")
    ])
    
    if verbose:
        print("   ✅ Company names cleaned")
    
    # Step 3: Extract and clean domains
    if verbose:
        print("\n🔧 Step 3: Extracting domains from websites...")
    
    # Check for website column
    website_col = None
    for possible in ["website", "web_site", "url", "domain"]:
        if possible in df.columns:
            website_col = possible
            break
    
    if website_col:
        # Standardize to 'website'
        if website_col != "website":
            df = df.rename({website_col: "website"})
        
        # Clean website and extract domain
        df = df.with_columns([
            pl.col("website").str.to_lowercase().str.strip().alias("website"),
            pl.col("website")
              .map_elements(extract_domain, return_dtype=pl.Utf8)
              .alias("domain")
        ])
        
        if verbose:
            print("   ✅ Domains extracted from websites")
    else:
        if verbose:
            print("   ⚠️ No website column found, creating empty domain column")
        df = df.with_columns([
            pl.lit(None, dtype=pl.Utf8).alias("domain")
        ])
    
    # Step 4: Clean and standardize other fields
    if verbose:
        print("\n🔧 Step 4: Standardizing data fields...")
    
    # Country normalization
    if "country" in df.columns:
        df = df.with_columns([
            pl.col("country").map_elements(normalize_country, return_dtype=pl.Utf8).alias("country")
        ])
        if verbose:
            print("   ✅ Normalized countries")
    
    # Clean industry
    if "industry" in df.columns:
        df = df.with_columns([
            pl.col("industry").str.strip().str.title().alias("industry")
        ])
        if verbose:
            print("   ✅ Standardized industries")
    
    # Clean employee_count (ensure it's numeric)
    if "employee_count" in df.columns:
        df = df.with_columns([
            pl.col("employee_count").cast(pl.Int32, strict=False).alias("employee_count")
        ])
        if verbose:
            print("   ✅ Validated employee counts")
    
    # Clean status
    if "status" in df.columns:
        df = df.with_columns([
            pl.col("status").str.to_lowercase().str.strip().alias("status")
        ])
    else:
        # Add default status
        df = df.with_columns([
            pl.lit("prospect").alias("status")
        ])
    
    # Step 5: Filter out invalid records
    if verbose:
        print("\n🔧 Step 5: Filtering invalid records...")
    
    before_filter = len(df)
    
    # Filter: must have name
    df = df.filter(
        pl.col("name").is_not_null() & (pl.col("name") != "")
    )
    
    invalid_count = before_filter - len(df)
    if verbose:
        print(f"   🗑️ Removed {invalid_count} rows with missing names")
    
    # Step 6: Calculate completeness score for deduplication
    if verbose:
        print("\n🔧 Step 6: Calculating data completeness...")
    
    # Calculate completeness score
    completeness_fields = []
    for field in ["name", "domain", "industry", "employee_count", "country"]:
        if field in df.columns:
            completeness_fields.append(field)
    
    if completeness_fields:
        score_expr = None
        for field in completeness_fields:
            field_score = pl.col(field).is_not_null().cast(pl.Int32)
            if score_expr is None:
                score_expr = field_score
            else:
                score_expr = score_expr + field_score
        
        df = df.with_columns([
            score_expr.alias("completeness_score")
        ])
    
    # Step 7: Deduplicate by domain (or name if no domain)
    if verbose:
        print("\n🔧 Step 7: Deduplicating accounts...")
    
    before_dedup = len(df)
    
    # Deduplicate by domain first (if domain exists and is not null)
    df_with_domain = df.filter(pl.col("domain").is_not_null())
    df_without_domain = df.filter(pl.col("domain").is_null())
    
    if len(df_with_domain) > 0:
        df_with_domain = (
            df_with_domain
            .sort("completeness_score", descending=True)
            .unique(subset=["domain"], keep="first")
        )
        if verbose:
            domain_dupes = before_dedup - len(df_with_domain) - len(df_without_domain)
            if domain_dupes > 0:
                print(f"   🗑️ Removed {domain_dupes} duplicate domains")
    
    # For records without domain, deduplicate by name (case-insensitive)
    if len(df_without_domain) > 0:
        df_without_domain = df_without_domain.with_columns([
            pl.col("name").str.to_lowercase().alias("name_lower")
        ])
        df_without_domain = (
            df_without_domain
            .sort("completeness_score", descending=True)
            .unique(subset=["name_lower"], keep="first")
            .drop("name_lower")
        )
    
    # Combine back together
    if len(df_with_domain) > 0 and len(df_without_domain) > 0:
        df = pl.concat([df_with_domain, df_without_domain])
    elif len(df_with_domain) > 0:
        df = df_with_domain
    else:
        df = df_without_domain
    
    # Drop completeness score
    if "completeness_score" in df.columns:
        df = df.drop("completeness_score")
    
    duplicate_count = before_dedup - len(df)
    if verbose:
        print(f"   🗑️ Total duplicates removed: {duplicate_count}")
    
    # Step 8: Add metadata
    df = df.with_columns([
        pl.lit("sheet").alias("source")
    ])
    
    # Step 9: Export cleaned data
    final_count = len(df)
    
    if verbose:
        print(f"\n💾 Saving cleaned data to: {output_path}")
    
    try:
        df.write_csv(output_path)
        if verbose:
            print(f"✅ Saved {final_count} clean accounts")
    except Exception as e:
        print(f"❌ Error saving CSV: {e}")
        sys.exit(1)
    
    # Generate statistics
    stats = {
        "original_count": original_count,
        "invalid_filtered": invalid_count,
        "duplicates_removed": duplicate_count,
        "final_count": final_count,
        "data_retained_pct": round((final_count / original_count) * 100, 1) if original_count > 0 else 0,
    }
    
    # Print summary
    if verbose:
        print("\n" + "=" * 60)
        print("📊 CLEANING SUMMARY")
        print("=" * 60)
        print(f"  Original rows:           {stats['original_count']}")
        print(f"  Invalid records filtered:{stats['invalid_filtered']}")
        print(f"  Duplicates removed:      {stats['duplicates_removed']}")
        print(f"  Final clean rows:        {stats['final_count']}")
        print(f"  Data retained:           {stats['data_retained_pct']}%")
        print("=" * 60)
        print("✅ Account cleaning complete!\n")
    
    return stats


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Clean and deduplicate account/company data from CSV"
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Input CSV file path"
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output CSV file path"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress progress messages"
    )
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not Path(args.input).exists():
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(1)
    
    # Create output directory if needed
    output_dir = Path(args.output).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run cleaning
    stats = clean_accounts(
        input_path=args.input,
        output_path=args.output,
        verbose=not args.quiet
    )
    
    # Exit with success
    sys.exit(0)


if __name__ == "__main__":
    main()