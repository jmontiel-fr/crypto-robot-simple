#!/usr/bin/env python3
"""
Stop Background HTTPS Server

This script stops the background HTTPS server.
"""

import os
import sys
import signal
from pathlib import Path

def stop_background_server():
    """Stop the background HTTPS server"""
    
    print("🛑 STOPPING BACKGROUND HTTPS SERVER")
    print("=" * 50)
    
    pid_file = Path("server.pid")
    
    if not pid_file.exists():
        print("❌ No server PID file found")
        print("   Server is not running or was not started with background script")
        return False
    
    try:
        # Read PID
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        print(f"🔍 Found server PID: {pid}")
        
        # Try to terminate the process
        try:
            if os.name == 'nt':  # Windows
                os.kill(pid, signal.SIGTERM)
            else:  # Unix/Linux
                os.kill(pid, signal.SIGTERM)
            
            print(f"✅ Sent termination signal to process {pid}")
            
            # Wait a moment
            import time
            time.sleep(2)
            
            # Check if process is still running
            try:
                os.kill(pid, 0)
                print(f"⚠️  Process still running, forcing termination...")
                os.kill(pid, signal.SIGKILL if os.name != 'nt' else signal.SIGTERM)
                time.sleep(1)
            except OSError:
                pass  # Process is gone
            
            print(f"✅ Server stopped successfully")
            
        except OSError as e:
            if e.errno == 3:  # No such process
                print(f"⚠️  Process {pid} was not running")
            else:
                print(f"❌ Error stopping process {pid}: {e}")
                return False
        
        # Remove PID file
        pid_file.unlink()
        print(f"🧹 Removed PID file")
        
        return True
        
    except Exception as e:
        print(f"❌ Error stopping server: {e}")
        return False

if __name__ == "__main__":
    success = stop_background_server()
    
    if success:
        print(f"\n🎉 Background server stopped successfully")
    else:
        print(f"\n💥 Failed to stop background server")
        sys.exit(1)