import pandas as pd
import os
from datetime import datetime
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_recipient_file(file_storage, email_col_name, name_col_name=None, dob_col_name=None):
    """
    Parses a CSV or Excel file and returns a list of recipient data.
    
    Args:
        file_storage: The uploaded file
        email_col_name: Name of the email column (required)
        name_col_name: Name of the name column (optional)
        dob_col_name: Name of the DOB column (optional)
        
    Returns:
        tuple: (list of recipient dicts, error_message)
               Each recipient dict contains: {'email': str, 'name': str|None, 'dob': date|None}
    """
    try:
        filename = secure_filename(file_storage.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        
        if ext == 'csv':
            df = pd.read_csv(file_storage)
        else:
            df = pd.read_excel(file_storage)
            
        # Case-insensitive column mapping
        col_map = {str(c).lower().strip(): c for c in df.columns}
        
        # Find email column
        email_search_key = email_col_name.lower().strip()
        if email_search_key in col_map:
            actual_email_col = col_map[email_search_key]
        elif email_col_name in df.columns:
            actual_email_col = email_col_name
        else:
            return None, f"Column '{email_col_name}' not found. Available columns: {', '.join(map(str, df.columns))}"
        
        # Find name column (optional)
        actual_name_col = None
        if name_col_name:
            name_search_key = name_col_name.lower().strip()
            if name_search_key in col_map:
                actual_name_col = col_map[name_search_key]
            elif name_col_name in df.columns:
                actual_name_col = name_col_name
        
        # Find DOB column (optional)
        actual_dob_col = None
        if dob_col_name:
            dob_search_key = dob_col_name.lower().strip()
            if dob_search_key in col_map:
                actual_dob_col = col_map[dob_search_key]
            elif dob_col_name in df.columns:
                actual_dob_col = dob_col_name
        
        # Build recipient list
        recipients = []
        for idx, row in df.iterrows():
            email = row[actual_email_col]
            
            # Skip invalid emails
            if pd.isna(email) or '@' not in str(email):
                continue
                
            email = str(email).strip()
            
            # Extract name if available
            name = None
            if actual_name_col and actual_name_col in row.index:
                name_val = row[actual_name_col]
                if not pd.isna(name_val):
                    name = str(name_val).strip()
            
            # Extract and parse DOB if available
            dob = None
            if actual_dob_col and actual_dob_col in row.index:
                dob_val = row[actual_dob_col]
                if not pd.isna(dob_val):
                    dob = parse_dob(dob_val)
            
            recipients.append({
                'email': email,
                'name': name,
                'dob': dob
            })
        
        # Remove duplicates based on email
        seen_emails = set()
        unique_recipients = []
        for recipient in recipients:
            if recipient['email'] not in seen_emails:
                seen_emails.add(recipient['email'])
                unique_recipients.append(recipient)
        
        return unique_recipients, None
        
    except Exception as e:
        return None, str(e)

def parse_dob(dob_value):
    """
    Parse DOB from various formats to a datetime.date object.
    Accepts: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY, datetime objects, etc.
    Returns None if parsing fails.
    """
    if pd.isna(dob_value):
        return None
        
    # If it's already a datetime/date object (from Excel)
    if isinstance(dob_value, (datetime, pd.Timestamp)):
        return dob_value.date()
    
    # Try parsing string formats
    dob_str = str(dob_value).strip()
    
    # Common date formats to try
    formats = [
        '%Y-%m-%d',      # 2000-01-15
        '%d/%m/%Y',      # 15/01/2000
        '%m/%d/%Y',      # 01/15/2000
        '%Y/%m/%d',      # 2000/01/15
        '%d-%m-%Y',      # 15-01-2000
        '%m-%d-%Y',      # 01-15-2000
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(dob_str, fmt).date()
        except ValueError:
            continue
    
    # If all formats fail, return None
    return None

