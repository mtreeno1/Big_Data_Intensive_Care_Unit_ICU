# Big Data Architecture for ICU Monitoring System

## 🏗️ System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    ICU REAL-TIME MONITORING SYSTEM                               │
│                         (Big Data Architecture)                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: DATA GENERATION                                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │  Patient 1  │  │  Patient 2  │  │  Patient N  │  │  Synthetic  │           │
│  │  Simulator  │  │  Simulator  │  │  Simulator  │  │   Dataset   │           │
│  │  (Python)   │  │  (Python)   │  │  (Python)   │  │  Replayer   │           │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘           │
│         │                │                │                │                     │
│         └────────────────┴────────────────┴────────────────┘                     │
│                                   │                                              │
└───────────────────────────────────┼──────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 2: MESSAGE QUEUE (Apache Kafka)                                          │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐       │
│  │                     KAFKA CLUSTER                                     │       │
│  │  ┌──────────────────────┐        ┌──────────────────────┐          │       │
│  │  │  Topic: vital-signs  │        │  Topic: patient-     │          │       │
│  │  │  - Partitions: 3     │        │         alerts       │          │       │
│  │  │  - Replication: 1    │        │  - Partitions: 2     │          │       │
│  │  │  - Retention: 7 days │        │  - Replication: 1    │          │       │
│  │  └──────────────────────┘        └──────────────────────┘          │       │
│  └─────────────────────────────────────────────────────────────────────┘       │
│                                                                                   │
└───────────────────────────────┬───────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 3: STREAM PROCESSING                                                      │
│                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐         │
│  │                  KAFKA CONSUMER GROUP                              │         │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │         │
│  │  │  Consumer 1  │  │  Consumer 2  │  │  Consumer N  │            │         │
│  │  │  (Python)    │  │  (Python)    │  │  (Python)    │            │         │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘            │         │
│  └─────────┼──────────────────┼──────────────────┼────────────────────┘         │
│            │                  │                  │                               │
│            └──────────────────┴──────────────────┘                               │
│                              │                                                   │
│                              ▼                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐         │
│  │              DATA PROCESSING PIPELINE                              │         │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐      │         │
│  │  │ Validate  │→ │ Transform │→ │ Aggregate │→ │   Store   │      │         │
│  │  │   Data    │  │   Data    │  │  Windows  │  │   Data    │      │         │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘      │         │
│  └────────────────────────────────────────────────────────────────────┘         │
│                              │                                                   │
└──────────────────────────────┼───────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 4: ML PROCESSING & ANOMALY DETECTION                                     │
│                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐         │
│  │                    ML INFERENCE ENGINE                             │         │
│  │  ┌─────────────────┐    ┌──────────────────┐   ┌──────────────┐  │         │
│  │  │ Isolation Forest │    │  LSTM Autoencoder │   │  XGBoost     │  │         │
│  │  │  (Unsupervised)  │    │   (Deep Learning) │   │ (Classifier) │  │         │
│  │  └─────────────────┘    └──────────────────┘   └──────────────┘  │         │
│  │                                                                    │         │
│  │  ┌─────────────────────────────────────────────────────────────┐ │         │
│  │  │              ANOMALY SCORING ENGINE                         │ │         │
│  │  │  - Real-time inference                                      │ │         │
│  │  │  - Multi-model ensemble                                     │ │         │
│  │  │  - Risk score calculation                                   │ │         │
│  │  └─────────────────────────────────────────────────────────────┘ │         │
│  └────────────────────────────────────────────────────────────────────┘         │
│                              │                                                   │
└──────────────────────────────┼───────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 5: ALERT & NOTIFICATION SYSTEM                                           │
│                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐         │
│  │                    ALERT DECISION ENGINE                           │         │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │         │
│  │  │  ML-Based    │  │  Threshold   │  │   Hybrid     │            │         │
│  │  │  Alerts      │  │  Alerts      │  │   Rules      │            │         │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘            │         │
│  │         └──────────────────┴──────────────────┘                    │         │
│  │                            │                                        │         │
│  │  ┌─────────────────────────▼────────────────────────────┐          │         │
│  │  │        ALERT PRIORITY & ROUTING                      │          │         │
│  │  │  - Severity classification (LOW/MED/HIGH/CRITICAL)   │          │         │
│  │  │  - Alert deduplication                               │          │         │
│  │  │  - Rate limiting                                     │          │         │
│  │  └──────────────────────────────────────────────────────┘          │         │
│  └────────────────────────────────────────────────────────────────────┘         │
│                              │                                                   │
│         ┌────────────────────┴────────────────────┐                             │
│         ▼                                          ▼                             │
│  ┌─────────────┐                          ┌──────────────┐                      │
│  │   Kafka     │                          │   Database   │                      │
│  │   Topic:    │                          │   Storage    │                      │
│  │   alerts    │                          │              │                      │
│  └─────────────┘                          └──────────────┘                      │
└──────────────────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 6: DATA STORAGE                                                           │
│                                                                                   │
│  ┌──────────────────────┐      ┌──────────────────────┐                         │
│  │   InfluxDB           │      │   PostgreSQL         │                         │
│  │   (Time-Series DB)   │      │   (Relational DB)    │                         │
│  │                      │      │                      │                         │
│  │  - Vital signs       │      │  - Patient metadata  │                         │
│  │  - Measurements      │      │  - Alert history     │                         │
│  │  - High-frequency    │      │  - User accounts     │                         │
│  │    data              │      │  - Configurations    │                         │
│  └──────────────────────┘      └──────────────────────┘                         │
│                                                                                   │
└───────────────────────────────┬───────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 7: API & APPLICATION LAYER                                               │
│                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐         │
│  │                     FastAPI REST API                               │         │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │         │
│  │  │  /patients   │  │   /vitals    │  │   /alerts    │            │         │
│  │  │  endpoints   │  │  endpoints   │  │  endpoints   │            │         │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │         │
│  │                                                                    │         │
│  │  ┌─────────────────────────────────────────────────────────────┐ │         │
│  │  │              WebSocket Server                               │ │         │
│  │  │  - Real-time data push to dashboard                         │ │         │
│  │  │  - Alert notifications                                      │ │         │
│  │  └─────────────────────────────────────────────────────────────┘ │         │
│  └────────────────────────────────────────────────────────────────────┘         │
│                                                                                   │
└───────────────────────────────┬───────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 8: VISUALIZATION & DASHBOARD                                             │
│                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐         │
│  │                   STREAMLIT DASHBOARD                              │         │
│  │                                                                    │         │
│  │  ┌─────────────────────────────────────────────────────────────┐  │         │
│  │  │  REAL-TIME MONITORING VIEW                                  │  │         │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │  │         │
│  │  │  │Patient 1 │  │Patient 2 │  │Patient 3 │  │Patient N │   │  │         │
│  │  │  │  Panel   │  │  Panel   │  │  Panel   │  │  Panel   │   │  │         │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │  │         │
│  │  └─────────────────────────────────────────────────────────────┘  │         │
│  │                                                                    │         │
│  │  ┌─────────────────────────────────────────────────────────────┐  │         │
│  │  │  ALERT MANAGEMENT                                           │  │         │
│  │  │  - Active alerts list                                       │  │         │
│  │  │  - Alert history                                            │  │         │
│  │  │  - Severity filtering                                       │  │         │
│  │  └─────────────────────────────────────────────────────────────┘  │         │
│  │                                                                    │         │
│  │  ┌─────────────────────────────────────────────────────────────┐  │         │
│  │  │  ANALYTICS & TRENDS                                         │  │         │
│  │  │  - Time-series charts                                       │  │         │
│  │  │  - Statistical summaries                                    │  │         │
│  │  │  - ML model performance                                     │  │         │
│  │  └─────────────────────────────────────────────────────────────┘  │         │
│  └────────────────────────────────────────────────────────────────────┘         │
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow

