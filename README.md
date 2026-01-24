# Literature Agent for Strategic Management Journal

A comprehensive literature analysis system that uses Large Language Models (LLMs) to process research papers section by section, extract key entities and relationships, and build a knowledge graph in Neo4j for intelligent querying.

## Features

- **LLM-Powered Extraction**: Uses OpenAI GPT models for accurate entity and relationship extraction
- **PDF Processing**: Extracts text from PDF files and identifies paper sections using LLM
- **Structured Data Extraction**: Identifies research questions, methodologies, findings, contributions, theories, and relationships
- **Knowledge Graph**: Builds rich relationships between papers and extracted entities
- **Neo4j Integration**: Stores and queries the knowledge graph
- **Batch Processing**: Processes papers organized in 5-year buckets
- **Natural Language Queries**: Ask questions about the literature

## Installation

### Prerequisites

1. **Python 3.8+**
2. **Neo4j Database** (Community or Enterprise edition)
3. **OpenAI API Key** (for LLM-based extraction)
4. **Git** (for cloning the repository)

### Setup

1. **Install dependencies**:
   ```bash
   python setup.py
   ```

2. **Install and start Neo4j**:
   - Download Neo4j from [neo4j.com](https://neo4j.com/download/)
   - Start the database (default: bolt://localhost:7687)
   - Set username: `neo4j` and password: `password` (or update `.env` file)

3. **Configure environment**:
   - Edit `.env` file to add your OpenAI API key
   - Update Neo4j credentials if different from defaults

## Usage

### Basic Usage

```python
from Kb import LiteratureAgent

# Initialize the agent with OpenAI API key
agent = LiteratureAgent(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j", 
    neo4j_password="password",
    openai_api_key="your_openai_api_key_here"
)

# Process all 5-year buckets
agent.process_all_buckets(Path("."))

# Query the knowledge graph
results = agent.query_knowledge_graph("What are the main research questions?")
```

### Command Line Usage

```bash
# Process all papers and build knowledge graph
python Kb.py

# The script will automatically:
# 1. Find all 5-year bucket folders (e.g., 1985-1989, 1990-1994, etc.)
# 2. Process each PDF in each bucket
# 3. Extract entities and relationships
# 4. Build the knowledge graph in Neo4j
```

### Example Queries

The system supports various types of queries:

```python
# Research questions
agent.query_knowledge_graph("What are the main research questions in recent papers?")

# Methodologies
agent.query_knowledge_graph("What methodologies are commonly used?")

# Findings
agent.query_knowledge_graph("What are the key findings?")

# Theories and concepts
agent.query_knowledge_graph("What theories are mentioned?")

# Contributions
agent.query_knowledge_graph("What are the main contributions?")
```

## Data Structure

### Paper Organization

Papers should be organized in 5-year buckets:
```
Strategic Management Journal/
├── 1985-1989/
│   ├── 1988_305.pdf
│   └── ...
├── 1990-1994/
│   ├── 1990_101.pdf
│   └── ...
└── ...
```

### Knowledge Graph Schema

The system creates the following node types and relationships:

**Nodes:**
- `Paper`: Research papers with metadata
- `ResearchQuestion`: Research questions extracted from papers
- `Methodology`: Research methodologies and techniques
- `Finding`: Research findings and results
- `Contribution`: Research contributions
- `Entity`: Theories, concepts, and other entities

**Relationships:**
- `HAS_RESEARCH_QUESTION`: Paper → ResearchQuestion
- `USES_METHODOLOGY`: Paper → Methodology
- `REPORTS_FINDING`: Paper → Finding
- `MAKES_CONTRIBUTION`: Paper → Contribution
- `MENTIONS_ENTITY`: Paper → Entity

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
OPENAI_API_KEY=your_openai_api_key_here  # Required
```

### Customization

You can customize the extraction by modifying the prompts in the `LLMExtractor` class:

```python
# Modify extraction prompts for better results
def extract_research_questions(self, text: str, section: str, paper_id: str):
    prompt = f"""
    Your custom prompt here...
    Text: {text}
    """
    # Custom extraction logic
```

## Troubleshooting

### Common Issues

1. **Neo4j Connection Error**:
   - Ensure Neo4j is running
   - Check connection credentials in `.env` file
   - Verify firewall settings

2. **OpenAI API Issues**:
   - Verify your API key is correct and has sufficient credits
   - Check rate limits and quotas
   - Ensure stable internet connection

3. **PDF Processing Errors**:
   - Ensure PDFs are not password-protected
   - Check file permissions
   - Verify PDF format compatibility

4. **Memory Issues**:
   - Process smaller batches of papers
   - Increase system memory
   - Use SSD storage for better performance

5. **LLM Response Parsing Errors**:
   - Check if LLM responses are valid JSON
   - Review extraction prompts for clarity
   - Monitor API response quality

### Performance Tips

1. **Batch Processing**: Process papers in smaller batches for better memory management
2. **Indexing**: Neo4j will automatically create indexes for better query performance
3. **Caching**: Consider implementing caching for frequently accessed data
4. **Parallel Processing**: Modify the code to process multiple papers simultaneously

## Advanced Usage

### Custom Entity Extraction

Extend the `LLMExtractor` class to add custom extraction logic:

```python
class CustomLLMExtractor(LLMExtractor):
    def extract_custom_entities(self, text: str, section: str, paper_id: str):
        # Your custom LLM-based extraction logic
        prompt = f"""
        Your custom extraction prompt here...
        Text: {text}
        """
        response = self.llm_client.extract_with_retry(prompt)
        # Process response
        pass
```

### Custom Queries

Write custom Cypher queries for specific research needs:

```python
def custom_query(self, query: str):
    cypher_query = """
    MATCH (p:Paper)-[:HAS_RESEARCH_QUESTION]->(rq:ResearchQuestion)
    WHERE p.year >= 2020
    RETURN p.title, rq.question
    ORDER BY p.year DESC
    """
    # Execute custom query
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error messages
3. Create an issue with detailed information about your problem
