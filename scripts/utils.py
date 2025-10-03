"""
Utility functions for data cleaning
Used by clean_contacts.py and clean_accounts.py
"""

import re
from typing import Optional


# Country normalization mapping
COUNTRY_MAP = {
    "usa": "United States",
    "us": "United States",
    "united states": "United States",
    "u.s.": "United States",
    "u.s.a.": "United States",
    "uk": "United Kingdom",
    "gb": "United Kingdom",
    "united kingdom": "United Kingdom",
    "u.k.": "United Kingdom",
    "great britain": "United Kingdom",
}


def extract_domain(url: Optional[str]) -> Optional[str]:
    """
    Extract clean domain from a website URL or email
    
    Examples:
        https://www.acme-corp.com/about-us -> acme-corp.com
        ACME-CORP.COM -> acme-corp.com
        www.acme-corp.com/ -> acme-corp.com
    
    Args:
        url: Website URL or domain string
        
    Returns:
        Clean domain or None if invalid
    """
    if not url or url == "":
        return None
    
    # Convert to lowercase
    domain = str(url).lower().strip()
    
    # Remove common protocols
    domain = domain.replace("http://", "")
    domain = domain.replace("https://", "")
    
    # Remove www prefix
    domain = domain.replace("www.", "")
    
    # Take only the domain part (before first slash)
    domain = domain.split("/")[0]
    
    # Remove trailing dots
    domain = domain.rstrip(".")
    
    # Basic validation - should have at least one dot
    if "." not in domain:
        return None
    
    return domain


def normalize_country(country: Optional[str]) -> Optional[str]:
    """
    Normalize country names to standard format
    
    Examples:
        UK -> United Kingdom
        usa -> United States
        gb -> United Kingdom
    
    Args:
        country: Country name or code
        
    Returns:
        Standardized country name or original if not in mapping
    """
    if not country or country == "":
        return None
    
    # Clean and lowercase
    clean = str(country).strip().lower()
    
    # Look up in mapping
    if clean in COUNTRY_MAP:
        return COUNTRY_MAP[clean]
    
    # Return title case if not in mapping
    return country.strip().title()


def clean_phone(phone: Optional[str]) -> Optional[str]:
    """
    Clean phone numbers to consistent format
    Keeps only digits and leading + sign
    
    Examples:
        (555) 123-4567 -> 5551234567
        +1-555-234-5678 -> +15552345678
        +44 20 7123 4567 -> +442071234567
    
    Args:
        phone: Phone number in any format
        
    Returns:
        Cleaned phone number or None if empty
    """
    if not phone or phone == "":
        return None
    
    phone_str = str(phone).strip()
    
    # Check if it starts with +
    has_plus = phone_str.startswith("+")
    
    # Remove all non-digit characters
    digits_only = re.sub(r"[^0-9]", "", phone_str)
    
    # Return None if no digits found
    if not digits_only:
        return None
    
    # Add + back if it was there
    if has_plus:
        return f"+{digits_only}"
    
    return digits_only


def clean_linkedin_url(url: Optional[str]) -> Optional[str]:
    """
    Standardize LinkedIn URLs to consistent format
    
    Examples:
        linkedin.com/in/johndoe -> https://linkedin.com/in/johndoe
        https://www.linkedin.com/in/johndoe -> https://linkedin.com/in/johndoe
        www.linkedin.com/in/johndoe/ -> https://linkedin.com/in/johndoe
    
    Args:
        url: LinkedIn URL in any format
        
    Returns:
        Standardized LinkedIn URL or None if invalid
    """
    if not url or url == "":
        return None
    
    # Convert to lowercase and strip
    clean_url = str(url).lower().strip()
    
    # Remove protocol and www
    clean_url = clean_url.replace("https://", "")
    clean_url = clean_url.replace("http://", "")
    clean_url = clean_url.replace("www.", "")
    
    # Remove trailing slash
    clean_url = clean_url.rstrip("/")
    
    # Validate it's a LinkedIn URL
    if not clean_url.startswith("linkedin.com"):
        return None
    
    # Add standard protocol
    return f"https://{clean_url}"


def clean_email(email: Optional[str]) -> Optional[str]:
    """
    Clean and validate email addresses
    
    Args:
        email: Email address
        
    Returns:
        Cleaned lowercase email or None if invalid
    """
    if not email or email == "":
        return None
    
    # Convert to lowercase and strip
    clean = str(email).lower().strip()
    
    # Basic validation - must contain @
    if "@" not in clean:
        return None
    
    return clean


