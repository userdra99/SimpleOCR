# SimpleOCR - Gmail Receipt Extractor

A locally-run Python application that extracts receipt information from Gmail emails using OCR (Optical Character Recognition) and exports the data to JSON format for easy API integration.

## Features

- 🔐 **Gmail API Integration** - Securely reads emails from your Gmail account
- 📄 **OCR Processing** - Extracts text from PDF and JPG attachments using Tesseract
- 🧾 **Receipt Parsing** - Intelligently extracts key information (date, vendor, total, items, tax)
- 📊 **JSON Output** - Exports data in JSON format for easy API integration
- 🔄 **Incremental Updates** - Appends new receipts without duplicates
- 🎯 **Smart Search** - Automatically finds receipt-related emails using keywords

## Requirements

### System Dependencies

1. **Python 3.8+**
2. **Tesseract OCR**
   - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`
   - Windows: Download from [UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
   - Additional language packs (optional): `sudo apt-get install tesseract-ocr-{lang}`

3. **Poppler** (for PDF processing)
   - Ubuntu/Debian: `sudo apt-get install poppler-utils`
   - macOS: `brew install poppler`
   - Windows: Included in most Tesseract installations

### Python Dependencies

Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Setup

### 0. Virtual Environment Setup (Already Done!)

The virtual environment is already set up. To activate it:

```bash
source activate.sh
```

Or manually:
```bash
source venv/bin/activate
```

For a complete setup guide, see `QUICKSTART.md`.

### 1. Gmail API Setup

**📖 For detailed step-by-step instructions, see [GMAIL_API_SETUP.md](GMAIL_API_SETUP.md)**

Quick steps:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Configure OAuth consent screen:
   - Go to "APIs & Services" > "OAuth consent screen"
   - Select "External" and fill in required information
   - Add scope: `https://www.googleapis.com/auth/gmail.readonly`
   - Add your email as a test user
5. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as the application type
   - Download the credentials JSON file
   - Rename it to `credentials.json` and place it in the project root

**⚠️ Important:** The detailed guide in `GMAIL_API_SETUP.md` includes troubleshooting, security notes, and screenshots to help you through the process.

### 2. Configuration

Create a `.env` file in the project root (optional - defaults are used if not provided):

```env
# Gmail API Credentials
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json

# Tesseract OCR (optional - only if tesseract is not in PATH)
# TESSERACT_CMD=/usr/bin/tesseract
# OCR_LANGUAGE=eng

# Output Configuration
OUTPUT_FORMAT=json
JSON_OUTPUT_FILE=receipts.json

# Temporary directory for downloads
TEMP_DIR=temp_attachments
```

## Usage

### Basic Usage

Run the script to process receipts from Gmail:

```bash
python main.py
```

### Advanced Usage

```bash
# Process specific number of emails
python main.py --max-emails 100

# Use custom Gmail search query
python main.py --query "from:amazon.com subject:receipt"

# Specify output format and file
python main.py --output-format json --output-file my_receipts.json

# Combine options
python main.py --max-emails 50 --query "receipt OR invoice" --output-file receipts.json
```

### Command Line Options

- `--max-emails N`: Maximum number of emails to process (default: 50)
- `--query QUERY`: Custom Gmail search query (default: uses receipt keywords)
- `--output-format FORMAT`: Output format - json, csv, or gsheets (default: json)
- `--output-file FILE`: Output file path (default: from config)

## Output Format

The application exports data in JSON format with the following structure:

```json
{
  "metadata": {
    "export_date": "2024-01-15T10:30:00",
    "last_updated": "2024-01-15T10:30:00",
    "total_receipts": 10,
    "new_receipts_this_export": 2,
    "format_version": "1.0"
  },
  "receipts": [
    {
      "date": "2024-01-15",
      "vendor": "Amazon",
      "total": 129.99,
      "subtotal": 119.99,
      "tax": 10.00,
      "items": [
        {
          "name": "Product Name",
          "price": 59.99
        }
      ],
      "email": {
        "subject": "Your Amazon order receipt",
        "from": "no-reply@amazon.com",
        "date": "Mon, 15 Jan 2024 10:00:00 -0800"
      },
      "raw_text_preview": "Amazon Order Receipt...",
      "extracted_at": "2024-01-15T10:30:00"
    }
  ]
}
```

