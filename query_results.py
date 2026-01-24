#!/usr/bin/env python3
"""
Query the knowledge graph to see what has been processed
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

def query_knowledge_graph():
    """Query the knowledge graph"""
    load_dotenv()
    
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    with driver.session() as session:
        # Count papers
        result = session.run("MATCH (p:Paper) RETURN count(p) as paper_count")
        paper_count = result.single()["paper_count"]
        print(f"📊 Total papers processed: {paper_count}")
        
        # Count research questions
        result = session.run("MATCH (rq:ResearchQuestion) RETURN count(rq) as question_count")
        question_count = result.single()["question_count"]
        print(f"❓ Total research questions: {question_count}")
        
        # Count methodologies
        result = session.run("MATCH (m:Methodology) RETURN count(m) as method_count")
        method_count = result.single()["method_count"]
        print(f"🔬 Total methodologies: {method_count}")
        
        # Show recent papers
        print(f"\n📚 Recent papers:")
        result = session.run("""
            MATCH (p:Paper) 
            RETURN p.paper_id as paper_id, p.year as year, p.volume as volume 
            ORDER BY p.year DESC 
            LIMIT 10
        """)
        
        for record in result:
            print(f"  - {record['paper_id']} ({record['year']}) Vol: {record['volume']}")
        
        # Show sample research questions
        print(f"\n❓ Sample research questions:")
        result = session.run("""
            MATCH (p:Paper)-[:HAS_RESEARCH_QUESTION]->(rq:ResearchQuestion)
            RETURN p.paper_id as paper_id, rq.question as question, rq.question_type as question_type
            LIMIT 5
        """)
        
        for record in result:
            print(f"  - {record['paper_id']} ({record['question_type']}): {record['question'][:100]}...")
        
        # Show sample methodologies
        print(f"\n🔬 Sample methodologies:")
        result = session.run("""
            MATCH (p:Paper)-[:USES_METHODOLOGY]->(m:Methodology)
            RETURN p.paper_id as paper_id, m.method_type as method_type, m.analysis_technique as analysis_technique
            LIMIT 5
        """)
        
        for record in result:
            print(f"  - {record['paper_id']}: {record['method_type']} - {record['analysis_technique']}")
    
    driver.close()

if __name__ == "__main__":
    query_knowledge_graph()
