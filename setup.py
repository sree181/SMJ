"""
Setup script for the Literature Agent
Handles installation of dependencies and initial configuration
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing requirements: {e}")
        return False
    return True

def check_openai_api_key():
    """Check if OpenAI API key is configured"""
    print("Checking OpenAI API key configuration...")
    try:
        from dotenv import load_dotenv
        import os
        load_dotenv()
        
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            print("✓ OpenAI API key found in environment")
            return True
        else:
            print("⚠ OpenAI API key not found. Please add it to your .env file:")
            print("   OPENAI_API_KEY=your_api_key_here")
            return False
    except Exception as e:
        print(f"✗ Error checking API key: {e}")
        return False

def create_env_file():
    """Create .env file for configuration"""
    env_content = """# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✓ Created .env file with default configuration")
    else:
        print("✓ .env file already exists")

def main():
    """Main setup function"""
    print("Setting up Literature Agent...")
    print("=" * 50)
    
    success = True
    
    # Install requirements
    if not install_requirements():
        success = False
    
    # Check OpenAI API key
    if not check_openai_api_key():
        success = False
    
    # Create environment file
    create_env_file()
    
    print("=" * 50)
    if success:
        print("✓ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Install and start Neo4j database")
        print("2. Update .env file with your OpenAI API key and Neo4j credentials")
        print("3. Run: python Kb.py")
    else:
        print("✗ Setup completed with errors. Please check the messages above.")

if __name__ == "__main__":
    main()