## API Integration

The JSON output is designed for easy API integration. You can:

1. **Read the JSON file** in your application:
   ```python
   import json
   with open('receipts.json', 'r') as f:
       data = json.load(f)
       receipts = data['receipts']
   ```

2. **Use the DataWriter class** to get JSON string directly:
   ```python
   from spreadsheet_writer import DataWriter
   writer = DataWriter()
   json_string = writer.get_receipts_json(receipts_data)
   ```

3. **Use the example Flask API** - A complete REST API example is provided:
   ```bash
   # Install Flask (if not already installed)
   pip install flask
   
   # Run the API server
   python api_example.py
   ```
   
   The API provides the following endpoints:
   - `GET /api/receipts` - Get all receipts (supports filtering by vendor, date, amount)
   - `GET /api/receipts/<id>` - Get specific receipt by index
   - `GET /api/receipts/stats` - Get statistics about receipts
   - `GET /api/receipts/vendors` - Get list of all vendors with totals
   
   Example API calls:
   - `http://localhost:5000/api/receipts?vendor=Amazon&min_total=50`
   - `http://localhost:5000/api/receipts/stats`
   - `http://localhost:5000/api/receipts/vendors`

## Project Structure

```
SimpleOCR/
├── main.py                 # Main orchestration script
├── gmail_reader.py         # Gmail API integration
├── ocr_processor.py        # OCR text extraction
├── receipt_parser.py       # Receipt data parsing
├── spreadsheet_writer.py   # Data export (JSON/CSV/Sheets)
├── api_example.py         # Example Flask REST API
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .gitignore            # Git ignore file
├── credentials.json      # Gmail API credentials (not in repo)
└── receipts.json         # Output file (generated)
```

## How It Works

1. **Authentication**: Authenticates with Gmail API using OAuth 2.0
2. **Email Search**: Searches for emails containing receipt-related keywords
3. **Attachment Download**: Downloads PDF and JPG attachments from emails
4. **OCR Processing**: Extracts text from images and PDFs using Tesseract OCR
5. **Text Parsing**: Parses extracted text to find receipt information (date, vendor, total, items)
6. **Data Export**: Exports structured data to JSON file
7. **Deduplication**: Prevents duplicate entries based on date, vendor, and total

## Troubleshooting

### Tesseract Not Found
- Ensure Tesseract is installed and in your PATH
- Or set `TESSERACT_CMD` in your `.env` file to the full path

### Gmail Authentication Errors
- Verify `credentials.json` is in the project root
- Delete `token.json` and re-authenticate if needed
- Ensure Gmail API is enabled in Google Cloud Console

### PDF Processing Issues
- Install Poppler utilities (required for pdf2image)
- On Linux: `sudo apt-get install poppler-utils`
- On macOS: `brew install poppler`

### Low OCR Accuracy
- Ensure images are clear and high resolution
- Try different OCR languages if receipts are in other languages
- Set `OCR_LANGUAGE` in `.env` (e.g., `eng+spa` for English and Spanish)

## Security Notes

- **Credentials**: Never commit `credentials.json` or `token.json` to version control
- **Permissions**: The application only requests read-only access to Gmail
- **Local Storage**: All processing happens locally on your machine
- **Temporary Files**: Downloaded attachments are automatically cleaned up

## License

This project is provided as-is for personal and commercial use.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions:
1. Check the Troubleshooting section above
2. Review the Gmail API documentation
3. Check Tesseract OCR documentation for OCR-related issues

