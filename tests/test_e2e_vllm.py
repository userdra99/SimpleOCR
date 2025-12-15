"""
End-to-End Tests for vLLM Integration
Tests complete pipeline from receipt text to structured output
"""
import pytest
import json
import subprocess
import os
from pathlib import Path

# These tests will run once the full implementation is complete
pytestmark = pytest.mark.e2e


# ============================================================================
# Pipeline Tests
# ============================================================================

class TestCompletePipeline:
    """Test complete pipeline integration"""

    @pytest.mark.skip(reason="Waiting for full implementation")
    def test_full_pipeline(self, sample_receipt_text, tmp_path):
        """Test complete pipeline from text to JSON output"""
        from src.ai_receipt_parser import AIReceiptParser
        from src.vllm_client import VLLMClient

        # Create temporary input file
        input_file = tmp_path / "receipt.txt"
        input_file.write_text(sample_receipt_text)

        # Run pipeline
        client = VLLMClient()
        parser = AIReceiptParser(vllm_client=client)
        result = parser.extract_fields(sample_receipt_text)

        # Save output
        output_file = tmp_path / "output.json"
        output_file.write_text(json.dumps(result, indent=2))

        # Verify output
        assert output_file.exists()
        output_data = json.loads(output_file.read_text())
        assert "vendor" in output_data
        assert "total" in output_data

    @pytest.mark.skip(reason="Waiting for full implementation")
    def test_pipeline_with_email_data(self, sample_receipt_text, sample_email_data, tmp_path):
        """Test pipeline with email metadata"""
        from src.ai_receipt_parser import AIReceiptParser
        from src.vllm_client import VLLMClient

        client = VLLMClient()
        parser = AIReceiptParser(vllm_client=client)
        result = parser.extract_fields(sample_receipt_text, email_data=sample_email_data)

        assert "vendor" in result
        assert result["vendor"] != ""


# ============================================================================
# CLI Integration Tests
# ============================================================================

class TestCLIIntegration:
    """Test CLI interface"""

    @pytest.mark.skip(reason="Waiting for CLI implementation")
    def test_cli_basic_usage(self, sample_receipt_text, tmp_path):
        """Test basic CLI usage"""
        # Create input file
        input_file = tmp_path / "receipt.txt"
        input_file.write_text(sample_receipt_text)

        output_file = tmp_path / "output.json"

        # Run CLI command
        result = subprocess.run(
            ["python", "main.py", "--use-ai", "--input", str(input_file), "--output", str(output_file)],
            capture_output=True,
            text=True,
            cwd="/home/dra/SimpleOCR"
        )

        assert result.returncode == 0
        assert output_file.exists()

        # Verify output
        with open(output_file) as f:
            data = json.load(f)
        assert "vendor" in data

    @pytest.mark.skip(reason="Waiting for CLI implementation")
    def test_cli_batch_mode(self, performance_test_receipts, tmp_path):
        """Test CLI batch processing"""
        # Create multiple input files
        input_dir = tmp_path / "inputs"
        input_dir.mkdir()

        for i, receipt in enumerate(performance_test_receipts[:5]):
            input_file = input_dir / f"receipt_{i}.txt"
            input_file.write_text(receipt["text"])

        output_dir = tmp_path / "outputs"
        output_dir.mkdir()

        # Run batch processing
        result = subprocess.run(
            ["python", "main.py", "--use-ai", "--batch", str(input_dir), "--output-dir", str(output_dir)],
            capture_output=True,
            text=True,
            cwd="/home/dra/SimpleOCR"
        )

        assert result.returncode == 0

        # Verify outputs
        output_files = list(output_dir.glob("*.json"))
        assert len(output_files) == 5


# ============================================================================
# JSON Output Format Tests
# ============================================================================

class TestJSONOutput:
    """Test JSON output format"""

    @pytest.mark.skip(reason="Waiting for full implementation")
    def test_output_schema(self, sample_receipt_text):
        """Test output conforms to expected schema"""
        from src.ai_receipt_parser import AIReceiptParser
        from src.vllm_client import VLLMClient

        client = VLLMClient()
        parser = AIReceiptParser(vllm_client=client)
        result = parser.extract_fields(sample_receipt_text)

        # Required fields
        required_fields = ["vendor", "date", "total", "confidence"]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

        # Field types
        assert isinstance(result["vendor"], str)
        assert isinstance(result["date"], str)
        assert isinstance(result["total"], (int, float))
        assert isinstance(result["confidence"], dict)

    @pytest.mark.skip(reason="Waiting for full implementation")
    def test_json_serialization(self, sample_receipt_text):
        """Test result can be serialized to JSON"""
        from src.ai_receipt_parser import AIReceiptParser
        from src.vllm_client import VLLMClient

        client = VLLMClient()
        parser = AIReceiptParser(vllm_client=client)
        result = parser.extract_fields(sample_receipt_text)

        # Should serialize without errors
        json_str = json.dumps(result)
        assert len(json_str) > 0

        # Should deserialize back
        parsed = json.loads(json_str)
        assert parsed == result


# ============================================================================
# Error Recovery Tests
# ============================================================================

