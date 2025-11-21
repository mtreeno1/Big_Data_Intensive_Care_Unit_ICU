#!/usr/bin/env python3
"""
Monitor All - Chạy tất cả monitors trong các terminal khác nhau
"""

import sys
import subprocess
import time
from pathlib import Path


def main():
    print("=" * 80)
    print("🚀 STARTING ALL MONITORS")
    print("=" * 80)
    print()
    
    scripts_dir = Path(__file__).parent
    
    # Instructions
    print("📋 This will open 3 monitoring terminals:")
    print("   1️⃣  Kafka Stream Monitor (real-time data)")
    print("   2️⃣  InfluxDB Monitor (time-series data)")
    print("   3️⃣  PostgreSQL Monitor (events & alerts)")
    print()
    print("⚠️  Make sure producer and consumer are running first!")
    print()
    input("Press Enter to continue...")
    
    try:
        # Try to detect terminal emulator
        terminals = [
            'gnome-terminal',
            'xterm',
            'konsole',
            'xfce4-terminal',
            'mate-terminal',
            'terminator'
        ]
        
        terminal_cmd = None
        for term in terminals:
            if subprocess.run(['which', term], capture_output=True).returncode == 0:
                terminal_cmd = term
                break
        
        if not terminal_cmd:
            print("❌ No terminal emulator found!")
            print("   Please run these commands manually in separate terminals:")
            print(f"   1. python {scripts_dir}/monitor_kafka.py")
            print(f"   2. python {scripts_dir}/monitor_influxdb.py")
            print(f"   3. python {scripts_dir}/monitor_postgres.py")
            return
        
        # Launch terminals
        print(f"✅ Using terminal: {terminal_cmd}")
        print()
        
        monitors = [
            ('Kafka Monitor', 'monitor_kafka.py'),
            ('InfluxDB Monitor', 'monitor_influxdb.py'),
            ('PostgreSQL Monitor', 'monitor_postgres.py')
        ]
        
        for name, script in monitors:
            print(f"🚀 Launching {name}...")
            
            if terminal_cmd == 'gnome-terminal':
                subprocess.Popen([
                    terminal_cmd,
                    '--',
                    sys.executable,
                    str(scripts_dir / script)
                ])
            elif terminal_cmd in ['xterm', 'konsole', 'xfce4-terminal']:
                subprocess.Popen([
                    terminal_cmd,
                    '-e',
                    f'{sys.executable} {scripts_dir / script}'
                ])
            else:
                subprocess.Popen([
                    terminal_cmd,
                    '-e',
                    sys.executable,
                    str(scripts_dir / script)
                ])
            
            time.sleep(1)
        
        print()
        print("✅ All monitors launched!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nManual commands:")
        print(f"   Terminal 1: python {scripts_dir}/monitor_kafka.py")
        print(f"   Terminal 2: python {scripts_dir}/monitor_influxdb.py")
        print(f"   Terminal 3: python {scripts_dir}/monitor_postgres.py")


if __name__ == "__main__":
    main()