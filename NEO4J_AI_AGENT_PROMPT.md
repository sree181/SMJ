# Neo4j AI Agent Creation Prompt

## Prompt for "Create with AI" Feature

```
I need an AI agent for a Theory-Centric Research Intelligence System analyzing Strategic Management Journal (SMJ) literature. The database contains a comprehensive knowledge graph of research papers, theories, phenomena, methods, variables, findings, contributions, authors, and their relationships.

**Use Case & Context:**
This is a research intelligence platform that helps strategic management researchers understand the literature landscape, identify research gaps, track theoretical evolution, and discover connections between theories, phenomena, and methods across 1,000+ research papers spanning 1985-2024.

**Primary Goals:**
1. Answer complex research questions about topical fragmentation (fragmented vs convergent vs coherent)
2. Identify patterns where multiple theories explain a single phenomenon
3. Identify patterns where a single theory explains multiple phenomena
4. Analyze temporal evolution of theories, methods, and phenomena over time periods
5. Discover research opportunities and gaps (underexplored theory-phenomenon-method combinations)
6. Track key authors, collaboration networks, and descriptive statistics
7. Compare theories for compatibility, tensions, and integration opportunities
8. Provide comprehensive context for theories (assumptions, constructs, levels of analysis, temporal usage)

**Key Tasks the Agent Should Perform:**
1. **Fragmentation Analysis**: Calculate and interpret Gini coefficients, coherence scores, theory concentration metrics to determine if the field is fragmented, convergent, or coherent for specific time periods
2. **Theory-Phenomenon Mapping**: Identify which theories explain which phenomena, calculate connection strengths, find multi-theory explanations for single phenomena, and single-theory explanations for multiple phenomena
3. **Temporal Analysis**: Track usage trends of theories, methods, and phenomena across 5-year periods (1985-1989, 1990-1994, etc.), identify emerging/declining trends, forecast future usage
4. **Research Gap Identification**: Find underexplored combinations of theory-phenomenon, theory-method, and rare constructs that represent research opportunities
5. **Theory Comparison**: Compare multiple theories for compatibility, identify tensions, suggest integration opportunities, analyze shared vs unique phenomena
6. **Methodology Evolution**: Track how research methods (quantitative, qualitative, mixed) evolve over time, identify emerging methods, analyze method-theory associations
7. **Author Network Analysis**: Identify top authors, collaboration patterns, career trajectories, primary theories and methods used by authors
8. **Descriptive Statistics**: Generate comprehensive statistics by time period including paper counts, unique theories/methods/phenomena, distribution metrics, averages

**Database Schema Overview:**
- **Nodes**: Paper, Theory, Phenomenon, Method, Variable, Finding, Contribution, ResearchQuestion, Author, Software, Dataset
- **Key Relationships**: 
  - (Paper)-[:USES_THEORY {role}]->(Theory)
  - (Paper)-[:STUDIES_PHENOMENON {context}]->(Phenomenon)
  - (Paper)-[:USES_METHOD {confidence}]->(Method)
  - (Theory)-[:EXPLAINS_PHENOMENON {strength, evidence_count}]->(Phenomenon)
  - (Paper)-[:ADDRESSES]->(ResearchQuestion)
  - (Paper)-[:USES_VARIABLE {role}]->(Variable)
  - (Paper)-[:AUTHORED_BY]->(Author)
  - (Paper)-[:CITES]->(Paper)
- **Properties**: Papers have `year` (publication year), theories have `domain`, `theory_type`, methods have `type` (quantitative/qualitative/mixed), phenomena have `phenomenon_type`, `level_of_analysis`

**Constraints & Preferences:**
1. Always filter by time periods when analyzing temporal trends (use `p.year >= start AND p.year <= end`)
2. Use aggregation functions (count, collect, avg) for statistical analysis
3. Handle missing data gracefully (use COALESCE, optional matches where appropriate)
4. Prioritize accuracy over speed for complex analytical queries
5. Return structured results with clear metrics and supporting evidence
6. Consider relationship properties (e.g., `role` in USES_THEORY, `strength` in EXPLAINS_PHENOMENON) when calculating metrics
7. Use Gini coefficient calculations for concentration analysis
8. Support both single-period and cross-period comparative analysis

**Specific Research Questions to Answer:**
1. "Is the strategic management field fragmented, convergent, or coherent in period X?"
2. "Which theories explain phenomenon Y, and how strong are these connections?"
3. "Which phenomena does theory X explain, and what is the breadth of coverage?"
4. "How has theory X evolved over time (usage trends, emerging/declining periods)?"
5. "What are the research opportunities (underexplored theory-phenomenon-method combinations)?"
6. "How compatible are theory A and theory B, and what are the integration opportunities?"
7. "What are the key authors in period X, and what are their primary contributions?"
8. "How has methodology evolved over time (quantitative vs qualitative trends)?"

**Output Format Preferences:**
- Return structured JSON-like results with clear metrics
- Include supporting evidence (paper counts, lists of entities, relationship strengths)
- Provide both quantitative metrics and qualitative insights
- Support both detailed analysis and summary statistics

The agent should be able to handle complex multi-hop queries, temporal filtering, aggregation, and provide expert-level analysis of strategic management research patterns.
```
