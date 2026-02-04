#!/usr/bin/env python3
"""
Quick Setup & Run Script
Sets up virtual environment and runs the discovery tool.
"""

import subprocess
import sys
import os

def main():
    print("🚀 SMS Bomber - Quick Setup")
    print("=" * 40)
    
    # Get project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(project_dir, "venv")
    requirements_file = os.path.join(project_dir, "sms_bomber", "requirements.txt")
    
    # Check if venv exists
    if not os.path.exists(venv_dir):
        print("\n📦 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        print("✅ Virtual environment created!")
    else:
        print("✅ Virtual environment already exists")
    
    # Determine pip and python paths
    if sys.platform == "win32":
        pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
        python_path = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        pip_path = os.path.join(venv_dir, "bin", "pip")
        python_path = os.path.join(venv_dir, "bin", "python")
    
    # Install requirements
    print("\n📥 Installing dependencies...")
    subprocess.run([pip_path, "install", "-r", requirements_file], check=True)
    print("✅ Dependencies installed!")
    
    print("\n" + "=" * 40)
    print("🎉 Setup complete!")
    print("\nTo activate the virtual environment:")
    print(f"  Windows:  .\\venv\\Scripts\\activate")
    print(f"  Linux:    source venv/bin/activate")
    print("\nThen run:")
    print("  python discover_providers.py")
    print("  python run.py 09123456789 -c 3 -v")


if __name__ == "__main__":
    main()
