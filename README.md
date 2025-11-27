# ICU Real-Time Patient Monitoring System 🏥

## Big Data Healthcare Analytics Project

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

### 📁 Project Structure

```
ICU/
├── data/                      # Data storage and samples
│   ├── raw/                   # Raw VitalDB data
│   ├── processed/             # Processed time-series
│   ├── icu_like_cases.csv     # Filtered 3,359 ICU cases
│   ├── patients.csv           # Patient metadata
│   └── clinical_data.csv      # Clinical parameters
├── src/
│   ├── data_generation/       # Patient vital signs simulator
│   ├── kafka_producer/        # Kafka producer (50 patients)
│   ├── kafka_consumer/        # Full E.T.L.A pipeline
│   ├── stream_processing/     # MEWS risk scorer + validator
│   ├── ml_models/             # Risk scoring algorithms
│   ├── alerting/              # 🆕 WebSocket alert server
│   ├── storage/               # InfluxDB + PostgreSQL managers
│   ├── database/              # SQLAlchemy models
│   ├── api/                   # REST API (future)
│   └── dashboard/             # Streamlit dashboard + alert component
├── scripts/                   # Operational scripts
│   ├── run_producer.py        # Start Kafka producer
│   ├── run_consumer.py        # Start consumer pipeline
│   ├── run_alert_server.py    # 🆕 Start WebSocket server
│   ├── test_alerts.py         # 🆕 Test alert system
│   ├── setup_alert_system.sh  # 🆕 One-command startup
│   └── stop_alert_system.sh   # 🆕 One-command shutdown
├── docs/                      # Documentation
│   ├── ACTIVE_ALERTING.md     # 🆕 Active alerting guide
│   ├── ARCHITECTURE.md        # System architecture
│   ├── DATA_SOURCES.md        # VitalDB dataset guide
│   └── QUICKSTART.md          # Quick start guide
├── notebooks/                 # Analysis notebooks
├── tests/                     # Unit and integration tests
├── config/                    # Configuration management
├── docker-compose.yml         # Docker orchestration
└── requirements.txt           # Python dependencies
```

---

## 🚀 Quick Start

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

### Launch System (One Command) 🎬

```bash
# Activate virtual environment first
source venv/bin/activate

# Start everything
./scripts/setup_alert_system.sh
```

### Access Dashboard

Open browser: **http://localhost:8501**

### Test Alerts

```bash
python scripts/test_alerts.py
```

### Stop System

```bash
./scripts/stop_alert_system.sh
```

---

## 📚 Features

### ✅ Completed

- Real-time data pipeline (Kafka)
- MEWS risk scoring
- Active alerting with WebSocket
- Audio + visual + browser notifications
- Multi-axis dashboard
- Search & filter patients

### 🔄 In Progress

- Alert escalation
- Historical analysis

### ⏳ Planned

- Telegram/Slack integration
- SMS notifications
- Mobile app

---

## 📖 Documentation

- **[ACTIVE_ALERTING.md](docs/ACTIVE_ALERTING.md)**: WebSocket alerting guide
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: System design
- **[DATA_SOURCES.md](docs/DATA_SOURCES.md)**: VitalDB documentation

---

## 🐛 Troubleshooting

See [ACTIVE_ALERTING.md](docs/ACTIVE_ALERTING.md#troubleshooting)

---

## 📜 License

MIT License

---

## 👥 Contributors

- Big Data Healthcare Analytics Project
- University of Engineering and Technology (UET)
- 2024

---

**Status**: Production Ready ✅

### License

MIT License

```

```
