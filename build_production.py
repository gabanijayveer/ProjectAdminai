#!/usr/bin/env python3
"""
Production build script for AI Data Chat
Builds the React frontend and prepares for deployment
"""

import subprocess
import sys
import shutil
import os
from pathlib import Path

def build_frontend():
    """Build the React frontend for production."""
    print("⚛️ Building React frontend for production...")
    frontend_dir = Path("frontend")
    
    if not frontend_dir.exists():
        print("❌ Frontend directory not found.")
        return False
    
    try:
        # Install dependencies if needed
        print("📦 Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
        
        # Build the frontend
        print("🔨 Building frontend...")
        subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True)
        
        print("✅ Frontend build completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Frontend build failed: {e}")
        return False

def setup_static_serving():
    """Set up static file serving for production."""
    print("📁 Setting up static file serving...")
    
    frontend_build = Path("frontend/build")
    static_dir = Path("static_build")
    
    if not frontend_build.exists():
        print("❌ Frontend build directory not found.")
        return False
    
    try:
        # Remove existing static build directory
        if static_dir.exists():
            shutil.rmtree(static_dir)
        
        # Copy build files to static directory
        shutil.copytree(frontend_build, static_dir)
        
        print("✅ Static files copied successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to copy static files: {e}")
        return False

def create_production_config():
    """Create production configuration files."""
    print("⚙️ Creating production configuration...")
    
    # Create production requirements
    prod_requirements = """# Production requirements for AI Data Chat
# FastAPI and server dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Database and AI dependencies
langchain-google-genai==1.0.8
langchain==0.2.16
mysql-connector-python==8.2.0
python-dotenv==1.0.0
PyMySQL==1.1.0

# Additional FastAPI utilities
pydantic==2.5.0
starlette==0.27.0
"""
    
    with open("requirements_prod.txt", "w") as f:
        f.write(prod_requirements)
    
    # Create production startup script
    prod_startup = """#!/usr/bin/env python3
import uvicorn
from config import FASTAPI_CONFIG

if __name__ == "__main__":
    uvicorn.run(
        "fastapi_app:app",
        host="0.0.0.0",
        port=FASTAPI_CONFIG['PORT'],
        workers=4,
        log_level="info"
    )
"""
    
    with open("start_production.py", "w") as f:
        f.write(prod_startup)
    
    # Make it executable
    os.chmod("start_production.py", 0o755)
    
    print("✅ Production configuration created!")
    return True

def create_dockerfile():
    """Create Dockerfile for containerized deployment."""
    print("🐳 Creating Dockerfile...")
    
    dockerfile_content = """# AI Data Chat - Production Dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    default-libmysqlclient-dev \\
    pkg-config \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements_prod.txt .
RUN pip install --no-cache-dir -r requirements_prod.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "start_production.py"]
"""
    
    with open("Dockerfile", "w") as f:
        f.write(dockerfile_content)
    
    # Create docker-compose.yml
    docker_compose = """version: '3.8'

services:
  ai-data-chat:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FASTAPI_ENV=production
      - DB_HOST=mysql
      - DB_USER=root
      - DB_PASSWORD=password
      - DB_NAME=custom
      - DB_PORT=3306
    depends_on:
      - mysql
    restart: unless-stopped

  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=custom
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    restart: unless-stopped

volumes:
  mysql_data:
"""
    
    with open("docker-compose.yml", "w") as f:
        f.write(docker_compose)
    
    print("✅ Docker configuration created!")
    return True

def main():
    """Main build function."""
    print("🏗️ AI Data Chat - Production Build")
    print("=" * 50)
    
    success = True
    
    # Build frontend
    if not build_frontend():
        success = False
    
    # Set up static serving
    if not setup_static_serving():
        success = False
    
    # Create production config
    if not create_production_config():
        success = False
    
    # Create Docker files
    if not create_dockerfile():
        success = False
    
    if success:
        print("\n🎉 Production build completed successfully!")
        print("\n📋 Next steps:")
        print("1. Install production dependencies: pip install -r requirements_prod.txt")
        print("2. Start production server: python start_production.py")
        print("3. Or use Docker: docker-compose up -d")
        print("\n🌐 Production URLs:")
        print("   - API: http://localhost:8000")
        print("   - Docs: http://localhost:8000/docs")
        print("   - Health: http://localhost:8000/health")
        return 0
    else:
        print("\n❌ Production build failed!")
        return 1

if __name__ == "__main__":
    exit(main())
