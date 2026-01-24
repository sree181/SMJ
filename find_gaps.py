#!/usr/bin/env python3
"""
Research gap analysis by connecting articles and identifying patterns
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI
from collections import defaultdict, Counter
import json

class ResearchGapAnalyzer:
    def __init__(self):
        load_dotenv()
        
        # Initialize Neo4j connection
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_user = os.getenv("NEO4J_USER")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
        
        # Initialize OpenAI
        self.llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def analyze_question_patterns(self):
        """Analyze patterns in research questions across papers"""
        with self.driver.session() as session:
            # Get all research questions with their types and years
            result = session.run("""
                MATCH (p:Paper)-[:HAS_RESEARCH_QUESTION]->(rq:ResearchQuestion)
                RETURN p.paper_id as paper_id, p.year as year, 
                       rq.question as question, rq.question_type as question_type
                ORDER BY p.year
            """)
            
            questions_by_year = defaultdict(list)
            question_types_by_year = defaultdict(Counter)
            question_topics = []
            
            for record in result:
                year = record['year']
                question = record['question']
                question_type = record['question_type']
                
                questions_by_year[year].append(question)
                question_types_by_year[year][question_type] += 1
                question_topics.append(question)
            
            return {
                'questions_by_year': dict(questions_by_year),
                'question_types_by_year': dict(question_types_by_year),
                'all_questions': question_topics
            }
    
    def analyze_methodology_evolution(self):
        """Analyze how methodologies evolve over time"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)-[:USES_METHODOLOGY]->(m:Methodology)
                RETURN p.paper_id as paper_id, p.year as year,
                       m.method_type as method_type, m.analysis_technique as technique
                ORDER BY p.year
            """)
            
            methods_by_year = defaultdict(list)
            method_types_by_year = defaultdict(Counter)
            
            for record in result:
                year = record['year']
                method_type = record['method_type']
                technique = record['technique']
                
                methods_by_year[year].append({
                    'method_type': method_type,
                    'technique': technique
                })
                method_types_by_year[year][method_type] += 1
            
            return {
                'methods_by_year': dict(methods_by_year),
                'method_types_by_year': dict(method_types_by_year)
            }
    
    def identify_research_gaps(self, analysis_data):
        """Use LLM to identify research gaps based on patterns"""
        
        # Prepare context for LLM
        context = f"""
        RESEARCH QUESTION ANALYSIS:
        """
        
        for year, questions in analysis_data['questions_by_year'].items():
            context += f"\n{year}: {len(questions)} questions\n"
            for q in questions[:3]:  # Show first 3 questions per year
                context += f"  - {q}\n"
        
        context += f"\nMETHODOLOGY EVOLUTION:\n"
        for year, methods in analysis_data['methods_by_year'].items():
            context += f"\n{year}: {len(methods)} methodologies\n"
            method_types = Counter([m['method_type'] for m in methods])
            for method_type, count in method_types.items():
                context += f"  - {method_type}: {count}\n"
        
        prompt = f"""
        As a strategic management research expert, analyze the following research patterns and identify potential research gaps.
        
        {context}
        
        Please identify:
        1. **Temporal Gaps**: What research questions or methodologies are missing in certain time periods?
        2. **Methodological Gaps**: What research methods are underutilized or missing?
        3. **Conceptual Gaps**: What theoretical frameworks or concepts need more research?
        4. **Empirical Gaps**: What empirical evidence is lacking?
        5. **Cross-temporal Gaps**: What questions were asked in earlier periods but not in recent ones?
        6. **Emerging Areas**: What new research directions are emerging?
        
        For each gap, provide:
        - Specific description of the gap
        - Why it's important
        - Suggested research questions to address it
        - Recommended methodologies
        
        Be specific and actionable in your recommendations.
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
            return f"Error analyzing gaps: {e}"
    
    def find_connected_papers(self, paper_id: str):
        """Find papers that are connected through similar research questions or methodologies"""
        with self.driver.session() as session:
            # Find papers with similar research questions
            similar_questions = session.run("""
                MATCH (p1:Paper {paper_id: $paper_id})-[:HAS_RESEARCH_QUESTION]->(rq1:ResearchQuestion)
                MATCH (p2:Paper)-[:HAS_RESEARCH_QUESTION]->(rq2:ResearchQuestion)
                WHERE p1 <> p2 AND toLower(rq1.question) CONTAINS toLower(rq2.question)
                RETURN DISTINCT p2.paper_id as connected_paper, p2.year as year,
                       rq2.question as similar_question
                LIMIT 5
            """, paper_id=paper_id)
            
            connections = []
            for record in similar_questions:
                connections.append({
                    'type': 'similar_question',
                    'paper_id': record['connected_paper'],
                    'year': record['year'],
                    'connection': record['similar_question']
                })
            
            # Find papers with similar methodologies
            similar_methods = session.run("""
                MATCH (p1:Paper {paper_id: $paper_id})-[:USES_METHODOLOGY]->(m1:Methodology)
                MATCH (p2:Paper)-[:USES_METHODOLOGY]->(m2:Methodology)
                WHERE p1 <> p2 AND m1.method_type = m2.method_type
                RETURN DISTINCT p2.paper_id as connected_paper, p2.year as year,
                       m2.method_type as similar_method
                LIMIT 5
            """, paper_id=paper_id)
            
            for record in similar_methods:
                connections.append({
                    'type': 'similar_methodology',
                    'paper_id': record['connected_paper'],
                    'year': record['year'],
                    'connection': record['similar_method']
                })
            
            return connections
    
    def create_paper_connections(self):
        """Create explicit connections between papers based on similarity"""
        with self.driver.session() as session:
            # Get all papers
            papers = session.run("MATCH (p:Paper) RETURN p.paper_id as paper_id")
            paper_list = [record['paper_id'] for record in papers]
            
            connections_created = 0
            
            for paper_id in paper_list:
                connections = self.find_connected_papers(paper_id)
                
                for connection in connections:
                    # Create relationship between papers
                    session.run("""
                        MATCH (p1:Paper {paper_id: $paper1})
                        MATCH (p2:Paper {paper_id: $paper2})
                        MERGE (p1)-[r:RELATED_TO {
                            connection_type: $connection_type,
                            connection_detail: $connection_detail,
                            year_diff: abs(p1.year - p2.year)
                        }]->(p2)
                    """, paper1=paper_id, paper2=connection['paper_id'],
                         connection_type=connection['type'],
                         connection_detail=connection['connection'])
                    
                    connections_created += 1
            
            return connections_created
    
    def analyze_network_structure(self):
        """Analyze the network structure of connected papers"""
        with self.driver.session() as session:
            # Find highly connected papers
            result = session.run("""
                MATCH (p:Paper)-[r:RELATED_TO]->(other:Paper)
                RETURN p.paper_id as paper_id, p.year as year, 
                       count(r) as connection_count
                ORDER BY connection_count DESC
                LIMIT 10
            """)
            
            highly_connected = []
            for record in result:
                highly_connected.append({
                    'paper_id': record['paper_id'],
                    'year': record['year'],
                    'connections': record['connection_count']
                })
            
            # Find isolated papers (no connections)
            isolated = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)-[:RELATED_TO]->() AND NOT ()-[:RELATED_TO]->(p)
                RETURN p.paper_id as paper_id, p.year as year
                LIMIT 10
            """)
            
            isolated_papers = []
            for record in isolated:
                isolated_papers.append({
                    'paper_id': record['paper_id'],
                    'year': record['year']
                })
            
            return {
                'highly_connected': highly_connected,
                'isolated_papers': isolated_papers
            }
    
    def generate_gap_report(self):
        """Generate a comprehensive research gap analysis report"""
        print("🔍 Analyzing research patterns...")
        
        # Analyze patterns
        question_analysis = self.analyze_question_patterns()
        method_analysis = self.analyze_methodology_evolution()
        
        print("🔗 Creating paper connections...")
        connections_created = self.create_paper_connections()
        print(f"Created {connections_created} paper connections")
        
        print("📊 Analyzing network structure...")
        network_analysis = self.analyze_network_structure()
        
        # Combine all analysis
        full_analysis = {
            'questions': question_analysis,
            'methodologies': method_analysis,
            'network': network_analysis
        }
        
        print("🤖 Generating gap analysis...")
        gap_analysis = self.identify_research_gaps(full_analysis)
        
        return {
            'gap_analysis': gap_analysis,
            'network_stats': {
                'total_connections': connections_created,
                'highly_connected_papers': len(network_analysis['highly_connected']),
                'isolated_papers': len(network_analysis['isolated_papers'])
            },
            'patterns': full_analysis
        }
    
    def close(self):
        """Close database connection"""
        self.driver.close()

def main():
    analyzer = ResearchGapAnalyzer()
    
    try:
        # Test connection
        with analyzer.driver.session() as session:
            result = session.run("RETURN 'Connected to Neo4j Aura!' as message")
            print(f"✓ {result.single()['message']}")
        
        # Generate comprehensive gap analysis
        report = analyzer.generate_gap_report()
        
        print("\n" + "="*80)
        print("📋 RESEARCH GAP ANALYSIS REPORT")
        print("="*80)
        
        print(f"\n📊 Network Statistics:")
        print(f"  - Total paper connections: {report['network_stats']['total_connections']}")
        print(f"  - Highly connected papers: {report['network_stats']['highly_connected_papers']}")
        print(f"  - Isolated papers: {report['network_stats']['isolated_papers']}")
        
        print(f"\n🔍 Research Gap Analysis:")
        print(report['gap_analysis'])
        
        # Save report to file
        with open('research_gap_analysis.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n💾 Full report saved to: research_gap_analysis.json")
        
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()
