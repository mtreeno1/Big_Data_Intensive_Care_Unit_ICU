# scripts/setup_complete_system.py
"""
Complete setup for ICU monitoring system
"""
import subprocess
import sys
from pathlib import Path
import time

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def run_command(cmd, description, check_output=False):
    """Run shell command"""
    print(f"\n🔧 {description}...")
    
    try:
        if check_output:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"✅ {description} - Success")
                if result.stdout:
                    print(result.stdout[:500])  # Limit output
                return True
            else:
                print(f"❌ {description} - Failed")
                if result.stderr:
                    print(result.stderr[:500])
                return False
        else:
            subprocess.run(cmd, shell=True, check=True)
            print(f"✅ {description} - Success")
            return True
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - Timeout")
        return False
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False

def main():
    print_header("ICU MONITORING SYSTEM - COMPLETE SETUP")
    
    steps = [
        # Step 1: Check Docker
        {
            'cmd': 'docker --version',
            'desc': 'Check Docker installation',
            'required': True
        },
        
        # Step 2: Start Docker containers
        {
            'cmd': 'docker-compose up -d',
            'desc': 'Start Kafka, PostgreSQL, InfluxDB',
            'required': True
        },
        
        # Step 3: Wait for services
        {
            'cmd': 'sleep 15',
            'desc': 'Wait for services to start',
            'required': True
        },
        
        # Step 4: Initialize databases
        {
            'cmd': 'python scripts/init_databases.py',
            'desc': 'Initialize PostgreSQL tables',
            'required': True
        },
        
        # Step 5: Load ICU patients
        {
            'cmd': 'python scripts/load_icu_patients.py --limit 50',
            'desc': 'Load 50 ICU patients from VitalDB data',
            'required': True
        },
        
        # Step 6: Check Kafka
        {
            'cmd': 'python scripts/monitor_kafka.py',
            'desc': 'Verify Kafka connection',
            'required': False
        }
    ]
    
    failed_steps = []
    
    for step in steps:
        success = run_command(step['cmd'], step['desc'], check_output=True)
        
        if not success and step['required']:
            failed_steps.append(step['desc'])
    
    # Summary
    print_header("SETUP SUMMARY")
    
    if failed_steps:
        print("\n❌ Setup completed with errors:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\n💡 Fix the errors above and run setup again")
        sys.exit(1)
    else:
        print("\n✅ Setup completed successfully!")
        print("\n📊 System is ready to use!")
        print("\nNext steps:")
        print("  1. Start Producer (Terminal 1):")
        print("     python scripts/run_producer.py")
        print("\n  2. Start Consumer (Terminal 2):")
        print("     python scripts/run_consumer.py")
        print("\n  3. Open Dashboard (Terminal 3):")
        print("     streamlit run src/dashboard/streamlit_app.py")
        print("\n" + "="*70)

if __name__ == "__main__":
    main()