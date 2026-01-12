import httpx
import asyncio
from src.domain.vector_store_interface import IEmbedder
from src.config import EMBEDDING_MODEL, OLLAMA_BASE_URL

class OllamaEmbedder(IEmbedder):
    """
    Generates embeddings using a local Ollama instance.
    """
    def __init__(self, model: str = EMBEDDING_MODEL, base_url: str = OLLAMA_BASE_URL):
        self.model = model
        self.base_url = base_url
        self._client = httpx.AsyncClient(timeout=60.0)

    async def embed(self, text: str) -> list[float]:
        """Generates an embedding for a single piece of text."""
        try:
            response = await self._client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text.strip()}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])
        except httpx.RequestError as e:
            print(f"Error requesting embedding from Ollama: {e}")
            return []

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generates embeddings for a batch of texts by running individual
        requests concurrently, as Ollama's API does not support batching.
        """
        tasks = [self.embed(text) for text in texts]
        embeddings = await asyncio.gather(*tasks)
        return [emb for emb in embeddings if emb]
