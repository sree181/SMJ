#!/usr/bin/env python3
"""
Interactive question-answering system for the literature knowledge graph
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI

class LiteratureQASystem:
    def __init__(self):
        load_dotenv()
        
        # Initialize Neo4j connection
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_user = os.getenv("NEO4J_USER")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
        
        # Initialize OpenAI
        self.llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def get_relevant_papers(self, query: str, limit: int = 10):
        """Get papers relevant to the query"""
        with self.driver.session() as session:
            # Search in research questions
            result = session.run("""
                MATCH (p:Paper)-[:HAS_RESEARCH_QUESTION]->(rq:ResearchQuestion)
                WHERE toLower(rq.question) CONTAINS toLower($query)
                RETURN p.paper_id as paper_id, p.year as year, rq.question as question
                LIMIT $limit
            """, query=query, limit=limit)
            
            papers = []
            for record in result:
                papers.append({
                    'paper_id': record['paper_id'],
                    'year': record['year'],
                    'question': record['question']
                })
            
            return papers
    
    def get_methodology_info(self, query: str, limit: int = 10):
        """Get methodology information relevant to the query"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)-[:USES_METHODOLOGY]->(m:Methodology)
                WHERE toLower(m.method_type) CONTAINS toLower($query) 
                   OR toLower(m.analysis_technique) CONTAINS toLower($query)
                RETURN p.paper_id as paper_id, p.year as year, 
                       m.method_type as method_type, m.analysis_technique as technique
                LIMIT $limit
            """, query=query, limit=limit)
            
            methods = []
            for record in result:
                methods.append({
                    'paper_id': record['paper_id'],
                    'year': record['year'],
                    'method_type': record['method_type'],
                    'technique': record['technique']
                })
            
            return methods
    
    def get_findings_info(self, query: str, limit: int = 10):
        """Get findings relevant to the query"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)-[:REPORTS_FINDING]->(f:Finding)
                WHERE toLower(f.finding) CONTAINS toLower($query)
                RETURN p.paper_id as paper_id, p.year as year, 
                       f.finding as finding, f.finding_type as finding_type
                LIMIT $limit
            """, query=query, limit=limit)
            
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
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
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
    
    def interactive_mode(self):
        """Interactive question-answering mode"""
        print("🤖 Literature Q&A System")
        print("Ask questions about the research papers in the knowledge graph.")
        print("Type 'quit' to exit, 'help' for examples.\n")
        
        while True:
            try:
                query = input("❓ Your question: ").strip()
                
                if query.lower() == 'quit':
                    print("Goodbye!")
                    break
                elif query.lower() == 'help':
                    print("\nExample questions:")
                    print("- What research questions are about mergers and acquisitions?")
                    print("- What methodologies are used in strategic management research?")
                    print("- What are the main findings about top management teams?")
                    print("- What research has been done on corporate performance?")
                    print("- What are the trends in strategic management research?")
                    continue
                elif not query:
                    continue
                
                answer = self.ask_question(query)
                print(f"\n💡 Answer:\n{answer}\n")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def close(self):
        """Close database connection"""
        self.driver.close()

def main():
    qa_system = LiteratureQASystem()
    
    try:
        # Test connection
        with qa_system.driver.session() as session:
            result = session.run("RETURN 'Connected to Neo4j Aura!' as message")
            print(f"✓ {result.single()['message']}")
        
        # Run interactive mode
        qa_system.interactive_mode()
        
    finally:
        qa_system.close()

if __name__ == "__main__":
    main()
