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

# AI imports (optional)
try:
    from src.vllm_client import VLLMClient, VLLMClientError
    from src.ai_receipt_parser import AIReceiptParser
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


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
    parser.add_argument(
        '--use-ai',
        action='store_true',
        help='Use AI-powered extraction via vLLM (requires vLLM server running)'
    )
    parser.add_argument(
        '--vllm-url',
        type=str,
        default=None,
        help='vLLM server URL (default: from config or http://localhost:8000)'
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

    # Initialize AI parser if requested
    ai_parser = None
    vllm_client = None
    if args.use_ai or config.VLLM_ENABLED:
        if not AI_AVAILABLE:
            print("WARNING: AI extraction requested but AI modules not available")
            print("Install dependencies: pip install aiohttp tenacity")
            print("Falling back to regex-only extraction")
        else:
            try:
                vllm_url = args.vllm_url or config.VLLM_SERVER_URL
                print(f"Initializing vLLM client at {vllm_url}...")

                vllm_client = VLLMClient(
                    server_url=vllm_url,
                    model_name=config.VLLM_MODEL_NAME,
                    timeout=config.VLLM_TIMEOUT,
                    max_retries=config.VLLM_MAX_RETRIES,
                    max_tokens=config.VLLM_MAX_TOKENS,
                    temperature=config.VLLM_TEMPERATURE
                )

                # Check server health
                if vllm_client.check_health():
                    print("✓ vLLM server is healthy")
                    ai_parser = AIReceiptParser(
                        vllm_client=vllm_client,
                        use_fallback=config.AI_USE_FALLBACK
                    )
                    print("✓ AI-powered extraction enabled")
                else:
                    print("WARNING: vLLM server is not responding")
                    print("Falling back to regex-only extraction")
                    vllm_client = None
            except Exception as e:
                print(f"WARNING: Failed to initialize AI extraction: {e}")
                print("Falling back to regex-only extraction")
                vllm_client = None
                ai_parser = None
    
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
                # Try AI extraction first if available
                receipt_data = None

                if ai_parser:
                    try:
                        print(f"    Using AI extraction...")
                        ai_fields = ai_parser.extract_fields(text_content, email_data)

                        # Combine AI fields with standard parser format
                        receipt_data = {
                            'date': ai_fields.get('event_date') or ai_fields.get('submission_date'),
                            'vendor': ai_fields.get('vendor'),
                            'total': ai_fields.get('claim_amount'),
                            'tax': ai_fields.get('tax'),
                            'invoice_number': ai_fields.get('invoice_number'),
                            'policy_number': ai_fields.get('policy_number'),
                            'submission_date': ai_fields.get('submission_date'),
                            'extraction_method': ai_fields.get('extraction_method', 'ai'),
                            'confidence': ai_fields.get('confidence', 0.0),
                            'raw_text': ai_fields.get('raw_text', ''),
                            'email_subject': email_data.get('subject', ''),
                            'email_from': email_data.get('from', ''),
                            'email_date': email_data.get('date', ''),
                        }

                        print(f"    AI extraction confidence: {receipt_data['confidence']:.2f} ({receipt_data['extraction_method']})")
                    except Exception as e:
                        print(f"    AI extraction error: {e}")
                        print(f"    Falling back to regex extraction...")
                        receipt_data = None

                # Fallback to regex parser if AI failed or not available
                if not receipt_data:
                    receipt_data = receipt_parser.parse(text_content, email_data)
                    receipt_data['extraction_method'] = 'regex'
                    receipt_data['confidence'] = 0.6

                # Only add if we found meaningful data
                if receipt_data.get('vendor') or receipt_data.get('total') or receipt_data.get('date'):
                    receipts_data.append(receipt_data)
                    total_str = f"${receipt_data.get('total', 'N/A')}" if receipt_data.get('total') else 'N/A'
                    print(f"    ✓ Extracted receipt: {receipt_data.get('vendor', 'Unknown')} - {total_str}")
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

