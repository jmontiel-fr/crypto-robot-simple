"""
Direct production web interface with HTTPS support using self-signed certificates
No nginx required - Flask handles HTTPS directly
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

def get_certificate_path(hostname, filename):
    """Get certificate path based on hostname with fallback to legacy paths"""
    # Docker-style certificate structure: certificates/<hostname>/
    docker_cert_path = os.path.join('certificates', hostname, filename)
    
    # Legacy certificate paths
    legacy_cert_path = os.getenv('SSL_CERT_PATH' if filename == 'cert.pem' else 'SSL_KEY_PATH', 
                                 f'certs/{filename}')
    
    # Check Docker-style path first (for containerized deployment)
    if os.path.exists(docker_cert_path):
        return docker_cert_path
    
    # Fallback to legacy path (for direct execution)
    if os.path.exists(legacy_cert_path):
        return legacy_cert_path
    
    # If neither exists, return Docker path (will cause error with helpful message)
    return docker_cert_path

def create_ssl_context():
    """Create SSL context for HTTPS with legacy certificate paths (backward compatibility)"""
    ssl_cert_path = os.getenv('SSL_CERT_PATH', 'certs/cert.pem')
    ssl_key_path = os.getenv('SSL_KEY_PATH', 'certs/key.pem')
    
    # Create SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(ssl_cert_path, ssl_key_path)
    return context

def create_ssl_context_for_hostname(hostname):
    """Create SSL context for HTTPS with hostname-based certificate selection"""
    cert_path = get_certificate_path(hostname, 'cert.pem')
    key_path = get_certificate_path(hostname, 'key.pem')
    
    # Create SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(cert_path, key_path)
    return context

def run_https_production():
    """Run Flask app with dynamic configuration from .env"""
    # Read all configuration from .env file
    port = int(os.getenv('FLASK_PORT', 5000))
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    protocol = os.getenv('FLASK_PROTOCOL', 'https')
    domain_name = os.getenv('DOMAIN_NAME', 'crypto-robot.local')
    hostname = os.getenv('HOSTNAME', domain_name)  # Docker certificate selection
    use_https = os.getenv('USE_HTTPS', 'true').lower() == 'true'
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Determine if HTTPS should be used based on protocol or use_https flag
    enable_https = (protocol.lower() == 'https') or use_https
    
    print(f"Starting Crypto Robot Web App")
    print(f"Configuration source: .env file")
    print(f"Domain: {domain_name}")
    print(f"Hostname: {hostname}")
    print(f"Protocol: {protocol.upper()}")
    print(f"HTTPS: {'Enabled' if enable_https else 'Disabled'}")
    print(f"Binding to: {host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"Real-time updates: Enabled (Flask-SocketIO)")
    print("=" * 60)
    
    # Configure Flask app with .env values
    app.config['DEBUG'] = debug
    app.config['TESTING'] = False
    app.config['ENV'] = os.getenv('FLASK_ENV', 'production')
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'crypto-robot-secret-key-change-this')
    app.config['DOMAIN_NAME'] = domain_name
    app.config['HOSTNAME'] = hostname
    app.config['USE_HTTPS'] = enable_https
    app.config['FLASK_PORT'] = port
    app.config['FLASK_HOST'] = host
    app.config['FLASK_PROTOCOL'] = protocol
    
    try:
        if enable_https:
            # Create SSL context with certificate selection based on hostname
            ssl_context = create_ssl_context_for_hostname(hostname)
            
            cert_path = get_certificate_path(hostname, 'cert.pem')
            key_path = get_certificate_path(hostname, 'key.pem')
            
            print(f"SSL Certificate: {cert_path}")
            print(f"SSL Private Key: {key_path}")
            print(f"Access URL: https://{hostname}:{port}")
            
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
            print(f"🌍 Access URL: http://{hostname}:{port}")
            
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
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_https_production()
