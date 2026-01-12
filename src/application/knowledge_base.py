from pathlib import Path
import hashlib
from src.domain.vector_store_interface import IVectorStore, IEmbedder, DocumentChunk, SearchResult

class KnowledgeBase:
    """
    Manages the ingestion and retrieval of documents from a directory (e.g., an Obsidian vault).
    """
    def __init__(self, vault_path: str, embedder: IEmbedder, vector_store: IVectorStore):
        self.vault_path = Path(vault_path)
        self.embedder = embedder
        self.vector_store = vector_store
        self.chunk_size = 1000  # Target characters per chunk
        self.chunk_overlap = 100 # Characters to overlap between chunks

    async def index_vault(self, force_reindex: bool = False):
        """
        Reads all markdown files, splits them into chunks, generates embeddings,
        and stores them in the vector store.

        Args:
            force_reindex: If True, clears the existing store before indexing.
        """
        if force_reindex:
            self.vector_store.clear()

        print(f"Starting vault indexing at: {self.vault_path}")
        markdown_files = list(self.vault_path.rglob("*.md"))

        all_chunks_to_embed = []

        for file_path in markdown_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                text_chunks = self._split_text(content)

                for i, chunk_text in enumerate(text_chunks):
                    if len(chunk_text.strip()) < 50: continue # Skip very short chunks

                    # Create a stable ID based on file path and chunk index
                    chunk_id = hashlib.md5(f"{file_path}_{i}".encode()).hexdigest()

                    all_chunks_to_embed.append(DocumentChunk(
                        id=chunk_id,
                        content=chunk_text,
                        metadata={"source": str(file_path.relative_to(self.vault_path))},
                        embedding=None # To be filled
                    ))
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

        if not all_chunks_to_embed:
            print("No new chunks to index.")
            return

        print(f"Generating embeddings for {len(all_chunks_to_embed)} chunks...")
        texts = [c.content for c in all_chunks_to_embed]
        embeddings = await self.embedder.embed_batch(texts)

        for chunk, emb in zip(all_chunks_to_embed, embeddings):
            chunk.embedding = emb

        await self.vector_store.add(all_chunks_to_embed)
        print(f"Successfully indexed {len(all_chunks_to_embed)} chunks from {len(markdown_files)} files.")

    async def retrieve_context(self, query: str, limit: int = 3) -> str:
        """
        Retrieves relevant context from the vector store based on a query.
        """
        if not query:
            return "No query provided."

        query_emb = await self.embedder.embed(query)
        if not query_emb:
            return "Could not generate query embedding."

        results = await self.vector_store.search(query_emb, limit=limit)

        if not results:
            return "No relevant context found in the vault."

        context_parts = []
        for res in results:
            source = res.chunk.metadata.get('source', 'Unknown')
            context_parts.append(f"Source: {source}\nContent: {res.chunk.content}")

        return "\n\n---\n\n".join(context_parts)

    def _split_text(self, text: str) -> list[str]:
        """A simple text splitter based on fixed size and overlap."""
        if not text:
            return []

        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start += self.chunk_size - self.chunk_overlap

        return chunks
