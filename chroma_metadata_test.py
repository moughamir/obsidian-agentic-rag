import chromadb
import shutil

print(f"ChromaDB version: {chromadb.__version__}")

# Setup client
db_path = "./temp_chroma_test_db"
client = chromadb.PersistentClient(path=db_path)
collection = client.get_or_create_collection(name="test_collection")

# --- Test Case ---
print("\nAttempting to add document with list metadata...")
try:
    collection.add(
        ids=["1"],
        documents=["test document"],
        metadatas=[{"tags": ["tag1", "tag2"]}]
    )
    print("✅ SUCCESS: ChromaDB accepted list metadata.")
except Exception as e:
    print(f"❌ FAILURE: ChromaDB raised an error: {e}")
finally:
    # Cleanup
    print("Cleaning up temporary database.")
    shutil.rmtree(db_path)
