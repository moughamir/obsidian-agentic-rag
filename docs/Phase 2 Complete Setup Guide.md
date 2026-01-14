# 🚀 Phase 2 Complete Setup Guide
## RAG/CAG + MCP + TOON + RT Kernel Integration

---

## 📦 What's New in Phase 2

Phase 1 gave you the multi-agent framework. Phase 2 adds:

✅ **Obsidian Vault Integration** - Direct access to your knowledge base  
✅ **Vector RAG** - Semantic search via embeddings  
✅ **GraphRAG** - Knowledge graph navigation via wikilinks  
✅ **Hybrid Search** - Combines vector + BM25 keyword search  
✅ **TOON Format** - 30-60% token savings  
✅ **RT Scheduler** - Real-time kernel optimization  
✅ **Complete Pipeline** - All components working together  

---

## 🔧 Installation

### Step 1: Install Dependencies

Now that all dependencies are managed via `pyproject.toml`, you can install the project with all development and performance-enhancing optional dependencies:

```bash
# Activate your venv (if not already active)
source venv/bin/activate

# Install the project in editable mode with dev and performance extras
pip install -e .[dev,performance]
```

These dependencies include:

*   `httpx>=0.27.0`
*   `pydantic>=2.6.0`
*   `mcp>=1.0.0`
*   `numpy>=1.26.0`
*   `python-dotenv>=1.0.0`
*   `sentence-transformers>=2.3.1` (Embeddings)
*   `chromadb>=0.4.22` (Vector database)
*   `rank-bm25>=0.2.2` (Keyword search)
*   `networkx>=3.2.1` (Graph navigation)
*   `PyYAML>=6.0` (YAML parsing)

**Development Dependencies (via `.[dev]`):**
*   `pytest>=8.0.0`
*   `pytest-asyncio>=0.23.0`
*   `coverage`

**Performance Dependencies (via `.[performance]`):**
*   `torch>=2.1.0` (Optional: GPU acceleration for embeddings)
*   `faiss-cpu>=1.7.4` (Optional: Faster vector search)


### Step 2: Verify Project Structure

All necessary files are included in the project structure. Ensure your local setup matches this for development.

```
obsidian-agent-rag/
├── src/
│   ├── domain/
│   │   ├── agent_interface.py
│   │
│   ├── application/
│   │   ├── orchestrator.py
│   │   └── rag_pipeline.py
│   │
│   ├── infrastructure/
│   │   ├── llm_client.py
│   │   ├── prompt_manager.py
│   │   ├── mcp_interface.py
│   │   ├── obsidian_mcp_client.py
│   │   ├── graph_navigator.py
│   │   ├── vector_rag.py
│   │   ├── toon_converter.py
│   │   └── rt_scheduler.py
│   │
│   └── agents/
│       ├── concrete_agent.py
│       ├── agent_factory.py
│       └── rag_agent.py
│
├── examples/
│   ├── example_usage.py
│   └── complete_rag_example.py
│
├── data/
│   └── vector_db/                    # ChromaDB storage (created on first run)
│
└── test_vault/                       # Your Obsidian vault (or create one for testing)
    ├── note1.md
    ├── note2.md
    └── ...
```

---

## 🎯 Quick Start Guide

### Option A: With Your Obsidian Vault

```bash
# 1. Point to your vault
python examples/complete_rag_example.py \
  --vault /path/to/your/obsidian/vault

# 2. With real Ollama (if installed)
python examples/complete_rag_example.py \
  --vault /path/to/your/vault \
  --use-ollama
```

### Option B: Create Test Vault

```bash
# Create test vault
mkdir -p test_vault

# Create sample notes
cat > test_vault/clean_architecture.md << 'EOF'
---
tags: [architecture, software]
---

# Clean Architecture

Clean architecture separates concerns into layers:

- **Domain Layer**: Core business logic
- **Application Layer**: Use cases
- **Infrastructure Layer**: External services

Key principle: Dependencies point inward.

See also: [[solid_principles]], [[design_patterns]]
EOF

cat > test_vault/solid_principles.md << 'EOF'
---
tags: [principles, oop]
---

# SOLID Principles

Five principles for better OOP design:

1. **Single Responsibility**: One reason to change
2. **Open/Closed**: Open for extension, closed for modification
3. **Liskov Substitution**: Subtypes must be substitutable
4. **Interface Segregation**: Many specific interfaces
5. **Dependency Inversion**: Depend on abstractions

Links to: [[clean_architecture]]
EOF

# Run with test vault
python examples/complete_rag_example.py --vault ./test_vault
```

