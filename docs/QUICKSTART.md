# Quick Start Guide - ICU Monitoring System

## 📋 Prerequisites

### Required Software:

- Python 3.9 or higher
- Docker & Docker Compose
- Git
- 4GB RAM minimum (8GB recommended)

---

## 🚀 Installation Steps

### Step 1: Environment Setup

```bash
# Navigate to project directory
cd /home/hdoop/UET/BigData/ICU

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# venv\Scripts\activate  # On Windows

# Upgrade pip
pip install --upgrade pip
```

### Step 2: Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

### Step 3: Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env if you need to change any settings
# (Default settings should work for local development)
```

### Step 4: Start Big Data Infrastructure

```bash
# Start Kafka, Zookeeper, PostgreSQL, and InfluxDB
docker-compose up -d

# Verify all containers are running
docker-compose ps

# Expected output:
# icu-zookeeper   - Running on port 2181
# icu-kafka       - Running on port 9092
# icu-postgres    - Running on port 5432
# icu-influxdb    - Running on port 8086
```

### Step 5: Wait for Services to Initialize

```bash
# Kafka needs ~30 seconds to fully start
# Check Kafka logs
docker-compose logs -f kafka

# Wait until you see: "started (kafka.server.KafkaServer)"
# Press Ctrl+C to exit logs
```

---

## 🎯 Project Roadmap

### Phase 1: Data Generation & Streaming ⬅️ **START HERE**

1. ✅ Project structure created
2. ⏳ Build patient data simulator
3. ⏳ Create Kafka producer
4. ⏳ Test data streaming

### Phase 2: Data Processing & Storage

5. ⏳ Build Kafka consumer
6. ⏳ Implement data validation
7. ⏳ Set up database storage

### Phase 3: ML Model Development

8. ⏳ Generate training dataset
9. ⏳ Train anomaly detection model
10. ⏳ Integrate ML inference

### Phase 4: Alert System

11. ⏳ Implement alert logic
12. ⏳ Create alert management
13. ⏳ Test alert scenarios

### Phase 5: Dashboard & Visualization

14. ⏳ Build Streamlit dashboard
15. ⏳ Real-time data display
16. ⏳ Alert visualization

---

## 🧪 Verify Installation

### Test Kafka Connection:

```bash
# Create a test topic
docker exec -it icu-kafka kafka-topics --create \
  --topic test-topic \
  --bootstrap-server localhost:9092 \
  --partitions 1 \
  --replication-factor 1

# List topics
docker exec -it icu-kafka kafka-topics --list \
  --bootstrap-server localhost:9092
```

### Test PostgreSQL Connection:

```bash
# Connect to PostgreSQL
docker exec -it icu-postgres psql -U icu_user -d icu_monitoring

# Inside psql, run:
# \dt  -- List tables (should be empty initially)
# \q   -- Quit
```

### Test InfluxDB:

```bash
# Open InfluxDB UI in browser
# http://localhost:8086

# Login credentials (from docker-compose.yml):
# Username: admin
# Password: adminpassword
```

---

## 📁 Project Structure Overview

```
ICU/
├── config/              ✅ Configuration files
├── data/               ✅ Data storage directories
├── src/
│   ├── data_generation/    ⏳ Next: Build this
│   ├── kafka_producer/     ⏳ Then this
│   ├── kafka_consumer/     ⏳ After that
│   ├── ml_models/          ⏳ Later
│   ├── alert_system/       ⏳ Later
│   └── dashboard/          ⏳ Final component
├── docker-compose.yml  ✅ Infrastructure setup
└── requirements.txt    ✅ Python dependencies
```

---

## 🎓 Learning Path

### Week 1-2: Foundation

- [x] Understand architecture
- [x] Set up environment
- [ ] Build data simulator
- [ ] Learn Kafka basics

### Week 3-4: Core Development

- [ ] Implement streaming pipeline
- [ ] Build ML models
- [ ] Create alert system

### Week 5-6: Integration

- [ ] Connect all components
- [ ] Build dashboard
- [ ] End-to-end testing

### Week 7-8: Enhancement

- [ ] Performance tuning
- [ ] Documentation
- [ ] Demo preparation

---

## 🆘 Troubleshooting

### Kafka won't start:

```bash
# Check if port 9092 is already in use
netstat -tuln | grep 9092

# If yes, stop the conflicting service or change port in docker-compose.yml
```

### Docker issues:

```bash
# Stop all containers
docker-compose down

# Remove volumes (caution: deletes data)
docker-compose down -v

# Restart
docker-compose up -d
```

### Python package conflicts:

```bash
# Clear pip cache
pip cache purge

# Reinstall
pip install -r requirements.txt --force-reinstall
```

---

## ✅ Next Steps

You've completed the setup! Now let's build the first component:

**NEXT: Create the Patient Data Simulator**

I'm ready to help you create:

1. Realistic patient vital signs simulator
2. Multiple patient profiles (healthy, at-risk, critical)
3. Temporal patterns and anomalies

Would you like me to create the data generator now?

---

## 📚 Useful Commands

```bash
# Activate environment
source venv/bin/activate

# Start infrastructure
docker-compose up -d

# Stop infrastructure
docker-compose down

# View logs
docker-compose logs -f [service_name]

# Restart a service
docker-compose restart [service_name]

# Check Python environment
pip list

# Run tests (when available)
pytest tests/
```

---

## 🔗 Useful URLs

- Kafka: http://localhost:9092
- InfluxDB UI: http://localhost:8086
- PostgreSQL: localhost:5432
- Dashboard (later): http://localhost:8501
- API (later): http://localhost:8000

---

Need help? Check the docs:

- `docs/ARCHITECTURE.md` - System architecture
- `docs/DATA_SOURCES.md` - Data sources guide
- `README.md` - Project overview
