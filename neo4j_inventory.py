#!/usr/bin/env python3
"""
Comprehensive Neo4j Database Inventory
Lists all nodes, relationships, and properties currently in the database
"""

import os
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Neo4jInventory:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    def get_all_node_labels(self):
        """Get all node labels in the database"""
        with self.driver.session() as session:
            result = session.run("CALL db.labels()")
            return [record["label"] for record in result]
    
    def get_all_relationship_types(self):
        """Get all relationship types in the database"""
        with self.driver.session() as session:
            result = session.run("CALL db.relationshipTypes()")
            return [record["relationshipType"] for record in result]
    
    def get_node_counts(self):
        """Get count of each node type"""
        labels = self.get_all_node_labels()
        counts = {}
        with self.driver.session() as session:
            for label in labels:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                counts[label] = result.single()["count"]
        return counts
    
    def get_relationship_counts(self):
        """Get count of each relationship type"""
        rel_types = self.get_all_relationship_types()
        counts = {}
        with self.driver.session() as session:
            for rel_type in rel_types:
                result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                counts[rel_type] = result.single()["count"]
        return counts
    
    def get_node_properties(self, label):
        """Get all properties for a node label"""
        with self.driver.session() as session:
            result = session.run(f"""
                MATCH (n:{label})
                RETURN keys(n) as keys
                LIMIT 100
            """)
            all_keys = set()
            for record in result:
                all_keys.update(record["keys"])
            return sorted(list(all_keys))
    
    def get_relationship_properties(self, rel_type):
        """Get all properties for a relationship type"""
        with self.driver.session() as session:
            result = session.run(f"""
                MATCH ()-[r:{rel_type}]->()
                RETURN keys(r) as keys
                LIMIT 100
            """)
            all_keys = set()
            for record in result:
                all_keys.update(record["keys"])
            return sorted(list(all_keys))
    
    def get_missing_data_analysis(self):
        """Analyze missing data"""
        analysis = {}
        with self.driver.session() as session:
            # Papers missing titles
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.title IS NULL OR p.title = ""
                RETURN count(p) as count
            """)
            analysis["papers_missing_titles"] = result.single()["count"]
            
            # Papers missing authors
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)<-[:AUTHORED]-() AND NOT (p)-[:AUTHORED_BY]->()
                RETURN count(p) as count
            """)
            analysis["papers_missing_authors"] = result.single()["count"]
            
            # Papers missing theories
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)-[:USES_THEORY]->()
                RETURN count(p) as count
            """)
            analysis["papers_missing_theories"] = result.single()["count"]
            
            # Papers missing methods
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)-[:USES_METHOD]->()
                RETURN count(p) as count
            """)
            analysis["papers_missing_methods"] = result.single()["count"]
            
            # Papers missing phenomena
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)-[:STUDIES_PHENOMENON]->()
                RETURN count(p) as count
            """)
            analysis["papers_missing_phenomena"] = result.single()["count"]
            
            # Papers missing research questions
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)-[:ADDRESSES]->()
                RETURN count(p) as count
            """)
            analysis["papers_missing_research_questions"] = result.single()["count"]
            
            # Papers missing findings
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)-[:HAS_FINDING]->()
                RETURN count(p) as count
            """)
            analysis["papers_missing_findings"] = result.single()["count"]
            
            # Papers missing contributions
            result = session.run("""
                MATCH (p:Paper)
                WHERE NOT (p)-[:HAS_CONTRIBUTION]->()
                RETURN count(p) as count
            """)
            analysis["papers_missing_contributions"] = result.single()["count"]
            
            # Total papers
            result = session.run("MATCH (p:Paper) RETURN count(p) as count")
            analysis["total_papers"] = result.single()["count"]
        
        return analysis
    
    def print_full_inventory(self):
        """Print comprehensive inventory"""
        print("=" * 80)
        print("NEO4J DATABASE INVENTORY")
        print("=" * 80)
        
        # Node labels
        print("\n" + "=" * 80)
        print("NODE LABELS")
        print("=" * 80)
        labels = self.get_all_node_labels()
        node_counts = self.get_node_counts()
        
        for label in sorted(labels):
            count = node_counts.get(label, 0)
            print(f"\n{label}: {count} nodes")
            
            # Get properties
            props = self.get_node_properties(label)
            if props:
                print(f"  Properties: {', '.join(props)}")
            
            # Sample node
            with self.driver.session() as session:
                result = session.run(f"MATCH (n:{label}) RETURN n LIMIT 1")
                if result.peek():
                    node = result.single()["n"]
                    print(f"  Sample: {dict(node)}")
        
        # Relationship types
        print("\n" + "=" * 80)
        print("RELATIONSHIP TYPES")
        print("=" * 80)
        rel_types = self.get_all_relationship_types()
        rel_counts = self.get_relationship_counts()
        
        for rel_type in sorted(rel_types):
            count = rel_counts.get(rel_type, 0)
            print(f"\n{rel_type}: {count} relationships")
            
            # Get properties
            props = self.get_relationship_properties(rel_type)
            if props:
                print(f"  Properties: {', '.join(props)}")
            
            # Sample relationship
            with self.driver.session() as session:
                result = session.run(f"""
                    MATCH (a)-[r:{rel_type}]->(b)
                    RETURN type(r) as type, keys(r) as keys, labels(a)[0] as from, labels(b)[0] as to
                    LIMIT 1
                """)
                if result.peek():
                    record = result.single()
                    print(f"  Pattern: ({record['from']})-[:{record['type']}]->({record['to']})")
        
        # Missing data analysis
        print("\n" + "=" * 80)
        print("MISSING DATA ANALYSIS")
        print("=" * 80)
        analysis = self.get_missing_data_analysis()
        total = analysis["total_papers"]
        
        print(f"\nTotal Papers: {total}")
        print(f"\nMissing Data:")
        for key, count in analysis.items():
            if key != "total_papers":
                pct = (count / total * 100) if total > 0 else 0
                print(f"  {key}: {count} ({pct:.1f}%)")
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Node Types: {len(labels)}")
        print(f"Relationship Types: {len(rel_types)}")
        print(f"Total Nodes: {sum(node_counts.values())}")
        print(f"Total Relationships: {sum(rel_counts.values())}")
    
    def close(self):
        self.driver.close()

if __name__ == "__main__":
    inventory = Neo4jInventory()
    try:
        inventory.print_full_inventory()
    finally:
        inventory.close()
