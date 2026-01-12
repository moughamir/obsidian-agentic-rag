# Project Overview

This project is a multi-agent Retrieval-Augmented Generation (RAG) system designed to work with an Obsidian vault. It leverages a clean architecture with a clear separation of concerns between the domain, application, and infrastructure layers. The system is designed to be extensible, with a factory pattern for creating different types of agents.

The core functionality revolves around a `RAGPipeline` that can retrieve information from an Obsidian vault using various strategies, including vector search, keyword search, and graph traversal of wikilinks. The retrieved context is then used by a series of specialized AI agents (e.g., Researcher, Synthesizer, Critic) orchestrated by an `AgentOrchestrator` to answer queries and generate responses.

The project also includes advanced features like:

*   **TOON (Text-Object-Oriented Notation):** A custom, token-efficient format for representing structured data, which can reduce LLM token usage by 30-60%.
*   **Real-time (RT) Kernel Scheduling:** The system can leverage a real-time Linux kernel to optimize for low-latency inference.
*   **Hybrid Search:** Combines semantic (vector) and keyword search for more robust retrieval.
*   **GraphRAG:** Expands context by navigating the knowledge graph of an Obsidian vault through wikilinks.

## Technologies Used

*   **Programming Language:** Python 3.10+
*   **Core Libraries:**
    *   `httpx`: For making asynchronous HTTP requests to LLM APIs and the Obsidian REST API.
    *   `pydantic`: For data validation and settings management.
    *   `numpy`: For numerical operations, likely related to vector embeddings.
    *   `python-dotenv`: For managing environment variables.
*   **Testing:**
    *   `pytest`: For running tests.
    *   `pytest-asyncio`: For testing asynchronous code.
*   **LLM Integration:** The system is designed to work with local LLMs via Ollama.
*   **Vector Search:** The project is set up to integrate with a vector database for semantic search, though the specific implementation is not detailed in the provided files.

## Building and Running

### 1. Setup Virtual Environment

It is recommended to use a virtual environment to manage project dependencies.

```bash
python -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

Install the project in editable mode, which will also install all required dependencies.

```bash
pip install -e .
```

For development, including running tests, install the development dependencies:

```bash
pip install -e .[dev]
```

### 3. Running the Application

The `examples/rag_example.py` script provides a comprehensive demonstration of the system's capabilities.

To run the example with a mock LLM:

```bash
python examples/rag_example.py --vault /path/to/your/obsidian/vault
```

To run the example with a real Ollama LLM:

```bash
python examples/rag_example.py --vault /path/to/your/obsidian/vault --use-ollama
```

### 4. Running Tests

Tests can be run using `pytest`:

```bash
pytest
```

## Development Conventions

*   **Clean Architecture:** The project follows a clean architecture pattern, with a strict separation between domain, application, and infrastructure layers.
*   **Dependency Inversion:** Interfaces are defined in the domain layer, and concrete implementations are provided in the infrastructure layer. This allows for easy swapping of external services like LLM clients and vector stores.
*   **Dependency Injection:** Dependencies are injected into components, promoting loose coupling and testability.
*   **Asynchronous Code:** The project makes extensive use of `asyncio` for non-blocking I/O operations, which is crucial for interacting with LLMs and other external services.
*   **Configuration:** Agent configurations are managed in `config/agents.yaml`, allowing for easy tuning of agent parameters like temperature and model.
*   **Prompts:** Prompts for the agents are stored in separate text files in the `prompts/` directory, keeping them separate from the application logic.
