#!/usr/bin/env python3
"""
Demo script for SMJ Research Chatbot
Shows the complete functionality without needing the web interface
"""

import requests
import json
import time
from typing import Dict, Any

class ChatbotDemo:
    def __init__(self, api_url: str = "http://localhost:5000"):
        self.api_url = api_url
        self.session = requests.Session()
    
    def check_health(self) -> bool:
        """Check if the API server is running"""
        try:
            response = self.session.get(f"{self.api_url}/api/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✓ API Server: {health_data['status']}")
                print(f"✓ Neo4j Connected: {health_data['neo4j_connected']}")
                return True
            else:
                print(f"✗ API Server returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Cannot connect to API server: {e}")
            return False
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """Ask a question and get response with graph data"""
        try:
            response = self.session.post(
                f"{self.api_url}/api/query",
                json={"query": question},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"✗ API returned status {response.status_code}")
                return {}
        except Exception as e:
            print(f"✗ Error asking question: {e}")
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        try:
            response = self.session.get(f"{self.api_url}/api/stats")
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except Exception as e:
            print(f"✗ Error getting stats: {e}")
            return {}
    
    def display_answer(self, data: Dict[str, Any], question: str):
        """Display the answer in a formatted way"""
        print(f"\n🤖 Question: {question}")
        print("=" * 60)
        print(f"💡 Answer:\n{data.get('answer', 'No answer available')}")
        
        if data.get('sources'):
            print(f"\n📚 Sources ({len(data['sources'])}):")
            for i, source in enumerate(data['sources'][:3], 1):
                print(f"  {i}. {source['content'][:100]}...")
        
        if data.get('graphData'):
            nodes = data['graphData'].get('nodes', [])
            edges = data['graphData'].get('edges', [])
            print(f"\n🕸️ Knowledge Graph: {len(nodes)} nodes, {len(edges)} edges")
            
            if nodes:
                print("   Key entities:")
                for node in nodes[:5]:
                    node_data = node.get('data', {})
                    print(f"   - {node_data.get('label', 'Unknown')} ({node_data.get('type', 'unknown')})")
    
    def run_demo(self):
        """Run the complete demo"""
        print("🎯 SMJ Research Chatbot Demo")
        print("=" * 50)
        
        # Check health
        if not self.check_health():
            print("\n❌ Cannot connect to the API server.")
            print("Please make sure the FastAPI server is running:")
            print("  python api_server.py")
            return
        
        # Get stats
        print("\n📊 Knowledge Graph Statistics:")
        stats = self.get_stats()
        if stats:
            for key, value in stats.items():
                print(f"   {key.title()}: {value}")
        
        # Demo questions
        demo_questions = [
            "What are the main research themes in strategic management?",
            "What methodologies are used in top management research?",
            "How do mergers and acquisitions affect management teams?",
            "What are the research gaps in the field?",
            "Which papers are most influential?"
        ]
        
        print(f"\n💬 Demo Questions ({len(demo_questions)}):")
        print("=" * 50)
        
        for i, question in enumerate(demo_questions, 1):
            print(f"\n[{i}/{len(demo_questions)}] Processing...")
            
            # Ask question
            data = self.ask_question(question)
            
            if data:
                self.display_answer(data, question)
            else:
                print(f"❌ Failed to get answer for: {question}")
            
            # Small delay between questions
            if i < len(demo_questions):
                time.sleep(1)
        
        print(f"\n🎉 Demo completed!")
        print(f"🌐 Web Interface: http://localhost:3000")
        print(f"📚 API Docs: http://localhost:5000/docs")

def main():
    demo = ChatbotDemo()
    demo.run_demo()

if __name__ == "__main__":
    main()
