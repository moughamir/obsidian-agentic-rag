# Obsidian Multi-Agent RAG System

Local, privacy-first AI agent system with specialized roles.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run example:**
   ```bash
   python examples/example_usage.py
   ```

3. **Run tests:**
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

## Next Steps

- [ ] Set up Ollama locally
- [ ] Test with real LLM
- [ ] Add Obsidian integration (Phase 2)
- [ ] Add vector search (Phase 3)
- [ ] Add MCP servers (Phase 4)