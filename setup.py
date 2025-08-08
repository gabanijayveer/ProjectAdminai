#!/usr/bin/env python3
"""
SQL Procedure Manager Frontend Setup Script
Installs dependencies and configures the application.
"""

import os
import sys
import subprocess
import mysql.connector
from config import DB_CONFIG, get_db_connection_string

def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"🔧 {title}")
    print("="*60)

def print_success(message):
    """Print a success message."""
    print(f"✅ {message}")

def print_error(message):
    """Print an error message."""
    print(f"❌ {message}")

def print_info(message):
    """Print an info message."""
    print(f"ℹ️  {message}")

def check_python_version():
    """Check if Python version is compatible."""
    print_header("Checking Python Version")
    
    if sys.version_info < (3, 8):
        print_error(f"Python 3.8+ required. Current version: {sys.version}")
        return False
    
    print_success(f"Python version: {sys.version}")
    return True

def install_dependencies():
    """Install required Python packages."""
    print_header("Installing Dependencies")
    
    try:
        print_info("Installing packages from requirements.txt...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print_success("All dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False

def test_database_connection():
    """Test MySQL database connection."""
    print_header("Testing Database Connection")
    
    try:
        print_info(f"Connecting to: {get_db_connection_string()}")
        
        # Try to connect without database first
        temp_config = DB_CONFIG.copy()
        database_name = temp_config.pop('database')
        
        conn = mysql.connector.connect(**temp_config)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SHOW DATABASES LIKE %s", (database_name,))
        db_exists = cursor.fetchone() is not None
        
        if not db_exists:
            print_info(f"Creating database: {database_name}")
            cursor.execute(f"CREATE DATABASE {database_name}")
            print_success(f"Database '{database_name}' created")
        else:
            print_success(f"Database '{database_name}' already exists")
        
        cursor.close()
        conn.close()
        
        # Test full connection
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        
        print_success("Database connection successful")
        return True
        
    except mysql.connector.Error as e:
        print_error(f"Database connection failed: {e}")
        print_info("Please check your database configuration in config.py")
        return False

def initialize_database():
    """Initialize database tables."""
    print_header("Initializing Database Tables")
    
    try:
        from app import init_db
        init_db()
        print_success("Database tables initialized")
        return True
    except Exception as e:
        print_error(f"Failed to initialize database: {e}")
        return False

def check_required_files():
    """Check if all required files exist."""
    print_header("Checking Required Files")
    
    required_files = [
        'app.py',
        'config.py',
        'Proceduremanager.py',
        'run_frontend.py',
        'requirements.txt',
        'templates/base.html',
        'templates/index.html',
        'templates/history.html',
        'templates/formulas.html'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print_success(f"Found: {file}")
        else:
            print_error(f"Missing: {file}")
            missing_files.append(file)
    
    if missing_files:
        print_error(f"Missing {len(missing_files)} required files")
        return False
    
    print_success("All required files found")
    return True

def create_static_directories():
    """Create static file directories."""
    print_header("Creating Static Directories")
    
    directories = [
        'static',
        'static/css',
        'static/js',
        'static/images'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print_success(f"Created directory: {directory}")
        else:
            print_info(f"Directory exists: {directory}")
    
    return True

def test_application():
    """Test if the application can start."""
    print_header("Testing Application")
    
    try:
        print_info("Testing application imports...")
        from app import app
        print_success("Application imports successful")
        
        print_info("Testing configuration...")
        from config import validate_db_config
        validate_db_config()
        print_success("Configuration validation successful")
        
        return True
    except Exception as e:
        print_error(f"Application test failed: {e}")
        return False

def print_final_instructions():
    """Print final setup instructions."""
    print_header("Setup Complete!")
    
    print("🎉 SQL Procedure Manager Frontend is ready!")
    print("\n📋 Next Steps:")
    print("1. Start the application:")
    print("   python run_frontend.py")
    print("\n2. Open your browser to:")
    print("   http://localhost:5000")
    print("\n3. Test with example queries:")
    print("   • Find top 3 performing employees")
    print("   • Analyze sales trends with growth rates")
    print("   • Statistical analysis of performance data")
    print("\n🔧 Configuration:")
    print("   • Database settings: config.py")
    print("   • Application settings: config.py")
    print("   • Procedure engine: Proceduremanager.py")
    print("\n📚 Documentation:")
    print("   • README.md - Complete usage guide")
    print("   • /formulas - Mathematical formulas reference")
    print("   • /history - Query execution history")

def main():
    """Main setup function."""
    print("🚀 SQL PROCEDURE MANAGER FRONTEND SETUP")
    print("Setting up your intelligent SQL procedure generation system...")
    
    steps = [
        ("Python Version", check_python_version),
        ("Required Files", check_required_files),
        ("Static Directories", create_static_directories),
        ("Dependencies", install_dependencies),
        ("Database Connection", test_database_connection),
        ("Database Tables", initialize_database),
        ("Application Test", test_application)
    ]
    
    failed_steps = []
    
    for step_name, step_function in steps:
        if not step_function():
            failed_steps.append(step_name)
    
    if failed_steps:
        print_header("Setup Failed")
        print_error(f"Failed steps: {', '.join(failed_steps)}")
        print_info("Please fix the issues above and run setup again.")
        return False
    
    print_final_instructions()
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
