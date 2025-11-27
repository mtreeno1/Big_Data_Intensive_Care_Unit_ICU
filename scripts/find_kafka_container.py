"""
Script tìm và test Kafka container
"""
import subprocess
import sys

def find_kafka_container():
    """Find Kafka container name"""
    result = subprocess.run(
        ['docker', 'ps', '--format', '{{.Names}}'],
        capture_output=True,
        text=True
    )
    
    containers = result.stdout.strip().split('\n')
    kafka_containers = [c for c in containers if 'kafka' in c.lower()]
    
    if not kafka_containers:
        print("❌ No Kafka container found!")
        print("\n📋 Running containers:")
        subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Image}}\t{{.Status}}'])
        sys.exit(1)
    
    kafka_container = kafka_containers[0]
    print(f"✅ Found Kafka container: {kafka_container}")
    return kafka_container

def test_kafka_commands(container_name):
    """Test Kafka commands"""
    print("\n" + "="*60)
    print("🧪 Testing Kafka Commands")
    print("="*60)
    
    # 1. List topics
    print("\n1️⃣ Listing topics...")
    subprocess.run([
        'docker', 'exec', '-it', container_name,
        'kafka-topics', '--bootstrap-server', 'localhost:9092', '--list'
    ])
    
    # 2. Describe patient-vital-signs topic
    print("\n2️⃣ Describing patient-vital-signs topic...")
    subprocess.run([
        'docker', 'exec', '-it', container_name,
        'kafka-topics', '--bootstrap-server', 'localhost:9092',
        '--describe', '--topic', 'patient-vital-signs'
    ])
    
    # 3. List consumer groups
    print("\n3️⃣ Listing consumer groups...")
    subprocess.run([
        'docker', 'exec', '-it', container_name,
        'kafka-consumer-groups', '--bootstrap-server', 'localhost:9092', '--list'
    ])
    
    # 4. Describe icu-consumers group
    print("\n4️⃣ Describing icu-consumers group...")
    subprocess.run([
        'docker', 'exec', '-it', container_name,
        'kafka-consumer-groups', '--bootstrap-server', 'localhost:9092',
        '--describe', '--group', 'icu-consumers'
    ])
    
    print("\n" + "="*60)
    print("✅ Tests completed!")
    print("="*60)

if __name__ == "__main__":
    kafka_container = find_kafka_container()
    test_kafka_commands(kafka_container)