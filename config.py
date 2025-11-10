"""
Configuration file for SimpleOCR - Gmail Receipt Extractor
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Gmail API Configuration
GMAIL_CREDENTIALS_FILE = os.getenv('GMAIL_CREDENTIALS_FILE', 'credentials.json')
GMAIL_TOKEN_FILE = os.getenv('GMAIL_TOKEN_FILE', 'token.json')
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Email Search Configuration
RECEIPT_KEYWORDS = [
    'receipt', 'invoice', 'purchase', 'order', 'payment',
    'transaction', 'billing', 'confirmation', 'thank you for your purchase'
]

# OCR Configuration
TESSERACT_CMD = os.getenv('TESSERACT_CMD', None)  # Set if tesseract is not in PATH
OCR_LANGUAGE = os.getenv('OCR_LANGUAGE', 'eng')

# Output Configuration
OUTPUT_FORMAT = os.getenv('OUTPUT_FORMAT', 'json')  # 'json', 'csv', or 'gsheets'
JSON_OUTPUT_FILE = os.getenv('JSON_OUTPUT_FILE', 'receipts.json')
CSV_OUTPUT_FILE = os.getenv('CSV_OUTPUT_FILE', 'receipts.csv')
GOOGLE_SHEETS_NAME = os.getenv('GOOGLE_SHEETS_NAME', 'Receipts')

# Receipt Parsing Configuration
DATE_FORMATS = [
    '%Y-%m-%d',
    '%m/%d/%Y',
    '%d/%m/%Y',
    '%B %d, %Y',
    '%b %d, %Y'
]

# Supported file types
SUPPORTED_ATTACHMENT_TYPES = {
    'image/jpeg': '.jpg',
    'image/jpg': '.jpg',
    'image/png': '.png',
    'application/pdf': '.pdf'
}

# Temporary directory for downloads
TEMP_DIR = os.getenv('TEMP_DIR', 'temp_attachments')

