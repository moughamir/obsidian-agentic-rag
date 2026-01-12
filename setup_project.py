#!/usr/bin/env python3
"""
Complete Setup Script with Import Fix
Creates project structure and sets up package properly
Run: python setup_project.py
"""

from pathlib import Path


def create_file(path: Path, content: str):
    """Create file with content"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n")
    print(f"✓ Created: {path}")


def setup_project():
    """Create complete project structure"""

    print("\n🚀 Setting up Obsidian Multi-Agent RAG Project")
    print("=" * 60)

    base = Path(".")

    # Create directory structure
    dirs = [
        "src/domain",
        "src/application",
        "src/infrastructure",
        "src/agents",
        "prompts",
        "examples",
        "tests",
        "config",
        "data",
    ]

    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    print("\n📁 Created directory structure")

    # Create __init__.py files
    for module in [
        "src",
        "src/domain",
        "src/application",
        "src/infrastructure",
        "src/agents",
        "tests",
        "examples",
    ]:
        create_file(Path(f"{module}/__init__.py"), "")

    # Create setup.py (IMPORTANT for imports)
    create_file(
        base / "setup.py",
        """
from setuptools import setup, find_packages

setup(
    name="obsidian-agent-rag",
    version="0.1.0",
    description="Multi-agent RAG system for Obsidian",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "httpx>=0.27.0",
        "pydantic>=2.6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0",
        ]
    },
)
        """,
    )

    # Create requirements.txt
    create_file(
        base / "requirements.txt",
        """
httpx==0.27.0
pydantic==2.6.0
pytest==8.0.0
pytest-asyncio==0.23.0
        """,
    )

    # Create prompts
    create_file(
        base / "prompts/researcher.txt",
        """
You are a Research Agent specialized in information retrieval.

Your responsibilities:
- Search thoroughly and accurately
- Cite sources and references
- Identify knowledge gaps
- Provide comprehensive findings

Always be precise and thorough in your research.
        """,
    )

    create_file(
        base / "prompts/synthesizer.txt",
        """
You are a Synthesis Agent specialized in combining information.

Your responsibilities:
- Integrate information from multiple sources
- Identify patterns and connections
- Resolve contradictions intelligently
- Create coherent narratives

Focus on clarity and coherence in your synthesis.
        """,
    )

    create_file(
        base / "prompts/critic.txt",
        """
You are a Critical Analysis Agent.

Your responsibilities:
- Validate claims against evidence
- Identify logical issues and fallacies
- Check for biases and assumptions
- Assess confidence levels

Be constructive but rigorous in your analysis.
        """,
    )

    create_file(
        base / "prompts/specialist.txt",
        """
You are a Specialist Agent with deep domain expertise.

Your responsibilities:
- Provide expert-level insights
- Apply domain-specific knowledge
- Identify nuanced patterns
- Offer professional recommendations

Leverage your expertise to provide high-quality analysis.
        """,
    )

    # Create README
    create_file(
        base / "README.md",
        """
# Obsidian Multi-Agent RAG System

Local, privacy-first AI agent system with specialized roles.

## Quick Start

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # OR
   venv\\Scripts\\activate  # Windows
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
        """,
    )

    # Create simple test
    create_file(
        base / "tests/test_basic.py",
        """
import pytest
from src.agents.agent_factory import AgentFactory
from src.domain.agent_interface import AgentTask


@pytest.mark.asyncio
async def test_agent_creation():
    '''Test basic agent creation'''
    factory = AgentFactory(use_mocks=True)
    agent = factory.create_researcher()

    assert agent.name == "Researcher"
    assert agent.role == "researcher"


@pytest.mark.asyncio
async def test_agent_processing():
    '''Test agent can process tasks'''
    factory = AgentFactory(use_mocks=True)
    agent = factory.create_researcher()

    task = AgentTask(instruction="What is 2+2?")
    response = await agent.process(task)

    assert response.agent_name == "Researcher"
    assert len(response.content) > 0
    assert 0 <= response.confidence <= 1
        """,
    )

    # Create pyproject.toml
    create_file(
        base / "pyproject.toml",
        """
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "obsidian-agent-rag"
version = "0.1.0"
description = "Multi-agent RAG system for Obsidian"
requires-python = ">=3.10"
dependencies = [
    "httpx>=0.27.0",
    "pydantic>=2.6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
        """,
    )

    # Create .gitignore
    create_file(
        base / ".gitignore",
        """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.venv
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Data
data/
*.db
*.sqlite

# Logs
logs/
*.log
        """,
    )

    # Create VS Code settings for proper imports
    vscode_dir = base / ".vscode"
    vscode_dir.mkdir(exist_ok=True)
    create_file(
        vscode_dir / "settings.json",
        """
{
    "python.analysis.extraPaths": [
        "${workspaceFolder}"
    ],
    "python.analysis.autoImportCompletions": true,
    "python.analysis.typeCheckingMode": "basic"
}
        """,
    )

    print("\n" + "=" * 60)
    print("✅ Project setup complete!")
    print("\n📋 Next steps:")
    print("  1. Create virtual environment:")
    print("     python -m venv venv")
    print("  2. Activate it:")
    print("     source venv/bin/activate  # Linux/Mac")
    print("     venv\\Scripts\\activate  # Windows")
    print("  3. Install package in editable mode:")
    print("     pip install -e .")
    print("  4. Copy code files from artifacts to src/")
    print("  5. Run example:")
    print("     python examples/example_usage.py")
    print("\n💡 The 'pip install -e .' step is crucial for imports to work!")
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    setup_project()
