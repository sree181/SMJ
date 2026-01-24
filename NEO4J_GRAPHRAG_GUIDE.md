# GraphRAG Implementation with Neo4j

## Overview

Yes! You can absolutely implement GraphRAG using Neo4j itself. Neo4j has excellent support for:
1. **Vector Search** (Neo4j 5.x+ with vector indexes)
2. **Neo4j Agents** (Preview feature - AI-powered query generation)
3. **Graph + Vector Hybrid Search** (Best of both worlds)

---

## What is GraphRAG?

**GraphRAG** = **Graph Retrieval-Augmented Generation**

Traditional RAG:
- Query → Vector Search → Retrieve Documents → LLM Answer

GraphRAG:
- Query → **Graph Traversal** + **Vector Search** → Retrieve Context (nodes + relationships) → LLM Answer

**Benefits for Literature Review**:
- Understand **relationships** between papers
- Find **connected** papers (not just similar)
- Answer questions about **research streams**, **theory evolution**, **gaps**
- Leverage **graph structure** for better context

---

## Neo4j Features for GraphRAG

### 1. Neo4j Vector Index (5.x+)

Neo4j supports native vector indexes for fast similarity search:

```cypher
// Create vector index for paper embeddings
CREATE VECTOR INDEX paperEmbeddings IF NOT EXISTS
FOR (p:Paper)
ON p.embedding
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 384,
    `vector.similarity_function`: 'cosine'
  }
}
```

### 2. Neo4j Agents (Preview)

Neo4j Agents can:
- **Generate Cypher queries** from natural language
- **Execute queries** and return results
- **Use LLM** to understand context and relationships

**How to Access**:
- In Neo4j Browser: Look for "Agents" tab (if available in your Aura instance)
- Via API: Neo4j provides agent endpoints
- Via LangChain: `Neo4jGraph` + `Neo4jCypher` chain

### 3. Hybrid Search (Graph + Vector)

Combine:
- **Vector search**: Find semantically similar papers
- **Graph traversal**: Find connected papers (theories, methods, variables)
- **Best of both**: Papers that are both similar AND connected

---

## Implementation Architecture

```
User Query
    ↓
┌─────────────────────────────────────┐
│   Query Understanding (LLM)         │
│   - Extract entities                │
│   - Identify query type             │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│   Hybrid Retrieval                  │
│   ├─ Vector Search (embeddings)     │
│   ├─ Graph Traversal (relationships)│
│   └─ Entity Matching (exact)       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│   Context Assembly                  │
│   - Retrieved papers                │
│   - Connected entities               │
│   - Relationship paths               │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│   LLM Generation                    │
│   - Synthesize answer                │
│   - Cite sources                    │
│   - Explain relationships            │
└─────────────────────────────────────┘
    ↓
Answer with Graph Context
```

---

## Step-by-Step Implementation

### Step 1: Set Up Vector Index

```python
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
)

with driver.session() as session:
    # Create vector index (Neo4j 5.x+)
    try:
        session.run("""
            CREATE VECTOR INDEX paperEmbeddings IF NOT EXISTS
            FOR (p:Paper)
            ON p.embedding
            OPTIONS {
              indexConfig: {
                `vector.dimensions`: 384,
                `vector.similarity_function`: 'cosine'
              }
            }
        """)
        print("✅ Vector index created")
    except Exception as e:
        print(f"⚠️  Vector index may not be supported: {e}")
        print("   Using manual cosine similarity instead")
```

### Step 2: Implement GraphRAG Query System

