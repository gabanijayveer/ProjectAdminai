#!/usr/bin/env python3
"""
FastAPI Application Runner
Replaces the Flask development server with uvicorn for FastAPI
"""

import uvicorn
import webbrowser
import time
import threading
from config import FASTAPI_CONFIG, FRONTEND_CONFIG

def open_browser():
    """Open browser after a short delay to ensure server is running."""
    time.sleep(2)  # Wait 2 seconds for server to start
    url = f"http://{FASTAPI_CONFIG['HOST']}:{FASTAPI_CONFIG['PORT']}"
    if FASTAPI_CONFIG['HOST'] == '0.0.0.0':
        url = f"http://localhost:{FASTAPI_CONFIG['PORT']}"
    
    print(f"🌐 Opening browser at: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"⚠️ Could not open browser automatically: {e}")
        print(f"📱 Please manually open: {url}")

def main():
    """Main function to run the FastAPI application."""
    print("🚀 Starting AI Data Chat FastAPI Application...")
    print(f"📊 App Name: {FRONTEND_CONFIG['APP_NAME']}")
    print(f"📦 Version: {FRONTEND_CONFIG['APP_VERSION']}")
    print(f"🌐 Host: {FASTAPI_CONFIG['HOST']}")
    print(f"🔌 Port: {FASTAPI_CONFIG['PORT']}")
    print(f"🔧 Debug Mode: {FASTAPI_CONFIG['DEBUG']}")
    print(f"🔄 Auto Reload: {FASTAPI_CONFIG['RELOAD']}")
    
    # Open browser automatically if configured
    if FRONTEND_CONFIG.get('AUTO_OPEN_BROWSER', True):
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
    
    # Run the FastAPI application with uvicorn
    try:
        uvicorn.run(
            "fastapi_app:app",
            host=FASTAPI_CONFIG['HOST'],
            port=FASTAPI_CONFIG['PORT'],
            reload=FASTAPI_CONFIG['RELOAD'],
            workers=FASTAPI_CONFIG['WORKERS'] if not FASTAPI_CONFIG['RELOAD'] else 1,
            log_level="info" if not FASTAPI_CONFIG['DEBUG'] else "debug",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
