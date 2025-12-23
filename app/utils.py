import pandas as pd
import os
from werkzeug.utils import secure_filename
import re

ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _read_file_to_df(file_storage):
    """Helper to read CSV or Excel into DataFrame."""
    try:
        filename = secure_filename(file_storage.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        
        # Reset file pointer to beginning just in case
        file_storage.seek(0)
        
        if ext == 'csv':
            # Try reading with default engine, handle common encoding issues if needed
            df = pd.read_csv(file_storage)
        else:
            df = pd.read_excel(file_storage)
        
        return df, None
    except Exception as e:
        return None, str(e)

def get_file_headers(file_storage):
    """
    Reads the file and returns a list of column headers.
    """
    df, error = _read_file_to_df(file_storage)
    if error:
        return None, error
        
    return df.columns.tolist(), None

def parse_recipient_file(file_storage, email_col_name):
    """
    Parses a CSV or Excel file and returns a list of unique valid emails.
    Strictly validates the selected column.
    """
    df, error = _read_file_to_df(file_storage)
    if error:
        return None, error
        
    # Normalize headers to match user input (strip whitespace from headers in DF)
    df.columns = df.columns.str.strip()
    
    if email_col_name not in df.columns:
        return None, f"Column '{email_col_name}' not found in file."
        
    # Extract potential emails
    raw_col_data = df[email_col_name].dropna()
    
    valid_emails = set()
    invalid_entries_found = False
    
    # Simple but effective email validation regex
    # Matches: something@something.something
    email_regex = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    
    for entry in raw_col_data:
        entry_str = str(entry).strip()
        
        if not entry_str: 
            continue # Skip empty strings
            
        if email_regex.match(entry_str):
            valid_emails.add(entry_str)
        else:
            # If we find ANY entry in this column that is not empty and not an email
            # We flag it.
            # However, requirements say: "If invalid or mixed data appears (e.g., names, numbers), show a clear error message"
            # We should probably be strict if the USER explicitly selected this column as the "Email Column".
            invalid_entries_found = True
            
    if invalid_entries_found and not valid_emails:
        # If mainly invalid data
        return None, "Selected column contains invalid email entries."
        
    if invalid_entries_found:
        # Mixed data? Requirements say: "If invalid or mixed data appears ... show a clear error message"
        # This implies we should fail if there is trash in the email column.
        return None, "Selected column contains invalid email entries."
        
    if not valid_emails:
        return None, "No valid emails found in the selected column."
    
    return list(valid_emails), None
