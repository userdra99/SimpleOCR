"""
Pytest Configuration and Shared Fixtures
Provides common test fixtures, mocks, and utilities
"""
import pytest
import json
import os
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List


# ============================================================================
# Test Configuration
# ============================================================================

@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration"""
    return {
        "vllm_url": "http://localhost:8000",
        "vllm_model": "meta-llama/Llama-3.2-3B-Instruct",
        "max_retries": 3,
        "timeout": 30,
        "confidence_threshold": 0.7,
    }


@pytest.fixture(scope="session")
def fixtures_dir():
    """Return path to fixtures directory"""
    return os.path.join(os.path.dirname(__file__), "fixtures")


# ============================================================================
# Mock vLLM Server
# ============================================================================

@pytest.fixture
def mock_vllm_response():
    """Mock successful vLLM API response"""
    return {
        "id": "cmpl-test-123",
        "object": "text_completion",
        "created": 1234567890,
        "model": "meta-llama/Llama-3.2-3B-Instruct",
        "choices": [
            {
                "index": 0,
                "text": json.dumps({
                    "vendor": "Whole Foods Market",
                    "date": "2024-03-15",
                    "total": 87.43,
                    "subtotal": 81.23,
                    "tax": 6.20,
                    "confidence": {
                        "vendor": 0.95,
                        "date": 0.98,
                        "total": 0.99,
                        "subtotal": 0.92,
                        "tax": 0.94
                    }
                }),
                "logprobs": None,
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 50,
            "total_tokens": 200
        }
    }


@pytest.fixture
def mock_vllm_error_response():
    """Mock vLLM error response"""
    return {
        "error": {
            "message": "Model is overloaded. Please try again later.",
            "type": "server_error",
            "code": 503
        }
    }


@pytest.fixture
def mock_vllm_client(mock_vllm_response):
    """Mock VLLMClient for testing"""
    client = MagicMock()
    client.generate.return_value = json.loads(
        mock_vllm_response["choices"][0]["text"]
    )
    client.is_healthy.return_value = True
    client.url = "http://localhost:8000"
    client.model = "meta-llama/Llama-3.2-3B-Instruct"
    return client


# ============================================================================
# Sample Receipt Data
# ============================================================================

@pytest.fixture
def sample_receipt_text():
    """Sample receipt text for testing"""
    return """
WHOLE FOODS MARKET
123 Main Street
San Francisco, CA 94102
Tel: (415) 555-0123

Date: 03/15/2024
Time: 14:32:15
Register: 5
Cashier: Sarah M.

ORGANIC BANANAS          3.99
AVOCADOS (3)            5.97
GREEK YOGURT            4.99
ALMOND MILK             6.49
MIXED GREENS            4.99
WHOLE WHEAT BREAD       3.99
FREE RANGE EGGS         7.99
ORGANIC COFFEE         14.99
SPARKLING WATER         8.99
OLIVE OIL              12.99
DARK CHOCOLATE          4.99

SUBTOTAL:              81.23
TAX (7.5%):             6.20
TOTAL:                 87.43

VISA ending in 1234
AUTH: 123456

Thank you for shopping!
"""


@pytest.fixture
def sample_receipt_minimal():
    """Minimal receipt with only essential fields"""
    return """
Coffee Shop Receipt
Date: 2024-03-15
Total: $5.50
"""


@pytest.fixture
def sample_receipt_complex():
    """Complex receipt with multiple items and discounts"""
    return """
TARGET STORE #1234
456 Oak Avenue, Austin, TX 78701
(512) 555-9876

Transaction Date: March 15, 2024
Time: 09:45 AM
Receipt #: T1234567890

ITEMS:
Widget A (2 @ $15.99)          $31.98
Widget B                       $24.99
Widget C - SALE                $19.99
    Regular Price: $29.99
    You Saved: $10.00
Service Fee                     $2.50

SUBTOTAL:                      $79.46
DISCOUNT (Member 10%):         -$7.95
SALES TAX (8.25%):             $5.90
TOTAL:                        $77.41

