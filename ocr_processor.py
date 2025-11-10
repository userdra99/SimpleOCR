"""
OCR Processor Module - Handles text extraction from PDFs and images using Tesseract
"""
import os
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import config


class OCRProcessor:
    def __init__(self):
        # Set tesseract command path if specified
        if config.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
    
    def extract_text_from_image(self, image_path):
        """Extract text from an image file (JPG, PNG, etc.)"""
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang=config.OCR_LANGUAGE)
            return text
        except Exception as e:
            print(f"Error extracting text from image {image_path}: {e}")
            return ""
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file"""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            
            # Extract text from each page
            full_text = ""
            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(image, lang=config.OCR_LANGUAGE)
                full_text += f"\n--- Page {i+1} ---\n{page_text}\n"
            
            return full_text
        except Exception as e:
            print(f"Error extracting text from PDF {pdf_path}: {e}")
            # Fallback: try PyPDF2 for text-based PDFs
            try:
                return self._extract_text_from_pdf_fallback(pdf_path)
            except Exception as e2:
                print(f"Fallback PDF extraction also failed: {e2}")
                return ""
    
    def _extract_text_from_pdf_fallback(self, pdf_path):
        """Fallback method using PyPDF2 for text-based PDFs"""
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
            return ""
    
    def extract_text_from_file(self, file_path):
        """Extract text from a file (automatically detects type)"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            return self.extract_text_from_image(file_path)
        else:
            print(f"Unsupported file type: {file_ext}")
            return ""
    
    def is_tesseract_available(self):
        """Check if Tesseract is available"""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