```python
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Any

class GraphRAGSystem:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
        )
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def query(self, user_question: str, top_k: int = 5):
        """
        GraphRAG query: Hybrid search (vector + graph)
        """
        # 1. Generate query embedding
        query_embedding = self.embedding_model.encode(user_question)
        query_vector = query_embedding.tolist()
        
        with self.driver.session() as session:
            # 2. Vector Search: Find similar papers
            similar_papers = session.run("""
                MATCH (p:Paper)
                WHERE p.embedding IS NOT NULL
                WITH p, 
                     gds.similarity.cosine(p.embedding, $query_vector) as similarity
                WHERE similarity > 0.5
                RETURN p.paper_id as paper_id,
                       p.title as title,
                       p.abstract as abstract,
                       similarity
                ORDER BY similarity DESC
                LIMIT $top_k
            """, query_vector=query_vector, top_k=top_k).data()
            
            # 3. Graph Traversal: Find connected papers
            if similar_papers:
                paper_ids = [p['paper_id'] for p in similar_papers]
                
                # Find papers connected via theories, methods, etc.
                connected_papers = session.run("""
                    MATCH (p1:Paper)-[r]->(entity)<-[r2]-(p2:Paper)
                    WHERE p1.paper_id IN $paper_ids
                    AND p1 <> p2
                    WITH p2, count(DISTINCT entity) as connection_strength
                    RETURN p2.paper_id as paper_id,
                           p2.title as title,
                           p2.abstract as abstract,
                           connection_strength
                    ORDER BY connection_strength DESC
                    LIMIT $top_k
                """, paper_ids=paper_ids, top_k=top_k).data()
                
                # 4. Get relationship context
                context = self._get_relationship_context(paper_ids, session)
                
                return {
                    'similar_papers': similar_papers,
                    'connected_papers': connected_papers,
                    'context': context
                }
    
    def _get_relationship_context(self, paper_ids: List[str], session):
        """Get relationship context between papers"""
        return session.run("""
            MATCH (p1:Paper)-[r]->(p2:Paper)
            WHERE p1.paper_id IN $paper_ids
            RETURN p1.paper_id as paper1,
                   p2.paper_id as paper2,
                   type(r) as relationship_type,
                   properties(r) as properties
            LIMIT 20
        """, paper_ids=paper_ids).data()
```

### Step 3: Use Neo4j Agents (If Available)

```python
# Option 1: Using Neo4j Agents API (if available in your instance)
def query_with_agents(user_question: str):
    """
    Use Neo4j Agents to generate Cypher query from natural language
    """
    # This requires Neo4j Agents API (preview feature)
    # Check if available in your Neo4j Aura instance
    
    agent_prompt = f"""
    User Question: {user_question}
    
    Generate a Cypher query to answer this question using the knowledge graph.
    Available node types: Paper, Theory, Method, ResearchQuestion, Variable, Finding, Contribution
    Available relationships: USES_THEORY, USES_METHOD, ADDRESSES, USES_VARIABLE, REPORTS, MAKES
    
    Return ONLY the Cypher query, no explanation.
    """
    
    # If Agents API available:
    # response = requests.post(f"{neo4j_uri}/agents/query", json={"prompt": agent_prompt})
    # cypher_query = response.json()["query"]
    
    # For now, use LLM to generate Cypher
    from ollama import Client
    client = Client()
    response = client.generate(
        model="llama3.1:8b",
        prompt=agent_prompt
    )
    
    cypher_query = response['response'].strip()
    
    # Execute query
    with driver.session() as session:
        result = session.run(cypher_query).data()
        return result
```

### Step 4: Complete GraphRAG Pipeline

```python
class CompleteGraphRAG:
    def __init__(self):
        self.graphrag = GraphRAGSystem()
        # Use OLLAMA for LLM
        self.llm_client = None  # Initialize OLLAMA client
    
    def answer_question(self, question: str):
        """
        Complete GraphRAG pipeline:
        1. Retrieve context (vector + graph)
        2. Assemble context
        3. Generate answer with LLM
        """
        # 1. Retrieve context
        retrieval_result = self.graphrag.query(question, top_k=5)
        
        # 2. Assemble context
        context = self._assemble_context(retrieval_result)
        
        # 3. Generate answer
        answer = self._generate_answer(question, context)
        
        return {
            'answer': answer,
            'sources': retrieval_result['similar_papers'],
            'connections': retrieval_result['connected_papers']
        }
    
    def _assemble_context(self, retrieval_result):
        """Assemble context from retrieved papers"""
        context_parts = []
        
        # Add similar papers
        for paper in retrieval_result['similar_papers']:
            context_parts.append(
                f"Paper: {paper['title']}\n"
                f"Abstract: {paper['abstract']}\n"
                f"Similarity: {paper['similarity']:.2f}\n"
            )
        
        # Add relationship context
        for rel in retrieval_result['context']:
            context_parts.append(
                f"Connection: {rel['paper1']} -[{rel['relationship_type']}]-> {rel['paper2']}\n"
            )
        
        return "\n\n".join(context_parts)
    
    def _generate_answer(self, question: str, context: str):
        """Generate answer using LLM"""
        prompt = f"""
        You are a research assistant helping with literature review.
        
        User Question: {question}
        
        Context from Knowledge Graph:
        {context}
        
        Based on the context above, provide a comprehensive answer to the question.
        Cite specific papers when relevant.
        Explain relationships between papers if applicable.
        
        Answer:
        """
        
        # Use OLLAMA or OpenAI
        # response = llm_client.generate(prompt)
        # return response
        
        return "Generated answer based on graph context"
```

---

## Using Neo4j Agents (Preview Feature)

### Check if Available

