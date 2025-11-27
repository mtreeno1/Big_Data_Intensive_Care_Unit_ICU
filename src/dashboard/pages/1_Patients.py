# src/dashboard/pages/1_Patients.py
"""
Patient Management Page
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st
import pandas as pd
from datetime import datetime
from src.database.session import SessionLocal
from src.database.models import Patient, Admission
from sqlalchemy import func

st.set_page_config(page_title="Patient Management", page_icon="👥", layout="wide")

def get_all_patients_with_status():
    """Get all patients with their current status"""
    db = SessionLocal()
    try:
        patients = db.query(Patient, Admission).outerjoin(
            Admission, Patient.patient_id == Admission.patient_id
        ).filter(
            Admission.discharge_time.is_(None)
        ).all()
        
        data = []
        for p, a in patients:
            age = (datetime.now().date() - p.date_of_birth).days // 365 if p.date_of_birth else None
            
            data.append({
                'patient_id': p.patient_id,
                'full_name': p.full_name,
                'age': age,
                'gender': p.gender,
                'blood_type': p.blood_type,
                'device_id': p.device_id,
                'department': a.department if a else 'N/A',
                'admission_time': a.admission_time if a else None,
                'risk_level': a.risk_level if a else 'STABLE',
                'risk_score': a.current_risk_score if a else 0,
                'diagnosis': a.initial_diagnosis if a else 'N/A',
                'physician': a.attending_physician if a else 'N/A',
                'admission_type': a.admission_type if a else 'N/A'
            })
        
        return pd.DataFrame(data)
    finally:
        db.close()

def get_patient_statistics():
    """Get patient statistics"""
    db = SessionLocal()
    try:
        total = db.query(func.count(Patient.patient_id)).scalar()
        
        active = db.query(func.count(Admission.admission_id)).filter(
            Admission.discharge_time.is_(None)
        ).scalar()
        
        risk_dist = db.query(
            Admission.risk_level,
            func.count(Admission.admission_id)
        ).filter(
            Admission.discharge_time.is_(None)
        ).group_by(Admission.risk_level).all()
        
        return {
            'total': total,
            'active': active,
            'risk_distribution': dict(risk_dist)
        }
    finally:
        db.close()

# Main page
st.title("👥 Patient Management")
st.markdown("---")

# Statistics
stats = get_patient_statistics()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Patients", stats['total'])

with col2:
    st.metric("Active Admissions", stats['active'])

risk_colors = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MODERATE': '🟡', 'STABLE': '🟢'}
risk_dist = stats['risk_distribution']

with col3:
    st.metric(f"{risk_colors.get('CRITICAL', '🔴')} Critical", risk_dist.get('CRITICAL', 0))

with col4:
    st.metric(f"{risk_colors.get('HIGH', '🟠')} High", risk_dist.get('HIGH', 0))

with col5:
    st.metric(f"{risk_colors.get('STABLE', '🟢')} Stable", risk_dist.get('STABLE', 0) + risk_dist.get('MODERATE', 0))

st.markdown("---")

# Filters
col1, col2, col3 = st.columns(3)

with col1:
    filter_risk = st.multiselect(
        "Filter by Risk Level",
        options=['CRITICAL', 'HIGH', 'MODERATE', 'STABLE'],
        default=['CRITICAL', 'HIGH', 'MODERATE', 'STABLE']
    )

with col2:
    filter_department = st.multiselect(
        "Filter by Department",
        options=['ICU', 'CCU', 'Emergency', 'Surgery'],
        default=None
    )

with col3:
    search_patient = st.text_input("🔍 Search Patient ID or Name")

# Get patients
df = get_all_patients_with_status()

# Apply filters
if not df.empty:
    # Risk filter
    df = df[df['risk_level'].isin(filter_risk)]
    
    # Department filter
    if filter_department:
        df = df[df['department'].isin(filter_department)]
    
    # Search filter
    if search_patient:
        df = df[
            df['patient_id'].str.contains(search_patient, case=False) |
            df['full_name'].str.contains(search_patient, case=False)
        ]
    
    # Sort by risk score (descending)
    df = df.sort_values('risk_score', ascending=False)
    
    st.markdown(f"### 📋 Patient List ({len(df)} patients)")
    
    # Display patients
    for idx, row in df.iterrows():
        with st.expander(
            f"{risk_colors.get(row['risk_level'], '⚪')} {row['full_name']} - {row['patient_id']} | Risk: {row['risk_level']}",
            expanded=(row['risk_level'] in ['CRITICAL', 'HIGH'])
        ):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Patient Information**")
                st.text(f"ID: {row['patient_id']}")
                st.text(f"Name: {row['full_name']}")
                st.text(f"Age: {row['age']} years")
                st.text(f"Gender: {row['gender']}")
                st.text(f"Blood Type: {row['blood_type']}")
                st.text(f"Device: {row['device_id']}")
            
            with col2:
                st.markdown("**Admission Details**")
                st.text(f"Department: {row['department']}")
                st.text(f"Type: {row['admission_type']}")
                st.text(f"Physician: {row['physician']}")
                if row['admission_time']:
                    hours_admitted = (datetime.now() - row['admission_time']).total_seconds() / 3600
                    st.text(f"Admitted: {hours_admitted:.1f}h ago")
                st.text(f"Diagnosis: {row['diagnosis']}")
            
            with col3:
                st.markdown("**Risk Assessment**")
                
                # Risk badge
                risk_level = row['risk_level']
                risk_score = row['risk_score']
                
                if risk_level == 'CRITICAL':
                    st.error(f"🔴 CRITICAL - Score: {risk_score:.1f}")
                elif risk_level == 'HIGH':
                    st.warning(f"🟠 HIGH - Score: {risk_score:.1f}")
                elif risk_level == 'MODERATE':
                    st.info(f"🟡 MODERATE - Score: {risk_score:.1f}")
                else:
                    st.success(f"🟢 STABLE - Score: {risk_score:.1f}")
                
                # Action buttons
                if st.button(f"View Details", key=f"view_{row['patient_id']}"):
                    st.session_state.selected_patient = row['patient_id']
                    st.switch_page("pages/2_Monitoring.py")
else:
    st.info("ℹ️ No patients found")

# Auto-refresh
if st.checkbox("Auto Refresh", value=True):
    import time
    refresh_interval = st.slider("Refresh interval (seconds)", 5, 60, 10)
    time.sleep(refresh_interval)
    st.rerun()