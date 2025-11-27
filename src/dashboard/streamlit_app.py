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
from sqlalchemy import func

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

# Load Alert Component HTML
alert_html_path = Path(__file__).parent / "alert_component.html"
with open(alert_html_path, 'r', encoding='utf-8') as f:
    alert_component_html = f.read()

# Custom CSS
st.markdown("""
<style>
    /* 1. Tinh chỉnh khoảng cách phần chính */
    .main > div {
        padding-top: 1.5rem;
    }

    /* 2. Thiết kế lại Metric Card (Thẻ chỉ số sinh tồn) */
    div[data-testid="stMetric"] {
        background-color: #1e2530; /* Màu nền tối sang trọng */
        border: 1px solid #2d3748; /* Viền xám nhẹ tạo khối */
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); /* Bóng đổ nhẹ */
        transition: transform 0.2s ease; /* Hiệu ứng khi rê chuột */
    }
    
    div[data-testid="stMetric"]:hover {
        border-color: #4a5568; /* Sáng viền khi hover */
        transform: translateY(-2px); /* Nổi lên nhẹ */
    }

    /* Màu chữ tiêu đề nhỏ (Label) - Xám sáng */
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        color: #a0aec0 !important;
        font-weight: 500;
    }

    /* Màu số liệu to (Value) - Trắng nổi bật */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        color: #ffffff !important;
        font-weight: 700;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.1);
    }

    /* 3. Thiết kế lại Risk Badges (Nhãn rủi ro) - Phong cách hiện đại */
    /* Cấu trúc chung cho badge */
    .risk-badge {
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: 700;
        text-align: center;
        display: inline-block;
        font-size: 0.9rem;
        letter-spacing: 0.5px;
        backdrop-filter: blur(4px);
        width: 100%;
        margin-top: 5px;
    }

    /* CRITICAL: Đỏ thẫm + Viền đỏ tươi + Chữ đỏ sáng */
    .risk-critical {
        background-color: rgba(220, 38, 38, 0.2); 
        color: #fca5a5;
        border: 1px solid #ef4444;
        box-shadow: 0 0 8px rgba(239, 68, 68, 0.3);
    }

    /* HIGH: Cam thẫm + Viền cam + Chữ cam sáng */
    .risk-high {
        background-color: rgba(234, 88, 12, 0.2);
        color: #fdba74;
        border: 1px solid #f97316;
    }

    /* MODERATE: Vàng thẫm + Viền vàng + Chữ vàng sáng */
    .risk-moderate {
        background-color: rgba(202, 138, 4, 0.2);
        color: #fde047;
        border: 1px solid #eab308;
    }

    /* STABLE: Xanh lục thẫm + Viền xanh + Chữ xanh sáng */
    .risk-stable {
        background-color: rgba(22, 163, 74, 0.2);
        color: #86efac;
        border: 1px solid #22c55e;
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
    """Get all active patients from PostgreSQL"""
    db = SessionLocal()
    try:
        patients = db.query(Patient, Admission).join(
            Admission, Patient.patient_id == Admission.patient_id
        ).filter(
            Admission.discharge_time.is_(None)
        ).all()
        
        return [
            {
                'patient_id': p.patient_id,
                'full_name': p.full_name,
                'age': (datetime.now().date() - p.date_of_birth).days // 365,
                'gender': p.gender,
                'device_id': p.device_id,
                'blood_type': p.blood_type,
                'chronic_conditions': p.chronic_conditions,
                'admission_id': a.admission_id,
                'admission_time': a.admission_time,
                'department': a.department,
                'risk_level': a.risk_level,
                'risk_score': a.current_risk_score,
                'diagnosis': a.initial_diagnosis
            }
            for p, a in patients
        ]
    except Exception as e:
        st.error(f"❌ Error getting patients: {e}")
        import traceback
        st.code(traceback.format_exc())
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
    
    # Embed Alert Component
    st.components.v1.html(alert_component_html, height=0, scrolling=False)
    
    # Header
    st.title("🏥 ICU Real-Time Monitoring Dashboard")
    st.markdown("---")

    # --- 🆕 NEW: QUẢN LÝ TRẠNG THÁI (SESSION STATE) ---
    # Giúp Streamlit "nhớ" bệnh nhân đang chọn dù có refresh trang
    if 'selected_patient_id' not in st.session_state:
        st.session_state.selected_patient_id = None
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # --- ✏️ MODIFIED: CHỌN BỆNH NHÂN ---
        # Lấy danh sách bệnh nhân một lần dùng chung
        patients = get_active_patients()
        
        # Tạo dictionary để tra cứu nhanh: {ID: "Tên (ID)"}
        patient_options = {p['patient_id']: f"{p['full_name']} ({p['patient_id']})" for p in patients}
        
        # Widget chọn bệnh nhân
        if patients:
            selected_id = st.selectbox(
                "🔍 Focus Patient (Tab 2 & 3)",
                options=list(patient_options.keys()),
                format_func=lambda x: patient_options.get(x, x),
                index=0,
                key="sb_patient_select"
            )
            st.session_state.selected_patient_id = selected_id
        else:
            st.warning("⚠️ No active patients found. Please load patients first.")
            selected_id = None
            st.session_state.selected_patient_id = None

        st.markdown("---")
        st.subheader("🗂️ Sort & Filter")
        
        # Widget chọn tiêu chí sắp xếp
        sort_option = st.selectbox(
            "Sort Patients By:",
            options=["Risk Level (Highest First)", "Name (A-Z)", "ID (Ascending)", "Admission Time (Newest)"],
            index=0
        )

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
            refresh_interval = st.slider("Refresh Interval (seconds)", 2, 60, 10)
        
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["👥 Patient Overview", "📈 Vital Signs", "🚨 Alerts"])
    
    with tab1:
        st.header("Active Patients Overview")
        
        # Search bar
        search_query = st.text_input("🔎 Filter Patients (Name, ID, Diagnosis)", "").lower()
        
        if not patients:
            st.info("ℹ️ No active patients")
        else:
            # Lọc danh sách dựa trên từ khóa tìm kiếm
            filtered_patients = [
                p for p in patients 
                if search_query in p['full_name'].lower() 
                or search_query in p['patient_id'].lower()
                or (p['diagnosis'] and search_query in p['diagnosis'].lower())
            ]

            # Sort by risk level
            risk_order = {'CRITICAL': 0, 'HIGH': 1, 'MODERATE': 2, 'STABLE': 3, None: 4}
            patients_sorted = sorted(filtered_patients, key=lambda x: risk_order.get(x['risk_level'], 4))
            
            # Hiển thị số lượng tìm thấy
            if search_query:
                st.caption(f"Found {len(patients_sorted)} matching patients.")

            for patient in patients_sorted:
                is_expanded = (patient['patient_id'] == st.session_state.selected_patient_id)
                risk_icon = "🔴" if patient['risk_level'] == 'CRITICAL' else "🟢"
                expander_title = f"{risk_icon} {patient['full_name']} ({patient['patient_id']})"
                
                with st.expander(expander_title, expanded=True):
                    render_patient_card(patient)
                    
                    # Get and display vitals
                    vitals_df = get_patient_vitals(patient['patient_id'], time_range)
                    
                    if not vitals_df.empty:
                        # Latest vitals
                        latest = vitals_df.iloc[-1]
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("💓 Heart Rate", f"{latest['heart_rate']:.0f}" if pd.notna(latest['heart_rate']) else "--")
                        with col2:
                            st.metric("🫁 SpO2", f"{latest['spo2']:.0f}%" if pd.notna(latest['spo2']) else "--")
                        with col3:
                            st.metric("🌡️ Temp", f"{latest['temperature']:.1f}°C" if pd.notna(latest['temperature']) else "--")
                        with col4:
                            st.metric("🫀 BP", f"{latest['bp_systolic']:.0f}/{latest['bp_diastolic']:.0f}" if pd.notna(latest['bp_systolic']) else "--")
                    else:
                        st.warning("⚠️ No data stream")
    
    with tab2:
        # Layout tìm kiếm
        t2_col1, t2_col2 = st.columns([3, 1])
        
        with t2_col2:
            patient_ids = [p['patient_id'] for p in patients]
            
            current_index = 0
            if st.session_state.selected_patient_id in patient_ids:
                current_index = patient_ids.index(st.session_state.selected_patient_id)
            
            selected_in_tab = st.selectbox(
                "🔎 Quick Search / Switch Patient",
                options=patient_ids,
                format_func=lambda x: next((f"{p['full_name']} ({p['patient_id']})" for p in patients if p['patient_id'] == x), x),
                index=current_index,
                key="tab2_patient_selector",
                label_visibility="collapsed",
                placeholder="Type name or ID..."
            )

            if selected_in_tab != st.session_state.selected_patient_id:
                st.session_state.selected_patient_id = selected_in_tab
                st.rerun()

        current_id = st.session_state.selected_patient_id
        
        with t2_col1:
            if current_id:
                p_name = next((p['full_name'] for p in patients if p['patient_id'] == current_id), "Unknown")
                st.subheader(f"📈 Vital Signs: {p_name}")
            else:
                st.subheader("📈 Vital Signs Trends")

        if current_id:
            vitals_df = get_patient_vitals(current_id, time_range)
            
            if not vitals_df.empty:
                # Plot vitals
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=vitals_df['timestamp'],
                    y=vitals_df['heart_rate'],
                    name='Heart Rate',
                    line=dict(color='#ff2b2b', width=2),
                    mode='lines+markers'
                ))
                
                fig.add_trace(go.Scatter(
                    x=vitals_df['timestamp'],
                    y=vitals_df['spo2'],
                    name='SpO2',
                    line=dict(color='#00f2ff', width=2),
                    mode='lines+markers',
                    yaxis='y2'
                ))
                
                fig.update_layout(
                    xaxis_title='Time',
                    yaxis=dict(
                        title='Heart Rate (bpm)', 
                        side='left', 
                        showgrid=True,
                        gridcolor='rgba(128,128,128,0.2)'
                    ),
                    yaxis2=dict(
                        title='SpO2 (%)', 
                        overlaying='y', 
                        side='right', 
                        showgrid=False
                    ),
                    height=450,
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(orientation="h", y=1.1),
                    hovermode="x unified"
                )
                
                # ✅ FIX: Thay use_container_width=True → width='stretch'
                st.plotly_chart(fig, width='stretch')
                
                # Bảng dữ liệu chi tiết
                with st.expander("📋 View Raw Data History"):
                    # ✅ FIX: Thay use_container_width=True → width='stretch'
                    st.dataframe(
                        vitals_df.sort_values(by='timestamp', ascending=False), 
                        width='stretch'
                    )
            else:
                st.warning(f"⚠️ No vital signs data stream available for **{p_name}** ({current_id}) yet.")
                st.info("💡 Tip: Check if the Simulator/Replayer is running.")
        else:
            st.info("⬅️ Please select a patient to view trends.")
    
    with tab3:
        st.header("🚨 Active Alerts")
        
        critical_patients = [p for p in patients if p['risk_level'] in ['CRITICAL', 'HIGH']]
        
        if critical_patients:
            for patient in critical_patients:
                alert_color = "red" if patient['risk_level'] == 'CRITICAL' else "orange"
                alert_icon = "🔴" if patient['risk_level'] == 'CRITICAL' else "🟠"
                
                st.markdown(f"""
                <div style="padding: 1rem; border: 2px solid {alert_color}; border-radius: 10px; margin-bottom: 1rem;">
                    <h3>{alert_icon} {patient['risk_level']} - {patient['full_name']}</h3>
                    <p><b>Diagnosis:</b> {patient['diagnosis']}</p>
                    <p><b>Risk Score:</b> {patient['risk_score']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No critical alerts at this moment.")
    
    # Auto refresh logic
    if auto_refresh:
        import time
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()