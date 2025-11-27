"""
Streamlit Dashboard for ICU Monitoring System
"""
# ✅ FIX: Add parent directory to Python path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient
from sqlalchemy import func, text

from config.config import settings
from src.database.session import SessionLocal
from src.database.models import Patient, Admission

# Page config
st.set_page_config(
    page_title="ICU Monitoring Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
    .risk-critical {
        background-color: #ff4444;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .risk-high {
        background-color: #ff9944;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .risk-moderate {
        background-color: #ffdd44;
        color: black;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .risk-stable {
        background-color: #44ff44;
        color: black;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize connections
@st.cache_resource
def init_connections():
    """Initialize database connections"""
    influx_client = InfluxDBClient(
        url=settings.INFLUX_URL,
        token=settings.INFLUX_TOKEN,
        org=settings.INFLUX_ORG
    )
    return influx_client

influx_client = init_connections()

def get_active_patients():
    """Get all active patients from PostgreSQL with graceful fallback if schema differs."""
    db = SessionLocal()
    try:
        # Preferred: ORM join if columns exist
        patients = db.query(Patient, Admission).join(
            Admission, Patient.patient_id == Admission.patient_id
        ).filter(
            Admission.discharge_time.is_(None)
        ).all()
        data = []
        for p, a in patients:
            try:
                age = (datetime.now().date() - p.date_of_birth).days // 365 if getattr(p, 'date_of_birth', None) else None
            except Exception:
                age = None
            data.append({
                'patient_id': p.patient_id,
                'full_name': getattr(p, 'full_name', p.patient_id),
                'age': age if age is not None else 'N/A',
                'gender': getattr(p, 'gender', 'N/A'),
                'device_id': getattr(p, 'device_id', 'N/A'),
                'blood_type': getattr(p, 'blood_type', 'Unknown'),
                'chronic_conditions': getattr(p, 'chronic_conditions', 'None'),
                'admission_id': a.admission_id,
                'admission_time': a.admission_time,
                'department': a.department,
                'risk_level': a.risk_level,
                'risk_score': a.current_risk_score,
                'diagnosis': a.initial_diagnosis
            })
        return data
    except Exception:
        # Fallback: query admissions only and fill placeholders
        try:
            rows = db.execute(text("""
                SELECT admission_id, patient_id, admission_time, department,
                       COALESCE(risk_level,'STABLE') as risk_level,
                       COALESCE(current_risk_score,0.0) as current_risk_score,
                       COALESCE(initial_diagnosis,'N/A') as initial_diagnosis
                FROM admissions
                WHERE discharge_time IS NULL
                ORDER BY admission_time DESC
            """)).fetchall()
            data = []
            for r in rows:
                data.append({
                    'patient_id': r.patient_id,
                    'full_name': r.patient_id,
                    'age': 'N/A',
                    'gender': 'N/A',
                    'device_id': 'N/A',
                    'blood_type': 'Unknown',
                    'chronic_conditions': 'None',
                    'admission_id': r.admission_id,
                    'admission_time': r.admission_time,
                    'department': r.department,
                    'risk_level': r.risk_level,
                    'risk_score': r.current_risk_score,
                    'diagnosis': r.initial_diagnosis
                })
            return data
        except Exception as e2:
            st.error(f"❌ Error getting patients: {e2}")
            return []
    finally:
        db.close()

def get_patient_vitals(patient_id: str, hours: int = 1):
    """Get vital signs from InfluxDB"""
    query = f'''
    from(bucket: "{settings.INFLUX_BUCKET}")
        |> range(start: -{hours}h)
        |> filter(fn: (r) => r["patient_id"] == "{patient_id}")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> keep(columns: ["_time", "heart_rate", "spo2", "temperature", "respiratory_rate", "blood_pressure_systolic", "blood_pressure_diastolic"])
    '''
    
    try:
        query_api = influx_client.query_api()
        result = query_api.query(query)
        
        data = []
        for table in result:
            for record in table.records:
                data.append({
                    'timestamp': record['_time'],
                    'heart_rate': record.values.get('heart_rate'),
                    'spo2': record.values.get('spo2'),
                    'temperature': record.values.get('temperature'),
                    'respiratory_rate': record.values.get('respiratory_rate'),
                    'bp_systolic': record.values.get('blood_pressure_systolic'),
                    'bp_diastolic': record.values.get('blood_pressure_diastolic')
                })
        
        return pd.DataFrame(data)
    
    except Exception as e:
        st.error(f"❌ Error fetching vitals: {e}")
        return pd.DataFrame()

def get_risk_distribution():
    """Get risk level distribution"""
    db = SessionLocal()
    try:
        dist = db.query(
            Admission.risk_level,
            func.count(Admission.admission_id).label('count')
        ).filter(
            Admission.discharge_time.is_(None)
        ).group_by(Admission.risk_level).all()
        
        return {level: count for level, count in dist}
    finally:
        db.close()


def get_recent_alerts(limit: int = 50) -> pd.DataFrame:
    """Read recent alerts from Postgres storage alerts table."""
    db = SessionLocal()
    try:
        rows = db.execute(text(
            """
            SELECT timestamp, patient_id, alert_type, severity, vital_type, value, message
            FROM alerts
            ORDER BY timestamp DESC
            LIMIT :lim
            """
        ), {"lim": limit}).fetchall()
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows, columns=[
            'timestamp','patient_id','alert_type','severity','vital_type','value','message'
        ])
        return df
    except Exception:
        return pd.DataFrame()
    finally:
        db.close()


def get_alert_count(hours: int = 24) -> int:
    db = SessionLocal()
    try:
        rows = db.execute(text(
            """
            SELECT COUNT(*) AS cnt
            FROM alerts
            WHERE timestamp >= NOW() - INTERVAL ':hrs hours'
            """
        ).bindparams(hrs=str(hours))).fetchone()
        if rows and len(rows) > 0:
            return int(rows[0])
        return 0
    except Exception:
        return 0
    finally:
        db.close()

def render_patient_card(patient):
    """Render a patient card"""
    risk_class = f"risk-{patient['risk_level'].lower()}" if patient['risk_level'] else "risk-stable"
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.markdown(f"### {patient['full_name']}")
        st.text(f"ID: {patient['patient_id']} | Age: {patient['age']} | {patient['gender']}")
        st.text(f"Blood Type: {patient['blood_type']} | Device: {patient['device_id']}")
    
    with col2:
        st.text(f"Department: {patient['department']}")
        st.text(f"Diagnosis: {patient['diagnosis']}")
        admitted_hours = (datetime.now() - patient['admission_time']).total_seconds() / 3600
        st.text(f"Admitted: {admitted_hours:.1f}h ago")
    
    with col3:
        if patient['risk_level']:
            st.markdown(f"<div class='{risk_class}'>{patient['risk_level']}</div>", unsafe_allow_html=True)
            st.metric("Risk Score", f"{patient['risk_score']:.2f}")

def main():
    """Main dashboard"""
    
    # Header
    st.title("🏥 ICU Real-Time Monitoring Dashboard")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Time range selector
        time_range = st.selectbox(
            "Time Range",
            options=[1, 6, 12, 24],
            format_func=lambda x: f"Last {x} hour{'s' if x > 1 else ''}",
            index=0
        )
        
        # Refresh interval
        auto_refresh = st.checkbox("Auto Refresh", value=True)
        if auto_refresh:
            refresh_interval = st.slider("Refresh Interval (seconds)", 5, 60, 10)
        
        st.markdown("---")
        st.markdown("### 📊 System Status")
        
        # System stats
        patients = get_active_patients()
        st.metric("Active Patients", len(patients))
        
        risk_dist = get_risk_distribution()
        for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            if level in risk_dist:
                emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}[level]
                st.metric(f"{emoji} {level}", risk_dist[level])
        # Alerts count (last 24h)
        try:
            alert_24h = get_alert_count(24)
            st.metric("🚨 Alerts (24h)", alert_24h)
        except Exception:
            pass
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["👥 Patient Overview", "📈 Vital Signs", "🚨 Alerts"])
    
    with tab1:
        st.header("Active Patients")
        
        patients = get_active_patients()
        
        if not patients:
            st.info("ℹ️ No active patients")
        else:
            # Sort by risk level (prioritize CRITICAL > HIGH > MEDIUM > LOW)
            risk_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, None: 4}
            patients_sorted = sorted(patients, key=lambda x: risk_order.get(x.get('risk_level'), 4))
            
            for patient in patients_sorted:
                with st.expander(f"{patient['full_name']} - {patient['risk_level'] or 'STABLE'}", expanded=True):
                    render_patient_card(patient)
                    
                    # Get and display vitals
                    vitals_df = get_patient_vitals(patient['patient_id'], time_range)
                    
                    if not vitals_df.empty:
                        # Latest vitals
                        latest = vitals_df.iloc[-1]
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("💓 Heart Rate", f"{latest['heart_rate']:.0f} bpm" if pd.notna(latest['heart_rate']) else "N/A")
                        with col2:
                            st.metric("🫁 SpO2", f"{latest['spo2']:.0f}%" if pd.notna(latest['spo2']) else "N/A")
                        with col3:
                            st.metric("🌡️ Temperature", f"{latest['temperature']:.1f}°C" if pd.notna(latest['temperature']) else "N/A")
                        with col4:
                            st.metric("🫀 BP", f"{latest['bp_systolic']:.0f}/{latest['bp_diastolic']:.0f}" if pd.notna(latest['bp_systolic']) else "N/A")
                    else:
                        st.warning("⚠️ No vital signs data available")
    
    with tab2:
        st.header("Vital Signs Trends")
        
        patients = get_active_patients()
        
        if patients:
            # Patient selector
            selected_patient = st.selectbox(
                "Select Patient",
                options=[p['patient_id'] for p in patients],
                format_func=lambda x: next(p['full_name'] for p in patients if p['patient_id'] == x)
            )
            
            # Get vitals
            vitals_df = get_patient_vitals(selected_patient, time_range)
            
            if not vitals_df.empty:
                # Plot vitals
                fig = go.Figure()
                
                # Heart Rate
                fig.add_trace(go.Scatter(
                    x=vitals_df['timestamp'],
                    y=vitals_df['heart_rate'],
                    name='Heart Rate',
                    mode='lines+markers'
                ))
                
                # SpO2
                fig.add_trace(go.Scatter(
                    x=vitals_df['timestamp'],
                    y=vitals_df['spo2'],
                    name='SpO2',
                    mode='lines+markers',
                    yaxis='y2'
                ))
                
                fig.update_layout(
                    title='Vital Signs Trends',
                    xaxis_title='Time',
                    yaxis_title='Heart Rate (bpm)',
                    yaxis2=dict(
                        title='SpO2 (%)',
                        overlaying='y',
                        side='right'
                    ),
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show data table
                st.subheader("📋 Detailed Data")
                st.dataframe(vitals_df.tail(20), use_container_width=True)
            else:
                st.warning("⚠️ No data available for selected patient")
        else:
            st.info("ℹ️ No active patients")
    
    with tab3:
        st.header("🚨 Alerts & Notifications")

        # Recent alerts table
        alerts_df = get_recent_alerts(limit=100)
        if alerts_df is not None and not alerts_df.empty:
            # Format timestamp
            try:
                alerts_df['timestamp'] = pd.to_datetime(alerts_df['timestamp'])
            except Exception:
                pass
            st.subheader("Recent Alerts")
            st.dataframe(alerts_df, use_container_width=True, height=400)
        else:
            st.info("ℹ️ No alerts recorded yet")

        # Also show currently high-risk patients (from admissions)
        st.subheader("Current High-Risk Patients")
        patients = get_active_patients()
        critical_patients = [p for p in patients if p['risk_level'] in ['CRITICAL', 'HIGH']]
        if critical_patients:
            for patient in critical_patients:
                alert_type = "🔴 CRITICAL" if patient['risk_level'] == 'CRITICAL' else "🟠 HIGH"
                with st.container():
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.markdown(f"### {alert_type}")
                        st.text(f"{patient['full_name']} ({patient['patient_id']})")
                    with col2:
                        st.text(f"Department: {patient['department']}")
                        st.text(f"Diagnosis: {patient['diagnosis']}")
                    with col3:
                        st.metric("Risk Score", f"{patient['risk_score']:.2f}")
                    st.markdown("---")
        else:
            st.success("✅ No current high-risk admissions")
    
    # Auto refresh
    if auto_refresh:
        import time
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()