---

## 🔬 Understanding the Components

### 1. MCP (Model Context Protocol)

**What it does**: Standardized way to connect agents to data sources

**Interfaces**:
- `IObsidianMCP` - Vault file operations
- `IGraphMCP` - Wikilink navigation
- `IVectorMCP` - Semantic search

**Implementations**:
- `ObsidianMCPClient` - REST API (requires plugin)
- `LocalObsidianReader` - Direct file access (no plugin needed) ✨

```python
# Use LocalObsidianReader (easiest)
from src.infrastructure.obsidian_mcp_client import LocalObsidianReader

client = LocalObsidianReader("/path/to/vault")
note = await client.get_note("my_note.md")
print(note.content)
```

### 2. Vector RAG (Semantic Search)

**What it does**: Finds relevant documents by meaning, not just keywords

**How it works**:
1. Converts text to embeddings (vectors)
2. Stores in ChromaDB
3. Searches by cosine similarity

```python
from src.infrastructure.vector_rag import VectorRAG

rag = VectorRAG()

# Add documents
await rag.add_documents(documents)

# Search
results = await rag.semantic_search("clean code principles", k=5)
```

### 3. GraphRAG (Wikilink Expansion)

**What it does**: Follows `[[wikilinks]]` to expand context

**Strategies**:
- **Outgoing links**: Notes you reference
- **Backlinks**: Notes that reference you
- **Path finding**: Connection between concepts

```python
from src.infrastructure.graph_navigator import GraphNavigator

navigator = GraphNavigator(obsidian_client)

# Expand context 2 hops deep
docs = await navigator.expand_context("architecture.md", depth=2)

# Find connection
path = await navigator.find_path("start.md", "end.md")
```

### 4. Hybrid Search (Best of Both)

**What it does**: Combines semantic (60%) + keyword (40%)

**Why**: 
- Vector search finds similar concepts
- BM25 finds exact term matches
- Together = better results

```python
# Hybrid is the default strategy
results = await rag.hybrid_search(
    "Python async patterns",
    k=5,
    vector_weight=0.6  # 60% vector, 40% keyword
)
```

### 5. TOON (Token Optimization)

**What it does**: Reduces tokens by 30-60% for structured data

**Format comparison**:

**JSON** (verbose):
```json
{
  "chunks": [
    {"id": 1, "score": 0.95, "content": "..."},
    {"id": 2, "score": 0.87, "content": "..."}
  ]
}
```

**TOON** (compact):
```
chunks
  id score content
  1  0.95  ...
  2  0.87  ...
```

```python
from src.infrastructure.toon_converter import TOONConverter

# Convert to TOON
toon_str = TOONConverter.to_toon(data)

# Compare savings
metrics = ContextOptimizer.compare_formats(data)
print(f"Token savings: {metrics['token_savings_pct']}%")
```

### 6. RT Scheduler (Performance)

**What it does**: Uses RT kernel for better performance

**Benefits**:
- Predictable latency
- Priority-based scheduling
- Better concurrent execution

```python
from src.infrastructure.rt_scheduler import RTScheduler

# Set priority for critical operations
@RTScheduler.with_priority(RTScheduler.PRIORITY_HIGH)
async def generate_embeddings():
    # This runs with high priority
    pass
```

**Setup on Arch Linux**:
```bash
# 1. Install RT kernel
sudo pacman -S linux-rt linux-rt-headers

# 2. Grant capability
sudo setcap cap_sys_nice=eip /usr/bin/python3

# 3. Reboot and select RT kernel in GRUB
```

---

## 🎨 Usage Examples

### Example 1: Simple RAG Query

```python
from src.application.rag_pipeline import RAGPipelineFactory
from src.agents.rag_agent import RAGAgentFactory
from src.infrastructure.llm_client import MockLLMClient
from src.infrastructure.prompt_manager import FilePromptLoader

# Setup
rag_pipeline = RAGPipelineFactory.create_local_pipeline(
    vault_path="./test_vault"
)

llm = MockLLMClient()
prompts = FilePromptLoader()

# Create RAG agent
agent = RAGAgentFactory.create_researcher_with_rag(
    rag_pipeline=rag_pipeline,
    llm_client=llm,
    prompt_loader=prompts
)

# Query
task = AgentTask(instruction="What are SOLID principles?")
response = await agent.process(task)

print(f"Sources: {response.sources}")
print(f"Answer: {response.content}")
```

