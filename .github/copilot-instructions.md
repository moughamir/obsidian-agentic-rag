# Copilot / AI Agent Instructions

Purpose: quickly orient an AI coding agent to be productive in this repository.

- **Big picture**: This repo implements a small, local multi-agent RAG system using Clean Architecture.
  - Domain: `src/domain/agent_interface.py` — core contracts (`IAgent`, `AgentTask`, `AgentResponse`).
  - Agents: `src/agents/` — `AgentFactory` wires `BaseAgent` implementations via DI.
  - Application: `src/application/orchestrator.py` — coordinates agents (sequence & parallel).
  - Infrastructure: `src/infrastructure/` — `ILLMClient` abstraction (`OllamaClient`, `MockLLMClient`) and `FilePromptLoader`.
  - Examples: `examples/example_usage.py` shows common usage and orchestration patterns.

- **Key patterns to preserve**:
  - Dependency Injection: agents are created with explicit `llm_client` and `prompt_loader`.
  - Abstractions first: implement features by depending on interfaces (`ILLMClient`, `IPromptLoader`, `IAgent`).
  - KISS and SOLID: keep implementations small and testable; prefer composition over inheritance.

- **How to run / test**:
  - Install in editable mode: `python -m pip install -e .`
  - Run examples: `python examples/example_usage.py` (the script uses `AgentFactory(use_mocks=True)` by default).
  - Run tests: `pytest -q` (tests use `pytest-asyncio`, see `requirements.txt`).

- **Mocks vs real LLM**:
  - To run without an external LLM use: `AgentFactory(use_mocks=True)` (MockLLMClient).
  - To use Ollama, ensure an Ollama instance is reachable at `http://localhost:11434` or pass a configured `OllamaClient(base_url=...)` to `AgentFactory`.

- **Prompts and customization**:
  - System prompts live in the `prompts/` folder and are loaded by `FilePromptLoader` as `prompts/{role}.txt`.
  - Defaults are defined in `src/infrastructure/prompt_manager.py`.

- **When modifying behavior**:
  - Add new LLM providers by implementing `ILLMClient.generate()` in a new class and injecting it via `AgentFactory`.
  - Add new prompt sources by implementing `IPromptLoader`.
  - Add agent roles by creating `AgentConfig` values and registering instances with `AgentOrchestrator.register()`.

- **Tests and conventions**:
  - Async tests use `@pytest.mark.asyncio` (see `tests/test_basic.py`).
  - Keep changes isolated: prefer constructor DI so tests can inject `MockLLMClient`.

- **Files to inspect for context**:
  - `src/domain/agent_interface.py`
  - `src/agents/agent_factory.py`
  - `src/agents/concrete_agent.py`
  - `src/infrastructure/llm_client.py`
  - `src/infrastructure/prompt_manager.py`
  - `src/application/orchestrator.py`
  - `examples/example_usage.py`


  **CI / Formatting / Commit hooks**

  - This repo includes a basic GitHub Actions workflow at `.github/workflows/ci.yml` that:
    - Installs the package (`pip install -e .`) and `requirements.txt`.
    - Installs `pre-commit` and runs hooks across all files.
    - Runs `pytest -q`.

  - Install and run locally:

    ```bash
    python -m pip install -e .
    pip install -r requirements.txt
    pip install pre-commit
    pre-commit install
    pre-commit run --all-files
    pytest -q
    ```

  - Pre-commit configuration is in `.pre-commit-config.yaml` and includes `black`, `ruff` (auto-fix), `isort`, and `mypy`.

  - When contributing: run `pre-commit install` once, then formatting and linters will run on each commit. CI will enforce the same checks on PRs to `main`.


