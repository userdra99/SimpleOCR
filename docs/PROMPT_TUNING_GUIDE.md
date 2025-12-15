# Prompt Fine-Tuning Guide for Field Extraction

## Target Fields

Your SimpleOCR system is optimized to extract these 5 critical fields from insurance claims and medical receipts:

1. **Event Date** - When the medical service occurred
2. **Submission Date** - When the claim/invoice was created
3. **Claim Amount** - Total amount being claimed
4. **Invoice Number** - Unique invoice/claim reference
5. **Policy Number** - Insurance policy or member ID

---

## What Was Changed

### 1. System Prompt Enhancement

**Location**: `src/ai_receipt_parser.py` - `SYSTEM_PROMPT` constant

**Changes Made**:
- ✅ Specialized for **insurance claims** and **medical receipts** (not generic receipts)
- ✅ Added expertise in distinguishing **Event Date vs Submission Date**
- ✅ Clarified the difference between **claim amounts** vs line items
- ✅ Emphasized distinction between **invoice numbers** and **policy numbers**
- ✅ Added medical/healthcare context

**Before**:
```python
"You are an expert at extracting structured information from receipt and invoice text."
```

**After**:
```python
"You are an expert at extracting structured data from insurance claims, medical invoices, and healthcare receipts.

EXPERTISE AREAS:
- Distinguishing between Event Date (when service occurred) and Submission Date (when billed)
- Identifying claim amounts vs. line items
- Recognizing invoice/claim numbers vs. policy/member IDs
..."
```

### 2. Extraction Prompt Template

**Location**: `src/ai_receipt_parser.py` - `EXTRACTION_PROMPT_TEMPLATE` constant

**Changes Made**:

#### ✅ Field-Specific Guidance for Each Field:

**Event Date**:
- Added specific keywords to search: "Date of Service", "DOS", "Treatment Date", "Visit Date", "Procedure Date"
- Clarified it's NOT the invoice date
- Added example format

**Submission Date**:
- Keywords: "Invoice Date", "Bill Date", "Claim Date", "Billing Date"
- Guidance: Usually more recent than event date
- Appears at top of document

**Claim Amount**:
- Keywords: "Total", "Amount Due", "Balance Due", "Total Charges", "Grand Total"
- Emphasized: Use FINAL total, not subtotals
- Must remove currency symbols

**Invoice Number**:
- Keywords: "Invoice #", "Claim #", "Bill #", "Reference #", "Document #"
- Format examples: INV-12345, CLM2024001, B-001234

**Policy Number**:
- Keywords: "Policy #", "Member ID", "Subscriber ID", "Insurance #", "Account #", "Patient ID"
- Format: Long alphanumeric code

#### ✅ Validation Rules Added:
- Dates must be YYYY-MM-DD format
- Amounts must be numeric only (no symbols)
- event_date should be ≤ submission_date
- Use null for missing fields

### 3. Enhanced Regex Fallback Patterns

**Location**: `src/ai_receipt_parser.py` - `__init__` method

**Changes Made**:

**Invoice Patterns** - Added medical/insurance specific:
```python
r'Claim\s*#?\s*:?\s*([A-Z0-9-]+)',      # Claim #
r'Bill\s*#?\s*:?\s*([A-Z0-9-]+)',        # Bill #
r'Invoice\s+No\.?\s*:?\s*([A-Z0-9-]+)', # Invoice No.
```

**Policy Patterns** - Enhanced for insurance:
```python
r'Policy\s+Number\s*:?\s*([A-Z0-9-]+)',   # Policy Number
r'Member\s+ID\s*:?\s*([A-Z0-9-]+)',       # Member ID
r'Subscriber\s+ID\s*:?\s*([A-Z0-9-]+)',   # Subscriber ID
r'Insurance\s*#?\s*:?\s*([A-Z0-9-]+)',    # Insurance #
```

**Event Date Patterns** - NEW patterns for medical dates:
```python
r'Date\s+of\s+Service\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # Date of Service
r'Service\s+Date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',       # Service Date
r'DOS\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',                   # DOS
r'Treatment\s+Date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',     # Treatment Date
r'Visit\s+Date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',         # Visit Date
```

---

## Testing the Improvements

### 1. Test with Sample Medical Receipt

Create a test file with medical receipt text:

```python
test_receipt = """
ABC Medical Clinic
123 Healthcare Ave
City, State 12345

Invoice Date: January 20, 2024
Invoice #: INV-2024-0157

Patient: John Doe
Member ID: POL-987654321
Date of Service: January 15, 2024

Services Rendered:
- Office Visit: $100.00
- Lab Work: $50.00

Subtotal: $150.00
Tax: $0.00
Total Amount Due: $150.00
"""

# Run extraction
python main.py --use-ai
```

