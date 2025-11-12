#!/usr/bin/env python3
"""
Run Producer with Real-time Visual Monitoring
Hiển thị trực quan dữ liệu đang streaming
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_generation.patient_simulator import MultiPatientSimulator
from src.kafka_producer.producer import VitalSignsProducer
from config.config import settings

# Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class VisualProducer:
    """Producer với hiển thị trực quan và theo dõi transitions"""
    
    def __init__(self, num_patients: int = 10, interval: float = 1.0):
        self.num_patients = num_patients
        self.interval = interval
        self.stats = {
            'total_sent': 0,
            'total_failed': 0,
            'batches': 0,
            'start_time': None
        }
        self.patient_stats = defaultdict(lambda: {
            'count': 0,
            'profile': 'UNKNOWN',
            'last_vitals': {}
        })
        self.transition_events = []  # Track transitions
    
    def clear_screen(self):
        """Clear terminal"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def format_vitals(self, vitals):
        """Format vital signs cho hiển thị"""
        return (
            f"HR: {vitals.get('heart_rate', 0):>3.0f} | "
            f"SpO2: {vitals.get('spo2', 0):>5.1f}% | "
            f"BP: {vitals.get('blood_pressure', {}).get('systolic', 0):>3.0f}/"
            f"{vitals.get('blood_pressure', {}).get('diastolic', 0):<3.0f} | "
            f"Temp: {vitals.get('temperature', 0):>5.2f}°C | "
            f"RR: {vitals.get('respiratory_rate', 0):>2.0f}"
        )
    
    def get_profile_color(self, profile):
        """Lấy màu theo profile"""
        if profile == 'HEALTHY':
            return Colors.GREEN, '✅'
        elif profile == 'AT_RISK':
            return Colors.YELLOW, '⚠️ '
        elif profile == 'CRITICAL':
            return Colors.RED, '🚨'
        else:
            return Colors.BLUE, 'ℹ️ '
    
    def display_header(self):
        """Hiển thị header"""
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*100}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'🏥 ICU PATIENT DATA PRODUCER - REAL-TIME MONITOR':^100}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*100}{Colors.END}")
    
    def display_config(self):
        """Hiển thị cấu hình"""
        print(f"\n{Colors.BOLD}⚙️  Configuration:{Colors.END}")
        print(f"   📡 Kafka: {settings.KAFKA_BOOTSTRAP_SERVERS}")
        print(f"   📨 Topic: {settings.KAFKA_TOPIC_VITAL_SIGNS}")
        print(f"   👥 Patients: {self.num_patients}")
        print(f"   ⏱️  Interval: {self.interval}s")
    
    def display_statistics(self):
        """Hiển thị thống kê tổng quan"""
        if self.stats['start_time']:
            elapsed = time.time() - self.stats['start_time']
            rate = self.stats['total_sent'] / elapsed if elapsed > 0 else 0
        else:
            elapsed = 0
            rate = 0
        
        print(f"\n{Colors.BOLD}📊 System Statistics:{Colors.END}")
        print(f"   ⏱️  Uptime: {int(elapsed)}s")
        print(f"   📦 Batches: {self.stats['batches']}")
        print(f"   ✅ Messages Sent: {self.stats['total_sent']}")
        print(f"   ❌ Failed: {self.stats['total_failed']}")
        print(f"   📈 Rate: {rate:.1f} msg/sec")
        
        # Profile distribution
        healthy = sum(1 for p in self.patient_stats.values() if p['profile'] == 'HEALTHY')
        at_risk = sum(1 for p in self.patient_stats.values() if p['profile'] == 'AT_RISK')
        critical = sum(1 for p in self.patient_stats.values() if p['profile'] == 'CRITICAL')
        
        print(f"\n{Colors.BOLD}👥 Patient Distribution:{Colors.END}")
        print(f"   {Colors.GREEN}✅ Healthy: {healthy}{Colors.END}")
        print(f"   {Colors.YELLOW}⚠️  At Risk: {at_risk}{Colors.END}")
        print(f"   {Colors.RED}🚨 Critical: {critical}{Colors.END}")
        
        # Add transition stats
        if self.transition_events:
            print(f"\n{Colors.BOLD}🔄 Recent Profile Transitions:{Colors.END}")
            recent_transitions = self.transition_events[-5:]  # Last 5
            for event in recent_transitions:
                color = Colors.YELLOW if event['to'] in ['AT_RISK', 'CRITICAL'] else Colors.GREEN
                print(f"   {color}{event['patient_id']}: "
                      f"{event['from']} → {event['to']} "
                      f"(batch {event['batch']} at {event['time']}){Colors.END}")
    
    def display_patients(self):
        """Hiển thị trạng thái từng bệnh nhân"""
        print(f"\n{Colors.BOLD}🩺 Patient Vital Signs (Live):{Colors.END}")
        print(f"{Colors.BOLD}{'─'*100}{Colors.END}")
        
        # Header
        print(f"{Colors.BOLD}{'Patient ID':<15} {'Profile':<12} {'Vitals':<60} {'Count':<8} {'Last Update'}{Colors.END}")
        print(f"{Colors.BOLD}{'─'*100}{Colors.END}")
        
        # Data rows
        for patient_id in sorted(self.patient_stats.keys()):
            stats = self.patient_stats[patient_id]
            color, symbol = self.get_profile_color(stats['profile'])
            
            vitals_str = self.format_vitals(stats['last_vitals'])
            time_str = datetime.now().strftime('%H:%M:%S')
            
            print(f"{color}{symbol} {patient_id:<13} {stats['profile']:<12} {vitals_str:<60} "
                  f"{stats['count']:<8} {time_str}{Colors.END}")
        
        print(f"{Colors.BOLD}{'─'*100}{Colors.END}")
    
    def display_footer(self):
        """Hiển thị footer"""
        print(f"\n{Colors.CYAN}{'⏸️  Press Ctrl+C to stop producer':^100}{Colors.END}")
        print(f"{Colors.CYAN}{'Refreshing every batch...':^100}{Colors.END}\n")
    
    def display_dashboard(self):
        """Hiển thị toàn bộ dashboard"""
        self.clear_screen()
        self.display_header()
        self.display_config()
        self.display_statistics()
        self.display_patients()
        self.display_footer()
    
    def run(self):
        """Chạy producer với hiển thị trực quan"""
        try:
            # Khởi tạo
            print(f"{Colors.BOLD}{Colors.GREEN}🚀 Initializing Producer...{Colors.END}")
            time.sleep(1)
            
            # Tạo simulator với transitions enabled
            simulator = MultiPatientSimulator(
                num_patients=self.num_patients,
                enable_transitions=True  # Bật transitions
            )
            print(f"{Colors.GREEN}✅ Patient simulator created (transitions enabled){Colors.END}")
            
            # Khởi tạo patient stats
            summary = simulator.get_patient_summary()
            for patient_id, info in summary['patients'].items():
                self.patient_stats[patient_id]['profile'] = info['profile']
            
            time.sleep(1)
            
            # Tạo Kafka producer
            producer = VitalSignsProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                topic=settings.KAFKA_TOPIC_VITAL_SIGNS
            )
            print(f"{Colors.GREEN}✅ Kafka producer connected{Colors.END}")
            time.sleep(1)
            
            # Bắt đầu streaming
            self.stats['start_time'] = time.time()
            print(f"\n{Colors.BOLD}{Colors.GREEN}🎬 Starting data stream...{Colors.END}\n")
            time.sleep(2)
            
            while True:
                # Generate batch
                batch = simulator.generate_batch()
                
                # Send to Kafka
                for reading in batch:
                    patient_id = reading['patient_id']
                    
                    # Check for profile change
                    if reading['metadata'].get('profile_changed', False):
                        old_profile = self.patient_stats[patient_id].get('profile', 'UNKNOWN')
                        new_profile = reading['profile']
                        
                        self.transition_events.append({
                            'patient_id': patient_id,
                            'from': old_profile,
                            'to': new_profile,
                            'batch': self.stats['batches'],
                            'time': datetime.now().strftime('%H:%M:%S')
                        })
                    
                    # Update stats
                    self.patient_stats[patient_id]['count'] += 1
                    self.patient_stats[patient_id]['last_vitals'] = reading['vital_signs']
                    self.patient_stats[patient_id]['profile'] = reading.get('profile', 'UNKNOWN')
                    
                    # Send
                    if producer.send_reading(reading):
                        self.stats['total_sent'] += 1
                    else:
                        self.stats['total_failed'] += 1
                
                self.stats['batches'] += 1
                
                # Flush
                producer.producer.flush()
                
                # Display dashboard
                self.display_dashboard()
                
                # Wait
                time.sleep(self.interval)
        
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}⚠️  Producer stopped by user{Colors.END}")
        
        except Exception as e:
            print(f"\n\n{Colors.RED}❌ Error: {e}{Colors.END}")
            import traceback
            traceback.print_exc()
            raise
        
        finally:
            if 'producer' in locals():
                print(f"\n{Colors.BLUE}🔄 Closing producer...{Colors.END}")
                producer.close()
            
            # Final stats
            print(f"\n{Colors.BOLD}{'='*100}{Colors.END}")
            print(f"{Colors.BOLD}📊 FINAL STATISTICS{Colors.END}")
            print(f"{Colors.BOLD}{'='*100}{Colors.END}")
            
            if self.stats['start_time']:
                elapsed = time.time() - self.stats['start_time']
                print(f"⏱️  Total runtime: {int(elapsed)}s")
                print(f"📦 Total batches: {self.stats['batches']}")
                print(f"✅ Messages sent: {self.stats['total_sent']}")
                print(f"❌ Failed: {self.stats['total_failed']}")
                print(f"🔄 Total transitions: {len(self.transition_events)}")
                if elapsed > 0:
                    print(f"📈 Average rate: {self.stats['total_sent'] / elapsed:.1f} msg/sec")
            
            print(f"{Colors.BOLD}{'='*100}{Colors.END}")
            print(f"\n{Colors.GREEN}👋 Producer terminated successfully{Colors.END}\n")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ICU Patient Data Producer (Visual)')
    parser.add_argument('--num-patients', type=int, default=10, 
                       help='Number of patients to simulate (default: 10)')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Interval between batches in seconds (default: 1.0)')
    
    args = parser.parse_args()
    
    producer = VisualProducer(
        num_patients=args.num_patients,
        interval=args.interval
    )
    
    producer.run()


if __name__ == "__main__":
    main()