class TestErrorRecovery:
    """Test error recovery in complete pipeline"""

    @pytest.mark.skip(reason="Waiting for full implementation")
    def test_recover_from_ai_failure(self, sample_receipt_text):
        """Test pipeline recovers from AI service failure"""
        from src.ai_receipt_parser import AIReceiptParser
        from src.vllm_client import VLLMClient

        client = VLLMClient()
        parser = AIReceiptParser(
            vllm_client=client,
            use_regex_fallback=True
        )

        # Simulate AI failure by using invalid URL
        client.url = "http://invalid-host:9999"

        # Should fall back to regex parsing
        result = parser.extract_fields(sample_receipt_text)

        assert "total" in result
        # May not have confidence scores in fallback mode

    @pytest.mark.skip(reason="Waiting for full implementation")
    def test_partial_extraction_on_error(self, malformed_receipt_texts):
        """Test partial extraction when some fields fail"""
        from src.ai_receipt_parser import AIReceiptParser
        from src.vllm_client import VLLMClient

        client = VLLMClient()
        parser = AIReceiptParser(vllm_client=client)

        # Test with various malformed receipts
        for name, text in malformed_receipt_texts.items():
            result = parser.extract_fields(text)

            # Should at least return a dict, even if empty
            assert isinstance(result, dict)


# ============================================================================
# Integration with Existing System Tests
# ============================================================================

class TestSystemIntegration:
    """Test integration with existing SimpleOCR system"""

    @pytest.mark.skip(reason="Waiting for full implementation")
    def test_integration_with_receipt_parser(self, sample_receipt_text):
        """Test AI parser integrates with existing ReceiptParser"""
        from receipt_parser import ReceiptParser
        from src.ai_receipt_parser import AIReceiptParser
        from src.vllm_client import VLLMClient

        # Traditional parser
        traditional = ReceiptParser()
        traditional_result = traditional.parse(sample_receipt_text)

        # AI parser
        client = VLLMClient()
        ai_parser = AIReceiptParser(vllm_client=client)
        ai_result = ai_parser.extract_fields(sample_receipt_text)

        # AI should extract at least as many fields as traditional
        assert len(ai_result) >= len([k for k, v in traditional_result.items() if v])

        # Both should extract total successfully
        assert ai_result["total"] == pytest.approx(traditional_result["total"], rel=0.01)

    @pytest.mark.skip(reason="Waiting for full implementation")
    def test_hybrid_mode_enhancement(self, sample_receipt_text):
        """Test hybrid mode improves over regex-only"""
        from receipt_parser import ReceiptParser
        from src.ai_receipt_parser import AIReceiptParser
        from src.vllm_client import VLLMClient

        # Traditional regex-based
        traditional = ReceiptParser()
        traditional_result = traditional.parse(sample_receipt_text)

        # Hybrid AI + regex
        client = VLLMClient()
        hybrid_parser = AIReceiptParser(vllm_client=client, use_hybrid=True)
        hybrid_result = hybrid_parser.extract_fields(sample_receipt_text)

        # Hybrid should have confidence scores
        assert "confidence" in hybrid_result

        # Hybrid should extract vendor more accurately
        assert len(hybrid_result["vendor"]) > 0


# ============================================================================
# Performance and Load Tests
# ============================================================================

class TestPerformanceE2E:
    """Test end-to-end performance"""

    @pytest.mark.skip(reason="Waiting for full implementation")
    @pytest.mark.slow
    def test_throughput(self, performance_test_receipts):
        """Test system throughput"""
        from src.ai_receipt_parser import AIReceiptParser
        from src.vllm_client import VLLMClient
        import time

        client = VLLMClient()
        parser = AIReceiptParser(vllm_client=client)

        start = time.time()
        results = []

        for receipt in performance_test_receipts[:50]:
            result = parser.extract_fields(receipt["text"])
            results.append(result)

        duration = time.time() - start
        throughput = len(results) / duration

        # Should process at least 1 receipt per second
        assert throughput >= 1.0, f"Throughput too low: {throughput} receipts/sec"

    @pytest.mark.skip(reason="Waiting for full implementation")
    @pytest.mark.slow
    def test_memory_usage(self, performance_test_receipts):
        """Test memory usage stays within bounds"""
        from src.ai_receipt_parser import AIReceiptParser
        from src.vllm_client import VLLMClient
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        client = VLLMClient()
        parser = AIReceiptParser(vllm_client=client)

        # Process many receipts
        for receipt in performance_test_receipts:
            parser.extract_fields(receipt["text"])

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (<100MB)
        assert memory_increase < 100, f"Excessive memory usage: {memory_increase}MB"


# ============================================================================
# Live vLLM Server Tests (Optional)
# ============================================================================

class TestLiveVLLMServer:
    """Tests requiring live vLLM server (run with --runlive flag)"""

    @pytest.mark.skip(reason="Requires live vLLM server")
    @pytest.mark.live
    def test_live_server_connection(self, test_config):
        """Test connection to live vLLM server"""
        from src.vllm_client import VLLMClient

        client = VLLMClient(url=test_config["vllm_url"])

        # Test health check
        is_healthy = client.is_healthy()
        assert is_healthy, "vLLM server is not healthy"

    @pytest.mark.skip(reason="Requires live vLLM server")
    @pytest.mark.live
    def test_live_extraction(self, sample_receipt_text, test_config):
        """Test extraction with live vLLM server"""
        from src.ai_receipt_parser import AIReceiptParser
        from src.vllm_client import VLLMClient

        client = VLLMClient(url=test_config["vllm_url"])
        parser = AIReceiptParser(vllm_client=client)

        result = parser.extract_fields(sample_receipt_text)

        # Verify extraction succeeded
        assert "vendor" in result
        assert "total" in result
        assert result["total"] > 0

        # Verify confidence scores
        assert "confidence" in result
        for field, score in result["confidence"].items():
            assert 0 <= score <= 1
