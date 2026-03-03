#!/usr/bin/env python3
"""
Simple WSGI server for AI-TD Detector Web Dashboard (Windows Compatible)

Usage:
    python simple_wsgi_server.py
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "engine"))

def main():
    """Run simple WSGI server using Flask's built-in server."""
    from app import app
    
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Starting AI-TD Dashboard (Simple WSGI) on port {port}...")
    print("Press Ctrl+C to stop the server")
    print(f"Access: http://localhost:{port}")
    
    try:
        # Use Flask's built-in server (production-ready for small deployments)
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
