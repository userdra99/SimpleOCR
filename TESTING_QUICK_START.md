# 🚀 Testing Quick Start - SimpleOCR vLLM Integration

## ⚡ Quick Commands

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html

# Run fast tests only (skip slow performance tests)
pytest -m "not slow"

# Run specific test file
pytest tests/test_vllm_client.py -v
```

## 📁 Test Structure

```
tests/
├── conftest.py                    # Shared fixtures (🔧 Important!)
├── test_vllm_client.py           # 60 unit tests
├── test_ai_receipt_parser.py    # 80 integration tests
├── test_e2e_vllm.py              # 35 E2E tests
├── test_performance.py           # 25 performance tests
├── test_utils.py                 # Test utilities
├── fixtures/
│   ├── sample_receipt_*.txt      # 4 sample receipts
│   ├── expected_outputs.json     # Ground truth
│   └── edge_cases.json           # 8 edge cases
└── mocks/
    └── vllm_responses.json       # 6 mock API responses
```

## 📊 Coverage by File

| Test File | Tests | Coverage Target | Focus Area |
|-----------|-------|-----------------|------------|
| test_vllm_client.py | 60 | 95% | VLLMClient unit tests |
| test_ai_receipt_parser.py | 80 | 90% | AI parser integration |
| test_e2e_vllm.py | 35 | 85% | Complete pipeline |
| test_performance.py | 25 | 80% | Benchmarks |

## 🎯 Test Categories

```bash
# Unit tests (fast, isolated)
pytest -m unit

# Integration tests
pytest -m integration

# End-to-end tests
pytest -m e2e

# Performance benchmarks (slow)
pytest -m slow

# Live server tests (requires vLLM running)
pytest -m live
```

## 🔧 Most Important Fixtures

### From `conftest.py`:

```python
# Mock vLLM client
def test_example(mock_vllm_client):
    parser = AIReceiptParser(vllm_client=mock_vllm_client)
    result = parser.extract_fields("receipt text")

# Sample receipt text
def test_with_receipt(sample_receipt_text):
    # Full Whole Foods receipt with 11 items

# Expected output
def test_validation(expected_receipt_fields):
    # Ground truth for comparison

# Mock HTTP responses
def test_http(mock_requests_success):
    # Successful HTTP response
```

## ⚠️ Important Notes

### Tests Are Currently Skipped
Most tests have `@pytest.mark.skip(reason="Waiting for implementation")`.

**Remove these decorators after implementing:**
- `src/vllm_client.py`
- `src/ai_receipt_parser.py`

### Example:
```python
# Before implementation:
@pytest.mark.skip(reason="Waiting for implementation")
def test_client_initialization():
    client = VLLMClient()

# After implementation:
def test_client_initialization():
    client = VLLMClient()
```

## 🎨 Test Writing Template

```python
import pytest

class TestNewFeature:
    """Test description"""

    def test_feature_works(self, mock_vllm_client):
        """Test specific behavior"""
        # Arrange
        parser = AIReceiptParser(vllm_client=mock_vllm_client)

        # Act
        result = parser.extract_fields("receipt text")

        # Assert
        assert "vendor" in result
        assert result["total"] > 0
```

## 📈 Coverage Requirements

- **Overall:** 90%+
- **Critical paths:** 100%
- **Unit tests:** 95%+
- **Integration tests:** 90%+

## 🐛 Troubleshooting

### Tests Skipped
**Problem:** All tests show as skipped
**Solution:** Remove `@pytest.mark.skip` decorators after implementation

### No Module Named 'src'
**Problem:** `ModuleNotFoundError: No module named 'src'`
**Solution:** Ensure `src/` directory exists with `__init__.py`

### Mock Not Working
**Problem:** Mock fixtures not found
**Solution:** Use fixtures from `conftest.py`, not custom mocks

### Tests Too Slow
**Problem:** Tests take too long
**Solution:** Run `pytest -m "not slow"` to skip performance tests

### Low Coverage
**Problem:** Coverage below 90%
**Solution:** Run `pytest --cov --cov-report=term-missing` to see missing lines

## 📚 Documentation

- **Comprehensive Guide:** `tests/README.md`
- **Coverage Report:** `docs/TEST_COVERAGE.md`
- **Summary:** `docs/TEST_SUITE_SUMMARY.md`
- **Configuration:** `pytest.ini`

## 🎯 Success Criteria

✅ All 200+ tests passing
✅ 90%+ coverage achieved
✅ Critical paths at 100%
✅ Performance targets met:
- Single extraction < 3s
- Average latency < 2s
- Throughput >= 1/s
- Memory < 10MB per receipt

## 🚀 Next Steps

1. ⏳ Wait for `src/vllm_client.py` implementation
2. ⏳ Wait for `src/ai_receipt_parser.py` implementation
3. ✅ Remove `@pytest.mark.skip` decorators
4. ✅ Run: `pytest --cov=src --cov-report=html`
5. ✅ Verify 90%+ coverage
6. ✅ Check performance benchmarks
7. ✅ Review coverage report in `htmlcov/index.html`

---

**Status:** ✅ Ready for Implementation
**Created:** 2025-12-16
**Tests:** 200+
**Coverage Goal:** 90%+
