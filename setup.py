#!/usr/bin/env python3
"""
Setup script for PDF Parsing & Workflow Project
Automatically sets up the project structure and installs dependencies
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_step(step_name, description=""):
    """Print a formatted step header"""
    print(f"\n{'='*60}")
    print(f"📦 {step_name}")
    if description:
        print(f"   {description}")
    print('='*60)

def run_command(command, description=""):
    """Run a command and handle errors"""
    print(f"\n🔄 {description if description else 'Running command...'}")
    print(f"   Command: {command}")

    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"   ✅ Success!")
        if result.stdout.strip():
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e}")
        if e.stderr:
            print(f"   Error details: {e.stderr}")
        return False

def create_directory_structure():
    """Create the proper Flask project structure"""
    print_step("CREATING PROJECT STRUCTURE")

    directories = [
        "templates",
        "static/css", 
        "static/js",
        "backend",
        "downloads",
        "logs"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created: {directory}/")

    # Create __init__.py files
    init_files = [
        "backend/__init__.py"
    ]

    for init_file in init_files:
        Path(init_file).touch()
        print(f"   ✅ Created: {init_file}")

def copy_corrected_files():
    """Copy the corrected files to their proper locations"""
    print_step("COPYING CORRECTED FILES", "Moving files to proper Flask structure")

    file_mappings = {
        "corrected_app.py": "app.py",
        "corrected_utils.py": "backend/utils.py", 
        "corrected_web_scraper.py": "backend/web_scraper.py",
        "corrected_app.js": "static/js/app.js",
        "corrected_index.html": "templates/index.html",
        "backend_init.py": "backend/__init__.py"
    }

    for source, destination in file_mappings.items():
        if os.path.exists(source):
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.copy2(source, destination)
            print(f"   ✅ Copied: {source} → {destination}")
        else:
            print(f"   ⚠️  Missing source file: {source}")

    # Copy original files that don't need changes
    original_files = {
        "style.css": "static/css/style.css",
        "pdf_processor.py": "backend/pdf_processor.py",
        "ai_summarizer.py": "backend/ai_summarizer.py"
    }

    for source, destination in original_files.items():
        if os.path.exists(source):
            os.makedirs(os.path.dirname(destination), exist_ok=True) 
            shutil.copy2(source, destination)
            print(f"   ✅ Copied: {source} → {destination}")

def install_python_dependencies():
    """Install Python dependencies"""
    print_step("INSTALLING PYTHON DEPENDENCIES")

    if not os.path.exists("requirements.txt"):
        print("   ❌ requirements.txt not found!")
        return False

    # Try to upgrade pip first
    run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip")

    # Install requirements
    success = run_command(f"{sys.executable} -m pip install -r requirements.txt", 
                         "Installing Python packages")

    if success:
        print("   ✅ All Python dependencies installed successfully!")
    else:
        print("   ❌ Failed to install some dependencies. Check the error above.")

    return success

def setup_chrome_driver():
    """Set up Chrome driver for Selenium"""
    print_step("SETTING UP CHROME DRIVER")

    print("   ℹ️  Chrome driver will be automatically downloaded by webdriver-manager")
    print("   ℹ️  Make sure you have Chrome browser installed on your system")

    # Test Chrome installation
    chrome_commands = ["google-chrome --version", "chrome --version", "chromium --version"]

    for cmd in chrome_commands:
        if run_command(cmd, f"Checking Chrome with: {cmd}"):
            print("   ✅ Chrome browser detected!")
            return True

    print("   ⚠️  Chrome browser not detected. Please install Chrome manually.")
    print("   ℹ️  Download from: https://www.google.com/chrome/")
    return False

def create_environment_file():
    """Create a .env file for environment variables"""
    print_step("CREATING ENVIRONMENT FILE")

    env_content = """# Environment Configuration for PDF Parsing Project
# Copy this file to .env and modify as needed

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-change-in-production

# Selenium Configuration  
CHROME_HEADLESS=True
SELENIUM_TIMEOUT=120
SELENIUM_RETRIES=3

# AI Model Configuration
AI_MODEL_NAME=ml6team/mt5-small-german-finetune-mlsum

# Logging
LOG_LEVEL=INFO
"""

    with open('.env.example', 'w') as f:
        f.write(env_content)

    print("   ✅ Created .env.example file")
    print("   ℹ️  Copy this to .env and modify as needed")

def run_tests():
    """Run basic tests to verify setup"""
    print_step("RUNNING BASIC TESTS")

    # Test imports
    test_imports = [
        "flask",
        "selenium", 
        "requests",
        "transformers",
        "fitz",  # PyMuPDF
    ]

    failed_imports = []

    for module in test_imports:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError as e:
            print(f"   ❌ {module} - {e}")
            failed_imports.append(module)

    if failed_imports:
        print(f"\n   ⚠️  Failed to import: {', '.join(failed_imports)}")
        return False
    else:
        print("\n   ✅ All required modules can be imported!")
        return True

def print_final_instructions():
    """Print final setup instructions"""
    print_step("SETUP COMPLETE! 🎉", "Your PDF Parsing project is ready to use")

    instructions = """
To start the application:
    python app.py

Then visit: http://localhost:5000

Project Structure:
    app.py                  - Main Flask application
    config.py              - Configuration settings
    requirements.txt       - Python dependencies
    templates/            - HTML templates
    static/              - CSS & JavaScript files
    backend/            - Python modules
    downloads/          - Downloaded PDF files
    logs/              - Application logs

Configuration:
    - Copy .env.example to .env for custom settings
    - Modify config.py for advanced configuration
    - Check logs/german_processor.log for debugging

Important Notes:
    - Make sure Chrome browser is installed
    - The AI model will be downloaded on first use (~500MB)
    - Internet connection required for web scraping
    - Some German websites may have anti-bot measures

Troubleshooting:
    - If Chrome driver fails, update Chrome browser
    - If AI model fails to load, check internet connection
    - If web scraping fails, try running in non-headless mode
    - Check logs/german_processor.log for detailed error information
"""

    print(instructions)

def main():
    """Main setup function"""
    print("PDF Parsing & Workflow Project Setup")
    print("Setting up your German Business Registry PDF processor...")

    try:
        # Step 1: Create directory structure
        create_directory_structure()

        # Step 2: Copy corrected files
        copy_corrected_files()

        # Step 3: Install dependencies
        if not install_python_dependencies():
            print("\nSome dependencies failed to install. The app may not work properly.")

        # Step 4: Setup Chrome driver
        setup_chrome_driver()

        # Step 5: Create environment file
        create_environment_file()

        # Step 6: Run basic tests
        if run_tests():
            print("\nAll tests passed!")
        else:
            print("\nSome tests failed. Check the errors above.")

        # Step 7: Final instructions
        print_final_instructions()

    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nSetup failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
