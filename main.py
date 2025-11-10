#!/usr/bin/env python3
"""
SimpleOCR - Gmail Receipt Extractor
Main orchestration script that ties together Gmail reading, OCR processing, 
receipt parsing, and data export.
"""
import os
import sys
import argparse
from gmail_reader import GmailReader
from ocr_processor import OCRProcessor
from receipt_parser import ReceiptParser
from spreadsheet_writer import DataWriter
import config


def main():
    """Main function to orchestrate the receipt extraction process"""
    parser = argparse.ArgumentParser(
        description='Extract receipts from Gmail emails using OCR'
    )
    parser.add_argument(
        '--max-emails',
        type=int,
        default=50,
        help='Maximum number of emails to process (default: 50)'
    )
    parser.add_argument(
        '--query',
        type=str,
        default='',
        help='Custom Gmail search query (default: uses receipt keywords)'
    )
    parser.add_argument(
        '--output-format',
        type=str,
        choices=['json', 'csv', 'gsheets'],
        default=None,
        help='Output format: json, csv, or gsheets (default: from config)'
    )
    parser.add_argument(
        '--output-file',
        type=str,
        default=None,
        help='Output file path (default: from config)'
    )
    
    args = parser.parse_args()
    
    # Override config with command line arguments
    if args.output_format:
        config.OUTPUT_FORMAT = args.output_format
    if args.output_file:
        if args.output_format == 'json' or config.OUTPUT_FORMAT == 'json':
            config.JSON_OUTPUT_FILE = args.output_file
        else:
            config.CSV_OUTPUT_FILE = args.output_file
    
    print("=" * 60)
    print("SimpleOCR - Gmail Receipt Extractor")
    print("=" * 60)
    print(f"Output format: {config.OUTPUT_FORMAT}")
    print(f"Output file: {config.JSON_OUTPUT_FILE if config.OUTPUT_FORMAT == 'json' else config.CSV_OUTPUT_FILE}")
    print("=" * 60)
    
    # Initialize components
    print("\n1. Initializing components...")
    gmail_reader = GmailReader()
    ocr_processor = OCRProcessor()
    receipt_parser = ReceiptParser()
    data_writer = DataWriter()
    
    # Check if Tesseract is available
    if not ocr_processor.is_tesseract_available():
        print("ERROR: Tesseract OCR is not installed or not in PATH")
        print("Please install Tesseract OCR:")
        print("  Ubuntu/Debian: sudo apt-get install tesseract-ocr")
        print("  macOS: brew install tesseract")
        print("  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        sys.exit(1)
    
    # Authenticate with Gmail
    print("\n2. Authenticating with Gmail...")
    try:
        gmail_reader.authenticate()
        print("✓ Gmail authentication successful")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("\nTo set up Gmail API:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Gmail API")
        print("4. Create OAuth 2.0 credentials (Desktop app)")
        print("5. Download credentials as 'credentials.json'")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Authentication failed: {e}")
        sys.exit(1)
    
    # Search for emails
    print(f"\n3. Searching for emails (max: {args.max_emails})...")
    try:
        messages = gmail_reader.search_emails(query=args.query, max_results=args.max_emails)
        print(f"✓ Found {len(messages)} emails")
    except Exception as e:
        print(f"ERROR: Failed to search emails: {e}")
        sys.exit(1)
    
    if not messages:
        print("No emails found. Exiting.")
        return
    
    # Process emails
    print("\n4. Processing emails and extracting receipts...")
    receipts_data = []
    
    for i, message in enumerate(messages, 1):
        print(f"\n  Processing email {i}/{len(messages)}...")
        
        try:
            # Get email content
            email_data = gmail_reader.get_email_content(message['id'])
            if not email_data:
                print(f"    ✗ Failed to get email content")
                continue
            
            print(f"    Subject: {email_data['subject'][:50]}...")
            
            # Extract text from email body
            text_content = email_data.get('body', '')
            
            # Process attachments
            attachments = email_data.get('attachments', [])
            if attachments:
                print(f"    Found {len(attachments)} attachment(s)")
                
                for attachment in attachments:
                    filename = attachment['filename']
                    print(f"      Processing attachment: {filename}")
                    
                    # Download attachment
                    file_path = gmail_reader.download_attachment(
                        message['id'],
                        attachment['attachment_id'],
                        filename
                    )
                    
                    if file_path:
                        # Extract text using OCR
                        attachment_text = ocr_processor.extract_text_from_file(file_path)
                        if attachment_text:
                            text_content += f"\n\n--- Attachment: {filename} ---\n{attachment_text}"
                            print(f"      ✓ Extracted {len(attachment_text)} characters")
                        else:
                            print(f"      ✗ Failed to extract text from attachment")
                        
                        # Clean up downloaded file
                        try:
                            os.remove(file_path)
                        except:
                            pass
            
            # Parse receipt data
            if text_content:
                receipt_data = receipt_parser.parse(text_content, email_data)
                
                # Only add if we found meaningful data
                if receipt_data.get('vendor') or receipt_data.get('total') or receipt_data.get('date'):
                    receipts_data.append(receipt_data)
                    print(f"    ✓ Extracted receipt: {receipt_data.get('vendor', 'Unknown')} - ${receipt_data.get('total', 'N/A')}")
                else:
                    print(f"    ✗ No receipt data found in email")
            else:
                print(f"    ✗ No text content to parse")
        
        except Exception as e:
            print(f"    ✗ Error processing email: {e}")
            continue
    
    # Write receipts to output
    print(f"\n5. Writing {len(receipts_data)} receipts to output...")
    try:
        data_writer.write_receipts(receipts_data)
        print("✓ Receipts exported successfully")
    except Exception as e:
        print(f"ERROR: Failed to write receipts: {e}")
        sys.exit(1)
    
    # Clean up temp directory
    try:
        import shutil
        if os.path.exists(config.TEMP_DIR) and os.path.isdir(config.TEMP_DIR):
            shutil.rmtree(config.TEMP_DIR)
    except:
        pass
    
    print("\n" + "=" * 60)
    print("Process completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    main()

