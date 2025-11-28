# ICU Real-Time Patient Monitoring System 🏥

## Big Data Healthcare Analytics Project

## 👥 Contributors

Luong Minh Tri 


Ngo Quang Dung

### 🎯 Project Overview

A **production-ready** real-time patient monitoring system using big data technologies to process vital signs from VitalDB dataset, detect critical conditions using MEWS scoring, and **actively alert** medical staff through WebSocket-based notifications with audio and browser alerts.

**Key Achievement**: Successfully implemented active alerting system that addresses the core problem: "Doctors cannot monitor screens 24/7" ✅

### 🏗️ Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   VitalDB   │───>│    Kafka     │───>│  Consumer   │
│   Dataset   │    │   (Stream)   │    │ (Processor) │
│  (3359 ICU) │    │              │    │  + MEWS     │
└─────────────┘    └──────────────┘    └─────────────┘
                                              │
                    ┌─────────────────────────┴───────────────┐
                    │                                         │
                    ▼                                         ▼
        ┌────────────────────┐                  ┌──────────────────────┐
        │    InfluxDB        │                  │    PostgreSQL        │
        │  (Time-Series)     │                  │  (Patient Metadata)  │
        └────────────────────┘                  └──────────────────────┘
                    │                                         │
                    └─────────────────────┬───────────────────┘
                                         ▼
                              ┌──────────────────┐
                              │  Streamlit       │
                              │  Dashboard       │
                              │  + WebSocket     │
                              │  + Audio Alerts  │
                              └──────────────────┘
```

**Active Alerting Flow**:

```
Vital Signs → Kafka → MEWS Scorer → Alert (if HIGH/CRITICAL)
→ patient-alerts topic → WebSocket Server → Dashboard
→ 🔊 Audio + 🚨 Popup + 📬 Browser Notification
```

### 🚀 Technology Stack

- **Message Queue**: Apache Kafka 2.6.0
- **Stream Processing**: Custom processor with MEWS scoring
- **Backend**: Python 3.12 + asyncio
- **ML/AI**: Scikit-learn (risk scoring)
- **Database**: PostgreSQL 15.14, InfluxDB (time-series)
- **Visualization**: Streamlit 1.28.1 + Plotly 5.18.0
- **Real-time Alerts**: WebSockets 12.0
- **Data Source**: VitalDB (6,388 real surgical cases)
- **Containerization**: Docker + docker-compose

### 📊 Dataset

**Source**: [VitalDB](https://vitaldb.net/) - Open Intraoperative Data  
**Total Cases**: 6,388 surgical patients  
**Filtered ICU Cases**: 3,359 cases matching criteria:

- ICU admission > 0 days
- Case duration > 4 hours
- High-risk procedures (cardiac, thoracic, vascular)
- Emergency operations
- ASA class 4-5
- Age > 70 years

**Vital Signs Tracked**:

- Heart Rate (HR)
- SpO2 (Oxygen Saturation)
- Blood Pressure (Systolic/Diastolic)
- Temperature
- Respiratory Rate

### Prerequisites

- Python 3.12+
- Docker & docker-compose
- 8GB RAM minimum
- 20GB disk space

### Installation

```bash
# 1. Clone repository
cd ~/UET/BigData/ICU

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
```

### Launch System 🎬

#### 1. Kích hoạt môi trường ảo (Nếu chưa)

source venv/bin/activate

#### 2. Khởi động Hạ tầng (Docker Containers: Kafka, Postgres, InfluxDB...)

#### Đợi khoảng 15-30s để các container khởi động hoàn toàn

#### 3. Làm sạch & Khởi tạo dữ liệu nền (Làm 1 lần)

** Xóa dữ liệu cũ để tránh xung đột ID **

python scripts/reset_database.py

#### 4. Nạp hồ sơ bệnh nhân (Metadata) bắt đầu streaming

** hoặc tùy chọn bệnh nhân theo hướng muốn streaming ở folder data **

python scripts/run_vitaldb_replayer.py

#### 5. Chạy consumer để thu thập dữ liệu từ kafka

python scripts/run_consumer.py

#### 6. Hiển thị giao diện

streamlit run src/dashboard/streamlit_app.py

##### Access Dashboard

Open browser: **http://localhost:8501**

### Stop System

docker compose down

## 📚 Features

### ✅ Completed

- Real-time data pipeline (Kafka)
- MEWS risk scoring
- Active alerting with WebSocket
- Audio + visual + browser notifications
- Multi-axis dashboard
- Search & filter patients

## 📜 License

MIT License

---

---

```

```
