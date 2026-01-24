#!/usr/bin/env python3
"""
Simple research gap analysis
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI
from collections import defaultdict, Counter

class SimpleGapAnalyzer:
    def __init__(self):
        load_dotenv()
        
        # Initialize Neo4j connection
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_user = os.getenv("NEO4J_USER")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
        
        # Initialize OpenAI
        self.llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def get_research_data(self):
        """Get all research data for analysis"""
        with self.driver.session() as session:
            # Get all research questions by year
            result = session.run("""
                MATCH (p:Paper)-[:HAS_RESEARCH_QUESTION]->(rq:ResearchQuestion)
                RETURN p.year as year, rq.question as question, rq.question_type as question_type
                ORDER BY p.year
            """)
            
            questions_by_year = defaultdict(list)
            question_types_by_year = defaultdict(Counter)
            
            for record in result:
                year = record['year']
                question = record['question']
                question_type = record['question_type']
                
                questions_by_year[year].append(question)
                question_types_by_year[year][question_type] += 1
            
            # Get methodologies by year
            result = session.run("""
                MATCH (p:Paper)-[:USES_METHODOLOGY]->(m:Methodology)
                RETURN p.year as year, m.method_type as method_type
                ORDER BY p.year
            """)
            
            methods_by_year = defaultdict(Counter)
            
            for record in result:
                year = record['year']
                method_type = record['method_type']
                methods_by_year[year][method_type] += 1
            
            return {
                'questions_by_year': dict(questions_by_year),
                'question_types_by_year': dict(question_types_by_year),
                'methods_by_year': dict(methods_by_year)
            }
    
    def create_paper_connections(self):
        """Create connections between papers based on similar content"""
        with self.driver.session() as session:
            # Get all papers
            papers = session.run("MATCH (p:Paper) RETURN p.paper_id as paper_id, p.year as year")
            paper_list = [(record['paper_id'], record['year']) for record in papers]
            
            connections_created = 0
            
            # Create connections based on similar research questions
            for paper1_id, year1 in paper_list:
                for paper2_id, year2 in paper_list:
                    if paper1_id != paper2_id:
                        # Check if they have similar research questions
                        result = session.run("""
                            MATCH (p1:Paper {paper_id: $paper1})-[:HAS_RESEARCH_QUESTION]->(rq1:ResearchQuestion)
                            MATCH (p2:Paper {paper_id: $paper2})-[:HAS_RESEARCH_QUESTION]->(rq2:ResearchQuestion)
                            WHERE toLower(rq1.question) CONTAINS toLower(rq2.question)
                               OR toLower(rq2.question) CONTAINS toLower(rq1.question)
                            RETURN count(*) as similarity
                        """, paper1=paper1_id, paper2=paper2_id)
                        
                        similarity = result.single()['similarity']
                        
                        if similarity > 0:
                            # Create connection
                            session.run("""
                                MATCH (p1:Paper {paper_id: $paper1})
                                MATCH (p2:Paper {paper_id: $paper2})
                                MERGE (p1)-[r:RELATED_TO {
                                    connection_type: 'similar_questions',
                                    similarity_score: $similarity,
                                    year_diff: abs($year1 - $year2)
                                }]->(p2)
                            """, paper1=paper1_id, paper2=paper2_id, 
                                 similarity=similarity, year1=year1, year2=year2)
                            
                            connections_created += 1
            
            return connections_created
    
    def analyze_gaps(self, research_data):
        """Analyze research gaps using LLM"""
        
        # Prepare context
        context = "RESEARCH PATTERNS BY YEAR:\n\n"
        
        for year in sorted(research_data['questions_by_year'].keys()):
            context += f"YEAR {year}:\n"
            context += f"  Research Questions ({len(research_data['questions_by_year'][year])}):\n"
            for q in research_data['questions_by_year'][year][:3]:  # Show first 3
                context += f"    - {q}\n"
            
            if year in research_data['methods_by_year']:
                context += f"  Methodologies: {dict(research_data['methods_by_year'][year])}\n"
            
            context += "\n"
        
        prompt = f"""
        As a strategic management research expert, analyze the following research patterns and identify potential research gaps.
        
        {context}
        
        Please identify:
        1. **Temporal Gaps**: What research questions or methodologies are missing in certain time periods?
        2. **Methodological Gaps**: What research methods are underutilized?
        3. **Conceptual Gaps**: What theoretical frameworks need more research?
        4. **Cross-temporal Gaps**: What questions were asked in earlier periods but not recently?
        5. **Emerging Areas**: What new research directions are emerging?
        
        For each gap, provide:
        - Specific description
        - Why it's important
        - Suggested research questions
        - Recommended methodologies
        
        Be specific and actionable.
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
    
    def get_network_stats(self):
        """Get network statistics"""
        with self.driver.session() as session:
            # Count connections
            result = session.run("MATCH ()-[r:RELATED_TO]->() RETURN count(r) as total_connections")
            total_connections = result.single()['total_connections']
            
            # Count papers
            result = session.run("MATCH (p:Paper) RETURN count(p) as total_papers")
            total_papers = result.single()['total_papers']
            
            return {
                'total_papers': total_papers,
                'total_connections': total_connections,
                'avg_connections_per_paper': total_connections / total_papers if total_papers > 0 else 0
            }
    
    def close(self):
        """Close database connection"""
        self.driver.close()

def main():
    analyzer = SimpleGapAnalyzer()
    
    try:
        # Test connection
        with analyzer.driver.session() as session:
            result = session.run("RETURN 'Connected to Neo4j Aura!' as message")
            print(f"✓ {result.single()['message']}")
        
        print("\n🔍 Analyzing research patterns...")
        research_data = analyzer.get_research_data()
        
        print("🔗 Creating paper connections...")
        connections_created = analyzer.create_paper_connections()
        print(f"Created {connections_created} paper connections")
        
        print("📊 Getting network statistics...")
        network_stats = analyzer.get_network_stats()
        
        print("\n" + "="*80)
        print("📋 RESEARCH GAP ANALYSIS REPORT")
        print("="*80)
        
        print(f"\n📊 Network Statistics:")
        print(f"  - Total papers: {network_stats['total_papers']}")
        print(f"  - Total connections: {network_stats['total_connections']}")
        print(f"  - Average connections per paper: {network_stats['avg_connections_per_paper']:.2f}")
        
        print(f"\n🔍 Research Gap Analysis:")
        gap_analysis = analyzer.analyze_gaps(research_data)
        print(gap_analysis)
        
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()
