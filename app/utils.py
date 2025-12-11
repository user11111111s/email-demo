import pandas as pd
import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_recipient_file(file_storage, email_col_name):
    """
    Parses a CSV or Excel file and returns a list of emails.
    """
    try:
        filename = secure_filename(file_storage.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        
        if ext == 'csv':
            df = pd.read_csv(file_storage)
        else:
            df = pd.read_excel(file_storage)
            
        # Normalize headers to match user input
        if email_col_name not in df.columns:
            return None, f"Column '{email_col_name}' not found in file."
            
        # Extract emails, drop NaNs/empty
        emails = df[email_col_name].dropna().unique().tolist()
        
        # Basic validation (could be improved)
        valid_emails = [e.strip() for e in emails if '@' in str(e)]
        
        return valid_emails, None
        
    except Exception as e:
        return None, str(e)
