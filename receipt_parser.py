"""
Receipt Parser Module - Extracts key information from receipt text
"""
import re
import dateparser
from datetime import datetime
import config


class ReceiptParser:
    def __init__(self):
        self.date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # MM/DD/YYYY or DD/MM/YYYY
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',   # YYYY/MM/DD
            r'[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}',  # Month DD, YYYY
        ]
        
        # Currency patterns
        self.currency_patterns = [
            r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $1,234.56
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*\$',  # 1,234.56$
            r'Total[:\s]+[\$]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Total: $123.45
            r'Amount[:\s]+[\$]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # Amount: $123.45
        ]
        
        # Vendor/merchant patterns
        self.vendor_patterns = [
            r'From[:\s]+(.+)',
            r'Merchant[:\s]+(.+)',
            r'Store[:\s]+(.+)',
            r'Vendor[:\s]+(.+)',
        ]
    
    def parse(self, text, email_data=None):
        """Parse receipt text and extract key information"""
        if not text:
            return {}
        
        receipt_data = {
            'date': self._extract_date(text, email_data),
            'vendor': self._extract_vendor(text, email_data),
            'total': self._extract_total(text),
            'subtotal': self._extract_subtotal(text),
            'tax': self._extract_tax(text),
            'items': self._extract_items(text),
            'raw_text': text[:500],  # Store first 500 chars
            'email_subject': email_data.get('subject', '') if email_data else '',
            'email_from': email_data.get('from', '') if email_data else '',
            'email_date': email_data.get('date', '') if email_data else '',
        }
        
        return receipt_data
    
    def _extract_date(self, text, email_data=None):
        """Extract date from receipt text"""
        # Try to find date in text
        for pattern in self.date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(0)
                parsed_date = dateparser.parse(date_str)
                if parsed_date:
                    return parsed_date.strftime('%Y-%m-%d')
        
        # Fallback to email date
        if email_data and email_data.get('date'):
            try:
                parsed_date = dateparser.parse(email_data['date'])
                if parsed_date:
                    return parsed_date.strftime('%Y-%m-%d')
            except:
                pass
        
        return ''
    
    def _extract_vendor(self, text, email_data=None):
        """Extract vendor/merchant name from receipt text"""
        # Try to find vendor in text
        for pattern in self.vendor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vendor = match.group(1).strip()
                # Clean up vendor name
                vendor = re.sub(r'[\n\r\t]+', ' ', vendor)
                vendor = vendor[:100]  # Limit length
                return vendor
        
        # Try to extract from email subject or from field
        if email_data:
            # Try subject first
            subject = email_data.get('subject', '')
            if subject:
                # Remove common email prefixes
                subject = re.sub(r'^Re:|^Fwd:|^FW:', '', subject, flags=re.IGNORECASE)
                subject = subject.strip()
                if subject and len(subject) < 100:
                    return subject
            
            # Try from field
            from_field = email_data.get('from', '')
            if from_field:
                # Extract name from "Name <email@domain.com>"
                match = re.match(r'^(.+?)\s*<', from_field)
                if match:
                    return match.group(1).strip()
                # Or use domain name
                match = re.search(r'@([^.]+)', from_field)
                if match:
                    return match.group(1).capitalize()
        
        return ''
    
    def _extract_total(self, text):
        """Extract total amount from receipt text"""
        # Look for total patterns (usually the largest number or explicitly labeled)
        totals = []
        
        # Find all currency amounts
        for pattern in self.currency_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1).replace(',', '')
                try:
                    amount = float(amount_str)
                    totals.append(amount)
                except ValueError:
                    continue
        
        if totals:
            # Return the largest amount (likely the total)
            return max(totals)
        
        return None
    
    def _extract_subtotal(self, text):
        """Extract subtotal from receipt text"""
        patterns = [
            r'Subtotal[:\s]+[\$]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Sub-total[:\s]+[\$]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        
        return None
    
    def _extract_tax(self, text):
        """Extract tax amount from receipt text"""
        patterns = [
            r'Tax[:\s]+[\$]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Sales Tax[:\s]+[\$]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'VAT[:\s]+[\$]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        
        return None
    
    def _extract_items(self, text):
        """Extract line items from receipt text"""
        # Simple item extraction - looks for patterns like "Item Name $XX.XX"
        items = []
        
        # Look for lines that might be items (contain currency and text)
        lines = text.split('\n')
        item_pattern = r'(.+?)\s+[\$]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        
        for line in lines:
            line = line.strip()
            if len(line) < 5:  # Skip very short lines
                continue
            
            match = re.search(item_pattern, line)
            if match:
                item_name = match.group(1).strip()
                item_price = match.group(2).replace(',', '')
                
                # Skip if it looks like a total or tax line
                if any(keyword in item_name.lower() for keyword in ['total', 'tax', 'subtotal', 'amount']):
                    continue
                
                try:
                    price = float(item_price)
                    items.append({
                        'name': item_name[:100],  # Limit length
                        'price': price
                    })
                except ValueError:
                    continue
        
        return items

