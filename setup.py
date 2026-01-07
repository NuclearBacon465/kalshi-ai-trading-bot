#!/usr/bin/env python3
"""
Setup script for Kalshi AI Trading Bot
Handles installation, configuration, and initial setup
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    if sys.version_info < (3, 12):
        print(f"⚠️  Python {sys.version.split()[0]} detected (Python 3.12+ recommended)")
        print("✅ Continuing with Python 3.11 (most features will work)")
    else:
        print(f"✅ Python version {sys.version.split()[0]} is compatible")
    return True


def create_virtual_environment():
    """Create a virtual environment."""
    if os.path.exists("venv"):
        print("✅ Virtual environment already exists")
        return True
    
    return run_command("python -m venv venv", "Creating virtual environment")


def install_dependencies():
    """Install required dependencies."""
    # Determine the correct pip command
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        pip_cmd = "venv/bin/pip"
    
    return run_command(f"{pip_cmd} install -r requirements.txt", "Installing dependencies")


def setup_environment_file():
    """Set up the environment file."""
    env_file = Path(".env")
    env_template = Path("env.template")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_template.exists():
        shutil.copy(env_template, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your API keys before running the bot")
        return True
    else:
        print("❌ env.template not found")
        return False


def create_directories():
    """Create necessary directories."""
    directories = ["logs", "data", "reports"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Created necessary directories")
    return True


def run_tests():
    """Run basic tests to verify installation."""
    print("🧪 Running basic tests...")
    
    # Determine the correct python command
    if os.name == 'nt':  # Windows
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        python_cmd = "venv/bin/python"
    
    # Test imports
    test_script = """
import sys
try:
    import httpx
    import aiohttp
    import pandas
    import numpy
    import openai
    import xai_sdk
    print("✅ All required packages imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
"""
    
    try:
        result = subprocess.run(
            [python_cmd, "-c", test_script],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Test failed: {e.stderr}")
        return False


def main():
    """Main setup function."""
    print("🚀 Setting up Kalshi AI Trading Bot...")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Setup environment file
    if not setup_environment_file():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Run tests
    if not run_tests():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit the .env file with your API keys")
    print("2. Activate the virtual environment:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("3. Run the bot: python beast_mode_bot.py")
    print("4. Or launch the dashboard: python launch_dashboard.py")
    print("\n📚 For more information, see the README.md file")


if __name__ == "__main__":
    main() 