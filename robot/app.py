"""
Thin wrapper to expose the full web application from src/web_app.py.
Ensures all routes (including /api/* and /simulator) work consistently.
"""
import os
import sys

# Ensure project root and src are on the path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
for p in (PROJECT_ROOT, SRC_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    # Prefer the full-featured app with Socket.IO and all routes
    from src.web_app import app as app  # noqa: F401
    try:
        # If available, also import socketio so running this file directly uses it
        from src.web_app import socketio  # type: ignore
    except Exception:
        socketio = None  # type: ignore
except Exception as e:
    # Minimal fallback app (should not be used in normal flow)
    print(f"[app.py] WARNING: Failed to import src.web_app ({e}). Falling back to minimal app - API routes unavailable.")
    from flask import Flask, render_template
    app = Flask(__name__)

    @app.route('/')
    def home():
        return render_template('index.html')


def check_binance_keys():
    """Optional Binance key validation - only for live trading"""
    import os
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_SECRET_KEY')
        
        # Allow running without keys for testing/simulations
        if not api_key or not api_secret or api_key == 'your_binance_api_key_here':
            print('⚠️  WARNING: Binance API keys not configured.')
            print('   Web interface will work for simulations only.')
            print('   Configure .env file for live trading.')
            return False
            
        # Only validate if keys are provided
        from binance.client import Client
        client = Client(api_key, api_secret)
        status = client.get_account_status()
        print('✅ Binance API keys are valid. Account status:', status)
        return True
    except Exception as e:
        print('⚠️  WARNING: Binance API keys validation failed.')
        print('   Web interface will work for simulations only.')
        print(f'   Error: {e}')
        return False

if __name__ == "__main__":
    print("🚀 Starting Crypto Robot Web Interface (Development Mode)")
    print("=" * 60)
    
    # Load environment variables for dynamic configuration
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get configuration from .env with fallbacks
    flask_port = int(os.getenv('FLASK_PORT', 5000))
    flask_host = os.getenv('FLASK_HOST', '0.0.0.0')
    flask_debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    flask_protocol = os.getenv('FLASK_PROTOCOL', 'http')
    use_https = os.getenv('USE_HTTPS', 'false').lower() == 'true'
    
    print(f"Configuration from .env:")
    print(f"  Host: {flask_host}")
    print(f"  Port: {flask_port}")
    print(f"  Protocol: {flask_protocol}")
    print(f"  Debug: {flask_debug}")
    print(f"  HTTPS: {use_https}")
    
    # Optional key check - don't exit if failed
    check_binance_keys()
    
    # Determine if HTTPS should be used
    enable_https = (flask_protocol.lower() == 'https') or use_https
    
    # Run with Socket.IO if available, else plain Flask
    if 'socketio' in globals() and socketio is not None:
        if enable_https:
            # Use HTTPS with SSL context
            import ssl
            from src.web_app_https import get_certificate_path
            
            try:
                hostname = os.getenv('HOSTNAME', os.getenv('DOMAIN_NAME', 'crypto-robot.local'))
                cert_path = get_certificate_path(hostname, 'cert.pem')
                key_path = get_certificate_path(hostname, 'key.pem')
                
                context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
                context.load_cert_chain(cert_path, key_path)
                
                print(f"🔒 HTTPS enabled with certificates for {hostname}")
                print(f"🌍 Access URL: https://{hostname}:{flask_port}")
                
                socketio.run(app, host=flask_host, port=flask_port, debug=flask_debug, 
                           ssl_context=context, allow_unsafe_werkzeug=True)
            except Exception as e:
                print(f"⚠️ HTTPS setup failed: {e}")
                print(f"🌍 Falling back to HTTP: http://{flask_host}:{flask_port}")
                socketio.run(app, host=flask_host, port=flask_port, debug=flask_debug, 
                           allow_unsafe_werkzeug=True)
        else:
            print(f"🌍 Access URL: http://{flask_host}:{flask_port}")
            socketio.run(app, host=flask_host, port=flask_port, debug=flask_debug, 
                       allow_unsafe_werkzeug=True)
    else:
        if enable_https:
            print("⚠️ HTTPS requested but Socket.IO not available, falling back to HTTP")
        print(f"🌍 Access URL: http://{flask_host}:{flask_port}")
        app.run(host=flask_host, port=flask_port, debug=flask_debug)

