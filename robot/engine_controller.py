#!/usr/bin/env python3
"""
Engine Controller for Crypto Robot
Manages automated trading engine lifecycle and monitoring
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.append(str(Path(__file__).parent / 'src'))

class EngineController:
    """Controller for managing the crypto robot engine"""
    
    def __init__(self):
        self.pid_file = Path('data/robot.pid')
        self.log_file = Path('logs/engine.log')
        self.status_file = Path('data/engine_status.json')
        
        # Ensure directories exist
        self.pid_file.parent.mkdir(exist_ok=True)
        self.log_file.parent.mkdir(exist_ok=True)
        self.status_file.parent.mkdir(exist_ok=True)
    
    def is_running(self):
        """Check if the engine is currently running"""
        if not self.pid_file.exists():
            return False
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is still running
            try:
                os.kill(pid, 0)  # Signal 0 just checks if process exists
                return True
            except OSError:
                # Process doesn't exist, clean up stale PID file
                self.pid_file.unlink()
                return False
                
        except (ValueError, FileNotFoundError):
            return False
    
    def get_status(self):
        """Get current engine status"""
        if self.is_running():
            try:
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Try to get status from status file
                if self.status_file.exists():
                    import json
                    with open(self.status_file, 'r') as f:
                        status_data = json.load(f)
                    
                    status_data['pid'] = pid
                    status_data['status'] = 'running'
                    return status_data
                else:
                    return {
                        'status': 'running',
                        'pid': pid,
                        'start_time': 'unknown'
                    }
            except:
                return {'status': 'unknown'}
        else:
            return {'status': 'stopped'}
    
    def start(self):
        """Start the crypto robot engine"""
        if self.is_running():
            print("⚠️  Engine is already running!")
            status = self.get_status()
            print(f"   PID: {status.get('pid', 'unknown')}")
            return False
        
        print("🚀 Starting Crypto Robot Engine...")
        
        try:
            # Start the robot in background
            process = subprocess.Popen([
                sys.executable, 'main.py', '--mode', 'robot'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Save PID
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # Save initial status
            import json
            status_data = {
                'status': 'starting',
                'start_time': datetime.now().isoformat(),
                'pid': process.pid
            }
            
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
            
            # Wait a moment to see if it starts successfully
            time.sleep(2)
            
            if process.poll() is None:  # Still running
                print(f"✅ Engine started successfully!")
                print(f"   PID: {process.pid}")
                print(f"   Log file: {self.log_file}")
                return True
            else:
                # Process died immediately
                stdout, stderr = process.communicate()
                print(f"❌ Engine failed to start!")
                if stderr:
                    print(f"   Error: {stderr.decode()}")
                
                # Clean up
                if self.pid_file.exists():
                    self.pid_file.unlink()
                
                return False
                
        except Exception as e:
            print(f"❌ Failed to start engine: {e}")
            return False
    
    def stop(self):
        """Stop the crypto robot engine"""
        if not self.is_running():
            print("⚠️  Engine is not running")
            return True
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            print(f"🛑 Stopping engine (PID: {pid})...")
            
            # Try graceful shutdown first
            os.kill(pid, signal.SIGTERM)
            
            # Wait for graceful shutdown
            for i in range(10):
                try:
                    os.kill(pid, 0)
                    time.sleep(1)
                except OSError:
                    break
            else:
                # Force kill if still running
                print("   Forcing shutdown...")
                os.kill(pid, signal.SIGKILL)
            
            # Clean up files
            if self.pid_file.exists():
                self.pid_file.unlink()
            
            if self.status_file.exists():
                self.status_file.unlink()
            
            print("✅ Engine stopped successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error stopping engine: {e}")
            return False
    
    def restart(self):
        """Restart the crypto robot engine"""
        print("🔄 Restarting Crypto Robot Engine...")
        
        if self.is_running():
            if not self.stop():
                return False
            
            # Wait a moment between stop and start
            time.sleep(2)
        
        return self.start()
    
    def monitor(self):
        """Monitor the engine in real-time"""
        print("📊 Monitoring Crypto Robot Engine (Press Ctrl+C to stop)")
        print("=" * 60)
        
        try:
            while True:
                status = self.get_status()
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                if status['status'] == 'running':
                    print(f"[{timestamp}] ✅ Engine running (PID: {status.get('pid', 'unknown')})")
                    
                    # Try to get additional info
                    try:
                        from robot_state import RobotState
                        robot_state = RobotState()
                        state_info = robot_state.get_status()
                        
                        if state_info:
                            print(f"           💰 Portfolio: {state_info.get('total_value', 'N/A')}")
                            print(f"           📈 Last Trade: {state_info.get('last_trade_time', 'N/A')}")
                    except:
                        pass
                        
                else:
                    print(f"[{timestamp}] ❌ Engine not running")
                
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            print(f"\n🛑 Monitoring stopped")

def main():
    """Main controller function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Crypto Robot Engine Controller')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'monitor'],
                       help='Action to perform')
    
    args = parser.parse_args()
    
    controller = EngineController()
    
    print("🤖 Crypto Robot - Engine Controller")
    print("=" * 40)
    
    if args.action == 'start':
        controller.start()
    elif args.action == 'stop':
        controller.stop()
    elif args.action == 'restart':
        controller.restart()
    elif args.action == 'status':
        status = controller.get_status()
        print(f"Status: {status['status']}")
        if status['status'] == 'running':
            print(f"PID: {status.get('pid', 'unknown')}")
            print(f"Start Time: {status.get('start_time', 'unknown')}")
    elif args.action == 'monitor':
        controller.monitor()

if __name__ == '__main__':
    main()