"""
vLLM Client Module - Handles communication with vLLM server for AI-powered text extraction
"""
import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import aiohttp
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


@dataclass
class VLLMResponse:
    """Response from vLLM server"""
    text: str
    confidence: float
    model: str
    usage: Dict[str, int]
    raw_response: Dict[str, Any]


class VLLMClientError(Exception):
    """Base exception for vLLM client errors"""
    pass


class VLLMConnectionError(VLLMClientError):
    """Connection to vLLM server failed"""
    pass


class VLLMTimeoutError(VLLMClientError):
    """Request to vLLM server timed out"""
    pass


class VLLMClient:
    """
    Client for interacting with vLLM server for text generation and extraction.

    Supports both synchronous and asynchronous requests with:
    - Exponential backoff retry logic
    - Connection pooling
    - Timeout handling
    - Response validation
    """

    def __init__(
        self,
        server_url: str,
        model_name: str = "Qwen/Qwen3-0.6B",
        timeout: int = 30,
        max_retries: int = 3,
        max_tokens: int = 512,
        temperature: float = 0.1,
    ):
        """
        Initialize vLLM client.

        Args:
            server_url: URL of vLLM server (e.g., "http://localhost:8000")
            model_name: Model identifier
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (lower = more deterministic)
        """
        self.server_url = server_url.rstrip('/')
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Endpoints
        self.completions_url = f"{self.server_url}/v1/completions"
        self.chat_completions_url = f"{self.server_url}/v1/chat/completions"
        self.models_url = f"{self.server_url}/v1/models"

        # Session for connection pooling
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with connection pooling"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=10,  # Connection pool size
                limit_per_host=5,
                ttl_dns_cache=300
            )
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
        return self._session

    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()

    def _build_prompt(self, system_prompt: str, user_prompt: str) -> str:
        """Build a formatted prompt for the model"""
        return f"{system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True
    )
    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> VLLMResponse:
        """
        Generate text asynchronously using vLLM server.

        Args:
            prompt: The input prompt
            system_prompt: Optional system instruction
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            VLLMResponse with generated text and metadata

        Raises:
            VLLMConnectionError: If unable to connect to server
            VLLMTimeoutError: If request times out
        """
        session = await self._get_session()

        # Build full prompt
        if system_prompt:
            full_prompt = self._build_prompt(system_prompt, prompt)
        else:
            full_prompt = prompt

        # Build request payload
        payload = {
            "model": self.model_name,
            "prompt": full_prompt,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
            "top_p": 0.95,
            "stop": ["User:", "\n\n\n"],
        }

        try:
            async with session.post(self.completions_url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise VLLMConnectionError(
                        f"vLLM server returned status {response.status}: {error_text}"
                    )

                result = await response.json()

                # Extract response
                choices = result.get("choices", [])
                if not choices:
                    raise VLLMClientError("No choices in vLLM response")

                generated_text = choices[0].get("text", "").strip()

                # Calculate confidence (simplified - based on finish reason)
                finish_reason = choices[0].get("finish_reason", "")
                confidence = 0.9 if finish_reason == "stop" else 0.7

                return VLLMResponse(
                    text=generated_text,
                    confidence=confidence,
                    model=result.get("model", self.model_name),
                    usage=result.get("usage", {}),
                    raw_response=result
                )

        except asyncio.TimeoutError as e:
            raise VLLMTimeoutError(f"Request timed out after {self.timeout}s") from e
        except aiohttp.ClientError as e:
            raise VLLMConnectionError(f"Failed to connect to vLLM server: {e}") from e

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> VLLMResponse:
        """
        Synchronous wrapper for generate_async.

        Args:
            prompt: The input prompt
            system_prompt: Optional system instruction
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            VLLMResponse with generated text and metadata
        """
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self.generate_async(prompt, system_prompt, temperature, max_tokens)
            )
        finally:
            # Clean up
            loop.run_until_complete(self.close())
            loop.close()

    def check_health(self) -> bool:
        """
        Check if vLLM server is healthy and responsive.

        Returns:
            True if server is healthy, False otherwise
        """
        try:
            response = requests.get(
                f"{self.server_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """
        List available models on the vLLM server.

        Returns:
            List of model names
        """
        try:
            response = requests.get(self.models_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model.get("id") for model in data.get("data", [])]
            return []
        except Exception:
            return []

    def extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract and parse JSON from model response.

        Args:
            response_text: The generated text from model

        Returns:
            Parsed JSON dict or None if parsing fails
        """
        # Try to find JSON in response
        # Look for {...} pattern
        import re
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, response_text, re.DOTALL)

        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # Try parsing the whole response
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return None

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup on context exit"""
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self.close())
        finally:
            loop.close()
