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

# ✅ Load WebSocket Alert Component
@st.cache_data
def load_alert_component():
    """Load alert HTML component with WebSocket"""
    alert_html_path = Path(__file__).parent / "alert_component.html"
    with open(alert_html_path, 'r', encoding='utf-8') as f:
        return f.read()

# Inject WebSocket alert component
st.components.v1.html(load_alert_component(), height=0, scrolling=False)

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
        
        # --- ✏️ MODIFIED: CHUYỂN CHỌN BỆNH NHÂN RA SIDEBAR ---
        # Lấy danh sách bệnh nhân một lần dùng chung
        patients = get_active_patients()
        
        # Tạo dictionary để tra cứu nhanh: {ID: "Tên (ID)"}
        patient_options = {p['patient_id']: f"{p['full_name']} ({p['patient_id']})" for p in patients}
        
        # Widget chọn bệnh nhân (Có chức năng tìm kiếm tích hợp sẵn của Streamlit)
        # index=None nghĩa là mặc định không chọn ai
        selected_id = st.selectbox(
            "🔍 Focus Patient (Tab 2 & 3)",
            options=list(patient_options.keys()),
            format_func=lambda x: patient_options.get(x, x),
            index=0 if patients else None,
            key="sb_patient_select" # Key quan trọng để giữ trạng thái
        )
        
        # Cập nhật session state
        st.session_state.selected_patient_id = selected_id

        st.markdown("---")
        st.markdown("---")
        st.subheader("🗂️ Sort & Filter")
        
        # Widget chọn tiêu chí sắp xếp
        sort_option = st.selectbox(
            "Sort Patients By:",
            options=["Risk Level (Highest First)", "Name (A-Z)", "ID (Ascending)", "Admission Time (Newest)"],
            index=0 # Mặc định chọn Risk Level
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
            refresh_interval = st.slider("Refresh Interval (seconds)", 5, 60, 10)
        
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["👥 Patient Overview", "📈 Vital Signs", "🚨 Alerts"])
    
    with tab1:
        st.header("Active Patients Overview")
        
        # --- 🆕 NEW: THANH TÌM KIẾM CHO TAB OVERVIEW ---
        # Giúp lọc nhanh danh sách thẻ bệnh nhân
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
                # Expander mở sẵn nếu là bệnh nhân đang chọn ở Sidebar
                is_expanded = (patient['patient_id'] == st.session_state.selected_patient_id)
                
                # Thêm icon cảnh báo vào tiêu đề expander
                risk_icon = "🔴" if patient['risk_level'] == 'CRITICAL' else "🟢"
                expander_title = f"{risk_icon} {patient['full_name']} ({patient['patient_id']})"
                
                with st.expander(expander_title, expanded=True): # Luôn expanded=True cho dễ nhìn dashboard tổng quan
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
        # --- 🆕 NEW: LAYOUT TÌM KIẾM TRONG TAB ---
        # Chia cột: Bên trái là Tiêu đề, Bên phải là Ô tìm kiếm nhanh
        t2_col1, t2_col2 = st.columns([3, 1])
        
        with t2_col2:
            # Lấy danh sách ID để làm options
            patient_ids = [p['patient_id'] for p in patients]
            
            # Tìm vị trí (index) của bệnh nhân đang chọn trong session_state
            # Để set giá trị mặc định cho dropdown này khớp với Sidebar
            current_index = 0
            if st.session_state.selected_patient_id in patient_ids:
                current_index = patient_ids.index(st.session_state.selected_patient_id)
            
            # Widget chọn bệnh nhân tại chỗ (Local Selector)
            selected_in_tab = st.selectbox(
                "🔎 Quick Search / Switch Patient",
                options=patient_ids,
                format_func=lambda x: next((f"{p['full_name']} ({p['patient_id']})" for p in patients if p['patient_id'] == x), x),
                index=current_index,
                key="tab2_patient_selector",
                label_visibility="collapsed", # Ẩn nhãn cho gọn
                placeholder="Type name or ID..."
            )

            # --- LOGIC ĐỒNG BỘ ---
            # Nếu người dùng chọn người khác ở đây, cập nhật ngược lại Session State
            if selected_in_tab != st.session_state.selected_patient_id:
                st.session_state.selected_patient_id = selected_in_tab
                st.rerun() # Load lại trang để Sidebar cũng cập nhật theo

        # --- PHẦN HIỂN THỊ BIỂU ĐỒ (Code cũ đã tinh chỉnh) ---
        current_id = st.session_state.selected_patient_id
        
        with t2_col1:
            if current_id:
                # Lấy tên bệnh nhân để hiện lên tiêu đề
                p_name = next((p['full_name'] for p in patients if p['patient_id'] == current_id), "Unknown")
                st.subheader(f"📈 Vital Signs: {p_name}")
            else:
                st.subheader("📈 Vital Signs Trends")

        if current_id:
            # Lấy dữ liệu
            vitals_df = get_patient_vitals(current_id, time_range)
            
            if not vitals_df.empty:
                # Plot vitals
                fig = go.Figure()
                
                # Heart Rate (Trục trái)
                fig.add_trace(go.Scatter(
                    x=vitals_df['timestamp'],
                    y=vitals_df['heart_rate'],
                    name='Heart Rate',
                    line=dict(color='#ff2b2b', width=2),
                    mode='lines+markers'
                ))
                
                # SpO2 (Trục phải)
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
                    hovermode="x unified" # Hiệu ứng hover đẹp hơn
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Bảng dữ liệu chi tiết
                with st.expander("📋 View Raw Data History"):
                    # Sắp xếp mới nhất lên đầu
                    st.dataframe(
                        vitals_df.sort_values(by='timestamp', ascending=False), 
                        use_container_width=True
                    )
            else:
                # Thông báo đẹp hơn khi không có data
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
                
                # Highlight card
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