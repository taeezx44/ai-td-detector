#!/usr/bin/env python3
"""
Production WSGI server for AI-TD Detector Web Dashboard

Usage:
    python wsgi_server.py
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "engine"))

def main():
    """Run production WSGI server with Gunicorn."""
    import subprocess
    
    # Get port from environment or default to 5000
    port = os.environ.get('PORT', '5000')
    
    # Try to find gunicorn in different locations
    gunicorn_cmd = None
    possible_paths = [
        r'C:\Users\Administrator\AppData\Local\Programs\Python\Python314\Scripts\gunicorn.exe',
        r'C:\Users\Administrator\AppData\Local\Programs\Python\Python314\Scripts\gunicorn',
        'gunicorn'
    ]
    
    for cmd in possible_paths:
        try:
            subprocess.run([cmd, '--version'], capture_output=True, check=True)
            gunicorn_cmd = cmd
            break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    if not gunicorn_cmd:
        print("Error: Gunicorn not found. Please install with: python -m pip install gunicorn")
        sys.exit(1)
    
    # Gunicorn command
    cmd = [
        gunicorn_cmd,
        'wsgi:application',
        '--bind', f'0.0.0.0:{port}',
        '--workers', '3',
        '--timeout', '120',
        '--keepalive', '5',
        '--max-requests', '1000',
        '--max-requests-jitter', '100',
        '--preload',
        '--access-logfile', '-',
        '--error-logfile', '-',
        '--log-level', 'info'
    ]
    
    print(f"Starting AI-TD Dashboard with Gunicorn on port {port}...")
    print(f"Using Gunicorn: {gunicorn_cmd}")
    print("Press Ctrl+C to stop the server")
    
    try:
        subprocess.run(cmd, cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
