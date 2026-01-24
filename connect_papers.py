#!/usr/bin/env python3
"""
Advanced paper connection system that creates rich relationships across papers
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI
from collections import defaultdict, Counter
import re

class PaperConnector:
    def __init__(self):
        load_dotenv()
        
        # Initialize Neo4j connection
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_user = os.getenv("NEO4J_USER")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
        
        # Initialize OpenAI
        self.llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def extract_concepts_and_theories(self, text: str, paper_id: str):
        """Extract concepts and theories using LLM"""
        if len(text) > 2000:
            text = text[:2000] + "..."
        
        prompt = f"""
        Analyze this research text and identify key concepts, theories, frameworks, and constructs mentioned.
        
        Text: {text}
        
        Extract in this JSON format:
        {{
            "concepts": [
                {{
                    "name": "concept name",
                    "type": "theory|framework|construct|variable|concept",
                    "description": "brief description",
                    "context": "where it appears"
                }}
            ],
            "relationships": [
                {{
                    "source": "concept1",
                    "target": "concept2", 
                    "relationship": "builds_on|extends|contradicts|supports|uses|relates_to",
                    "strength": "strong|moderate|weak"
                }}
            ]
        }}
        
        Focus on:
        - Theoretical frameworks (e.g., Resource-Based View, Agency Theory)
        - Key constructs (e.g., competitive advantage, performance)
        - Variables and concepts
        - Methodological approaches
        - Relationships between concepts
        
        Only return valid JSON, no additional text.
        """
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.1
            )
            
            import json
            data = json.loads(response.choices[0].message.content.strip())
            return data.get("concepts", []), data.get("relationships", [])
        except Exception as e:
            print(f"Error extracting concepts: {e}")
            return [], []
    
    def create_concept_network(self):
        """Create a network of concepts across all papers"""
        with self.driver.session() as session:
            # Get all papers with their research questions
            result = session.run("""
                MATCH (p:Paper)-[:HAS_RESEARCH_QUESTION]->(rq:ResearchQuestion)
                RETURN p.paper_id as paper_id, p.year as year, 
                       rq.question as question, rq.context as context
            """)
            
            all_concepts = {}
            concept_papers = defaultdict(list)
            
            for record in result:
                paper_id = record['paper_id']
                year = record['year']
                question = record['question']
                context = record.get('context', '')
                
                # Combine question and context for analysis
                text = f"{question} {context}"
                
                print(f"Extracting concepts from {paper_id}...")
                concepts, relationships = self.extract_concepts_and_theories(text, paper_id)
                
                # Store concepts
                for concept in concepts:
                    concept_name = concept['name']
                    if concept_name not in all_concepts:
                        all_concepts[concept_name] = {
                            'type': concept['type'],
                            'description': concept['description'],
                            'papers': []
                        }
                    
                    all_concepts[concept_name]['papers'].append({
                        'paper_id': paper_id,
                        'year': year,
                        'context': concept['context']
                    })
                    
                    concept_papers[concept_name].append(paper_id)
                
                # Store relationships
                for rel in relationships:
                    session.run("""
                        MERGE (c1:Concept {name: $source})
                        MERGE (c2:Concept {name: $target})
                        MERGE (c1)-[r:RELATES_TO {
                            relationship_type: $relationship,
                            strength: $strength,
                            paper_id: $paper_id,
                            year: $year
                        }]->(c2)
                    """, source=rel['source'], target=rel['target'],
                         relationship=rel['relationship'], strength=rel['strength'],
                         paper_id=paper_id, year=year)
            
            # Create concept nodes
            for concept_name, concept_data in all_concepts.items():
                session.run("""
                    MERGE (c:Concept {name: $name})
                    SET c.type = $type, c.description = $description,
                        c.paper_count = $paper_count
                """, name=concept_name, type=concept_data['type'],
                     description=concept_data['description'],
                     paper_count=len(concept_data['papers']))
            
            # Link concepts to papers
            for concept_name, papers in concept_papers.items():
                for paper_id in papers:
                    session.run("""
                        MATCH (p:Paper {paper_id: $paper_id})
                        MATCH (c:Concept {name: $concept_name})
                        MERGE (p)-[:USES_CONCEPT]->(c)
                    """, paper_id=paper_id, concept_name=concept_name)
            
            return len(all_concepts)
    
    def create_temporal_connections(self):
        """Create connections based on temporal evolution of concepts"""
        with self.driver.session() as session:
            # Find concepts that appear in multiple papers across time
            result = session.run("""
                MATCH (p:Paper)-[:USES_CONCEPT]->(c:Concept)
                WITH c, collect(DISTINCT p.year) as years, collect(p.paper_id) as papers
                WHERE size(years) > 1
                RETURN c.name as concept_name, years, papers
                ORDER BY size(years) DESC
            """)
            
            temporal_connections = 0
            
            for record in result:
                concept_name = record['concept_name']
                years = sorted(record['years'])
                papers = record['papers']
                
                # Create temporal evolution relationships
                for i in range(len(papers) - 1):
                    paper1 = papers[i]
                    paper2 = papers[i + 1]
                    year1 = years[i]
                    year2 = years[i + 1]
                    
                    session.run("""
                        MATCH (p1:Paper {paper_id: $paper1})
                        MATCH (p2:Paper {paper_id: $paper2})
                        MATCH (c:Concept {name: $concept_name})
                        MERGE (p1)-[r:EVOLVES_TO {
                            concept: $concept_name,
                            time_gap: $time_gap,
                            connection_type: 'temporal_evolution'
                        }]->(p2)
                    """, paper1=paper1, paper2=paper2, concept_name=concept_name,
                         time_gap=year2 - year1)
                    
                    temporal_connections += 1
            
            return temporal_connections
    
    def create_methodological_connections(self):
        """Create connections based on methodological similarities"""
        with self.driver.session() as session:
            # Find papers with similar methodologies
            result = session.run("""
                MATCH (p1:Paper)-[:USES_METHODOLOGY]->(m1:Methodology)
                MATCH (p2:Paper)-[:USES_METHODOLOGY]->(m2:Methodology)
                WHERE p1 <> p2 AND m1.method_type = m2.method_type
                RETURN DISTINCT p1.paper_id as paper1, p2.paper_id as paper2,
                       m1.method_type as method_type
            """)
            
            method_connections = 0
            
            for record in result:
                paper1 = record['paper1']
                paper2 = record['paper2']
                method_type = record['method_type']
                
                session.run("""
                    MATCH (p1:Paper {paper_id: $paper1})
                    MATCH (p2:Paper {paper_id: $paper2})
                    MERGE (p1)-[r:METHODOLOGICALLY_SIMILAR {
                        method_type: $method_type,
                        connection_type: 'methodological_similarity'
                    }]->(p2)
                """, paper1=paper1, paper2=paper2, method_type=method_type)
                
                method_connections += 1
            
            return method_connections
    
    def create_theoretical_connections(self):
        """Create connections based on theoretical frameworks"""
        with self.driver.session() as session:
            # Find papers that use the same theoretical concepts
            result = session.run("""
                MATCH (p1:Paper)-[:USES_CONCEPT]->(c:Concept)<-[:USES_CONCEPT]-(p2:Paper)
                WHERE p1 <> p2 AND c.type IN ['theory', 'framework']
                RETURN DISTINCT p1.paper_id as paper1, p2.paper_id as paper2,
                       c.name as concept_name, c.type as concept_type
            """)
            
            theoretical_connections = 0
            
            for record in result:
                paper1 = record['paper1']
                paper2 = record['paper2']
                concept_name = record['concept_name']
                concept_type = record['concept_type']
                
                session.run("""
                    MATCH (p1:Paper {paper_id: $paper1})
                    MATCH (p2:Paper {paper_id: $paper2})
                    MERGE (p1)-[r:THEORETICALLY_RELATED {
                        shared_concept: $concept_name,
                        concept_type: $concept_type,
                        connection_type: 'theoretical_similarity'
                    }]->(p2)
                """, paper1=paper1, paper2=paper2, concept_name=concept_name,
                     concept_type=concept_type)
                
                theoretical_connections += 1
            
            return theoretical_connections
    
    def create_citation_network(self):
        """Create connections based on potential citations and references"""
        with self.driver.session() as session:
            # Find papers that might cite each other based on similar research questions
            result = session.run("""
                MATCH (p1:Paper)-[:HAS_RESEARCH_QUESTION]->(rq1:ResearchQuestion)
                MATCH (p2:Paper)-[:HAS_RESEARCH_QUESTION]->(rq2:ResearchQuestion)
                WHERE p1 <> p2 AND p1.year < p2.year
                AND (toLower(rq1.question) CONTAINS toLower(rq2.question)
                     OR toLower(rq2.question) CONTAINS toLower(rq1.question))
                RETURN DISTINCT p1.paper_id as cited_paper, p2.paper_id as citing_paper,
                       p1.year as cited_year, p2.year as citing_year
            """)
            
            citation_connections = 0
            
            for record in result:
                cited_paper = record['cited_paper']
                citing_paper = record['citing_paper']
                cited_year = record['cited_year']
                citing_year = record['citing_year']
                
                session.run("""
                    MATCH (cited:Paper {paper_id: $cited_paper})
                    MATCH (citing:Paper {paper_id: $citing_paper})
                    MERGE (citing)-[r:CITES {
                        cited_year: $cited_year,
                        citing_year: $citing_year,
                        time_gap: $time_gap,
                        connection_type: 'potential_citation'
                    }]->(cited)
                """, cited_paper=cited_paper, citing_paper=citing_paper,
                     cited_year=cited_year, citing_year=citing_year,
                     time_gap=citing_year - cited_year)
                
                citation_connections += 1
            
            return citation_connections
    
    def analyze_network_structure(self):
        """Analyze the network structure of connected papers"""
        with self.driver.session() as session:
            # Get network statistics
            stats = {}
            
            # Count different types of connections
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as connection_type, count(r) as count
            """)
            
            for record in result:
                stats[record['connection_type']] = record['count']
            
            # Find most connected papers
            result = session.run("""
                MATCH (p:Paper)-[r]->(other:Paper)
                RETURN p.paper_id as paper_id, p.year as year, 
                       count(r) as connection_count
                ORDER BY connection_count DESC
                LIMIT 5
            """)
            
            most_connected = []
            for record in result:
                most_connected.append({
                    'paper_id': record['paper_id'],
                    'year': record['year'],
                    'connections': record['connection_count']
                })
            
            # Find bridge papers (connect different clusters)
            result = session.run("""
                MATCH (p:Paper)-[r1]->(other1:Paper)-[r2]->(other2:Paper)
                WHERE p <> other2 AND NOT (p)-[:RELATED_TO]->(other2)
                RETURN DISTINCT p.paper_id as bridge_paper, 
                       count(DISTINCT other2) as bridge_connections
                ORDER BY bridge_connections DESC
                LIMIT 5
            """)
            
            bridge_papers = []
            for record in result:
                bridge_papers.append({
                    'paper_id': record['bridge_paper'],
                    'bridge_connections': record['bridge_connections']
                })
            
            return {
                'connection_stats': stats,
                'most_connected': most_connected,
                'bridge_papers': bridge_papers
            }
    
    def create_all_connections(self):
        """Create all types of connections between papers"""
        print("🔗 Creating comprehensive paper connections...")
        
        # Create concept network
        print("1. Extracting concepts and creating concept network...")
        concept_count = self.create_concept_network()
        print(f"   ✓ Extracted {concept_count} concepts")
        
        # Create temporal connections
        print("2. Creating temporal evolution connections...")
        temporal_count = self.create_temporal_connections()
        print(f"   ✓ Created {temporal_count} temporal connections")
        
        # Create methodological connections
        print("3. Creating methodological similarity connections...")
        method_count = self.create_methodological_connections()
        print(f"   ✓ Created {method_count} methodological connections")
        
        # Create theoretical connections
        print("4. Creating theoretical framework connections...")
        theoretical_count = self.create_theoretical_connections()
        print(f"   ✓ Created {theoretical_count} theoretical connections")
        
        # Create citation network
        print("5. Creating potential citation connections...")
        citation_count = self.create_citation_network()
        print(f"   ✓ Created {citation_count} citation connections")
        
        # Analyze network structure
        print("6. Analyzing network structure...")
        network_analysis = self.analyze_network_structure()
        
        return {
            'concept_count': concept_count,
            'temporal_count': temporal_count,
            'method_count': method_count,
            'theoretical_count': theoretical_count,
            'citation_count': citation_count,
            'network_analysis': network_analysis
        }
    
    def close(self):
        """Close database connection"""
        self.driver.close()

