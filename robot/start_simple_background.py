#!/usr/bin/env python3
"""
Simple Background Server Starter - No Unicode Issues

Starts the web server in background without emoji characters.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def start_simple_background():
    """Start the web server in background"""
    
    print("STARTING HTTPS SERVER IN BACKGROUND")
    print("=" * 50)
    print("Protected Fixed Sim6 v3.0 - Background Mode")
    
    # Check if server is already running
    pid_file = Path("server.pid")
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Check if process is still running
            try:
                os.kill(old_pid, 0)  # Check if process exists
                print(f"Server already running with PID {old_pid}")
                print("Use 'python stop_background_server.py' to stop it first")
                return False
            except OSError:
                # Process doesn't exist, remove stale PID file
                pid_file.unlink()
                print("Removed stale PID file")
        except Exception as e:
            print(f"Error checking existing server: {e}")
    
    try:
        # Start the web app directly
        print("Starting web server process...")
        
        # Use subprocess to start the server in background
        process = subprocess.Popen([
            sys.executable, 'src/web_app.py'
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
            print("HTTPS Server started successfully!")
            print(f"PID: {process.pid}")
            print("URL: http://localhost:5000")
            print("Fixed Sim6 Dashboard: http://localhost:5000/fixed-sim6")
            
            print("\nPROTECTED FIXED SIM6 V3.0 ACTIVE:")
            print("  - USDC Protection: Enabled")
            print("  - Market Regime Detection: Active")
            print("  - Risk Management: Enhanced")
            print("  - Background Mode: Running")
            
            print("\nMANAGEMENT COMMANDS:")
            print("  Stop server: python stop_background_server.py")
            print("  Check status: python check_server_status.py")
            
            return True
        else:
            # Process failed to start
            stdout, stderr = process.communicate()
            print("Failed to start server")
            print(f"Exit code: {process.returncode}")
            if stderr:
                print(f"Error: {stderr.decode()}")
            
            # Clean up PID file
            if pid_file.exists():
                pid_file.unlink()
            
            return False
            
    except Exception as e:
        print(f"Error starting background server: {e}")
        
        # Clean up PID file
        if pid_file.exists():
            pid_file.unlink()
        
        return False

if __name__ == "__main__":
    success = start_simple_background()
    
    if success:
        print("\nSUCCESS! HTTPS Server running in background")
        print("Access your dashboard at: http://localhost:5000")
    else:
        print("\nFAILED to start background server")
        sys.exit(1)