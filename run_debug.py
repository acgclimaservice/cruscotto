#!/usr/bin/env python3
"""
Run Flask server in debug mode with enhanced logging
"""

from app import app
import logging
import sys

def setup_logging():
    """Setup enhanced logging"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('debug_offerte.log')
        ]
    )

if __name__ == "__main__":
    print("🔍 Starting Flask server in DEBUG mode...")
    print("📝 Logs will be saved to debug_offerte.log")
    print("🌐 Server will run on http://localhost:5000")
    print("\nLook for [DEBUG] and [ERROR] messages to track offerte requests\n")
    
    setup_logging()
    
    # Enable Flask debugging only if in development
    debug_mode = False  # Set to True only for local development
    app.config['DEBUG'] = debug_mode
    app.config['TESTING'] = False

    # Run server
    app.run(host='0.0.0.0', port=5000, debug=debug_mode, use_reloader=False)