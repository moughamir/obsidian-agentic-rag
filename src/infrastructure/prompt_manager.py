"""
Step 2: Prompt Management
Single Responsibility: Load and format prompts
Open/Closed: Easy to add new prompt sources (files, DB, etc.)
"""

from abc import ABC, abstractmethod
from pathlib import Path


class IPromptLoader(ABC):
    """Abstraction for loading prompts from different sources"""

    @abstractmethod
    def load(self, role: str) -> str:
        """Load system prompt for a role"""
        pass


class FilePromptLoader(IPromptLoader):
    """Loads prompts from text files"""

    def __init__(self, prompts_dir: str = "./prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(exist_ok=True)

    def load(self, role: str) -> str:
        """Load prompt from file: prompts/{role}.txt"""
        prompt_file = self.prompts_dir / f"{role}.txt"

        if not prompt_file.exists():
            return self._get_default_prompt(role)

        return prompt_file.read_text()

    def _get_default_prompt(self, role: str) -> str:
        """Fallback default prompts"""
        defaults = {
            "researcher": "You are a research assistant. Find accurate information and cite sources.",
            "synthesizer": "You are a synthesis expert. Combine information coherently.",
            "critic": "You are a critical analyst. Validate claims and identify issues.",
        }
        return defaults.get(role, "You are a helpful AI assistant.")


class PromptBuilder:
    """Builds complete prompts from components (Strategy Pattern)"""

    @staticmethod
    def build(
        system_prompt: str, task: str, context: str = "", previous: str = ""
    ) -> str:
        """
        Single responsibility: Format prompt components
        KISS: Simple string concatenation
        """
        parts = [f"SYSTEM: {system_prompt}"]

        if context:
            parts.append(f"\nCONTEXT:\n{context}")

        if previous:
            parts.append(f"\nPREVIOUS RESULTS:\n{previous}")

        parts.append(f"\nTASK: {task}")
        parts.append("\nRESPONSE:")

        return "\n".join(parts)
