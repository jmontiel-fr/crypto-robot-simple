#!/usr/bin/env python3
"""
Simple HTTPS web app runner for Protected Fixed Sim6 v3.0
Avoids Unicode issues on Windows
"""
import os
import sys
import ssl
from flask import Flask
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.web_app import app, socketio

def create_ssl_context():
    """Create SSL context for HTTPS with self-signed certificates"""
    ssl_cert_path = os.getenv('SSL_CERT_PATH', 'certs/cert.pem')
    ssl_key_path = os.getenv('SSL_KEY_PATH', 'certs/key.pem')
    
    # Create SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(ssl_cert_path, ssl_key_path)
    return context

def run_simple_https():
    """Run Flask app with HTTPS support - simple version"""
    port = int(os.getenv('FLASK_PORT', 5000))
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    domain_name = os.getenv('DOMAIN_NAME', 'crypto-robot.local')
    use_https = os.getenv('USE_HTTPS', 'true').lower() == 'true'
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("Starting Crypto Robot Web App (HTTPS Mode)")
    print(f"Domain: {domain_name}")
    print(f"HTTPS: {'Enabled' if use_https else 'Disabled'}")
    print(f"Binding to: {host}:{port}")
    print(f"Debug mode: {debug}")
    print("Real-time updates: Enabled (Flask-SocketIO)")
    print("=" * 60)
    
    # Configure for production
    app.config['DEBUG'] = debug
    app.config['TESTING'] = False
    app.config['ENV'] = os.getenv('FLASK_ENV', 'production')
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'crypto-robot-secret-key-change-this')
    app.config['DOMAIN_NAME'] = domain_name
    app.config['USE_HTTPS'] = use_https
    
    try:
        if use_https:
            # Create SSL context
            ssl_context = create_ssl_context()
            
            print(f"SSL Certificate: {os.getenv('SSL_CERT_PATH', 'certs/cert.pem')}")
            print(f"SSL Private Key: {os.getenv('SSL_KEY_PATH', 'certs/key.pem')}")
            print(f"Access URL: https://{domain_name}:{port}")
            print(f"Dashboard: https://{domain_name}:{port}/fixed-sim6")
            print("")
            print("PROTECTED FIXED SIM6 V3.0 ACTIVE")
            print("The only strategy you need!")
            print("")
            
            # Run with HTTPS
            socketio.run(
                app, 
                host=host, 
                port=port, 
                debug=debug,
                ssl_context=ssl_context,
                use_reloader=False,
                log_output=True
            )
        else:
            print(f"Access URL: http://{domain_name}:{port}")
            
            # Run without HTTPS
            socketio.run(
                app, 
                host=host, 
                port=port, 
                debug=debug,
                use_reloader=False,
                log_output=True
            )
            
    except FileNotFoundError as e:
        print(f"SSL Certificate Error: {e}")
        print("Generate self-signed certificates with:")
        print("   python generate_ssl_cert.py")
        sys.exit(1)
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_simple_https()