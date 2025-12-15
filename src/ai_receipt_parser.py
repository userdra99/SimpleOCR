"""
AI Receipt Parser Module - Uses vLLM for intelligent field extraction from receipts

This module leverages Qwen LLM via vLLM server to extract structured data from receipt text,
with fallback to regex patterns for robustness.
"""
import re
import json
from typing import Dict, Optional, Any, List
from datetime import datetime
import dateparser

from src.vllm_client import VLLMClient, VLLMClientError, VLLMResponse


class AIReceiptParser:
    """
    AI-powered receipt parser using vLLM for intelligent field extraction.

    Extracts key fields from receipt text:
    - Event Date
    - Submission Date
    - Claim Amount
    - Invoice Number
    - Policy Number
    - Vendor name
    - Tax information
    """

    # Enhanced system prompt for insurance claims and medical receipts
    SYSTEM_PROMPT = """You are an expert at extracting structured data from insurance claims, medical invoices, and healthcare receipts.

EXPERTISE AREAS:
- Distinguishing between Event Date (when service occurred) and Submission Date (when billed)
- Identifying claim amounts vs. line items
- Recognizing invoice/claim numbers vs. policy/member IDs
- Extracting medical provider information

KEY RULES:
- Event Date is when the medical service/treatment occurred (look for "Date of Service", "DOS", "Visit Date")
- Submission Date is when the claim/invoice was created (look for "Invoice Date", "Claim Date")
- Claim Amount is the FINAL total, not subtotals
- Invoice Number is the document reference (INV-xxx, CLM-xxx, etc.)
- Policy Number is the insurance identifier (POL-xxx, Member ID, etc.)

Always return valid JSON with exact field names. Use null for missing/unclear fields."""

    # Enhanced user prompt template
    EXTRACTION_PROMPT_TEMPLATE = """Extract the following fields from this insurance claim/medical receipt:

CRITICAL FIELDS (priority order):

1. **event_date** (YYYY-MM-DD):
   - Date when medical service/treatment was provided
   - Search for: "Date of Service", "Service Date", "DOS", "Treatment Date", "Visit Date", "Procedure Date"
   - This is NOT the invoice/bill creation date
   - Example: "DOS: 01/15/2024" → "2024-01-15"

2. **submission_date** (YYYY-MM-DD):
   - Date when invoice/claim was created or submitted
   - Search for: "Invoice Date", "Bill Date", "Claim Date", "Date" (at document top), "Billing Date"
   - Usually the more recent date if multiple dates exist
   - Example: "Invoice Date: 01/20/2024" → "2024-01-20"

3. **claim_amount** (number only):
   - Total amount being claimed/charged
   - Search for: "Total", "Amount Due", "Balance Due", "Total Charges", "Claim Amount", "Grand Total"
   - Use the FINAL total amount, not subtotals or line items
   - Remove all currency symbols ($, €, £, etc.)
   - Example: "Total: $150.00" → 150.00

4. **invoice_number** (string):
   - Unique invoice or claim reference number
   - Search for: "Invoice #", "Invoice No.", "Invoice Number", "Claim #", "Bill #", "Reference #", "Document #"
   - Format: Alphanumeric code (INV-12345, CLM2024001, B-001234, etc.)
   - Example: "Invoice #: INV-2024-0015" → "INV-2024-0015"

5. **policy_number** (string):
   - Insurance policy number or member/subscriber ID
   - Search for: "Policy #", "Policy Number", "Member ID", "Subscriber ID", "Insurance #", "Account #", "Patient ID"
   - Usually a long alphanumeric code
   - Example: "Member ID: POL-123456789" → "POL-123456789"

OPTIONAL FIELDS:
- vendor: Medical provider/clinic/hospital name (first provider name mentioned)
- tax: Tax amount if listed separately (numeric, no symbols)

DOCUMENT TEXT:
{text}

Return ONLY valid JSON (no explanations, no markdown):
{{
  "event_date": "YYYY-MM-DD or null",
  "submission_date": "YYYY-MM-DD or null",
  "claim_amount": number or null,
  "invoice_number": "string or null",
  "policy_number": "string or null",
  "vendor": "string or null",
  "tax": number or null
}}

VALIDATION RULES:
- All dates must be in YYYY-MM-DD format
- All amounts must be numeric only (no $, €, £, or other symbols)
- If a field is not found, use null
- event_date should typically be earlier than or equal to submission_date"""

    def __init__(self, vllm_client: Optional[VLLMClient] = None, use_fallback: bool = True):
        """
        Initialize AI Receipt Parser.

        Args:
            vllm_client: VLLMClient instance (will be created if not provided)
            use_fallback: Whether to use regex fallback if AI extraction fails
        """
        self.vllm_client = vllm_client
        self.use_fallback = use_fallback
        self._fallback_initialized = False

        # Fallback regex patterns (similar to ReceiptParser)
        self.date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # MM/DD/YYYY or DD/MM/YYYY
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',    # YYYY/MM/DD
            r'[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}',  # Month DD, YYYY
        ]

        self.amount_patterns = [
            r'Total[:\s]+[\$£€]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Amount[:\s]+[\$£€]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'[\$£€]\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        ]

        self.invoice_patterns = [
            r'Invoice\s*#?\s*:?\s*([A-Z0-9-]+)',
            r'Claim\s*#?\s*:?\s*([A-Z0-9-]+)',
            r'Bill\s*#?\s*:?\s*([A-Z0-9-]+)',
            r'Receipt\s*#?\s*:?\s*([A-Z0-9-]+)',
            r'Reference\s*#?\s*:?\s*([A-Z0-9-]+)',
            r'Invoice\s+No\.?\s*:?\s*([A-Z0-9-]+)',
        ]

        self.policy_patterns = [
            r'Policy\s*#?\s*:?\s*([A-Z0-9-]+)',
            r'Policy\s+Number\s*:?\s*([A-Z0-9-]+)',
            r'Member\s+ID\s*:?\s*([A-Z0-9-]+)',
            r'Subscriber\s+ID\s*:?\s*([A-Z0-9-]+)',
            r'Insurance\s*#?\s*:?\s*([A-Z0-9-]+)',
            r'Account\s*#?\s*:?\s*([A-Z0-9-]+)',
        ]

        # Enhanced date patterns for medical/insurance documents
        self.event_date_patterns = [
            r'Date\s+of\s+Service\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'Service\s+Date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'DOS\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'Treatment\s+Date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'Visit\s+Date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ]

    def set_vllm_client(self, client: VLLMClient):
        """Set or update the vLLM client"""
        self.vllm_client = client

    def extract_fields(self, text: str, email_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract receipt fields using AI with fallback to regex.

        Args:
            text: Receipt text to parse
            email_data: Optional email metadata for additional context

        Returns:
            Dictionary with extracted fields and confidence scores
        """
        result = {
            'event_date': None,
            'submission_date': None,
            'claim_amount': None,
            'invoice_number': None,
            'policy_number': None,
            'vendor': None,
            'tax': None,
            'extraction_method': 'none',
            'confidence': 0.0,
            'raw_text': text[:500] if text else '',
        }

        if not text or not text.strip():
            return result

        # Try AI extraction first
        if self.vllm_client:
            try:
                ai_result = self._extract_with_ai(text)
                if ai_result and ai_result.get('confidence', 0) > 0.5:
                    # Merge AI results
                    for key in ['event_date', 'submission_date', 'claim_amount',
                                'invoice_number', 'policy_number', 'vendor', 'tax']:
                        if ai_result.get(key) is not None:
                            result[key] = ai_result[key]

                    result['extraction_method'] = 'ai'
                    result['confidence'] = ai_result.get('confidence', 0.8)

                    # If AI extraction successful, return
                    if self._has_meaningful_data(result):
                        return result
            except VLLMClientError as e:
                print(f"AI extraction failed: {e}")

        # Fallback to regex extraction
        if self.use_fallback:
            regex_result = self._extract_with_regex(text, email_data)

            # Merge regex results (only fill in missing fields)
            for key in ['event_date', 'submission_date', 'claim_amount',
                        'invoice_number', 'policy_number', 'vendor', 'tax']:
                if result[key] is None and regex_result.get(key) is not None:
                    result[key] = regex_result[key]

            if result['extraction_method'] == 'none':
                result['extraction_method'] = 'regex'
                result['confidence'] = regex_result.get('confidence', 0.6)
            else:
                result['extraction_method'] = 'hybrid'
                result['confidence'] = (result['confidence'] + regex_result.get('confidence', 0.6)) / 2

        return result

    def _extract_with_ai(self, text: str) -> Dict[str, Any]:
        """
        Extract fields using AI/LLM.

        Args:
            text: Receipt text

        Returns:
            Dictionary with extracted fields and confidence
        """
        if not self.vllm_client:
            raise VLLMClientError("vLLM client not initialized")

        # Truncate text if too long (to fit in context window)
        max_text_length = 2000
        if len(text) > max_text_length:
            text = text[:max_text_length] + "..."

        # Build prompt
        prompt = self.EXTRACTION_PROMPT_TEMPLATE.format(text=text)

        # Generate with AI
        response: VLLMResponse = self.vllm_client.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.1,  # Low temperature for deterministic output
            max_tokens=512
        )

        # Parse JSON from response
        extracted_data = self.vllm_client.extract_json_from_response(response.text)

        if not extracted_data:
            raise VLLMClientError("Failed to parse JSON from AI response")

        # Validate and clean extracted data
        cleaned_data = self._validate_extracted_data(extracted_data)
        cleaned_data['confidence'] = response.confidence

        return cleaned_data

    def _extract_with_regex(self, text: str, email_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Fallback extraction using regex patterns.

        Args:
            text: Receipt text
            email_data: Optional email metadata

        Returns:
            Dictionary with extracted fields
        """
        result = {
            'event_date': self._extract_date_regex(text, email_data),
            'submission_date': None,  # Usually same as event_date or email date
            'claim_amount': self._extract_amount_regex(text),
            'invoice_number': self._extract_invoice_regex(text),
            'policy_number': self._extract_policy_regex(text),
            'vendor': self._extract_vendor_regex(text, email_data),
            'tax': self._extract_tax_regex(text),
            'confidence': 0.6,
        }

        # Set submission date to event date if not found
        if result['event_date'] and not result['submission_date']:
            result['submission_date'] = result['event_date']

        return result

    def _validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean extracted data from AI.

        Args:
            data: Raw extracted data

        Returns:
            Cleaned and validated data
        """
        cleaned = {}

        # Validate dates
        for date_field in ['event_date', 'submission_date']:
            date_value = data.get(date_field)
            if date_value and date_value != "null":
                parsed_date = self._parse_date(str(date_value))
                cleaned[date_field] = parsed_date
            else:
                cleaned[date_field] = None

        # Validate amounts
        for amount_field in ['claim_amount', 'tax']:
            amount_value = data.get(amount_field)
            if amount_value is not None and amount_value != "null":
                try:
                    cleaned[amount_field] = float(amount_value)
                except (ValueError, TypeError):
                    cleaned[amount_field] = None
            else:
                cleaned[amount_field] = None

        # Validate strings
        for string_field in ['invoice_number', 'policy_number', 'vendor']:
            string_value = data.get(string_field)
            if string_value and string_value != "null":
                cleaned[string_field] = str(string_value).strip()[:200]
            else:
                cleaned[string_field] = None

        return cleaned

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to YYYY-MM-DD format"""
        try:
            parsed = dateparser.parse(date_str)
            if parsed:
                return parsed.strftime('%Y-%m-%d')
        except Exception:
            pass
        return None

    def _has_meaningful_data(self, data: Dict[str, Any]) -> bool:
        """Check if extracted data has meaningful information"""
        key_fields = ['claim_amount', 'invoice_number', 'vendor', 'event_date']
        return any(data.get(field) is not None for field in key_fields)

    # Fallback regex extraction methods
    def _extract_date_regex(self, text: str, email_data: Optional[Dict] = None) -> Optional[str]:
        """Extract date using regex"""
        for pattern in self.date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(0)
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    return parsed_date

        # Fallback to email date
        if email_data and email_data.get('date'):
            return self._parse_date(email_data['date'])

        return None

    def _extract_amount_regex(self, text: str) -> Optional[float]:
        """Extract amount using regex"""
        amounts = []
        for pattern in self.amount_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1).replace(',', '')
                try:
                    amounts.append(float(amount_str))
                except ValueError:
                    continue

        return max(amounts) if amounts else None

    def _extract_invoice_regex(self, text: str) -> Optional[str]:
        """Extract invoice number using regex"""
        for pattern in self.invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:50]
        return None

    def _extract_policy_regex(self, text: str) -> Optional[str]:
        """Extract policy number using regex"""
        for pattern in self.policy_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:50]
        return None

    def _extract_vendor_regex(self, text: str, email_data: Optional[Dict] = None) -> Optional[str]:
        """Extract vendor using regex and email data"""
        # Try email subject first
        if email_data and email_data.get('subject'):
            subject = email_data['subject']
            subject = re.sub(r'^Re:|^Fwd:|^FW:', '', subject, flags=re.IGNORECASE).strip()
            if subject and len(subject) < 100:
                return subject

        # Try email from field
        if email_data and email_data.get('from'):
            from_field = email_data['from']
            match = re.match(r'^(.+?)\s*<', from_field)
            if match:
                return match.group(1).strip()

        # Try first line of text
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and len(line) < 100:
                return line

        return None

    def _extract_tax_regex(self, text: str) -> Optional[float]:
        """Extract tax amount using regex"""
        tax_patterns = [
            r'Tax[:\s]+[\$£€]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Sales Tax[:\s]+[\$£€]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'VAT[:\s]+[\$£€]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        ]

        for pattern in tax_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue

        return None
