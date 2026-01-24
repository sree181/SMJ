#!/usr/bin/env python3
"""
Advanced Connection Explorer
Query and visualize the multi-dimensional paper connections
"""

import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI
import json
from typing import List, Dict, Any

class ConnectionExplorer:
    """Advanced system for exploring paper connections"""
    
    def __init__(self):
        load_dotenv()
        
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_user = os.getenv("NEO4J_USER")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
        self.llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def close(self):
        self.driver.close()
    
    def find_connected_papers(self, paper_id: str, connection_types: List[str] = None) -> Dict[str, Any]:
        """Find all papers connected to a specific paper"""
        if connection_types is None:
            connection_types = ['conceptual', 'methodological', 'temporal', 'semantic']
        
        with self.driver.session() as session:
            # Get the paper info
            paper_info = session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                RETURN p.paper_id as paper_id, p.year as year, 
                       p.degree_centrality as centrality, p.community_id as community
            """, paper_id=paper_id).single()
            
            if not paper_info:
                return {"error": f"Paper {paper_id} not found"}
            
            # Get connected papers
            connections = []
            for conn_type in connection_types:
                result = session.run(f"""
                    MATCH (p1:Paper {{paper_id: $paper_id}})-[r:{conn_type.upper()}_RELATED]->(p2:Paper)
                    RETURN p2.paper_id as connected_paper, p2.year as year,
                           r.strength as strength, r.similarity as similarity,
                           r.connection_type as connection_type
                    ORDER BY r.strength DESC
                """, paper_id=paper_id)
                
                for record in result:
                    connections.append({
                        'paper_id': record['connected_paper'],
                        'year': record['year'],
                        'strength': record['strength'],
                        'similarity': record.get('similarity', 0),
                        'connection_type': record['connection_type']
                    })
            
            return {
                'source_paper': dict(paper_info),
                'connections': connections,
                'total_connections': len(connections)
            }
    
    def find_research_paths(self, paper1_id: str, paper2_id: str, max_hops: int = 3) -> List[List[str]]:
        """Find research paths between two papers"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH path = shortestPath((p1:Paper {paper_id: $paper1})-[*1..$max_hops]-(p2:Paper {paper_id: $paper2}))
                RETURN [node in nodes(path) | node.paper_id] as path
            """, paper1=paper1_id, paper2=paper2_id, max_hops=max_hops)
            
            paths = []
            for record in result:
                paths.append(record['path'])
            
            return paths
    
    def find_research_clusters(self) -> Dict[str, Any]:
        """Find research clusters and communities"""
        with self.driver.session() as session:
            # Get community information
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.community_id IS NOT NULL
                RETURN p.community_id as community_id, 
                       collect(p.paper_id) as papers,
                       collect(p.year) as years,
                       avg(p.degree_centrality) as avg_centrality
                ORDER BY size(papers) DESC
            """)
            
            communities = []
            for record in result:
                communities.append({
                    'community_id': record['community_id'],
                    'paper_count': len(record['papers']),
                    'papers': record['papers'],
                    'year_range': f"{min(record['years'])}-{max(record['years'])}",
                    'avg_centrality': record['avg_centrality']
                })
            
            return {'communities': communities}
    
    def find_influential_papers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Find most influential papers based on centrality measures"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.degree_centrality IS NOT NULL
                RETURN p.paper_id as paper_id, p.year as year,
                       p.degree_centrality as degree_centrality,
                       p.betweenness_centrality as betweenness_centrality,
                       p.closeness_centrality as closeness_centrality
                ORDER BY p.degree_centrality DESC
                LIMIT $limit
            """, limit=limit)
            
            influential_papers = []
            for record in result:
                influential_papers.append({
                    'paper_id': record['paper_id'],
                    'year': record['year'],
                    'degree_centrality': record['degree_centrality'],
                    'betweenness_centrality': record['betweenness_centrality'],
                    'closeness_centrality': record['closeness_centrality']
                })
            
            return influential_papers
    
    def find_research_gaps(self) -> Dict[str, Any]:
        """Find research gaps using connection analysis"""
        with self.driver.session() as session:
            # Find isolated papers (low connectivity)
            isolated = session.run("""
                MATCH (p:Paper)
                WHERE p.degree_centrality < 0.1 OR p.degree_centrality IS NULL
                RETURN p.paper_id as paper_id, p.year as year,
                       p.degree_centrality as centrality
                ORDER BY p.year
            """)
            
            isolated_papers = []
            for record in isolated:
                isolated_papers.append({
                    'paper_id': record['paper_id'],
                    'year': record['year'],
                    'centrality': record['centrality']
                })
            
            # Find temporal gaps
            temporal_gaps = session.run("""
                MATCH (p1:Paper)-[r:TEMPORALLY_RELATED]->(p2:Paper)
                WHERE r.year_gap > 2
                RETURN p1.paper_id as paper1, p2.paper_id as paper2,
                       p1.year as year1, p2.year as year2, r.year_gap as gap
                ORDER BY r.year_gap DESC
                LIMIT 10
            """)
            
            gaps = []
            for record in temporal_gaps:
                gaps.append({
                    'paper1': record['paper1'],
                    'paper2': record['paper2'],
                    'year1': record['year1'],
                    'year2': record['year2'],
                    'gap_years': record['gap']
                })
            
            return {
                'isolated_papers': isolated_papers,
                'temporal_gaps': gaps
            }
    
    def analyze_entity_evolution(self, entity_name: str) -> Dict[str, Any]:
        """Analyze how an entity evolves across papers"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)-[:CONTAINS_ENTITY]->(e:Entity)
                WHERE toLower(e.normalized_name) CONTAINS toLower($entity_name)
                RETURN p.paper_id as paper_id, p.year as year,
                       e.normalized_name as entity_name, e.entity_type as entity_type,
                       e.frequency as frequency
                ORDER BY p.year
            """, entity_name=entity_name)
            
            evolution = []
            for record in result:
                evolution.append({
                    'paper_id': record['paper_id'],
                    'year': record['year'],
                    'entity_name': record['entity_name'],
                    'entity_type': record['entity_type'],
                    'frequency': record['frequency']
                })
            
            return {
                'entity_name': entity_name,
                'evolution': evolution,
                'first_appearance': evolution[0]['year'] if evolution else None,
                'latest_appearance': evolution[-1]['year'] if evolution else None
            }
    
    def generate_research_insights(self, query: str) -> str:
        """Generate research insights using LLM and connection data"""
        with self.driver.session() as session:
            # Get connection statistics
            stats = session.run("""
                MATCH ()-[r]->()
                WHERE r.connection_type IN ['conceptual', 'methodological', 'temporal', 'semantic']
                RETURN r.connection_type as type, count(r) as count, avg(r.strength) as avg_strength
            """)
            
            connection_stats = {}
            for record in stats:
                connection_stats[record['type']] = {
                    'count': record['count'],
                    'avg_strength': record['avg_strength']
                }
            
            # Get influential papers
            influential = self.find_influential_papers(5)
            
            # Get research clusters
            clusters = self.find_research_clusters()
            
            # Prepare context for LLM
            context = f"""
            RESEARCH CONNECTION ANALYSIS DATA:
            
            Connection Statistics:
            {json.dumps(connection_stats, indent=2)}
            
            Most Influential Papers:
            {json.dumps(influential, indent=2)}
            
            Research Communities:
            {json.dumps(clusters, indent=2)}
            
            User Query: {query}
            """
            
            prompt = f"""
            As a research analyst, analyze the following connection data and provide insights about the research landscape.
            
            {context}
            
            Please provide:
            1. Key insights about the research network structure
            2. Patterns in research connections
            3. Influential papers and their impact
            4. Research communities and their characteristics
            5. Potential research opportunities based on connection gaps
            6. Recommendations for future research directions
            
            Be specific and data-driven in your analysis.
            """
            
            try:
                response = self.llm_client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                    temperature=0.3
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                return f"Error generating insights: {e}"
    
    def interactive_explorer(self):
        """Interactive connection explorer"""
        print("🔍 Advanced Connection Explorer")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("1. Find connected papers")
            print("2. Find research paths between papers")
            print("3. Find research clusters")
            print("4. Find influential papers")
            print("5. Find research gaps")
            print("6. Analyze entity evolution")
            print("7. Generate research insights")
            print("8. Exit")
            
            try:
                choice = input("\nEnter your choice (1-8): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nExiting gracefully...")
                break
            
            try:
                if choice == '1':
                    try:
                        paper_id = input("Enter paper ID: ").strip()
                    except (EOFError, KeyboardInterrupt):
                        print("Operation cancelled.")
                        continue
                    result = self.find_connected_papers(paper_id)
                    print(f"\n📊 Connected Papers for {paper_id}:")
                    print(json.dumps(result, indent=2))
                
                elif choice == '2':
                    try:
                        paper1 = input("Enter first paper ID: ").strip()
                        paper2 = input("Enter second paper ID: ").strip()
                    except (EOFError, KeyboardInterrupt):
                        print("Operation cancelled.")
                        continue
                    paths = self.find_research_paths(paper1, paper2)
                    print(f"\n🛤️ Research Paths between {paper1} and {paper2}:")
                    for i, path in enumerate(paths, 1):
                        print(f"  Path {i}: {' → '.join(path)}")
                
                elif choice == '3':
                    clusters = self.find_research_clusters()
                    print(f"\n🏘️ Research Clusters:")
                    print(json.dumps(clusters, indent=2))
                
                elif choice == '4':
                    try:
                        limit_input = input("Number of papers to show (default 10): ").strip()
                        limit = int(limit_input) if limit_input else 10
                    except (EOFError, KeyboardInterrupt):
                        print("Operation cancelled.")
                        continue
                    except ValueError:
                        limit = 10
                        print("Invalid input, using default value of 10.")
                    influential = self.find_influential_papers(limit)
                    print(f"\n⭐ Most Influential Papers:")
                    print(json.dumps(influential, indent=2))
                
                elif choice == '5':
                    gaps = self.find_research_gaps()
                    print(f"\n🕳️ Research Gaps:")
                    print(json.dumps(gaps, indent=2))
                
                elif choice == '6':
                    try:
                        entity = input("Enter entity name: ").strip()
                    except (EOFError, KeyboardInterrupt):
                        print("Operation cancelled.")
                        continue
                    evolution = self.analyze_entity_evolution(entity)
                    print(f"\n📈 Entity Evolution for '{entity}':")
                    print(json.dumps(evolution, indent=2))
                
                elif choice == '7':
                    try:
                        query = input("Enter your research question: ").strip()
                    except (EOFError, KeyboardInterrupt):
                        print("Operation cancelled.")
                        continue
                    insights = self.generate_research_insights(query)
                    print(f"\n💡 Research Insights:")
                    print(insights)
                
                elif choice == '8':
                    print("Goodbye!")
                    break
                
                else:
                    print("Invalid choice. Please try again.")
            
            except Exception as e:
                print(f"Error: {e}")
                logger.error(f"Error in interactive explorer: {e}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        explorer = ConnectionExplorer()
        try:
            with explorer.driver.session() as session:
                result = session.run("RETURN 'Connected to Neo4j Aura!' as message")
                print(f"✓ {result.single()['message']}")
            
            explorer.interactive_explorer()
        finally:
            explorer.close()
    elif len(sys.argv) > 1 and sys.argv[1] == "demo":
        # Demo mode
        explorer = ConnectionExplorer()
        try:
            with explorer.driver.session() as session:
                result = session.run("RETURN 'Connected to Neo4j Aura!' as message")
                print(f"✓ {result.single()['message']}")
            
            # Test finding connected papers
            print('\n🔍 Testing connection exploration...')
            result = explorer.find_connected_papers('1988_305')
            print(f'Connected papers for 1988_305: {result["total_connections"]} connections')
            
            # Test finding influential papers
            influential = explorer.find_influential_papers(3)
            print(f'\n⭐ Most influential papers:')
            for paper in influential:
                print(f'  - {paper["paper_id"]} ({paper["year"]}): centrality={paper["degree_centrality"]:.3f}')
            
            # Test research clusters
            clusters = explorer.find_research_clusters()
            print(f'\n🏘️ Research clusters: {len(clusters["communities"])} communities found')
            
        finally:
            explorer.close()
    else:
        # Command-line interface
        if len(sys.argv) < 2:
            print("Usage:")
            print("  python explore_connections.py interactive")
            print("  python explore_connections.py demo")
            print("  python explore_connections.py connected <paper_id>")
            print("  python explore_connections.py influential [limit]")
            print("  python explore_connections.py clusters")
            print("  python explore_connections.py gaps")
            print("  python explore_connections.py insights <query>")
            return
        
        explorer = ConnectionExplorer()
        try:
            with explorer.driver.session() as session:
                result = session.run("RETURN 'Connected to Neo4j Aura!' as message")
                print(f"✓ {result.single()['message']}")
            
            command = sys.argv[1]
            
            if command == "connected":
                if len(sys.argv) < 3:
                    print("Error: Please provide a paper ID")
                    return
                paper_id = sys.argv[2]
                result = explorer.find_connected_papers(paper_id)
                print(f'\n📊 Connected Papers for {paper_id}:')
                print(json.dumps(result, indent=2))
            
            elif command == "influential":
                limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
                influential = explorer.find_influential_papers(limit)
                print(f'\n⭐ Most Influential Papers:')
                print(json.dumps(influential, indent=2))
            
            elif command == "clusters":
                clusters = explorer.find_research_clusters()
                print(f'\n🏘️ Research Clusters:')
                print(json.dumps(clusters, indent=2))
            
            elif command == "gaps":
                gaps = explorer.find_research_gaps()
                print(f'\n🕳️ Research Gaps:')
                print(json.dumps(gaps, indent=2))
            
            elif command == "insights":
                if len(sys.argv) < 3:
                    print("Error: Please provide a research question")
                    return
                query = " ".join(sys.argv[2:])
                insights = explorer.generate_research_insights(query)
                print(f'\n💡 Research Insights for: "{query}"')
                print(insights)
            
            else:
                print(f"Unknown command: {command}")
                print("Available commands: connected, influential, clusters, gaps, insights")
        
        finally:
            explorer.close()

if __name__ == "__main__":
    main()