def main():
    connector = PaperConnector()
    
    try:
        # Test connection
        with connector.driver.session() as session:
            result = session.run("RETURN 'Connected to Neo4j Aura!' as message")
            print(f"✓ {result.single()['message']}")
        
        # Create all connections
        results = connector.create_all_connections()
        
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE PAPER CONNECTION REPORT")
        print("="*80)
        
        print(f"\n🔗 Connection Summary:")
        print(f"  - Concepts extracted: {results['concept_count']}")
        print(f"  - Temporal connections: {results['temporal_count']}")
        print(f"  - Methodological connections: {results['method_count']}")
        print(f"  - Theoretical connections: {results['theoretical_count']}")
        print(f"  - Citation connections: {results['citation_count']}")
        
        print(f"\n📈 Network Statistics:")
        for conn_type, count in results['network_analysis']['connection_stats'].items():
            print(f"  - {conn_type}: {count}")
        
        print(f"\n🌟 Most Connected Papers:")
        for paper in results['network_analysis']['most_connected']:
            print(f"  - {paper['paper_id']} ({paper['year']}): {paper['connections']} connections")
        
        print(f"\n🌉 Bridge Papers (connect different clusters):")
        for paper in results['network_analysis']['bridge_papers']:
            print(f"  - {paper['paper_id']}: {paper['bridge_connections']} bridge connections")
        
    finally:
        connector.close()

if __name__ == "__main__":
    main()
