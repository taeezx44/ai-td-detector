#!/usr/bin/env python3
"""
WSGI entry point for AI-TD Detector Web Dashboard

Production-ready WSGI configuration for deployment on:
- Heroku
- Render
- DigitalOcean App Platform
- AWS Elastic Beanstalk
- Google Cloud Platform
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "engine"))

# Import Flask app
from app import app

# Production WSGI configuration
if __name__ == "__main__":
    # Development mode (direct execution)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
else:
    # Production WSGI mode
    # Configure app for production
    app.debug = False
    
    # Set secure headers
    @app.after_request
    def set_secure_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    # Export app for WSGI server
    application = app
