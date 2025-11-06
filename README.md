# ICU Real-Time Patient Monitoring System

## Big Data Healthcare Analytics Project

### Project Overview

A scalable real-time patient monitoring system using big data technologies to process vital signs, detect anomalies, and alert medical staff.

### Architecture

- **Data Ingestion**: Apache Kafka for streaming vital signs data
- **Stream Processing**: Apache Spark Streaming / Kafka Streams
- **ML Processing**: Real-time anomaly detection using trained models
- **Storage**: Time-series database (InfluxDB) + PostgreSQL
- **Alert System**: ML-based predictions with notification service
- **Visualization**: Real-time dashboard

### Technology Stack

- **Message Queue**: Apache Kafka
- **Stream Processing**: Apache Spark / Kafka Streams
- **Backend**: FastAPI / Flask
- **ML/AI**: scikit-learn, TensorFlow/PyTorch
- **Database**: PostgreSQL, InfluxDB
- **Visualization**: Streamlit / React + D3.js
- **Containerization**: Docker

### Project Structure

```
ICU/
├── data/                      # Data storage and samples
│   ├── raw/                   # Raw sensor data
│   ├── processed/             # Processed data
│   ├── models/                # Trained ML models
│   └── synthetic/             # Synthetic/simulated data
├── src/
│   ├── data_generation/       # Simulates patient vital signs
│   ├── kafka_producer/        # Sends data to Kafka topics
│   ├── kafka_consumer/        # Consumes data from Kafka
│   ├── stream_processing/     # Real-time data processing
│   ├── ml_models/             # ML model training and inference
│   ├── alert_system/          # Alert generation and notification
│   ├── api/                   # REST API endpoints
│   └── dashboard/             # Visualization interface
├── notebooks/                 # Jupyter notebooks for analysis
├── tests/                     # Unit and integration tests
├── config/                    # Configuration files
├── docker/                    # Docker configurations
├── scripts/                   # Utility scripts
└── docs/                      # Documentation

```

### Getting Started

1. Set up environment: `pip install -r requirements.txt`
2. Start Kafka: `docker-compose up -d kafka zookeeper`
3. Run data generator: `python src/data_generation/simulator.py`
4. Start consumer: `python src/kafka_consumer/consumer.py`
5. Launch dashboard: `streamlit run src/dashboard/app.py`

### Contributors

- Your Name - University Project

### License

MIT License
