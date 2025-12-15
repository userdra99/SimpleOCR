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

    # System prompt for the LLM
    SYSTEM_PROMPT = """You are an expert at extracting structured information from receipt and invoice text.
Your task is to analyze the provided text and extract key fields in JSON format.
Always respond with valid JSON only, no additional text or explanation.
If a field cannot be found, use null for that field.
For dates, use YYYY-MM-DD format.
For amounts, use decimal numbers without currency symbols."""

    # User prompt template
    EXTRACTION_PROMPT_TEMPLATE = """Extract the following fields from this receipt/invoice text:
- event_date: The date when the purchase/transaction occurred
- submission_date: The date when the claim/receipt was submitted (if different from event date)
- claim_amount: The total amount to be claimed (usually the final total)
- invoice_number: The invoice or receipt number
- policy_number: Any policy or account number
- vendor: The merchant or vendor name
- tax: Tax amount if present

Receipt text:
{text}

Respond with JSON in this exact format:
{{
  "event_date": "YYYY-MM-DD or null",
  "submission_date": "YYYY-MM-DD or null",
  "claim_amount": number or null,
  "invoice_number": "string or null",
  "policy_number": "string or null",
  "vendor": "string or null",
  "tax": number or null
}}"""

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
            r'Receipt\s*#?\s*:?\s*([A-Z0-9-]+)',
            r'Order\s*#?\s*:?\s*([A-Z0-9-]+)',
            r'Reference\s*:?\s*([A-Z0-9-]+)',
        ]

        self.policy_patterns = [
            r'Policy\s*#?\s*:?\s*([A-Z0-9-]+)',
            r'Account\s*#?\s*:?\s*([A-Z0-9-]+)',
            r'Member\s*#?\s*:?\s*([A-Z0-9-]+)',
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
