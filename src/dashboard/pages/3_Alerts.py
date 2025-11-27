# src/dashboard/pages/3_Alerts.py
"""
Alerts and Notifications Page
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.database.session import SessionLocal
from src.database.models import Patient, Admission
from sqlalchemy import desc

st.set_page_config(page_title="Alerts", page_icon="🚨", layout="wide")

def get_critical_patients():
    """Get patients with critical/high risk"""
    db = SessionLocal()
    try:
        patients = db.query(Patient, Admission).join(
            Admission, Patient.patient_id == Admission.patient_id
        ).filter(
            Admission.discharge_time.is_(None),
            Admission.risk_level.in_(['CRITICAL', 'HIGH'])
        ).order_by(desc(Admission.current_risk_score)).all()
        
        data = []
        for p, a in patients:
            age = (datetime.now().date() - p.date_of_birth).days // 365 if p.date_of_birth else None
            hours_admitted = (datetime.now() - a.admission_time).total_seconds() / 3600
            
            data.append({
                'patient_id': p.patient_id,
                'full_name': p.full_name,
                'age': age,
                'gender': p.gender,
                'department': a.department,
                'risk_level': a.risk_level,
                'risk_score': a.current_risk_score,
                'diagnosis': a.initial_diagnosis,
                'physician': a.attending_physician,
                'hours_admitted': hours_admitted,
                'admission_time': a.admission_time
            })
        
        return pd.DataFrame(data)
    finally:
        db.close()

# Main page
st.title("🚨 Critical Alerts & Notifications")
st.markdown("---")

# Get critical patients
critical_df = get_critical_patients()

# Statistics
col1, col2, col3 = st.columns(3)

with col1:
    critical_count = len(critical_df[critical_df['risk_level'] == 'CRITICAL'])
    st.metric("🔴 Critical Patients", critical_count)

with col2:
    high_count = len(critical_df[critical_df['risk_level'] == 'HIGH'])
    st.metric("🟠 High Risk Patients", high_count)

with col3:
    total_count = len(critical_df)
    st.metric("⚠️ Total Alerts", total_count)

st.markdown("---")

if critical_df.empty:
    st.success("✅ No critical alerts at this time")
else:
    st.subheader(f"⚠️ Active Alerts ({len(critical_df)})")
    
    # Sort by risk score
    critical_df = critical_df.sort_values('risk_score', ascending=False)
    
    for idx, row in critical_df.iterrows():
        # Alert box
        if row['risk_level'] == 'CRITICAL':
            alert_type = "🔴 CRITICAL ALERT"
            container_type = st.error
        else:
            alert_type = "🟠 HIGH RISK ALERT"
            container_type = st.warning
        
        with container_type(f"{alert_type}: {row['full_name']} ({row['patient_id']})"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Patient Info**")
                st.text(f"ID: {row['patient_id']}")
                st.text(f"Age: {row['age']} | {row['gender']}")
                st.text(f"Department: {row['department']}")
            
            with col2:
                st.markdown("**Clinical Info**")
                st.text(f"Diagnosis: {row['diagnosis']}")
                st.text(f"Physician: {row['physician']}")
                st.text(f"Admitted: {row['hours_admitted']:.1f}h ago")
            
            with col3:
                st.markdown("**Risk Assessment**")
                st.metric("Risk Score", f"{row['risk_score']:.1f}")
                
                if st.button(f"View Vitals", key=f"vitals_{row['patient_id']}"):
                    st.session_state.selected_patient = row['patient_id']
                    st.switch_page("pages/2_Monitoring.py")

# Auto refresh
if st.checkbox("Auto Refresh Alerts", value=True):
    import time
    time.sleep(10)
    st.rerun()