def is_valid_email(email: Optional[str]) -> bool:
    """
    Check if email is valid and not a generic/test email
    
    Args:
        email: Email address
        
    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False
    
    email_lower = email.lower()
    
    # Must contain @
    if "@" not in email_lower:
        return False
    
    # Filter out test/generic emails
    invalid_prefixes = ["test@", "example@", "info@", "admin@", "noreply@"]
    for prefix in invalid_prefixes:
        if email_lower.startswith(prefix):
            return False
    
    # Filter out common test domains
    invalid_domains = ["example.com", "test.com", "localhost"]
    domain = email_lower.split("@")[-1]
    if domain in invalid_domains:
        return False
    
    return True


def calculate_completeness_score(row_dict: dict, fields: list) -> int:
    """
    Calculate how complete a data row is based on non-null fields
    
    Args:
        row_dict: Dictionary representing a data row
        fields: List of field names to check
        
    Returns:
        Count of non-null/non-empty fields
    """
    score = 0
    for field in fields:
        value = row_dict.get(field)
        if value and value != "" and value != "N/A":
            score += 1
    return score


def normalize_column_name(col: str) -> str:
    """
    Normalize column names to snake_case
    
    Examples:
        "Full Name " -> "full_name"
        "Email Address" -> "email_address"
        "company_name" -> "company_name"
    
    Args:
        col: Original column name
        
    Returns:
        Normalized column name
    """
    # Strip whitespace
    clean = col.strip()
    
    # Convert to lowercase
    clean = clean.lower()
    
    # Replace spaces with underscores
    clean = clean.replace(" ", "_")
    
    # Remove any duplicate underscores
    while "__" in clean:
        clean = clean.replace("__", "_")
    
    return clean


def get_column_mapping(actual_columns: list, expected_schema: dict) -> dict:
    """
    Map actual CSV columns to expected schema
    Handles common variations in column naming
    
    Args:
        actual_columns: List of actual column names from CSV
        expected_schema: Dict of {canonical_name: [possible_variations]}
        
    Returns:
        Dict mapping actual columns to canonical names
    """
    mapping = {}
    
    # Normalize actual columns
    normalized_actual = {normalize_column_name(col): col for col in actual_columns}
    
    # For each expected field, find matching actual column
    for canonical, variations in expected_schema.items():
        for variation in variations:
            normalized_variation = normalize_column_name(variation)
            if normalized_variation in normalized_actual:
                actual_col = normalized_actual[normalized_variation]
                mapping[actual_col] = canonical
                break
    
    return mapping


# Common column name variations for contacts
CONTACT_COLUMN_SCHEMA = {
    "full_name": ["full_name", "full name", "name", "contact name", "contact_name"],
    "email": ["email", "email address", "email_address", "e-mail", "contact email"],
    "company_name": ["company_name", "company name", "company", "account", "organization"],
    "title": ["title", "job title", "job_title", "position", "role"],
    "phone": ["phone", "phone number", "phone_number", "telephone", "mobile"],
    "country": ["country", "country/region", "location", "region"],
    "linkedin": ["linkedin", "linkedin url", "linkedin_url", "linkedin profile"],
}


# Common column name variations for accounts
ACCOUNT_COLUMN_SCHEMA = {
    "name": ["name", "company name", "company_name", "account name", "organization"],
    "website": ["website", "web site", "url", "company website", "domain"],
    "industry": ["industry", "sector", "vertical", "business type"],
    "employee_count": ["employee_count", "employee count", "employees", "company size", "headcount"],
    "country": ["country", "country/region", "billing country", "location"],
}


if __name__ == "__main__":
    # Test the utility functions
    print("Testing utility functions...")
    
    # Test domain extraction
    print("\n--- Domain Extraction ---")
    test_urls = [
        "https://www.acme-corp.com/about-us",
        "ACME-CORP.COM",
        "www.acme-corp.com/",
        "http://techflow.io",
    ]
    for url in test_urls:
        print(f"{url:40} -> {extract_domain(url)}")
    
    # Test country normalization
    print("\n--- Country Normalization ---")
    test_countries = ["USA", "uk", "United Kingdom", "GB", "France"]
    for country in test_countries:
        print(f"{country:20} -> {normalize_country(country)}")
    
    # Test phone cleaning
    print("\n--- Phone Cleaning ---")
    test_phones = [
        "(555) 123-4567",
        "+1-555-234-5678",
        "+44 20 7123 4567",
        "07700 900123",
    ]
    for phone in test_phones:
        print(f"{phone:20} -> {clean_phone(phone)}")
    
    # Test email validation
    print("\n--- Email Validation ---")
    test_emails = [
        "sarah.johnson@acme.com",
        "test@example.com",
        "info@company.com",
        "valid.user@company.co.uk",
    ]
    for email in test_emails:
        print(f"{email:30} -> Valid: {is_valid_email(email)}")
    
    print("\n✅ All utility functions tested!")