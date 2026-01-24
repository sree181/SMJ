# Official Neo4j GraphRAG Setup Guide

## Overview

This guide uses the **official `neo4j-graphrag` Python package** from Neo4j, which provides production-grade GraphRAG capabilities.

**Documentation**: https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_rag.html

---

## Installation

```bash
pip install neo4j-graphrag
```

For OLLAMA support (already installed):
```bash
# OLLAMA support is built-in, no extra install needed
```

---

## Key Components

### 1. Vector Index Creation
```python
from neo4j_graphrag.indexes import create_vector_index

create_vector_index(
    driver=driver,
    index_name="paper-embeddings",
    label="Paper",
    embedding_property="embedding",
    dimensions=384,
    similarity_fn="cosine"
)
```

### 2. Retriever Options

#### VectorRetriever (Vector Search Only)
```python
from neo4j_graphrag.retrievers import VectorRetriever

retriever = VectorRetriever(
    driver=driver,
    index_name="paper-embeddings",
    embedder=embedder
)
```

#### VectorCypherRetriever (Vector + Graph Traversal)
```python
from neo4j_graphrag.retrievers import VectorCypherRetriever

retriever = VectorCypherRetriever(
    driver=driver,
    index_name="paper-embeddings",
    retrieval_query="""
    MATCH (p:Paper)-[r]->(entity)
    WHERE p IN $nodes
    RETURN p, collect(DISTINCT type(r)) as rel_types
    """,
    embedder=embedder
)
```

### 3. LLM Integration (OLLAMA)
```python
from neo4j_graphrag.llm import OllamaLLM

llm = OllamaLLM(
    model_name="llama3.1:8b",
    host="http://localhost:11434"
)
```

### 4. GraphRAG Pipeline
```python
from neo4j_graphrag.generation import GraphRAG

rag = GraphRAG(
    retriever=retriever,
    llm=llm
)

response = rag.search(
    query_text="What papers use Resource-Based View?",
    retriever_config={"top_k": 5}
)

print(response.answer)
```

---

## Complete Implementation

See `neo4j_graphrag_official.py` for the complete implementation.

### Features:
- ✅ Vector index creation
- ✅ Vector index population
- ✅ VectorCypherRetriever (vector + graph)
- ✅ OLLAMA LLM integration
- ✅ Complete GraphRAG pipeline

---

## Usage

### Step 1: Generate Embeddings (if not done)
```bash
python advanced_paper_features.py
```

### Step 2: Setup GraphRAG
```bash
python neo4j_graphrag_official.py
```

This will:
1. Create vector index
2. Populate index with embeddings
3. Initialize GraphRAG pipeline

### Step 3: Query
```python
from neo4j_graphrag_official import OfficialNeo4jGraphRAG

graphrag = OfficialNeo4jGraphRAG()
graphrag.setup_complete_pipeline()

response = graphrag.search("What papers use Resource-Based View?")
print(response.answer)
```

---

## Advantages of Official Package

✅ **Production-Grade**: Official Neo4j package, well-tested
✅ **Optimized**: Built for Neo4j vector indexes
✅ **Flexible**: Multiple retriever types (Vector, VectorCypher, Hybrid, Text2Cypher)
✅ **LLM Support**: Works with OpenAI, OLLAMA, Anthropic, Azure, VertexAI, etc.
✅ **Maintained**: Actively developed by Neo4j team

---

## Retriever Types Available

1. **VectorRetriever**: Simple vector similarity search
2. **VectorCypherRetriever**: Vector search + graph traversal
3. **HybridRetriever**: Vector + full-text search
4. **HybridCypherRetriever**: Vector + full-text + graph traversal
5. **Text2CypherRetriever**: LLM generates Cypher query

---

## Next Steps

1. ✅ Install `neo4j-graphrag`
2. ✅ Run `neo4j_graphrag_official.py` to setup
3. ⏳ Test queries
4. ⏳ Integrate into your application

---

## References

- **Official Docs**: https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_rag.html
- **Quickstart**: https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_rag.html#quickstart
- **Configuration**: https://neo4j.com/docs/neo4j-graphrag-python/current/user_guide_rag.html#graphrag-configuration

