#!/usr/bin/env python3
"""
OLLAMA Setup Script for SMJ Research Processing
Installs and configures OLLAMA with appropriate models
"""

import subprocess
import sys
import time
import requests
import json
from pathlib import Path

def check_ollama_installed():
    """Check if OLLAMA is installed"""
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ OLLAMA is installed: {result.stdout.strip()}")
            return True
        else:
            print("✗ OLLAMA is not installed")
            return False
    except FileNotFoundError:
        print("✗ OLLAMA is not installed")
        return False

def install_ollama():
    """Install OLLAMA"""
    print("📥 Installing OLLAMA...")
    
    try:
        # Download and install OLLAMA
        if sys.platform == "darwin":  # macOS
            subprocess.run(['curl', '-fsSL', 'https://ollama.ai/install.sh', '|', 'sh'], shell=True)
        elif sys.platform == "linux":
            subprocess.run(['curl', '-fsSL', 'https://ollama.ai/install.sh', '|', 'sh'], shell=True)
        else:
            print("❌ Unsupported platform. Please install OLLAMA manually from https://ollama.ai/")
            return False
        
        print("✓ OLLAMA installed successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to install OLLAMA: {e}")
        print("Please install OLLAMA manually from https://ollama.ai/")
        return False

def start_ollama_service():
    """Start OLLAMA service"""
    print("🚀 Starting OLLAMA service...")
    
    try:
        # Start OLLAMA in background
        subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)  # Wait for service to start
        
        # Test connection
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            print("✓ OLLAMA service is running")
            return True
        else:
            print("❌ OLLAMA service failed to start")
            return False
    except Exception as e:
        print(f"❌ Failed to start OLLAMA service: {e}")
        return False

def pull_model(model_name: str):
    """Pull a specific OLLAMA model"""
    print(f"📦 Pulling model: {model_name}")
    
    try:
        result = subprocess.run(['ollama', 'pull', model_name], 
                              capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"✓ Successfully pulled {model_name}")
            return True
        else:
            print(f"❌ Failed to pull {model_name}: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout pulling {model_name}. This is normal for large models.")
        return True
    except Exception as e:
        print(f"❌ Error pulling {model_name}: {e}")
        return False

def test_model(model_name: str):
    """Test if a model is working"""
    print(f"🧪 Testing model: {model_name}")
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": "What is strategic management? Answer in one sentence.",
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Model {model_name} is working")
            print(f"  Response: {result.get('response', '')[:100]}...")
            return True
        else:
            print(f"❌ Model {model_name} test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing model {model_name}: {e}")
        return False

def get_available_models():
    """Get list of available models"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            return [model['name'] for model in models]
        return []
    except Exception as e:
        print(f"Error getting available models: {e}")
        return []

def main():
    """Main setup function"""
    print("🎯 OLLAMA Setup for SMJ Research Processing")
    print("=" * 50)
    
    # Check if OLLAMA is installed
    if not check_ollama_installed():
        print("\n📥 Installing OLLAMA...")
        if not install_ollama():
            print("❌ Setup failed. Please install OLLAMA manually.")
            return
    else:
        print("✓ OLLAMA is already installed")
    
    # Start OLLAMA service
    if not start_ollama_service():
        print("❌ Setup failed. Please start OLLAMA manually: ollama serve")
        return
    
    # Recommended models for research extraction
    recommended_models = [
        "llama3.1:8b",      # Best balance of quality and speed
        "mistral:7b",        # Alternative high-quality model
        "codellama:7b"       # Good for structured data extraction
    ]
    
    print(f"\n📦 Recommended models for research extraction:")
    for i, model in enumerate(recommended_models, 1):
        print(f"  {i}. {model}")
    
    # Check available models
    available_models = get_available_models()
    if available_models:
        print(f"\n📋 Currently available models:")
        for model in available_models:
            print(f"  - {model}")
    
    # Pull recommended models
    print(f"\n🚀 Setting up recommended models...")
    for model in recommended_models:
        if model not in available_models:
            if not pull_model(model):
                print(f"⚠️  Failed to pull {model}, but continuing...")
        else:
            print(f"✓ {model} is already available")
    
    # Test the primary model
    primary_model = recommended_models[0]
    if not test_model(primary_model):
        print(f"⚠️  Warning: {primary_model} test failed")
    
    print("\n" + "=" * 50)
    print("🎉 OLLAMA Setup Complete!")
    print("=" * 50)
    print("✅ OLLAMA service is running")
    print("✅ Models are ready for research extraction")
    print("\n🚀 You can now run:")
    print("  python batch_processor_ollama.py")
    print("\n💡 To stop OLLAMA service:")
    print("  pkill ollama")
    print("\n📚 For more models, visit: https://ollama.ai/library")

if __name__ == "__main__":
    main()
