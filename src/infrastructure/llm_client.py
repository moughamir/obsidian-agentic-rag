"""
Step 3: LLM Integration
Dependency Inversion: Depend on ILLMClient abstraction, not concrete Ollama
Single Responsibility: Only handle LLM communication
"""

from abc import ABC, abstractmethod
from typing import Optional

import httpx


class ILLMClient(ABC):
    """Abstraction for LLM providers (Ollama, OpenAI, etc.)"""

    @abstractmethod
    async def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate response from LLM"""
        pass


class OllamaClient(ILLMClient):
    """
    Concrete implementation for Ollama
    Single Responsibility: Ollama API communication only
    """

    def __init__(
        self, model: str = "llama3.1:8b", base_url: str = "http://localhost:11434"
    ):
        self.model = model
        self.base_url = base_url

    async def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """
        KISS: Simple HTTP call to Ollama
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": False,
                },
            )
            response.raise_for_status()
            return response.json()["response"]


class MockLLMClient(ILLMClient):
    """Mock for testing - no external dependencies"""

    async def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Return mock response for testing"""
        import asyncio

        await asyncio.sleep(0.1)  # Simulate latency
        return f"Mock response for: {prompt[:50]}..."
