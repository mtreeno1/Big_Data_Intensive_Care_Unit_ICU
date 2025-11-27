# src/dashboard/pages/2_Monitoring.py
"""
Real-time Vital Signs Monitoring Page
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient

from config.config import settings
from src.database.session import SessionLocal
from src.database.models import Patient, Admission

st.set_page_config(page_title="Real-time Monitoring", page_icon="📈", layout="wide")

@st.cache_resource
def get_influx_client():
    return InfluxDBClient(
        url=settings.INFLUX_URL,
        token=settings.INFLUX_TOKEN,
        org=settings.INFLUX_ORG
    )

def get_patient_list():
    """Get list of active patients"""
    db = SessionLocal()
    try:
        patients = db.query(Patient, Admission).join(
            Admission, Patient.patient_id == Admission.patient_id
        ).filter(
            Admission.discharge_time.is_(None)
        ).all()
        
        return [(p.patient_id, f"{p.full_name} ({p.patient_id})") for p, a in patients]
    finally:
        db.close()

def get_patient_vitals(patient_id, hours=1):
    """Get vital signs from InfluxDB"""
    client = get_influx_client()
    query_api = client.query_api()
    
    query = f'''
    from(bucket: "{settings.INFLUX_BUCKET}")
        |> range(start: -{hours}h)
        |> filter(fn: (r) => r["patient_id"] == "{patient_id}")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''
    
    try:
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
        st.error(f"Error fetching vitals: {e}")
        return pd.DataFrame()

def create_vital_chart(df, vital_name, y_column, color, normal_range=None):
    """Create a chart for a vital sign"""
    fig = go.Figure()
    
    # Add trace
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df[y_column],
        mode='lines+markers',
        name=vital_name,
        line=dict(color=color, width=2),
        marker=dict(size=6)
    ))
    
    # Add normal range if provided
    if normal_range:
        fig.add_hrect(
            y0=normal_range[0], y1=normal_range[1],
            fillcolor="green", opacity=0.1,
            layer="below", line_width=0,
        )
    
    fig.update_layout(
        title=vital_name,
        xaxis_title="Time",
        yaxis_title=vital_name,
        height=300,
        showlegend=False
    )
    
    return fig

# Main page
st.title("📈 Real-time Vital Signs Monitoring")
st.markdown("---")

# Patient selector
patients = get_patient_list()

if not patients:
    st.warning("⚠️ No active patients")
    st.stop()

# Check if patient selected from another page
if 'selected_patient' not in st.session_state:
    st.session_state.selected_patient = patients[0][0]

patient_dict = {pid: pname for pid, pname in patients}
selected_patient = st.selectbox(
    "Select Patient",
    options=list(patient_dict.keys()),
    format_func=lambda x: patient_dict[x],
    index=0 if st.session_state.selected_patient not in patient_dict else list(patient_dict.keys()).index(st.session_state.selected_patient)
)

# Time range selector
col1, col2 = st.columns([3, 1])

with col1:
    time_range = st.select_slider(
        "Time Range",
        options=[0.25, 0.5, 1, 2, 6, 12, 24],
        value=1,
        format_func=lambda x: f"{x} hour{'s' if x != 1 else ''}" if x >= 1 else f"{int(x*60)} minutes"
    )

with col2:
    auto_refresh = st.checkbox("Auto Refresh", value=True)

st.markdown("---")

# Get vitals
with st.spinner(f"Loading vitals for last {time_range}h..."):
    vitals_df = get_patient_vitals(selected_patient, time_range)

if vitals_df.empty:
    st.warning("⚠️ No vital signs data available for this patient")
    st.info("💡 Make sure the Producer is running and streaming data")
else:
    # Latest vitals display
    st.subheader("📊 Latest Vital Signs")
    
    latest = vitals_df.iloc[-1]
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        hr = latest['heart_rate']
        hr_status = "🟢" if 60 <= hr <= 100 else "🔴"
        st.metric(f"{hr_status} Heart Rate", f"{hr:.0f} bpm" if pd.notna(hr) else "N/A")
    
    with col2:
        spo2 = latest['spo2']
        spo2_status = "🟢" if spo2 >= 95 else "🔴" if spo2 < 90 else "🟡"
        st.metric(f"{spo2_status} SpO2", f"{spo2:.0f}%" if pd.notna(spo2) else "N/A")
    
    with col3:
        temp = latest['temperature']
        temp_status = "🟢" if 36.5 <= temp <= 37.5 else "🔴"
        st.metric(f"{temp_status} Temperature", f"{temp:.1f}°C" if pd.notna(temp) else "N/A")
    
    with col4:
        rr = latest['respiratory_rate']
        rr_status = "🟢" if 12 <= rr <= 20 else "🔴"
        st.metric(f"{rr_status} Resp. Rate", f"{rr:.0f} /min" if pd.notna(rr) else "N/A")
    
    with col5:
        bp_sys = latest['bp_systolic']
        bp_status = "🟢" if 90 <= bp_sys <= 140 else "🔴"
        st.metric(f"{bp_status} BP Systolic", f"{bp_sys:.0f} mmHg" if pd.notna(bp_sys) else "N/A")
    
    with col6:
        bp_dia = latest['bp_diastolic']
        st.metric("BP Diastolic", f"{bp_dia:.0f} mmHg" if pd.notna(bp_dia) else "N/A")
    
    st.markdown("---")
    
    # Vital signs trends
    st.subheader("📈 Vital Signs Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Heart Rate
        fig_hr = create_vital_chart(vitals_df, "Heart Rate (bpm)", "heart_rate", "red", (60, 100))
        st.plotly_chart(fig_hr, use_container_width=True)
        
        # Temperature
        fig_temp = create_vital_chart(vitals_df, "Temperature (°C)", "temperature", "orange", (36.5, 37.5))
        st.plotly_chart(fig_temp, use_container_width=True)
        
        # Blood Pressure
        fig_bp = go.Figure()
        fig_bp.add_trace(go.Scatter(x=vitals_df['timestamp'], y=vitals_df['bp_systolic'], 
                                     name='Systolic', mode='lines+markers', line=dict(color='blue')))
        fig_bp.add_trace(go.Scatter(x=vitals_df['timestamp'], y=vitals_df['bp_diastolic'], 
                                     name='Diastolic', mode='lines+markers', line=dict(color='lightblue')))
        fig_bp.update_layout(title="Blood Pressure (mmHg)", height=300)
        st.plotly_chart(fig_bp, use_container_width=True)
    
    with col2:
        # SpO2
        fig_spo2 = create_vital_chart(vitals_df, "SpO2 (%)", "spo2", "blue", (95, 100))
        st.plotly_chart(fig_spo2, use_container_width=True)
        
        # Respiratory Rate
        fig_rr = create_vital_chart(vitals_df, "Respiratory Rate (/min)", "respiratory_rate", "green", (12, 20))
        st.plotly_chart(fig_rr, use_container_width=True)
    
    # Data table
    with st.expander("📋 View Raw Data"):
        st.dataframe(
            vitals_df.tail(50).sort_values('timestamp', ascending=False),
            use_container_width=True
        )

# Auto refresh
if auto_refresh:
    import time
    time.sleep(5)
    st.rerun()