import os
from dotenv import load_dotenv

load_dotenv()

# --- Environment Variables ---
OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "./my_vault")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/vectors.json")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
