"""
Utility Functions for Tests
Helper functions and test data generators
"""
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Any


def generate_random_receipt(
    vendor: str = None,
    num_items: int = 5,
    date: str = None,
    include_tax: bool = True,
    include_discount: bool = False
) -> Dict[str, Any]:
    """
    Generate a random receipt for testing

    Args:
        vendor: Vendor name (random if None)
        num_items: Number of line items
        date: Receipt date (today if None)
        include_tax: Include tax calculation
        include_discount: Include discount

    Returns:
        Dictionary with receipt text and expected fields
    """
    if vendor is None:
        vendor = random.choice([
            "Whole Foods", "Target", "Walmart", "CVS",
            "Starbucks", "McDonald's", "Amazon Go"
        ])

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    # Generate random items
    items = []
    subtotal = 0.0
    for i in range(num_items):
        item_name = f"Item {i+1}"
        price = round(random.uniform(5.0, 50.0), 2)
        items.append({"name": item_name, "price": price})
        subtotal += price

    # Calculate discount
    discount = 0.0
    if include_discount:
        discount = round(subtotal * 0.1, 2)  # 10% discount

    # Calculate tax
    tax = 0.0
    if include_tax:
        tax = round((subtotal - discount) * 0.075, 2)  # 7.5% tax

    total = round(subtotal - discount + tax, 2)

    # Build receipt text
    receipt_lines = [
        f"{vendor}",
        "123 Main Street",
        f"Date: {date}",
        "",
    ]

    for item in items:
        receipt_lines.append(f"{item['name']:<30} ${item['price']:>6.2f}")

    receipt_lines.append("")
    receipt_lines.append(f"{'Subtotal:':<30} ${subtotal:>6.2f}")

    if include_discount:
        receipt_lines.append(f"{'Discount:':<30} $-{discount:>5.2f}")

    if include_tax:
        receipt_lines.append(f"{'Tax:':<30} ${tax:>6.2f}")

    receipt_lines.append(f"{'TOTAL:':<30} ${total:>6.2f}")

    receipt_text = "\n".join(receipt_lines)

    return {
        "text": receipt_text,
        "expected": {
            "vendor": vendor,
            "date": date,
            "total": total,
            "subtotal": subtotal,
            "tax": tax if include_tax else None,
            "discount": discount if include_discount else None,
            "items": items
        }
    }


def generate_batch_receipts(count: int = 10, **kwargs) -> List[Dict[str, Any]]:
    """
    Generate multiple random receipts

    Args:
        count: Number of receipts to generate
        **kwargs: Arguments passed to generate_random_receipt

    Returns:
        List of receipt dictionaries
    """
    return [generate_random_receipt(**kwargs) for _ in range(count)]


def generate_stress_test_receipts(
    small_count: int = 50,
    medium_count: int = 30,
    large_count: int = 10
) -> List[Dict[str, Any]]:
    """
    Generate receipts for stress testing

    Args:
        small_count: Number of small receipts (1-10 items)
        medium_count: Number of medium receipts (11-50 items)
        large_count: Number of large receipts (51-100 items)

    Returns:
        List of receipt dictionaries
    """
    receipts = []

    # Small receipts
    for _ in range(small_count):
        receipts.append(generate_random_receipt(
            num_items=random.randint(1, 10)
        ))

    # Medium receipts
    for _ in range(medium_count):
        receipts.append(generate_random_receipt(
            num_items=random.randint(11, 50)
        ))

    # Large receipts
    for _ in range(large_count):
        receipts.append(generate_random_receipt(
            num_items=random.randint(51, 100)
        ))

    return receipts


def corrupt_receipt_text(text: str, corruption_rate: float = 0.1) -> str:
    """
    Introduce random corruption into receipt text for robustness testing

    Args:
        text: Original receipt text
        corruption_rate: Fraction of characters to corrupt (0-1)

    Returns:
        Corrupted receipt text
    """
    chars = list(text)
    num_corruptions = int(len(chars) * corruption_rate)

    for _ in range(num_corruptions):
        idx = random.randint(0, len(chars) - 1)
        corruption_type = random.choice(['delete', 'replace', 'insert'])

        if corruption_type == 'delete':
            chars[idx] = ''
        elif corruption_type == 'replace':
            chars[idx] = random.choice(string.ascii_letters + string.digits + string.punctuation)
        elif corruption_type == 'insert':
            chars.insert(idx, random.choice(string.ascii_letters))

    return ''.join(chars)


def add_ocr_errors(text: str, error_rate: float = 0.05) -> str:
    """
    Simulate common OCR errors for testing

    Args:
        text: Original text
        error_rate: Fraction of characters to introduce errors

    Returns:
        Text with OCR errors
    """
    # Common OCR substitutions
    ocr_errors = {
        '0': 'O',
        'O': '0',
        '1': 'l',
        'l': '1',
        '5': 'S',
        'S': '5',
        '8': 'B',
        'B': '8'
    }

    chars = list(text)
    num_errors = int(len(chars) * error_rate)

    for _ in range(num_errors):
        idx = random.randint(0, len(chars) - 1)
        if chars[idx] in ocr_errors:
            chars[idx] = ocr_errors[chars[idx]]

    return ''.join(chars)


