import asyncio
import argparse
import sys
from pathlib import Path

# Add the project root to the Python path to allow for absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.application.knowledge_base import KnowledgeBase
from src.infrastructure.ollama_embedder import OllamaEmbedder
from src.infrastructure.local_vector_store import LocalVectorStore
from src.config import OBSIDIAN_VAULT_PATH, VECTOR_DB_PATH

async def main(force_reindex: bool):
    """
    Initializes the knowledge base and runs the indexing process.
    """
    print("--- Obsidian Vault Indexer ---")

    # Check if the vault path exists
    vault_path = Path(OBSIDIAN_VAULT_PATH)
    if not vault_path.exists() or not vault_path.is_dir():
        print(f"Error: The specified Obsidian vault path does not exist or is not a directory.")
        print(f"Please check your .env file or the path: {vault_path.resolve()}")
        return

    print(f"Vault Path: {vault_path.resolve()}")
    print(f"Vector DB Path: {Path(VECTOR_DB_PATH).resolve()}")

    # Initialize components
    embedder = OllamaEmbedder()
    vector_store = LocalVectorStore(persist_path=VECTOR_DB_PATH)
    kb = KnowledgeBase(vault_path=str(vault_path), embedder=embedder, vector_store=vector_store)

    # Run indexing
    await kb.index_vault(force_reindex=force_reindex)

    print("\nIndexing process complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manually index the Obsidian vault.")
    parser.add_argument(
        "--force-reindex",
        action="store_true",
        help="If set, clears the existing vector store before starting the indexing process."
    )
    args = parser.parse_args()

    try:
        asyncio.run(main(args.force_reindex))
    except KeyboardInterrupt:
        print("\nIndexing cancelled by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