### Example 2: Multi-Agent with RAG

```python
# Create multiple RAG agents
researcher = RAGAgentFactory.create_researcher_with_rag(...)
synthesizer = RAGAgentFactory.create_synthesizer_with_rag(...)

# Orchestrate
orchestrator = AgentOrchestrator()
orchestrator.register(researcher)
orchestrator.register(synthesizer)

# Execute pipeline
results = await orchestrator.execute_sequence(
    agent_names=["RAG_Researcher", "RAG_Synthesizer"],
    task_instruction="Explain clean architecture",
    context=""  # RAG fills this automatically
)
```

### Example 3: Compare Retrieval Strategies

```python
strategies = ["vector", "keyword", "hybrid", "graph", "full"]

for strategy in strategies:
    result = await rag_pipeline.augmented_query(
        query="async programming",
        strategy=strategy
    )
    
    print(f"{strategy}: {len(result['documents'])} docs")
    print(f"  Tokens: {result['metrics']['context_tokens']}")
```

---

## 🐛 Troubleshooting

### Import Error: sentence-transformers

```bash
# Install with CPU support
pip install sentence-transformers

# Or with GPU support (if you have CUDA)
pip install sentence-transformers torch torchvision
```

### Import Error: chromadb

```bash
pip install chromadb
```

### ChromaDB Permission Error

```bash
# Ensure data directory is writable
chmod -R 755 data/
```

### RT Scheduling Not Available

This is normal if:
- Not on Linux
- RT kernel not installed
- No elevated privileges

**Solution**: System runs fine without RT, just uses normal priority.

### Vector Search Too Slow

```bash
# Use smaller embedding model
# In vector_rag.py, change:
EmbeddingConfig(model_name="all-MiniLM-L6-v2")  # Fast, 80MB

# Or install FAISS for faster search
pip install faiss-cpu
```

---

## 📊 Performance Tips

### 1. Optimize Embedding Model

```python
# Fast (80MB): Good for development
model_name="all-MiniLM-L6-v2"

# Balanced (130MB): Better quality
model_name="BAAI/bge-small-en-v1.5"

# Best (550MB): Production quality
model_name="nomic-ai/nomic-embed-text-v1.5"
```

### 2. Tune Hybrid Search Ratio

```python
# More semantic (better for concepts)
vector_weight=0.7  # 70% vector, 30% keyword

# More keyword (better for exact terms)
vector_weight=0.5  # 50% vector, 50% keyword
```

### 3. Adjust Graph Depth

```python
# Faster, less context
depth=1

# Balanced (recommended)
depth=2

# Comprehensive, slower
depth=3
```

### 4. Enable TOON Everywhere

```python
config = RAGConfig(
    use_toon=True,  # 30-60% token savings
    use_rt_scheduling=True,  # Better performance
    rerank=True  # More accurate results
)
```

---

## ✅ Success Checklist

- [ ] Installed Phase 2 dependencies
- [ ] Copied all Phase 2 artifacts
- [ ] Created or pointed to Obsidian vault
- [ ] Ran `complete_rag_example.py` successfully
- [ ] Understood MCP, RAG, GraphRAG concepts
- [ ] Tried different retrieval strategies
- [ ] Tested TOON token optimization
- [ ] (Optional) Set up RT kernel on Arch

---

## 🎓 What You Can Do Now

With Phase 2 complete, you can:

✅ Query your Obsidian vault with AI agents  
✅ Use semantic search to find related concepts  
✅ Follow wikilinks to expand context automatically  
✅ Reduce token usage with TOON format  
✅ Run with RT priority for better performance  
✅ Create specialized agents with domain knowledge  
✅ Build complex multi-agent workflows  

---

## 🚀 Next Steps (Phase 3+)

Future enhancements:

**Phase 3**: Advanced Features
- Conversation memory
- Agent reflection and learning
- Multi-modal support (images, PDFs)

**Phase 4**: Production
- Async batch processing
- Distributed deployment
- Monitoring and observability

**Phase 5**: Integration
- Aether Browser integration
- Cognitive Internet node capabilities
- Federated learning experiments

---

## 💡 Pro Tips

1. **Start with LocalObsidianReader** - No plugin needed, works immediately
2. **Use hybrid search** - Best balance of semantic + keyword
3. **Enable TOON** - Significant token savings
4. **Graph depth = 2** - Good context without being slow
5. **Mock LLM first** - Test RAG pipeline before using real Ollama