def generate_internationalized_receipt(
    language: str = 'es',
    currency: str = 'EUR'
) -> Dict[str, Any]:
    """
    Generate receipt in different languages/currencies

    Args:
        language: Language code ('es', 'fr', 'de', 'ja', 'zh')
        currency: Currency code ('EUR', 'GBP', 'JPY', 'CNY')

    Returns:
        Receipt dictionary with internationalized content
    """
    translations = {
        'es': {
            'vendor': 'Supermercado Central',
            'date': 'Fecha',
            'subtotal': 'Subtotal',
            'tax': 'IVA',
            'total': 'TOTAL'
        },
        'fr': {
            'vendor': 'Supermarché Central',
            'date': 'Date',
            'subtotal': 'Sous-total',
            'tax': 'TVA',
            'total': 'TOTAL'
        },
        'de': {
            'vendor': 'Zentralmarkt',
            'date': 'Datum',
            'subtotal': 'Zwischensumme',
            'tax': 'MwSt',
            'total': 'GESAMT'
        },
        'ja': {
            'vendor': 'スーパーマーケット',
            'date': '日付',
            'subtotal': '小計',
            'tax': '消費税',
            'total': '合計'
        },
        'zh': {
            'vendor': '超市',
            'date': '日期',
            'subtotal': '小计',
            'tax': '税',
            'total': '总计'
        }
    }

    currency_symbols = {
        'EUR': '€',
        'GBP': '£',
        'JPY': '¥',
        'CNY': '¥',
        'USD': '$'
    }

    trans = translations.get(language, translations['es'])
    symbol = currency_symbols.get(currency, '€')

    date = datetime.now().strftime("%d/%m/%Y")
    subtotal = 45.50
    tax = 3.41
    total = 48.91

    receipt_text = f"""
{trans['vendor']}
{trans['date']}: {date}

Item 1: {symbol}15.00
Item 2: {symbol}20.50
Item 3: {symbol}10.00

{trans['subtotal']}: {symbol}{subtotal:.2f}
{trans['tax']}: {symbol}{tax:.2f}
{trans['total']}: {symbol}{total:.2f}
"""

    return {
        "text": receipt_text.strip(),
        "expected": {
            "vendor": trans['vendor'],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total": total,
            "subtotal": subtotal,
            "tax": tax,
            "currency": currency,
            "language": language
        }
    }


def validate_receipt_fields(fields: Dict[str, Any], strict: bool = True) -> List[str]:
    """
    Validate extracted receipt fields

    Args:
        fields: Extracted fields dictionary
        strict: If True, require all fields

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    required_fields = ['vendor', 'date', 'total']
    optional_fields = ['subtotal', 'tax', 'items', 'confidence']

    # Check required fields
    for field in required_fields:
        if field not in fields:
            errors.append(f"Missing required field: {field}")
        elif fields[field] is None or fields[field] == "":
            errors.append(f"Empty required field: {field}")

    # Validate types
    if 'total' in fields:
        if not isinstance(fields['total'], (int, float)):
            errors.append(f"Invalid total type: {type(fields['total'])}")
        elif fields['total'] < 0 and not fields.get('is_refund', False):
            errors.append(f"Negative total without refund flag: {fields['total']}")

    if 'date' in fields and fields['date']:
        try:
            datetime.strptime(fields['date'], '%Y-%m-%d')
        except ValueError:
            errors.append(f"Invalid date format: {fields['date']}")

    if 'confidence' in fields:
        if not isinstance(fields['confidence'], dict):
            errors.append(f"Invalid confidence type: {type(fields['confidence'])}")
        else:
            for key, score in fields['confidence'].items():
                if not 0 <= score <= 1:
                    errors.append(f"Confidence score out of range: {key}={score}")

    return errors


def calculate_extraction_accuracy(
    extracted: Dict[str, Any],
    expected: Dict[str, Any]
) -> Dict[str, float]:
    """
    Calculate accuracy metrics for extraction

    Args:
        extracted: Extracted fields
        expected: Expected fields

    Returns:
        Dictionary with accuracy metrics
    """
    metrics = {
        'vendor_match': 0.0,
        'date_match': 0.0,
        'total_accuracy': 0.0,
        'overall_score': 0.0
    }

    # Vendor match (fuzzy)
    if 'vendor' in extracted and 'vendor' in expected:
        extracted_vendor = extracted['vendor'].lower()
        expected_vendor = expected['vendor'].lower()
        # Simple substring match
        if expected_vendor in extracted_vendor or extracted_vendor in expected_vendor:
            metrics['vendor_match'] = 1.0
        else:
            metrics['vendor_match'] = 0.0

    # Date match (exact)
    if 'date' in extracted and 'date' in expected:
        metrics['date_match'] = 1.0 if extracted['date'] == expected['date'] else 0.0

    # Total accuracy (within 1%)
    if 'total' in extracted and 'total' in expected:
        if expected['total'] > 0:
            error = abs(extracted['total'] - expected['total']) / expected['total']
            metrics['total_accuracy'] = max(0.0, 1.0 - error)

    # Overall score
    metrics['overall_score'] = sum(metrics.values()) / len(metrics)

    return metrics