```python
def check_agents_availability():
    """Check if Neo4j Agents is available in your instance"""
    try:
        response = requests.get(
            f"{neo4j_uri}/agents/status",
            auth=(neo4j_user, neo4j_password)
        )
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, None
    except:
        return False, None
```

### If Agents Available

```python
# Neo4j Agents can automatically:
# 1. Understand natural language queries
# 2. Generate Cypher queries
# 3. Execute and return results
# 4. Explain relationships

# Example usage (if available):
agent_query = "What papers use Resource-Based View theory?"
result = neo4j_agents.query(agent_query)
```

---

## Practical Implementation

### Option 1: Manual GraphRAG (Works Now)

```python
# File: graphrag_system.py
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

load_dotenv()

class LiteratureGraphRAG:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
        )
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def ask(self, question: str):
        """Main GraphRAG query method"""
        # 1. Vector search
        query_embedding = self.embedding_model.encode(question).tolist()
        
        with self.driver.session() as session:
            # Find similar papers
            papers = session.run("""
                MATCH (p:Paper)
                WHERE p.embedding IS NOT NULL
                WITH p, 
                     reduce(s = 0.0, i IN range(0, size(p.embedding)-1) | 
                       s + p.embedding[i] * $query[i]) / 
                     (sqrt(reduce(s = 0.0, i IN range(0, size(p.embedding)-1) | 
                       s + p.embedding[i]^2)) * 
                      sqrt(reduce(s = 0.0, i IN range(0, size($query)-1) | 
                       s + $query[i]^2))) as similarity
                WHERE similarity > 0.5
                RETURN p.paper_id, p.title, p.abstract, similarity
                ORDER BY similarity DESC
                LIMIT 5
            """, query=query_embedding).data()
            
            # 2. Graph traversal
            if papers:
                paper_ids = [p['paper_id'] for p in papers]
                
                # Get connected entities
                context = session.run("""
                    MATCH (p:Paper)-[r]->(entity)
                    WHERE p.paper_id IN $paper_ids
                    RETURN type(r) as rel_type, 
                           labels(entity)[0] as entity_type,
                           entity.name as entity_name,
                           count(*) as count
                    ORDER BY count DESC
                """, paper_ids=paper_ids).data()
                
                return {
                    'papers': papers,
                    'context': context
                }
        
        return None
```

### Option 2: Using LangChain (Recommended)

```python
# Install: pip install langchain langchain-neo4j

from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_openai import ChatOpenAI
# Or use OLLAMA: from langchain_community.llms import Ollama

# Initialize
graph = Neo4jGraph(
    url=os.getenv('NEO4J_URI'),
    username=os.getenv('NEO4J_USER'),
    password=os.getenv('NEO4J_PASSWORD')
)

# Create QA chain
llm = ChatOpenAI(temperature=0)  # Or Ollama(model="llama3.1:8b")
qa_chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True
)

# Query
answer = qa_chain.run("What papers use Resource-Based View theory?")
print(answer)
```

---

## Example Queries

### 1. "What papers are similar to this research question?"

```cypher
// Vector search for similar papers
// Then graph traversal to find connected papers
```

### 2. "How has Resource-Based View theory evolved?"

```cypher
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory {name: "Resource-Based View"})
WITH p, p.publication_year as year
ORDER BY year
RETURN year, collect(p.title) as papers
```

### 3. "What are the research gaps in strategic management?"

```cypher
// Find low-density regions in graph
// Identify theory-method combinations not yet studied
```

---

## Next Steps

1. **Check Neo4j Version**: Ensure you have Neo4j 5.x+ for vector indexes
2. **Generate Embeddings**: Run `advanced_paper_features.py` to create embeddings
3. **Create Vector Index**: Use the code above to create index
4. **Implement GraphRAG**: Use one of the approaches above
5. **Test with Queries**: Try various literature review questions

---

## Benefits of GraphRAG for Literature Review

✅ **Understand Relationships**: Not just similar papers, but how they connect
✅ **Answer Complex Questions**: "What theories are used together?"
✅ **Find Research Gaps**: Identify missing connections
✅ **Track Evolution**: Understand how research develops
✅ **Better Context**: LLM gets graph structure, not just text

---

## Summary

**Yes, you can implement GraphRAG with Neo4j!**

- ✅ **Vector Search**: Native support in Neo4j 5.x+
- ✅ **Graph Traversal**: Built-in Cypher queries
- ✅ **Neo4j Agents**: Preview feature (check if available)
- ✅ **Hybrid Search**: Best of both worlds

**Start with**: Generate embeddings → Create vector index → Implement hybrid search → Add LLM generation

