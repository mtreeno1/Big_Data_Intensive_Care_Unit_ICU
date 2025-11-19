"""
Real-time ICU Patient Monitoring Dashboard
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import sys
from pathlib import Path

# ✅ Fix: Add correct path to root directory
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from config.config import settings
from influxdb_client import InfluxDBClient
from src.database.session import SessionLocal
from src.database.models import Patient, Admission

# Page config
st.set_page_config(
    page_title="ICU Patient Monitor",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stAlert {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .critical {
        background-color: #ff4b4b;
        color: white;
    }
    .high {
        background-color: #ffa500;
        color: white;
    }
    .normal {
        background-color: #00cc00;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize connections
@st.cache_resource
def init_influx():
    return InfluxDBClient(
        url=settings.INFLUX_URL,
        token=settings.INFLUX_TOKEN,
        org=settings.INFLUX_ORG
    )

def get_active_patients():
    """Get list of active patients"""
    with SessionLocal() as db:
        admissions = db.query(Admission).filter(
            Admission.discharge_time.is_(None)
        ).all()
        
        patients_data = []
        for adm in admissions:
            patients_data.append({
                'patient_id': adm.patient_id,
                'risk_level': adm.risk_level or 'UNKNOWN',
                'risk_score': adm.current_risk_score or 0.0,
                'admit_time': adm.admit_time
            })
        
        return pd.DataFrame(patients_data)

def get_vital_signs(patient_id: str, minutes: int = 10):
    """Get recent vital signs for a patient"""
    client = init_influx()
    query_api = client.query_api()
    
    query = f'''
    from(bucket:"{settings.INFLUX_BUCKET}")
      |> range(start: -{minutes}m)
      |> filter(fn: (r) => r._measurement == "vital_signs")
      |> filter(fn: (r) => r.patient_id == "{patient_id}")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''
    
    result = query_api.query(query)
    
    data = []
    for table in result:
        for record in table.records:
            data.append({
                'time': record.get_time(),
                'heart_rate': record.values.get('heart_rate'),
                'spo2': record.values.get('spo2'),
                'temperature': record.values.get('temperature'),
                'respiratory_rate': record.values.get('respiratory_rate'),
                'blood_pressure_systolic': record.values.get('blood_pressure_systolic'),
                'blood_pressure_diastolic': record.values.get('blood_pressure_diastolic'),
            })
    
    return pd.DataFrame(data)

def get_risk_color(risk_level):
    """Get color for risk level"""
    colors = {
        'LOW': '🟢',
        'MEDIUM': '🟡',
        'HIGH': '🟠',
        'CRITICAL': '🔴',
        'UNKNOWN': '⚪'
    }
    return colors.get(risk_level, '⚪')

# Main Dashboard
def main():
    st.title("🏥 ICU Patient Monitoring Dashboard")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        auto_refresh = st.checkbox("Auto Refresh", value=True)
        refresh_interval = st.slider("Refresh Interval (seconds)", 3, 30, 5)
        time_range = st.selectbox("Time Range (minutes)", [5, 10, 15, 30, 60], index=1)
        
        st.markdown("---")
        st.markdown("### 📊 System Status")
        
        # Test connections
        try:
            init_influx()
            st.success("✅ InfluxDB Connected")
        except:
            st.error("❌ InfluxDB Disconnected")
        
        try:
            SessionLocal()
            st.success("✅ PostgreSQL Connected")
        except:
            st.error("❌ PostgreSQL Disconnected")
        
        st.info("⚙️ Kafka Streaming")
    
    # Get active patients
    try:
        patients_df = get_active_patients()
    except Exception as e:
        st.error(f"❌ Error getting patients: {e}")
        return
    
    if patients_df.empty:
        st.warning("⚠️ No active patients in ICU")
        st.info("💡 Start the producer to generate patient data: `python scripts/run_producer.py`")
        return
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Total Patients", len(patients_df))
    
    with col2:
        critical = len(patients_df[patients_df['risk_level'] == 'CRITICAL'])
        st.metric("🔴 Critical", critical)
    
    with col3:
        high = len(patients_df[patients_df['risk_level'] == 'HIGH'])
        st.metric("🟠 High Risk", high)
    
    with col4:
        avg_risk = patients_df['risk_score'].mean()
        st.metric("📊 Avg Risk Score", f"{avg_risk:.2f}")
    
    st.markdown("---")
    
    # Patient List with Risk Levels
    st.header("📋 Active Patients")
    
    # Sort by risk score descending
    patients_df = patients_df.sort_values('risk_score', ascending=False)
    
    for idx, patient in patients_df.iterrows():
        with st.expander(
            f"{get_risk_color(patient['risk_level'])} {patient['patient_id']} - "
            f"{patient['risk_level']} (Score: {patient['risk_score']:.2f})",
            expanded=(patient['risk_level'] in ['CRITICAL', 'HIGH'])
        ):
            # Get vital signs
            try:
                vitals_df = get_vital_signs(patient['patient_id'], time_range)
            except Exception as e:
                st.error(f"❌ Error getting vital signs: {e}")
                continue
            
            if vitals_df.empty:
                st.warning("⚠️ No recent vital signs data")
                continue
            
            # Latest values
            latest = vitals_df.iloc[-1]
            
            # Display current vitals
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "💓 Heart Rate",
                    f"{latest['heart_rate']:.0f} bpm" if pd.notna(latest['heart_rate']) else "N/A"
                )
            
            with col2:
                st.metric(
                    "🫁 SpO2",
                    f"{latest['spo2']:.0f}%" if pd.notna(latest['spo2']) else "N/A"
                )
            
            with col3:
                st.metric(
                    "🌡️ Temperature",
                    f"{latest['temperature']:.1f}°C" if pd.notna(latest['temperature']) else "N/A"
                )
            
            with col4:
                st.metric(
                    "💨 Resp Rate",
                    f"{latest['respiratory_rate']:.0f}/min" if pd.notna(latest['respiratory_rate']) else "N/A"
                )
            
            # Vital signs charts
            st.markdown("#### 📈 Vital Signs Trends")
            
            # Heart Rate Chart
            if vitals_df['heart_rate'].notna().any():
                fig_hr = go.Figure()
                fig_hr.add_trace(go.Scatter(
                    x=vitals_df['time'],
                    y=vitals_df['heart_rate'],
                    mode='lines+markers',
                    name='Heart Rate',
                    line=dict(color='red', width=2)
                ))
                fig_hr.update_layout(
                    title="Heart Rate",
                    xaxis_title="Time",
                    yaxis_title="bpm",
                    height=250,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_hr, use_container_width=True)
            
            # SpO2 Chart
            if vitals_df['spo2'].notna().any():
                fig_spo2 = go.Figure()
                fig_spo2.add_trace(go.Scatter(
                    x=vitals_df['time'],
                    y=vitals_df['spo2'],
                    mode='lines+markers',
                    name='SpO2',
                    line=dict(color='blue', width=2)
                ))
                fig_spo2.update_layout(
                    title="Blood Oxygen (SpO2)",
                    xaxis_title="Time",
                    yaxis_title="%",
                    height=250,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_spo2, use_container_width=True)
            
            # Blood Pressure Chart
            if vitals_df['blood_pressure_systolic'].notna().any():
                fig_bp = go.Figure()
                fig_bp.add_trace(go.Scatter(
                    x=vitals_df['time'],
                    y=vitals_df['blood_pressure_systolic'],
                    mode='lines+markers',
                    name='Systolic',
                    line=dict(color='green', width=2)
                ))
                fig_bp.add_trace(go.Scatter(
                    x=vitals_df['time'],
                    y=vitals_df['blood_pressure_diastolic'],
                    mode='lines+markers',
                    name='Diastolic',
                    line=dict(color='orange', width=2)
                ))
                fig_bp.update_layout(
                    title="Blood Pressure",
                    xaxis_title="Time",
                    yaxis_title="mmHg",
                    height=250,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_bp, use_container_width=True)
    
    # Auto refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()