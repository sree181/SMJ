#!/usr/bin/env python3
"""
Demo question-answering system that shows all available data
"""

import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI

class DemoQASystem:
    def __init__(self):
        load_dotenv()
        
        # Initialize Neo4j connection
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_user = os.getenv("NEO4J_USER")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
        
        # Initialize OpenAI
        self.llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def get_all_data(self):
        """Get all available data from the knowledge graph"""
        with self.driver.session() as session:
            # Get all research questions
            result = session.run("""
                MATCH (p:Paper)-[:HAS_RESEARCH_QUESTION]->(rq:ResearchQuestion)
                RETURN p.paper_id as paper_id, p.year as year, 
                       rq.question as question, rq.question_type as question_type
                ORDER BY p.year
            """)
            
            questions = []
            for record in result:
                questions.append({
                    'paper_id': record['paper_id'],
                    'year': record['year'],
                    'question': record['question'],
                    'question_type': record['question_type']
                })
            
            # Get all methodologies
            result = session.run("""
                MATCH (p:Paper)-[:USES_METHODOLOGY]->(m:Methodology)
                RETURN p.paper_id as paper_id, p.year as year,
                       m.method_type as method_type, m.analysis_technique as technique
                ORDER BY p.year
            """)
            
            methodologies = []
            for record in result:
                methodologies.append({
                    'paper_id': record['paper_id'],
                    'year': record['year'],
                    'method_type': record['method_type'],
                    'technique': record['technique']
                })
            
            # Get all findings
            result = session.run("""
                MATCH (p:Paper)-[:REPORTS_FINDING]->(f:Finding)
                RETURN p.paper_id as paper_id, p.year as year,
                       f.finding as finding, f.finding_type as finding_type
                ORDER BY p.year
            """)
            
            findings = []
            for record in result:
                findings.append({
                    'paper_id': record['paper_id'],
                    'year': record['year'],
                    'finding': record['finding'],
                    'finding_type': record['finding_type']
                })
            
            return {
                'questions': questions,
                'methodologies': methodologies,
                'findings': findings
            }
    
    def generate_answer(self, query: str, all_data: dict):
        """Generate answer using all available data"""
        
        # Prepare context
        context = f"""
        AVAILABLE RESEARCH DATA:
        
        RESEARCH QUESTIONS ({len(all_data['questions'])} total):
        """
        
        for q in all_data['questions']:
            context += f"- {q['paper_id']} ({q['year']}) [{q['question_type']}]: {q['question']}\n"
        
        context += f"\nMETHODOLOGIES ({len(all_data['methodologies'])} total):\n"
        for m in all_data['methodologies']:
            context += f"- {m['paper_id']} ({m['year']}): {m['method_type']} - {m['technique']}\n"
        
        context += f"\nFINDINGS ({len(all_data['findings'])} total):\n"
        for f in all_data['findings']:
            context += f"- {f['paper_id']} ({f['year']}) [{f['finding_type']}]: {f['finding']}\n"
        
        prompt = f"""
        You are a research assistant analyzing strategic management literature. 
        Based on the following research data, answer the user's question.
        
        Question: {query}
        
        Available Research Data:
        {context}
        
        Please provide:
        1. A direct answer to the question based on the available data
        2. Specific examples from the papers
        3. Patterns or trends you notice
        4. Any insights about the research landscape
        
        Be specific and cite the paper IDs when referencing studies.
        If the question asks about something not in the data, say so clearly.
        """
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating answer: {e}"
    
    def ask_question(self, query: str):
        """Ask a question and get an answer"""
        print(f"\n🔍 Question: '{query}'")
        print("📊 Loading all available research data...")
        
        # Get all data
        all_data = self.get_all_data()
        
        print(f"Found {len(all_data['questions'])} research questions, {len(all_data['methodologies'])} methodologies, {len(all_data['findings'])} findings")
        
        if not all_data['questions'] and not all_data['methodologies'] and not all_data['findings']:
            return "No research data found in the knowledge graph."
        
        # Generate answer
        answer = self.generate_answer(query, all_data)
        return answer
    
    def close(self):
        """Close database connection"""
        self.driver.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python demo_qa.py 'Your question here'")
        print("Example: python demo_qa.py 'What research questions are about mergers?'")
        return
    
    query = sys.argv[1]
    
    qa_system = DemoQASystem()
    
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
