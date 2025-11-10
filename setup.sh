#!/bin/bash
# Setup script for SimpleOCR
# This script helps set up the virtual environment and check system dependencies

set -e

echo "=========================================="
echo "SimpleOCR Setup Script"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ Found: $PYTHON_VERSION"
else
    echo "✗ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "Checking System Dependencies"
echo "=========================================="

# Check Tesseract
echo ""
if command -v tesseract &> /dev/null; then
    TESSERACT_VERSION=$(tesseract --version 2>&1 | head -n1)
    echo "✓ Tesseract OCR: $TESSERACT_VERSION"
else
    echo "✗ Tesseract OCR not found"
    echo "  Install with: sudo apt-get install tesseract-ocr"
    echo "  Or: brew install tesseract (macOS)"
fi

# Check Poppler
echo ""
if command -v pdftoppm &> /dev/null || command -v pdftotext &> /dev/null; then
    echo "✓ Poppler utilities found"
else
    echo "⚠ Poppler not found (needed for PDF processing)"
    echo "  Install with: sudo apt-get install poppler-utils"
    echo "  Or: brew install poppler (macOS)"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Set up Gmail API credentials:"
echo "   - Download credentials.json from Google Cloud Console"
echo "   - Place it in the project directory"
echo ""
echo "2. Activate the virtual environment:"
echo "   source activate.sh"
echo "   # or"
echo "   source venv/bin/activate"
echo ""
echo "3. Run the application:"
echo "   python main.py"
echo ""
echo "For more information, see README.md"
echo ""

