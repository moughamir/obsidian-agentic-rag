# Obsidian Multi-Agent RAG System

Local, privacy-first AI agent system with specialized roles.

## Quick Start

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # OR
   venv\Scripts\activate  # Windows
   ```

2. **Install in development mode:**
   ```bash
   pip install -e .
   ```

3. **Copy artifacts to src/ directories:**
   - artifact #1 → src/domain/agent_interface.py
   - artifact #2 → src/infrastructure/prompt_manager.py
   - artifact #3 → src/infrastructure/llm_client.py
   - artifact #4 → src/agents/concrete_agent.py
   - artifact #5 → src/agents/agent_factory.py
   - artifact #6 → src/application/orchestrator.py
   - artifact #7 → examples/example_usage.py

4. **Run example:**
   ```bash
   python examples/example_usage.py
   ```

5. **Run tests:**
   ```bash
   pytest tests/
   ```

## Architecture

- **Domain Layer**: Core interfaces (IAgent, AgentTask, AgentResponse)
- **Application Layer**: Orchestration logic (AgentOrchestrator)
- **Infrastructure Layer**: External services (LLM clients, prompt loaders)
- **Agents Layer**: Concrete implementations (BaseAgent, Factory)

## Design Principles

- **Clean Architecture**: Separation of concerns, dependency inversion
- **SOLID**: Single responsibility, open/closed, etc.
- **KISS**: Keep it simple and maintainable
- **DI**: Dependency injection throughout

## Troubleshooting

If you get import errors, make sure you:
1. Installed the package: `pip install -e .`
2. Activated your virtual environment
3. Have all `__init__.py` files in place

## Next Steps

- [ ] Set up Ollama locally
- [ ] Test with real LLM
- [ ] Add Obsidian integration (Phase 2)
- [ ] Add vector search (Phase 3)
- [ ] Add MCP servers (Phase 4)
