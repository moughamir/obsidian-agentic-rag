# Contributing

Thanks for contributing! This file lists quick guidelines to get contributions into this repository smoothly.

1. Setup

   - Create and activate a virtualenv:

     ```bash
     python -m venv venv
     source venv/bin/activate
     ```

   - Install the package and dev deps:

     ```bash
     python -m pip install -e .
     pip install -r requirements.txt
     pip install pre-commit
     ```

2. Pre-commit & formatting

   - Install git hooks once:

     ```bash
     pre-commit install
     ```

   - Run the full hooks locally before pushing:

     ```bash
     pre-commit run --all-files
     ```

   - Formatting/config: black, ruff (auto-fix), isort, mypy.

3. Tests

   - Tests are async. Run with:

     ```bash
     pytest -q
     ```

   - Use `AgentFactory(use_mocks=True)` in tests to avoid external LLM calls.

4. Branches & PRs

   - Branch naming: `feature/<short-desc>`, `fix/<short-desc>`, or `docs/<short-desc>`.
   - Open PRs against `main`. Ensure CI passes and pre-commit hooks run clean.
   - PR checklist (include in description):
     - [ ] Tests added/updated if applicable
     - [ ] pre-commit run locally
     - [ ] Reference relevant files (prompts, agents, llm client)

5. Project-specific notes

   - Architecture: follow Clean Architecture boundaries in `src/`:
     - `src/domain/agent_interface.py` — core contracts
     - `src/agents/` — agent implementations and `AgentFactory`
     - `src/application/orchestrator.py` — orchestrator (sequence/parallel)
     - `src/infrastructure/` — `ILLMClient` and `IPromptLoader` abstractions

   - Adding a new LLM provider: implement `ILLMClient.generate()` and inject via `AgentFactory`.
   - Adding prompt sources: implement `IPromptLoader` (e.g., DB-backed loader) and pass to `AgentFactory`.

6. Editing prompts

   - System prompts live in `prompts/{role}.txt`. Updating these affects agents immediately.

7. CI

   - CI workflow at `.github/workflows/ci.yml` runs pre-commit and `pytest` on PRs to `main`.

8. Questions

   - If unsure where to add code, prefer adding an abstraction in `src/domain/` and implement it in `src/infrastructure/`.

Thanks — maintainers will review changes and request any needed updates.
