#!/usr/bin/env python3
"""
Network-enabled startup script for AI Data Chat
Starts both FastAPI backend and React frontend with network access
"""

import subprocess
import sys
import time
import threading
import webbrowser
import socket
import os
from pathlib import Path

def get_local_ip():
    """Get the local network IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "192.168.1.8"  # Fallback to your detected IP

def start_backend():
    """Start the FastAPI backend server with network access."""
    print("🚀 Starting FastAPI backend server...")
    try:
        # Set environment for development
        env = os.environ.copy()
        env['FASTAPI_ENV'] = 'development'
        
        subprocess.run([
            sys.executable, "run_fastapi.py"
        ], env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Backend server failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")

def start_frontend():
    """Start the React frontend development server with network access."""
    print("⚛️ Starting React frontend server with network access...")
    frontend_dir = Path("frontend")

    if not frontend_dir.exists():
        print("❌ Frontend directory not found. Please run this script from the project root.")
        sys.exit(1)

    try:
        # Set environment variables for network access
        env = os.environ.copy()
        env['HOST'] = '0.0.0.0'  # Allow network access
        env['PORT'] = '3000'
        env['REACT_APP_API_URL'] = f'http://{get_local_ip()}:8000'  # Point to network backend

        print(f"🌐 Frontend will be accessible at:")
        print(f"   Local: http://localhost:3000")
        print(f"   Network: http://{get_local_ip()}:3000")

        subprocess.run([
            "npm", "start"
        ], cwd=frontend_dir, env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Frontend server failed: {e}")
        print("💡 Try running: cd frontend && npm install")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped")

def open_browser_delayed():
    """Open browser after servers have started."""
    time.sleep(5)  # Wait for servers to start
    local_ip = get_local_ip()
    print("🌐 Opening browser...")
    try:
        webbrowser.open(f"http://{local_ip}:3000")
    except Exception as e:
        print(f"⚠️ Could not open browser: {e}")
        print(f"📱 Please manually open: http://{local_ip}:3000")

def check_prerequisites():
    """Check if all prerequisites are met."""
    print("🔍 Checking prerequisites...")
    
    # Check Python
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print("✅ Python version OK")
    
    # Check Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js version: {result.stdout.strip()}")
        else:
            print("❌ Node.js not found")
            return False
    except FileNotFoundError:
        print("❌ Node.js not found. Please install Node.js 16+")
        return False
    
    # Check npm
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm version: {result.stdout.strip()}")
        else:
            print("❌ npm not found")
            return False
    except FileNotFoundError:
        print("❌ npm not found")
        return False
    
    # Check frontend dependencies
    frontend_dir = Path("frontend")
    if not (frontend_dir / "node_modules").exists():
        print("⚠️ Frontend dependencies not installed")
        print("💡 Installing frontend dependencies...")
        try:
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
            print("✅ Frontend dependencies installed")
        except subprocess.CalledProcessError:
            print("❌ Failed to install frontend dependencies")
            return False
    else:
        print("✅ Frontend dependencies OK")
    
    return True

def main():
    """Main function to start network-enabled development environment."""
    local_ip = get_local_ip()

    print("🌐 AI Data Chat - Network Development Environment")
    print("=" * 70)
    print("📱 LOCAL ACCESS:")
    print("🔹 Backend API: http://localhost:8000")
    print("🔹 Frontend App: http://localhost:3000")
    print("🔹 API Docs: http://localhost:8000/docs")
    print("\n🌐 NETWORK ACCESS:")
    print(f"🔹 Backend API: http://{local_ip}:8000")
    print(f"🔹 Frontend App: http://{local_ip}:3000")
    print(f"🔹 API Docs: http://{local_ip}:8000/docs")
    print("=" * 70)
    print("🔐 Default Login: admin@example.com / admin123")
    print("=" * 70)
    
    # Check prerequisites
    if not check_prerequisites():
        print("❌ Prerequisites not met. Please fix the issues above.")
        return 1
    
    # Start browser opener in background
    browser_thread = threading.Thread(target=open_browser_delayed)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start backend in background
    backend_thread = threading.Thread(target=start_backend)
    backend_thread.daemon = True
    backend_thread.start()
    
    # Give backend time to start
    print("⏳ Starting backend server...")
    time.sleep(3)
    
    # Start frontend (this will block)
    try:
        start_frontend()
    except KeyboardInterrupt:
        print("\n🛑 Development environment stopped")
        return 0

if __name__ == "__main__":
    exit(main())
