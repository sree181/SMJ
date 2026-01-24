#!/usr/bin/env python3
"""
Startup script for SMJ Research Chatbot
Installs dependencies and starts both FastAPI server and React app
"""

import subprocess
import sys
import os
import time
import threading
from pathlib import Path

def run_command(command, cwd=None, shell=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=shell, 
            cwd=cwd, 
            capture_output=True, 
            text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def install_python_dependencies():
    """Install Python dependencies"""
    print("🐍 Installing Python dependencies...")
    success, stdout, stderr = run_command("pip install -r requirements.txt")
    if success:
        print("✓ Python dependencies installed successfully")
    else:
        print(f"✗ Failed to install Python dependencies: {stderr}")
        return False
    return True

def install_node_dependencies():
    """Install Node.js dependencies"""
    print("📦 Installing Node.js dependencies...")
    success, stdout, stderr = run_command("npm install")
    if success:
        print("✓ Node.js dependencies installed successfully")
    else:
        print(f"✗ Failed to install Node.js dependencies: {stderr}")
        return False
    return True

def start_fastapi_server():
    """Start FastAPI server in background"""
    print("🚀 Starting FastAPI server...")
    try:
        # Start FastAPI server
        process = subprocess.Popen(
            [sys.executable, "api_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if server is running
        if process.poll() is None:
            print("✓ FastAPI server started on http://localhost:5000")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"✗ Failed to start FastAPI server: {stderr}")
            return None
    except Exception as e:
        print(f"✗ Error starting FastAPI server: {e}")
        return None

def start_react_app():
    """Start React app"""
    print("⚛️ Starting React app...")
    try:
        process = subprocess.Popen(
            ["npm", "start"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for app to start
        time.sleep(5)
        
        if process.poll() is None:
            print("✓ React app started on http://localhost:3000")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"✗ Failed to start React app: {stderr}")
            return None
    except Exception as e:
        print(f"✗ Error starting React app: {e}")
        return None

def check_environment():
    """Check if required environment variables are set"""
    print("🔍 Checking environment...")
    
    required_vars = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"✗ Missing environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        return False
    
    print("✓ Environment variables configured")
    return True

def main():
    """Main startup function"""
    print("🎯 SMJ Research Chatbot Startup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("package.json").exists() or not Path("api_server.py").exists():
        print("✗ Please run this script from the Strategic Management Journal directory")
        return
    
    # Check environment
    if not check_environment():
        return
    
    # Install dependencies
    if not install_python_dependencies():
        return
    
    if not install_node_dependencies():
        return
    
    print("\n🚀 Starting services...")
    
    # Start FastAPI server
    fastapi_process = start_fastapi_server()
    if not fastapi_process:
        return
    
    # Start React app
    react_process = start_react_app()
    if not react_process:
        fastapi_process.terminate()
        return
    
    print("\n🎉 SMJ Research Chatbot is running!")
    print("📱 React App: http://localhost:3000")
    print("🔌 API Server: http://localhost:5000")
    print("📚 API Docs: http://localhost:5000/docs")
    print("\nPress Ctrl+C to stop all services")
    
    try:
        # Wait for processes
        while True:
            time.sleep(1)
            if fastapi_process.poll() is not None:
                print("✗ FastAPI server stopped unexpectedly")
                break
            if react_process.poll() is not None:
                print("✗ React app stopped unexpectedly")
                break
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        fastapi_process.terminate()
        react_process.terminate()
        print("✓ Services stopped")

if __name__ == "__main__":
    main()
