# src/infrastructure/prompt_manager.py
import os
from pathlib import Path
from typing import Protocol

__all__ = ["FilePromptLoader", "IPromptLoader", "PromptBuilder"]


class IPromptLoader(Protocol):
    """Protocol for prompt loaders used by agents and factories."""

    def load(self, role: str) -> str:
        """Return the system prompt text for the given role"""
        ...


class PromptBuilder:
    """Small helper utilities to build prompts using a prompt loader."""

    @staticmethod
    def build_system_prompt(role: str, loader: IPromptLoader) -> str:
        """Return the system prompt for a role using the provided loader."""
        return loader.load(role)


class FilePromptLoader:
    """Loads agent prompts from text files."""

    def __init__(self, base_path: str = "prompts"):
        self.base_path = Path(base_path)
        if not self.base_path.exists() or not self.base_path.is_dir():
            raise FileNotFoundError(
                f"Prompt directory not found at: {self.base_path.resolve()}"
            )

    def load(self, role: str) -> str:
        """
        Loads the system prompt for a given agent role.
        The role is expected to correspond to a filename (e.g., 'supervisor' -> 'supervisor.txt').
        """
        prompt_file = self.base_path / f"{role}.txt"

        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            # Fallback for roles that might not have a dedicated file
            # or for specialist prompts.
            specialist_file = self.base_path / "specialist.txt"
            if specialist_file.exists():
                with open(specialist_file, "r", encoding="utf-8") as f:
                    return f.read().strip().replace("{role}", role.capitalize())

            return f"You are a helpful assistant role-playing as a {role.capitalize()}."
