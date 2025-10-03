"""
Contact data cleaning script
Cleans and deduplicates contact/people data from CSV exports

Usage:
    python clean_contacts.py --input incoming/contacts.csv --output incoming/contacts_clean.csv
"""

import argparse
import sys
from pathlib import Path
import polars as pl
from utils import (
    extract_domain,
    normalize_country,
    clean_phone,
    clean_linkedin_url,
    clean_email,
    is_valid_email,
    normalize_column_name,
    CONTACT_COLUMN_SCHEMA,
)


def clean_contacts(input_path: str, output_path: str, verbose: bool = True) -> dict:
    """
    Clean contact data from CSV
    
    Args:
        input_path: Path to input CSV file
        output_path: Path to save cleaned CSV
        verbose: Print progress messages
        
    Returns:
        Dict with cleaning statistics
    """
    
    if verbose:
        print(f"📂 Reading contacts from: {input_path}")
    
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
    
    # Step 2: Clean email addresses (critical field)
    if verbose:
        print("\n🔧 Step 2: Cleaning email addresses...")
    
    if "email" in df.columns:
        df = df.with_columns([
            pl.col("email").map_elements(clean_email, return_dtype=pl.Utf8).alias("email")
        ])
    else:
        print("⚠️ Warning: No 'email' column found. Checking for alternatives...")
        # Try to find email column with different name
        possible_email_cols = ["email_address", "e_mail", "contact_email"]
        found = False
        for col in possible_email_cols:
            if col in df.columns:
                df = df.rename({col: "email"})
                df = df.with_columns([
                    pl.col("email").map_elements(clean_email, return_dtype=pl.Utf8).alias("email")
                ])
                found = True
                if verbose:
                    print(f"   ✅ Found email column: {col}")
                break
        
        if not found:
            print("❌ Error: Could not find email column. Cannot proceed.")
            sys.exit(1)
    
    # Step 3: Extract domain from email
    if verbose:
        print("\n🔧 Step 3: Extracting domains from emails...")
    
    df = df.with_columns([
        pl.col("email")
          .str.split("@")
          .list.get(1)
          .alias("email_domain")
    ])
    
    # Step 4: Clean and standardize fields
    if verbose:
        print("\n🔧 Step 4: Standardizing data fields...")
    
    # Country normalization
    if "country" in df.columns:
        df = df.with_columns([
            pl.col("country").map_elements(normalize_country, return_dtype=pl.Utf8).alias("country")
        ])
        if verbose:
            print("   ✅ Normalized countries")
    
    # Phone cleaning
    if "phone" in df.columns:
        df = df.with_columns([
            pl.col("phone").map_elements(clean_phone, return_dtype=pl.Utf8).alias("phone")
        ])
        if verbose:
            print("   ✅ Cleaned phone numbers")
    
    # LinkedIn URL cleaning
    if "linkedin" in df.columns:
        df = df.with_columns([
            pl.col("linkedin").map_elements(clean_linkedin_url, return_dtype=pl.Utf8).alias("linkedin")
        ])
        if verbose:
            print("   ✅ Standardized LinkedIn URLs")
    
    # Clean full_name if exists
    if "full_name" in df.columns:
        df = df.with_columns([
            pl.col("full_name").str.strip().alias("full_name")
        ])
    
    # Clean title if exists
    if "title" in df.columns:
        df = df.with_columns([
            pl.col("title")
              .str.strip()
              .map_elements(lambda x: None if x == "N/A" else x, return_dtype=pl.Utf8)
              .alias("title")
        ])
    
    # Step 5: Filter out invalid emails
    if verbose:
        print("\n🔧 Step 5: Filtering invalid emails...")
    
    before_filter = len(df)
    
    # Filter rows with valid emails
    df = df.filter(
        pl.col("email").map_elements(is_valid_email, return_dtype=pl.Boolean)
    )
    
    invalid_count = before_filter - len(df)
    if verbose:
        print(f"   🗑️ Removed {invalid_count} rows with invalid emails")
    
    # Step 6: Calculate completeness score for deduplication
    if verbose:
        print("\n🔧 Step 6: Calculating data completeness...")
    
    # Calculate completeness score (used for keeping best duplicate)
    completeness_fields = []
    for field in ["full_name", "email", "title", "phone", "linkedin"]:
        if field in df.columns:
            completeness_fields.append(field)
    
    if completeness_fields:
        # Build completeness score expression
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
    
    # Step 7: Deduplicate by email (keep most complete)
    if verbose:
        print("\n🔧 Step 7: Deduplicating contacts...")
    
    before_dedup = len(df)
    
    # Sort by completeness score (highest first) then deduplicate
    df = (
        df.sort("completeness_score", descending=True)
          .unique(subset=["email"], keep="first")
    )
    
    # Drop completeness score column
    if "completeness_score" in df.columns:
        df = df.drop("completeness_score")
    
    duplicate_count = before_dedup - len(df)
    if verbose:
        print(f"   🗑️ Removed {duplicate_count} duplicate contacts")
    
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
            print(f"✅ Saved {final_count} clean contacts")
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
        print(f"  Invalid emails filtered: {stats['invalid_filtered']}")
        print(f"  Duplicates removed:      {stats['duplicates_removed']}")
        print(f"  Final clean rows:        {stats['final_count']}")
        print(f"  Data retained:           {stats['data_retained_pct']}%")
        print("=" * 60)
        print("✅ Contact cleaning complete!\n")
    
    return stats


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Clean and deduplicate contact data from CSV"
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
    stats = clean_contacts(
        input_path=args.input,
        output_path=args.output,
        verbose=not args.quiet
    )
    
    # Exit with success
    sys.exit(0)


if __name__ == "__main__":
    main()