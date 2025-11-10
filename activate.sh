#!/bin/bash
# Activation script for SimpleOCR virtual environment
# Usage: source activate.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SCRIPT_DIR/venv/bin/activate"

echo "✓ Virtual environment activated"
echo "✓ Python: $(python --version)"
echo "✓ Pip: $(pip --version | cut -d' ' -f2)"

# Check if Tesseract is available
if command -v tesseract &> /dev/null; then
    echo "✓ Tesseract OCR: $(tesseract --version 2>&1 | head -n1)"
else
    echo "⚠ Tesseract OCR not found - install with: sudo apt-get install tesseract-ocr"
fi

# Check if Poppler is available (for PDF processing)
if command -v pdftoppm &> /dev/null || command -v pdftotext &> /dev/null; then
    echo "✓ Poppler utilities found"
else
    echo "⚠ Poppler not found - install with: sudo apt-get install poppler-utils"
fi

echo ""
echo "To deactivate, run: deactivate"