**Expected Output**:
```json
{
  "event_date": "2024-01-15",
  "submission_date": "2024-01-20",
  "claim_amount": 150.00,
  "invoice_number": "INV-2024-0157",
  "policy_number": "POL-987654321",
  "vendor": "ABC Medical Clinic",
  "tax": 0.00,
  "extraction_method": "ai",
  "confidence": 0.95
}
```

### 2. Test Edge Cases

**Multiple Dates**:
```
DOS: 01/10/2024
Invoice Date: 01/15/2024
Received: 01/20/2024
```
Should extract: event_date=01/10/2024, submission_date=01/15/2024

**Multiple Amounts**:
```
Subtotal: $100.00
Tax: $10.00
Total: $110.00
```
Should extract: claim_amount=110.00, tax=10.00

---

## Further Customization

### If You Need Different Keywords

Edit `src/ai_receipt_parser.py`:

```python
# Line ~31-50: Update EXTRACTION_PROMPT_TEMPLATE

# Example: Add your custom keywords
"Search for: 'Date of Service', 'DOS', 'YOUR_CUSTOM_KEYWORD'"
```

### If You Need Different Date Formats

The system supports:
- YYYY-MM-DD
- MM/DD/YYYY
- DD/MM/YYYY
- Month DD, YYYY

To add more formats, update:
```python
# Line ~106-112: Add to event_date_patterns
self.event_date_patterns = [
    r'YOUR_CUSTOM_DATE_PATTERN',
    # ...
]
```

### Adjusting AI Confidence Threshold

Edit `config.py`:

```python
# Lower threshold for more permissive extraction
AI_MIN_CONFIDENCE = 0.3  # Default: 0.5

# Higher threshold for stricter extraction
AI_MIN_CONFIDENCE = 0.7
```

---

## Performance Tuning

### For Better Accuracy

In `config.py`:

```python
# More deterministic output
VLLM_TEMPERATURE = 0.05  # Default: 0.1 (lower = more consistent)

# More tokens for complex receipts
VLLM_MAX_TOKENS = 1024  # Default: 512
```

### For Faster Processing

```python
# Reduce max tokens
VLLM_MAX_TOKENS = 256

# Reduce retries
VLLM_MAX_RETRIES = 1  # Default: 3
```

---

## Validation & Error Handling

The system automatically:

1. **Validates dates**: Ensures YYYY-MM-DD format
2. **Validates amounts**: Removes currency symbols, ensures numeric
3. **Validates relationship**: Checks event_date ≤ submission_date
4. **Fallback**: Uses regex if AI extraction fails or confidence < 0.5
5. **Hybrid mode**: Combines AI + regex for maximum accuracy

---

## Common Issues & Solutions

### Issue: Wrong Date Extracted

**Solution**: Check if document has multiple dates
```python
# Specify which date pattern should have priority
# Edit the order in event_date_patterns (first pattern = highest priority)
```

### Issue: Amount Includes Currency Symbol

**Problem**: AI returned "$150.00" instead of 150.00

**Solution**: Already handled! System automatically strips symbols in `_validate_extracted_data()`

### Issue: Invoice Number Not Found

**Check**:
1. Does it use a different keyword? (Add to prompt)
2. Is it in an unusual format? (Update regex pattern)
3. Does fallback regex work? (Test with `--use-ai` off)

---

## Quick Reference

| Field | Keywords to Add | Location in Code |
|-------|----------------|------------------|
| Event Date | DOS, Service Date, Visit | EXTRACTION_PROMPT_TEMPLATE line ~55 |
| Submission Date | Bill Date, Claim Date | EXTRACTION_PROMPT_TEMPLATE line ~63 |
| Claim Amount | Total Charges, Grand Total | EXTRACTION_PROMPT_TEMPLATE line ~71 |
| Invoice Number | Claim #, Reference # | EXTRACTION_PROMPT_TEMPLATE line ~79 |
| Policy Number | Member ID, Subscriber ID | EXTRACTION_PROMPT_TEMPLATE line ~87 |

---

## Testing Commands

```bash
# Test with AI extraction
python main.py --use-ai --max-emails 5

# Test regex fallback only
python main.py --max-emails 5

# Test with specific receipt file
python -c "
from src.ai_receipt_parser import AIReceiptParser
from src.vllm_client import VLLMClient

client = VLLMClient(server_url='http://localhost:8000')
parser = AIReceiptParser(vllm_client=client)

with open('test_receipt.txt') as f:
    text = f.read()

result = parser.extract_fields(text)
print(json.dumps(result, indent=2))
"
```

---

## Summary of Changes

✅ **Specialized for insurance/medical context**
✅ **Enhanced field-specific extraction guidance**
✅ **Added medical-specific keywords (DOS, Member ID, etc.)**
✅ **Improved date pattern recognition**
✅ **Better distinction between similar fields**
✅ **Validation rules for data quality**
✅ **Enhanced regex fallback patterns**

Your system is now optimized for extracting the exact 5 fields you need from insurance claims and medical receipts! 🎉
