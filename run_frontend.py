#!/usr/bin/env python3
"""
AI Data Chat - React Frontend Launcher
Starts the React development server with network access for AI chat with data.
"""

import os
import sys
import subprocess
import webbrowser
import time
import threading
import socket

def get_local_ip():
    """Get the local network IP address."""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "192.168.1.x"

def open_browser():
    """Open the web browser after a short delay."""
    time.sleep(3)
    webbrowser.open('http://localhost:3000')

def main():
    """Main function to start the React development server."""
    print("="*60)
    print("🤖 AI DATA CHAT - REACT FRONTEND")
    print("="*60)
    print("⚛️ Modern React + TypeScript Interface")
    print("� User Authentication & Session Management")
    print("📝 Markdown Rendering for LLM Responses")
    print("🌐 Network Accessible Interface")
    print("="*60)

    # Check if frontend directory exists
    if not os.path.exists('frontend'):
        print("❌ Frontend directory not found!")
        print("💡 Please run this script from the project root directory.")
        return

    if not os.path.exists('frontend/package.json'):
        print("❌ Frontend package.json not found!")
        print("💡 Please ensure the React app is properly set up.")
        return

    # Get network IP
    local_ip = get_local_ip()

    print("✅ React frontend found")
    print("🔗 Starting React development server...")
    print("📱 Local access: http://localhost:3000")
    print(f"🌐 Network access: http://{local_ip}:3000")
    print("🔌 Backend API: http://localhost:8000")
    print("📱 Opening browser automatically...")
    print("\n" + "="*60)
    print("FEATURES AVAILABLE:")
    print("="*60)
    print("🔐 User Authentication: Email/password login system")
    print("🤖 AI Chat: Direct conversation with your data")
    print("� Markdown Rendering: Beautiful LLM response formatting")
    print("� History: Personal query history with search/filter")
    print("⚡ Real-time Status: Live execution monitoring")
    print("💾 Persistent Storage: MySQL database with user accounts")
    print("🌐 Network Access: Available on local network")
    print("🔒 JWT Security: Secure token-based authentication")
    print("="*60)

    # Open browser in a separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()

    try:
        # Start React development server
        print("\n🚀 Starting React development server...")
        print("⚠️  Make sure FastAPI backend is running: python run_fastapi.py")
        print("⚠️  Default login: admin@example.com / admin123")
        print("\n")

        # Change to frontend directory and start npm
        os.chdir('frontend')

        # Set environment variable for network access
        env = os.environ.copy()
        env['HOST'] = '0.0.0.0'  # Allow network access
        env['PORT'] = '3000'

        # Start React dev server
        subprocess.run(['npm', 'start'], env=env, check=True)

    except KeyboardInterrupt:
        print("\n🛑 React development server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting React server: {e}")
        print("💡 Try running: cd frontend && npm install")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("💡 Make sure you're in the project root directory")

if __name__ == '__main__':
    main()
