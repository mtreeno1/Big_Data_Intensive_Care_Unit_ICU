import sqlite3
from datetime import datetime
import pandas as pd

class PatientDatabase:
    def __init__(self, db_path='patients.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Khởi tạo database và bảng patients"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                patient_id TEXT PRIMARY KEY,
                age INTEGER,
                gender TEXT,
                admission_type TEXT,
                diagnosis TEXT,
                apache_score REAL,
                heart_rate REAL,
                blood_pressure_systolic REAL,
                blood_pressure_diastolic REAL,
                temperature REAL,
                respiratory_rate REAL,
                spo2 REAL,
                icu_stay_days INTEGER,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_patient(self, patient_data):
        """Thêm một bệnh nhân"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO patients 
            (patient_id, age, gender, admission_type, diagnosis, 
             apache_score, heart_rate, blood_pressure_systolic, 
             blood_pressure_diastolic, temperature, respiratory_rate, 
             spo2, icu_stay_days, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patient_data['patient_id'],
            patient_data.get('age'),
            patient_data.get('gender'),
            patient_data.get('admission_type'),
            patient_data.get('diagnosis'),
            patient_data.get('apache_score'),
            patient_data.get('heart_rate'),
            patient_data.get('blood_pressure_systolic'),
            patient_data.get('blood_pressure_diastolic'),
            patient_data.get('temperature'),
            patient_data.get('respiratory_rate'),
            patient_data.get('spo2'),
            patient_data.get('icu_stay_days'),
            patient_data.get('status', 'active')
        ))
        
        conn.commit()
        conn.close()
        print(f"✅ Đã thêm bệnh nhân: {patient_data['patient_id']}")
    
    def bulk_add_patients(self, df):
        """Thêm nhiều bệnh nhân từ DataFrame"""
        conn = sqlite3.connect(self.db_path)
        
        # Chuẩn bị dữ liệu
        df['status'] = 'active'
        
        df.to_sql('patients', conn, if_exists='append', index=False)
        
        conn.close()
        print(f"✅ Đã thêm {len(df)} bệnh nhân vào database")
    
    def get_patient(self, patient_id):
        """Lấy thông tin bệnh nhân"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM patients WHERE patient_id = ?', (patient_id,))
        patient = cursor.fetchone()
        
        conn.close()
        return patient
    
    def get_all_patients(self):
        """Lấy tất cả bệnh nhân"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('SELECT * FROM patients', conn)
        conn.close()
        return df