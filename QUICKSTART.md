# Quick Start Guide

## Virtual Environment Setup

The project is already set up with a virtual environment. Here's how to use it:

### Option 1: Use the activation script (Recommended)

```bash
source activate.sh
```

This will:
- Activate the virtual environment
- Show Python and pip versions
- Check for system dependencies (Tesseract, Poppler)

### Option 2: Manual activation

```bash
source venv/bin/activate
```

### Option 3: Re-run setup (if needed)

```bash
./setup.sh
```

This will:
- Create virtual environment (if it doesn't exist)
- Install all Python dependencies
- Check system dependencies

## System Dependencies

### Tesseract OCR (Required)

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### Poppler (Required for PDF processing)

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**macOS:**
```bash
brew install poppler
```

**Windows:**
Usually included with Tesseract installation

## Verify Installation

After activating the virtual environment, verify everything is working:

```bash
# Check Python packages
python -c "import pytesseract; import gmail_reader; print('✓ All packages installed')"

# Check Tesseract (if installed)
tesseract --version
```

## Next Steps

1. **Set up Gmail API credentials:**
   - **See detailed guide:** `GMAIL_API_SETUP.md` (comprehensive step-by-step instructions)
   - Quick steps:
     1. Go to https://console.cloud.google.com/
     2. Create a new project
     3. Enable Gmail API
     4. Configure OAuth consent screen
     5. Create OAuth 2.0 credentials (Desktop app type)
     6. Download as `credentials.json` and place in project root
   - **Full instructions with screenshots and troubleshooting:** See `GMAIL_API_SETUP.md`

2. **Run the application:**
   ```bash
   python main.py
   ```

3. **Or use the example API:**
   ```bash
   python api_example.py
   ```

## Common Commands

```bash
# Activate virtual environment
source activate.sh

# Run main script
python main.py

# Run with options
python main.py --max-emails 100 --output-file receipts.json

# Run API server
python api_example.py

# Deactivate virtual environment
deactivate
```

## Troubleshooting

### Virtual environment not activating
- Make sure you're in the project directory
- Try: `source venv/bin/activate` directly

### Tesseract not found
- Install Tesseract (see above)
- Or set path in `.env`: `TESSERACT_CMD=/usr/bin/tesseract`

### Import errors
- Make sure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Gmail authentication errors
- Verify `credentials.json` is in the project root
- Delete `token.json` and re-authenticate

## Getting Help

- Check the main README.md for detailed documentation
- Review error messages for specific issues
- Ensure all system dependencies are installed