### Real-Time Data Pipeline:

```
1. Data Generation → 2. Kafka Producer → 3. Kafka Topic → 4. Consumer Group →
5. Stream Processing → 6. ML Inference → 7. Alert Decision → 8. Storage → 9. Dashboard
```

### Latency Goals:

- Data generation → Kafka: < 10ms
- Kafka → Consumer: < 50ms
- ML Inference: < 100ms
- Alert generation: < 200ms
- Dashboard update: < 500ms
- **Total E2E latency: < 1 second**

---

## 🔧 Technology Justification (Big Data Context)

### Apache Kafka

- **Why**: Industry standard for real-time streaming
- **Big Data Feature**: Handles millions of messages/second, horizontal scaling
- **Use Case**: Decouple data producers from consumers, enable multiple processing pipelines

### InfluxDB

- **Why**: Optimized for time-series data
- **Big Data Feature**: Compress time-series data, fast queries for time ranges
- **Use Case**: Store high-frequency vital signs (multiple readings/second)

### Python + Pandas/NumPy

- **Why**: Rich ecosystem for data science and ML
- **Big Data Feature**: Integration with Spark, efficient array operations
- **Use Case**: Data processing, feature engineering, model inference

### FastAPI

- **Why**: High-performance async Python framework
- **Big Data Feature**: Async I/O for concurrent requests
- **Use Case**: Real-time API for dashboard, WebSocket support

---

## 🎯 Big Data Capabilities Demonstrated

1. **Volume**: Process millions of vital sign measurements per day
2. **Velocity**: Real-time streaming with sub-second latency
3. **Variety**: Structured (vitals) + Semi-structured (alerts) + Time-series
4. **Veracity**: Handle missing data, outliers, sensor errors
5. **Scalability**: Kafka partitioning, consumer groups, horizontal scaling
6. **ML Integration**: Real-time inference on streaming data
7. **Storage Strategy**: Hybrid (time-series + relational)

---

## 📈 Scalability Features

### Horizontal Scaling:

- **Kafka**: Add more brokers, increase partitions
- **Consumers**: Add more consumer instances in the group
- **API**: Deploy multiple FastAPI instances behind load balancer

### Performance Optimization:

- **Batch Processing**: Process messages in micro-batches
- **Parallel Processing**: Multi-threaded consumers
- **Caching**: Redis for frequently accessed data
- **Indexing**: Proper database indexes for queries

---

## 🔐 Production Considerations (Future)

- Authentication & Authorization
- Data encryption (at rest and in transit)
- Audit logging
- Monitoring & Alerting (Prometheus + Grafana)
- Backup & Disaster Recovery
- HIPAA compliance considerations

---

This architecture balances:
✅ Big data principles
✅ Real-time processing
✅ ML integration
✅ Practical implementation for university project
✅ Scalability for future enhancement