Payment Method: Credit Card
Card: VISA ****5678
"""


@pytest.fixture
def expected_receipt_fields():
    """Expected extracted fields from sample receipt"""
    return {
        "vendor": "Whole Foods Market",
        "date": "2024-03-15",
        "total": 87.43,
        "subtotal": 81.23,
        "tax": 6.20,
        "items": [
            {"name": "ORGANIC BANANAS", "price": 3.99},
            {"name": "AVOCADOS (3)", "price": 5.97},
            {"name": "GREEK YOGURT", "price": 4.99},
        ],
        "confidence": {
            "vendor": 0.95,
            "date": 0.98,
            "total": 0.99,
            "subtotal": 0.92,
            "tax": 0.94
        }
    }


# ============================================================================
# Mock Email Data
# ============================================================================

@pytest.fixture
def sample_email_data():
    """Sample email metadata"""
    return {
        "subject": "Your Whole Foods Market Receipt",
        "from": "receipts@wholefoods.com",
        "date": "2024-03-15T14:32:15Z",
        "message_id": "msg-12345"
    }


# ============================================================================
# Performance Test Data
# ============================================================================

@pytest.fixture
def performance_test_receipts():
    """Generate multiple receipts for performance testing"""
    receipts = []
    vendors = ["Whole Foods", "Target", "CVS", "Starbucks", "Amazon"]

    for i in range(100):
        vendor = vendors[i % len(vendors)]
        receipts.append({
            "text": f"""
{vendor} Store
Date: 2024-03-{(i % 28) + 1:02d}
Transaction #{i:06d}

Item 1: ${10 + (i % 50)}.99
Item 2: ${5 + (i % 30)}.49

Subtotal: ${15 + (i % 80)}.48
Tax: ${1 + (i % 10)}.20
Total: ${16 + (i % 90)}.68
""",
            "expected": {
                "vendor": vendor,
                "date": f"2024-03-{(i % 28) + 1:02d}",
                "total": 16 + (i % 90) + 0.68
            }
        })

    return receipts


# ============================================================================
# Error Scenarios
# ============================================================================

@pytest.fixture
def malformed_receipt_texts():
    """Various malformed or edge case receipts"""
    return {
        "empty": "",
        "no_amounts": "Store Name\nDate: 2024-03-15\nThank you!",
        "invalid_date": "Store\nDate: not-a-date\nTotal: $10.00",
        "negative_total": "Store\nDate: 2024-03-15\nTotal: -$50.00",
        "missing_vendor": "Date: 2024-03-15\nTotal: $25.00",
        "special_chars": "Store™\nDäté: 2024-03-15\nTötäl: €50.00",
        "very_large": "STORE\n" + ("Item X $9.99\n" * 1000) + "Total: $9999.00",
        "unicode_mixed": "咖啡店 Coffee Shop\n日期 Date: 2024-03-15\nTotal: ¥500",
    }


# ============================================================================
# HTTP Mocks
# ============================================================================

@pytest.fixture
def mock_requests_success(mock_vllm_response):
    """Mock successful HTTP requests"""
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_vllm_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def mock_requests_timeout():
    """Mock HTTP timeout"""
    with patch('requests.post') as mock_post:
        mock_post.side_effect = TimeoutError("Request timeout")
        yield mock_post


@pytest.fixture
def mock_requests_connection_error():
    """Mock connection error"""
    with patch('requests.post') as mock_post:
        mock_post.side_effect = ConnectionError("Connection refused")
        yield mock_post


@pytest.fixture
def mock_requests_server_error():
    """Mock server error response"""
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"
        mock_response.raise_for_status.side_effect = Exception("503 Server Error")
        mock_post.return_value = mock_response
        yield mock_post


# ============================================================================
# Test Utilities
# ============================================================================

@pytest.fixture
def assert_receipt_fields():
    """Utility to assert receipt fields are valid"""
    def _assert(fields: Dict[str, Any], required_keys: List[str] = None):
        if required_keys is None:
            required_keys = ["vendor", "date", "total"]

        for key in required_keys:
            assert key in fields, f"Missing required field: {key}"
            assert fields[key] is not None, f"Field {key} is None"
            assert fields[key] != "", f"Field {key} is empty"

        # Validate data types
        if "total" in fields:
            assert isinstance(fields["total"], (int, float)), "Total must be numeric"
            assert fields["total"] > 0, "Total must be positive"

        if "date" in fields:
            assert len(fields["date"]) >= 8, "Date too short"

        if "confidence" in fields:
            for key, score in fields["confidence"].items():
                assert 0 <= score <= 1, f"Confidence {key} out of range: {score}"

    return _assert


@pytest.fixture
def load_fixture():
    """Load fixture file"""
    def _load(filename: str):
        fixtures_path = os.path.join(
            os.path.dirname(__file__), "fixtures", filename
        )
        with open(fixtures_path, 'r') as f:
            if filename.endswith('.json'):
                return json.load(f)
            return f.read()
    return _load
