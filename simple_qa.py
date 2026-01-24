#!/usr/bin/env python3
"""
Simple question-answering system that can handle direct questions
"""

import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI

class SimpleQASystem:
    def __init__(self):
        load_dotenv()
        
        # Initialize Neo4j connection
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_user = os.getenv("NEO4J_USER")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
        
        # Initialize OpenAI
        self.llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def get_relevant_papers(self, search_query: str, limit: int = 5):
        """Get papers relevant to the query"""
        with self.driver.session() as session:
            # Search in research questions with more flexible matching
            result = session.run("""
                MATCH (p:Paper)-[:HAS_RESEARCH_QUESTION]->(rq:ResearchQuestion)
                WHERE toLower(rq.question) CONTAINS toLower($search_query)
                   OR toLower(rq.question) CONTAINS toLower($search_query1)
                   OR toLower(rq.question) CONTAINS toLower($search_query2)
                RETURN p.paper_id as paper_id, p.year as year, rq.question as question
                LIMIT $limit
            """, search_query=search_query, 
                 search_query1=search_query.replace(' and ', ' ').replace(' or ', ' '),
                 search_query2=search_query.split()[0] if search_query.split() else search_query,
                 limit=limit)
            
            papers = []
            for record in result:
                papers.append({
                    'paper_id': record['paper_id'],
                    'year': record['year'],
                    'question': record['question']
                })
            
            return papers
    
    def get_methodology_info(self, search_query: str, limit: int = 5):
        """Get methodology information relevant to the query"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)-[:USES_METHODOLOGY]->(m:Methodology)
                WHERE toLower(m.method_type) CONTAINS toLower($search_query) 
                   OR toLower(m.analysis_technique) CONTAINS toLower($search_query)
                RETURN p.paper_id as paper_id, p.year as year, 
                       m.method_type as method_type, m.analysis_technique as technique
                LIMIT $limit
            """, search_query=search_query, limit=limit)
            
            methods = []
            for record in result:
                methods.append({
                    'paper_id': record['paper_id'],
                    'year': record['year'],
                    'method_type': record['method_type'],
                    'technique': record['technique']
                })
            
            return methods
    
    def get_findings_info(self, search_query: str, limit: int = 5):
        """Get findings relevant to the query"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)-[:REPORTS_FINDING]->(f:Finding)
                WHERE toLower(f.finding) CONTAINS toLower($search_query)
                RETURN p.paper_id as paper_id, p.year as year, 
                       f.finding as finding, f.finding_type as finding_type
                LIMIT $limit
            """, search_query=search_query, limit=limit)
            
            findings = []
            for record in result:
                findings.append({
                    'paper_id': record['paper_id'],
                    'year': record['year'],
                    'finding': record['finding'],
                    'finding_type': record['finding_type']
                })
            
            return findings
    
    def generate_answer(self, query: str, context_data: dict):
        """Generate a comprehensive answer using LLM"""
        context_text = f"""
        Based on the following research data, answer the user's question: "{query}"
        
        RELEVANT RESEARCH QUESTIONS:
        """
        
        for paper in context_data.get('papers', []):
            context_text += f"- {paper['paper_id']} ({paper['year']}): {paper['question']}\n"
        
        context_text += "\nRELEVANT METHODOLOGIES:\n"
        for method in context_data.get('methods', []):
            context_text += f"- {method['paper_id']} ({method['year']}): {method['method_type']} - {method['technique']}\n"
        
        context_text += "\nRELEVANT FINDINGS:\n"
        for finding in context_data.get('findings', []):
            context_text += f"- {finding['paper_id']} ({finding['year']}): {finding['finding']}\n"
        
        prompt = f"""
        You are a research assistant analyzing strategic management literature. 
        Based on the following research data, provide a comprehensive answer to the user's question.
        
        Question: {query}
        
        Research Data:
        {context_text}
        
        Please provide:
        1. A direct answer to the question
        2. Key findings from the literature
        3. Methodologies used in relevant studies
        4. Any patterns or trends you notice
        5. Suggestions for further research if applicable
        
        Be specific and cite the paper IDs when referencing studies.
        """
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating answer: {e}"
    
    def ask_question(self, query: str):
        """Main method to ask a question and get an answer"""
        print(f"\n🔍 Searching for: '{query}'")
        
        # Get relevant data
        papers = self.get_relevant_papers(query, 5)
        methods = self.get_methodology_info(query, 5)
        findings = self.get_findings_info(query, 5)
        
        print(f"Found {len(papers)} relevant papers, {len(methods)} methodologies, {len(findings)} findings")
        
        if not papers and not methods and not findings:
            return "No relevant information found in the knowledge graph."
        
        # Generate comprehensive answer
        context_data = {
            'papers': papers,
            'methods': methods,
            'findings': findings
        }
        
        answer = self.generate_answer(query, context_data)
        return answer
    
    def close(self):
        """Close database connection"""
        self.driver.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_qa.py 'Your question here'")
        print("Example: python simple_qa.py 'What research questions are about mergers?'")
        return
    
    query = sys.argv[1]
    
    qa_system = SimpleQASystem()
    
    try:
        # Test connection
        with qa_system.driver.session() as session:
            result = session.run("RETURN 'Connected to Neo4j Aura!' as message")
            print(f"✓ {result.single()['message']}")
        
        # Ask the question
        answer = qa_system.ask_question(query)
        print(f"\n💡 Answer:\n{answer}")
        
    finally:
        qa_system.close()

if __name__ == "__main__":
    main()
