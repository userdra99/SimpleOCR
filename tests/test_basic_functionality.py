"""
Basic functionality tests - unskipped tests to verify implementation
"""
import pytest
from src.vllm_client import VLLMClient
from src.ai_receipt_parser import AIReceiptParser


class TestVLLMClientBasics:
    """Basic VLLMClient tests without mocking"""

    def test_client_initialization(self):
        """Test VLLMClient initializes correctly"""
        client = VLLMClient(
            server_url="http://localhost:8000",
            model_name="Qwen/Qwen3-0.6B",
            timeout=30
        )
        assert client.server_url == "http://localhost:8000"
        assert client.model_name == "Qwen/Qwen3-0.6B"
        assert client.timeout == 30

    def test_client_attributes(self):
        """Test VLLMClient has expected attributes"""
        client = VLLMClient(server_url="http://localhost:8000", model_name="Qwen/Qwen3-0.6B")

        # Check attributes
        assert hasattr(client, 'server_url')
        assert hasattr(client, 'model_name')
        assert hasattr(client, 'timeout')
        assert client.server_url == "http://localhost:8000"

    def test_client_config(self):
        """Test VLLMClient configuration"""
        client = VLLMClient(
            server_url="http://test:9000",
            model_name="test-model",
            timeout=60,
            max_retries=5
        )

        assert client.server_url == "http://test:9000"
        assert client.model_name == "test-model"
        assert client.timeout == 60
        assert client.max_retries == 5


class TestAIReceiptParserBasics:
    """Basic AIReceiptParser tests"""

    def test_parser_initialization(self):
        """Test AIReceiptParser initializes"""
        client = VLLMClient(server_url="http://localhost:8000")
        parser = AIReceiptParser(vllm_client=client, use_fallback=True)

        assert parser.vllm_client is not None
        assert parser.use_fallback is True

    def test_parser_without_client(self):
        """Test parser works without vLLM client (regex only)"""
        parser = AIReceiptParser(vllm_client=None, use_fallback=True)

        # Should still work with regex fallback
        result = parser.extract_fields(
            "Invoice #12345\nPolicy: POL-67890\nTotal: $150.00\nDate: 2024-01-15",
            {}
        )

        assert isinstance(result, dict)
        # With regex fallback, should extract something
        assert len(result) > 0


class TestImports:
    """Test that modules can be imported"""

    def test_import_vllm_client(self):
        """Test VLLMClient can be imported"""
        from src.vllm_client import VLLMClient, VLLMClientError
        assert VLLMClient is not None
        assert VLLMClientError is not None

    def test_import_ai_parser(self):
        """Test AIReceiptParser can be imported"""
        from src.ai_receipt_parser import AIReceiptParser
        assert AIReceiptParser is not None

    def test_src_package(self):
        """Test src package structure"""
        import src
        assert hasattr(src, 'VLLMClient')
        assert hasattr(src, 'AIReceiptParser')
