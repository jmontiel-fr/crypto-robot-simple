#!/usr/bin/env python3
"""
Start HTTPS Server in Background - Protected Fixed Sim6 v3.0

This script starts the HTTPS server in the background and keeps it running.
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def start_background_server():
    """Start the HTTPS server in background"""
    
    print("🚀 STARTING HTTPS SERVER IN BACKGROUND")
    print("=" * 50)
    print("🎯 Protected Fixed Sim6 v3.0 - Background Mode")
    
    # Check if server is already running
    pid_file = Path("server.pid")
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Check if process is still running
            try:
                os.kill(old_pid, 0)  # Check if process exists
                print(f"⚠️  Server already running with PID {old_pid}")
                print(f"   Use 'python stop_background_server.py' to stop it first")
                return False
            except OSError:
                # Process doesn't exist, remove stale PID file
                pid_file.unlink()
                print("🧹 Removed stale PID file")
        except Exception as e:
            print(f"⚠️  Error checking existing server: {e}")
    
    try:
        # Start the server in background
        print("🔧 Starting HTTPS server process...")
        
        # Use subprocess to start the server in background
        process = subprocess.Popen([
            sys.executable, 'start_https_server.py'
        ], 
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        
        # Save PID for later stopping
        with open(pid_file, 'w') as f:
            f.write(str(process.pid))
        
        # Wait a moment to check if it started successfully
        time.sleep(3)
        
        if process.poll() is None:
            print(f"✅ HTTPS Server started successfully!")
            print(f"   PID: {process.pid}")
            print(f"   URL: https://crypto-robot.local:5000")
            print(f"   Fixed Sim6 Dashboard: https://crypto-robot.local:5000/fixed-sim6")
            print(f"   Log file: server.log")
            
            print(f"\n🎯 PROTECTED FIXED SIM6 V3.0 ACTIVE:")
            print(f"   • USDC Protection: Enabled")
            print(f"   • Market Regime Detection: Active")
            print(f"   • Risk Management: Enhanced")
            print(f"   • Background Mode: Running")
            
            print(f"\n🔧 MANAGEMENT COMMANDS:")
            print(f"   Stop server: python stop_background_server.py")
            print(f"   Check status: python check_server_status.py")
            print(f"   View logs: type server.log")
            
            return True
        else:
            # Process failed to start
            stdout, stderr = process.communicate()
            print(f"❌ Failed to start server")
            print(f"   Exit code: {process.returncode}")
            if stderr:
                print(f"   Error: {stderr.decode()}")
            
            # Clean up PID file
            if pid_file.exists():
                pid_file.unlink()
            
            return False
            
    except Exception as e:
        print(f"❌ Error starting background server: {e}")
        
        # Clean up PID file
        if pid_file.exists():
            pid_file.unlink()
        
        return False

if __name__ == "__main__":
    success = start_background_server()
    
    if success:
        print(f"\n🎉 SUCCESS! HTTPS Server running in background")
        print(f"   Access your dashboard at: https://crypto-robot.local:5000")
    else:
        print(f"\n💥 FAILED to start background server")
        sys.exit(1)