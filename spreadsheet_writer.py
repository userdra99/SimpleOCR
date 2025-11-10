"""
Data Writer Module - Handles writing receipt data to JSON, CSV, or Google Sheets
"""
import os
import json
import csv
import pandas as pd
import config
from datetime import datetime


class DataWriter:
    def __init__(self):
        self.output_format = config.OUTPUT_FORMAT
        self.json_file = config.JSON_OUTPUT_FILE
        self.csv_file = config.CSV_OUTPUT_FILE
        self.gsheets_name = config.GOOGLE_SHEETS_NAME
        
    def write_receipts(self, receipts_data):
        """Write receipts data to output format"""
        if not receipts_data:
            print("No receipts data to write")
            return
        
        if self.output_format == 'json':
            self._write_to_json(receipts_data)
        elif self.output_format == 'csv':
            self._write_to_csv(receipts_data)
        elif self.output_format == 'gsheets':
            self._write_to_google_sheets(receipts_data)
        else:
            print(f"Unknown output format: {self.output_format}")
            print("Defaulting to JSON output")
            self._write_to_json(receipts_data)
    
    def _write_to_json(self, receipts_data):
        """Write receipts to JSON file"""
        if not receipts_data:
            return
        
        # Prepare data with metadata
        output_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'total_receipts': len(receipts_data),
                'format_version': '1.0'
            },
            'receipts': []
        }
        
        # Process each receipt
        for receipt in receipts_data:
            receipt_entry = {
                'date': receipt.get('date', ''),
                'vendor': receipt.get('vendor', ''),
                'total': receipt.get('total'),
                'subtotal': receipt.get('subtotal'),
                'tax': receipt.get('tax'),
                'items': receipt.get('items', []),
                'email': {
                    'subject': receipt.get('email_subject', ''),
                    'from': receipt.get('email_from', ''),
                    'date': receipt.get('email_date', '')
                },
                'raw_text_preview': receipt.get('raw_text', '')[:500],
                'extracted_at': datetime.now().isoformat()
            }
            output_data['receipts'].append(receipt_entry)
        
        # Load existing data if file exists (for appending/updating)
        existing_data = {'metadata': {}, 'receipts': []}
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse existing JSON file. Creating new file.")
                existing_data = {'metadata': {}, 'receipts': []}
        
        # Merge receipts (avoid duplicates based on date, vendor, total)
        existing_receipts = existing_data.get('receipts', [])
        existing_keys = {
            (r.get('date', ''), r.get('vendor', ''), r.get('total'))
            for r in existing_receipts
        }
        
        # Add new receipts that don't already exist
        new_receipts = []
        for receipt in output_data['receipts']:
            key = (receipt.get('date', ''), receipt.get('vendor', ''), receipt.get('total'))
            if key not in existing_keys:
                new_receipts.append(receipt)
                existing_keys.add(key)
        
        # Combine existing and new receipts
        combined_receipts = existing_receipts + new_receipts
        
        # Update metadata
        final_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'total_receipts': len(combined_receipts),
                'new_receipts_this_export': len(new_receipts),
                'format_version': '1.0'
            },
            'receipts': combined_receipts
        }
        
        # Write to JSON file with pretty formatting
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        
        print(f"Updated JSON file: {self.json_file}")
        print(f"Total receipts: {len(combined_receipts)} (added {len(new_receipts)} new)")
    
    def get_receipts_json(self, receipts_data):
        """Get receipts data as JSON string (for API integration)"""
        if not receipts_data:
            return json.dumps({'receipts': [], 'metadata': {'total': 0}}, indent=2)
        
        output_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'total_receipts': len(receipts_data),
                'format_version': '1.0'
            },
            'receipts': []
        }
        
        for receipt in receipts_data:
            receipt_entry = {
                'date': receipt.get('date', ''),
                'vendor': receipt.get('vendor', ''),
                'total': receipt.get('total'),
                'subtotal': receipt.get('subtotal'),
                'tax': receipt.get('tax'),
                'items': receipt.get('items', []),
                'email': {
                    'subject': receipt.get('email_subject', ''),
                    'from': receipt.get('email_from', ''),
                    'date': receipt.get('email_date', '')
                },
                'raw_text_preview': receipt.get('raw_text', '')[:500],
                'extracted_at': datetime.now().isoformat()
            }
            output_data['receipts'].append(receipt_entry)
        
        return json.dumps(output_data, indent=2, ensure_ascii=False)
    
    def _write_to_csv(self, receipts_data):
        """Write receipts to CSV file"""
        if not receipts_data:
            return
        
        # Flatten receipt data for CSV
        rows = []
        for receipt in receipts_data:
            # Main receipt row
            row = {
                'Date': receipt.get('date', ''),
                'Vendor': receipt.get('vendor', ''),
                'Total': receipt.get('total', ''),
                'Subtotal': receipt.get('subtotal', ''),
                'Tax': receipt.get('tax', ''),
                'Email Subject': receipt.get('email_subject', ''),
                'Email From': receipt.get('email_from', ''),
                'Email Date': receipt.get('email_date', ''),
                'Items Count': len(receipt.get('items', [])),
                'Raw Text Preview': receipt.get('raw_text', '')[:200],
            }
            rows.append(row)
        
        # Write to CSV
        df = pd.DataFrame(rows)
        
        # Check if file exists to append or create new
        if os.path.exists(self.csv_file):
            # Append mode - add new rows
            existing_df = pd.read_csv(self.csv_file)
            # Combine and remove duplicates based on date, vendor, and total
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(
                subset=['Date', 'Vendor', 'Total'],
                keep='last'
            )
            combined_df.to_csv(self.csv_file, index=False)
            print(f"Updated CSV file: {self.csv_file}")
        else:
            # Create new file
            df.to_csv(self.csv_file, index=False)
            print(f"Created CSV file: {self.csv_file}")
        
        print(f"Total receipts: {len(rows)}")
    
    def _write_to_google_sheets(self, receipts_data):
        """Write receipts to Google Sheets"""
        try:
            import gspread
            from google.oauth2.service_account import ServiceAccountCredentials
            
            # Check for Google Sheets credentials
            creds_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS', 'sheets_credentials.json')
            if not os.path.exists(creds_file):
                print(f"Google Sheets credentials not found: {creds_file}")
                print("Falling back to CSV output")
                self._write_to_csv(receipts_data)
                return
            
            # Authenticate
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
            client = gspread.authorize(creds)
            
            # Open or create spreadsheet
            try:
                sheet = client.open(self.gsheets_name).sheet1
            except:
                sheet = client.create(self.gsheets_name).sheet1
            
            # Prepare data
            headers = ['Date', 'Vendor', 'Total', 'Subtotal', 'Tax', 
                      'Email Subject', 'Email From', 'Email Date', 'Items Count']
            
            # Clear existing data and add headers if empty
            if not sheet.get_all_values():
                sheet.append_row(headers)
            
            # Add receipt data
            for receipt in receipts_data:
                row = [
                    receipt.get('date', ''),
                    receipt.get('vendor', ''),
                    receipt.get('total', ''),
                    receipt.get('subtotal', ''),
                    receipt.get('tax', ''),
                    receipt.get('email_subject', ''),
                    receipt.get('email_from', ''),
                    receipt.get('email_date', ''),
                    len(receipt.get('items', []))
                ]
                sheet.append_row(row)
            
            print(f"Updated Google Sheets: {self.gsheets_name}")
            
        except Exception as e:
            print(f"Error writing to Google Sheets: {e}")
            print("Falling back to CSV output")
            self._write_to_csv(receipts_data)

