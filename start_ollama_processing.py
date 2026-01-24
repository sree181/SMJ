#!/usr/bin/env python3
"""
Start OLLAMA-based batch processing for SMJ papers (1985-1994)
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def check_ollama_running():
    """Check if OLLAMA is running"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def start_ollama():
    """Start OLLAMA service"""
    print("🚀 Starting OLLAMA service...")
    try:
        subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
        
        if check_ollama_running():
            print("✅ OLLAMA service started successfully")
            return True
        else:
            print("❌ Failed to start OLLAMA service")
            return False
    except Exception as e:
        print(f"❌ Error starting OLLAMA: {e}")
        return False

def main():
    """Main function to start OLLAMA processing"""
    print("🎯 SMJ OLLAMA Batch Processing Starter")
    print("=" * 50)
    
    # Check if OLLAMA is running
    if not check_ollama_running():
        print("OLLAMA is not running. Starting it now...")
        if not start_ollama():
            print("❌ Cannot start OLLAMA. Please install and start it manually:")
            print("   1. Install: https://ollama.ai/")
            print("   2. Start: ollama serve")
            return
    else:
        print("✅ OLLAMA is already running")
    
    # Check if we're in the right directory
    if not Path("batch_processor_ollama.py").exists():
        print("❌ batch_processor_ollama.py not found. Please run from the correct directory.")
        return
    
    # Check environment variables
    if not os.getenv("NEO4J_URI"):
        print("⚠️  NEO4J_URI not set. Using default localhost connection.")
        print("   For Neo4j Aura, set NEO4J_URI in .env file")
    
    print("\n🚀 Starting batch processing...")
    print("📅 Processing period: 1985-1994")
    print("🤖 Using OLLAMA models (cost-effective)")
    print("⏱️  Estimated time: 2-4 hours")
    print("\nPress Ctrl+C to stop processing")
    print("=" * 50)
    
    try:
        # Start batch processing
        subprocess.run([sys.executable, "batch_processor_ollama.py"])
    except KeyboardInterrupt:
        print("\n\n⏹️  Processing stopped by user")
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")

if __name__ == "__main__":
    main()
