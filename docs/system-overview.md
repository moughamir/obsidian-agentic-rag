```shell
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│                    (CLI / API / Browser)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AGENT ORCHESTRATOR                             │
│    Coordinates Multiple Specialized Agents                       │
│    (Sequential & Parallel Execution)                             │
└─────┬───────────────────────────────────────────────┬───────────┘
      │                                               │
      ▼                                               ▼
┌──────────────────────┐                    ┌──────────────────────┐
│   BASE AGENTS        │                    │   RAG AGENTS         │
│   (Phase 1)          │                    │   (Phase 2)          │
│                      │                    │                      │
│ - Researcher         │                    │ - RAG_Researcher     │
│ - Synthesizer        │                    │ - RAG_Synthesizer    │
│ - Critic             │                    │ - Specialists        │
│ - Planner            │                    │                      │
│                      │                    │ (With Context        │
│ (No Context)         │                    │  Retrieval)          │
└──────────┬───────────┘                    └───────────┬──────────┘
           │                                            │
           │                                            ▼
           │                                   ┌──────────────────┐
           │                                   │  RAG PIPELINE    │
           │                                   │  (Phase 2)       │
           │                                   └────────┬─────────┘
           │                                            │
           │         ┌──────────────────────────────────┼─────────────────┐
           │         │                                  │                 │
           │         ▼                                  ▼                 ▼
           │  ┌─────────────┐                  ┌─────────────┐  ┌─────────────┐
           │  │ OBSIDIAN    │                  │ VECTOR RAG  │  │ GRAPH       │
           │  │ MCP CLIENT  │                  │             │  │ NAVIGATOR   │
           │  │             │                  │ - Semantic  │  │             │
           │  │ - REST API  │                  │ - Hybrid    │  │ - Wikilinks │
           │  │ - Local FS  │                  │ - Rerank    │  │ - Backlinks │
           │  └─────────────┘                  └─────────────┘  └─────────────┘
           │         │                                  │                 │
           │         └──────────────────────────────────┴─────────────────┘
           │                                  │
           ▼                                  ▼
    ┌──────────────┐               ┌──────────────────┐
    │  LLM CLIENT  │               │  OBSIDIAN VAULT  │
    │              │               │  (Knowledge Base)│
    │ - Ollama     │               │                  │
    │ - Mock       │               │ - Notes          │
    └──────────────┘               │ - Wikilinks      │
           │                       │ - Tags           │
           │                       │ - Frontmatter    │
           │                       └──────────────────┘
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OPTIMIZATION LAYER                            │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ TOON         │  │ RT SCHEDULER │  │ VECTOR DB    │         │
│  │ CONVERTER    │  │              │  │              │         │
│  │              │  │ - Priority   │  │ - ChromaDB   │         │
│  │ 30-60% token │  │ - CPU Pin    │  │ - Embeddings │         │
│  │ savings      │  │ - Real-time  │  │ - BM25       │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```
