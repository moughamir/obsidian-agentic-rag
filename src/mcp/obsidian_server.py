import asyncio
from mcp.server import Server, InitializationOptions, NotificationOptions
from mcp.types import Tool, TextContent

# Application Components
from src.application.knowledge_base import KnowledgeBase
from src.application.orchestrator import AgentOrchestrator
from src.agents.agent_factory import AgentFactory

# Infrastructure Components
from src.infrastructure.ollama_embedder import OllamaEmbedder
from src.infrastructure.local_vector_store import LocalVectorStore

# Configuration
from src.config import OBSIDIAN_VAULT_PATH, VECTOR_DB_PATH

# --- MCP Server Setup ---
server = Server("obsidian-agent-rag")

# Global variables to hold initialized components for the server context
_kb: KnowledgeBase | None = None
_orchestrator: AgentOrchestrator | None = None

def set_dependencies(kb: KnowledgeBase, orchestrator: AgentOrchestrator):
    """Injects initialized components into the global server scope."""
    global _kb, _orchestrator
    _kb = kb
    _orchestrator = orchestrator

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Defines the tools available to the MCP client."""
    return [
        Tool(
            name="search_vault",
            description="Searches the local Obsidian vault for notes relevant to a query.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query to find relevant notes."}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="ask_researcher",
            description="Asks the Researcher agent to perform a task, optionally using provided context.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "The primary task or question for the agent."},
                    "context": {"type": "string", "description": "Optional context, typically from 'search_vault', to guide the agent."}
                },
                "required": ["task"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Executes the requested tool."""
    if name == "search_vault":
        if not _kb:
            return [TextContent(type="text", text="Error: KnowledgeBase not initialized.")]
        query = arguments.get("query", "")
        context = await _kb.retrieve_context(query)
        return [TextContent(type="text", text=context)]

    elif name == "ask_researcher":
        if not _orchestrator:
            return [TextContent(type="text", text="Error: AgentOrchestrator not initialized.")]

        task = arguments.get("task", "")
        context = arguments.get("context", "") # Can be empty

        # Combine task and context for the agent
        full_task_prompt = f"Task: {task}"
        if context:
            full_task_prompt += f"\n\nUse the following context to inform your answer:\n---\n{context}\n---"

        # Execute the agent sequence
        response = await _orchestrator.execute_sequence(["Researcher"], full_task_prompt)
        final_content = response[-1].content if response else "Agent did not produce a response."
        return [TextContent(type="text", text=final_content)]

    return [TextContent(type="text", text=f"Error: Unknown tool '{name}'.")]

async def main():
    """Initializes all components and starts the MCP server."""
    print("Initializing components for MCP server...")

    # 1. Initialize Infrastructure & Application Services
    embedder = OllamaEmbedder()
    vector_store = LocalVectorStore(persist_path=VECTOR_DB_PATH)
    kb = KnowledgeBase(vault_path=OBSIDIAN_VAULT_PATH, embedder=embedder, vector_store=vector_store)

    # 2. Initialize Agent Orchestrator
    agent_factory = AgentFactory(use_mocks=False)
    orchestrator = AgentOrchestrator()
    orchestrator.register(agent_factory.create_researcher("Researcher"))

    # 3. Inject dependencies into the server
    set_dependencies(kb, orchestrator)

    print("Components initialized. Starting MCP stdio server...")

    # 4. Run the server
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="obsidian-agent-rag",
                server_version="0.2.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shut down.")
