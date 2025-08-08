#!/usr/bin/env python3
"""
Frontend-only startup script for AI Data Chat React application
"""

import subprocess
import sys
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
        return "192.168.1.8"

def main():
    """Start only the React frontend server."""
    print("⚛️ Starting React Frontend Only...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found. Please run this script from the project root.")
        return 1

    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print("📦 Installing frontend dependencies...")
        try:
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return 1

    local_ip = get_local_ip()
    
    print("🌐 Frontend Server Configuration:")
    print(f"📱 Local Access: http://localhost:3000")
    print(f"🌐 Network Access: http://{local_ip}:3000")
    print(f"🔗 Backend API: http://{local_ip}:8000")
    print("=" * 50)
    print("⚠️ Make sure the backend is running on port 8000")
    print("💡 Run 'python run_fastapi.py' in another terminal")
    print("=" * 50)

    try:
        # Set environment variables for network access
        env = os.environ.copy()
        env['HOST'] = '0.0.0.0'  # Allow network access
        env['PORT'] = '3000'
        env['REACT_APP_API_URL'] = f'http://{local_ip}:8000'

        subprocess.run([
            "npm", "start"
        ], cwd=frontend_dir, env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Frontend server failed: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped")
        return 0

if __name__ == "__main__":
    exit(main())
