import httpx
from abc import ABC, abstractmethod
import os

class ILLMClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str, temperature: float = 0.7) -> str:
        pass

class OllamaClient(ILLMClient):
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.base_url = base_url

    async def generate(self, prompt: str, temperature: float = 0.7) -> str:
        # Check for model override in env
        model = os.getenv("LLM_MODEL", "llama3.1:8b")

        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature}
            }
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

class MockLLMClient(ILLMClient):
    """
    Mock LLM for Phase 1 testing.
    Returns a deterministic echo of the prompt to verify pipeline flow.
    """
    async def generate(self, prompt: str, temperature: float = 0.7) -> str:
        # Extract a snippet of the prompt for the mock response
        lines = prompt.split('\n\n')
        system_prompt = next((l for l in lines if l.startswith("SYSTEM:")), "SYSTEM: No System Prompt Found")
        instruction_section = next((l for l in lines if l.startswith("INSTRUCTION:")), "INSTRUCTION: No Instruction Found")
        instruction_text = instruction_section.replace("INSTRUCTION:", "").strip()

        response = (
            f"[MOCK LLM RESPONSE]\n"
            f"Temperature: {temperature}\n"
            f"System Role: {system_prompt.replace('SYSTEM:', '').strip()}\n"
            f"Instruction: {instruction_text[:100]}...\n"
            f"Action: Processing task as mock agent."
        )
        return response
