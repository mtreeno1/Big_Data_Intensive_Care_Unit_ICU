# Data Sources for ICU Real-Time Patient Monitoring System

## 📊 Recommended Data Sources

### 1. **Public Healthcare Datasets** (For Training ML Models)

#### MIMIC-III / MIMIC-IV (MIT)

- **What**: Medical Information Mart for Intensive Care
- **Content**: De-identified health data from ICU patients
- **Size**: 60,000+ ICU admissions
- **Access**: Requires registration and CITI training
- **Use Case**: Train ML models for anomaly detection
- **URL**: https://physionet.org/content/mimiciii/
- **Note**: You said to ignore for now, but keep this for future model training

#### PhysioNet Databases

- **What**: Repository of physiological signals
- **Content**: ECG, blood pressure, respiratory waveforms
- **Size**: Multiple datasets available
- **Access**: Free with registration
- **Use Case**: Time-series pattern learning
- **URL**: https://physionet.org/about/database/

#### eICU Collaborative Research Database

- **What**: Multi-center ICU database
- **Content**: 200,000+ ICU admissions from multiple hospitals
- **Access**: Requires credentialing
- **Use Case**: Multi-patient pattern analysis
- **URL**: https://physionet.org/content/eicu-crd/

---

### 2. **Synthetic Data Generation** (Recommended for Prototyping)

#### ✅ Custom Patient Simulator (We'll Build This)

**Advantages**:

- Full control over parameters
- No privacy concerns
- Unlimited data generation
- Can simulate specific conditions

**What We'll Simulate**:

```python
Patient Vital Signs:
├── Heart Rate (HR): 40-180 bpm
├── SpO₂: 85-100%
├── Blood Pressure: Systolic (80-200) / Diastolic (50-120)
├── Temperature: 35-42°C
├── Respiratory Rate: 8-40 breaths/min
└── Additional: ECG patterns, consciousness level
```

**Scenarios to Simulate**:

- Normal stable patient
- Gradual deterioration
- Sudden critical events (cardiac arrest, septic shock)
- Post-surgery recovery
- Chronic conditions (COPD, heart failure)
- Multiple patients simultaneously

---

### 3. **Real-Time Streaming Simulation**

#### Option A: Time-Series Pattern Generation

```python
# Realistic patterns with:
- Circadian rhythms (day/night variations)
- Respiratory sinus arrhythmia
- Blood pressure variations
- Temperature fluctuations
- Noise and measurement errors
```

#### Option B: Replay Historical Data

```python
# Record-and-replay approach:
- Load historical dataset
- Stream it through Kafka at real-time speed
- Add random variations
```

---

### 4. **For Your Big Data Project - Recommended Approach**

#### 🎯 **Phase 1: Start with Synthetic Data** (Current Phase)

**Why**:

- No legal/privacy issues
- Can generate millions of records
- Control over anomaly patterns
- Fast iteration and testing

**Implementation**:

```
Data Generator → Kafka Producer → Kafka Topic
     ↓
Generate 10-100 patients
Each sends data every 1-5 seconds
Different health conditions
Realistic temporal patterns
```

#### 🎯 **Phase 2: Add Real Dataset for ML Training**

**Why**:

- Train more accurate models
- Validate against real patterns
- Academic credibility

**Suggested Dataset**:

- **PhysioNet Challenge Datasets** (Freely available)
- **UCI ML Repository - Healthcare datasets**
- **Kaggle Healthcare Competitions**

#### 🎯 **Phase 3: Big Data Volume Simulation**

**Why**: Demonstrate big data skills

- Simulate 1000+ concurrent patients
- Generate GBs of streaming data
- Test scalability of Kafka + Spark
- Process millions of records/hour

---

## 📁 Data Schema Design

### Vital Signs Stream (Kafka Topic: `vital-signs`)

```json
{
  "patient_id": "PT-001",
  "room_id": "ICU-101",
  "timestamp": "2025-11-04T10:30:45.123Z",
  "vitals": {
    "heart_rate": 75,
    "spo2": 98,
    "blood_pressure": {
      "systolic": 120,
      "diastolic": 80
    },
    "temperature": 37.0,
    "respiratory_rate": 16
  },
  "device_id": "MONITOR-001",
  "quality_indicators": {
    "hr_confidence": 0.95,
    "spo2_confidence": 0.98
  }
}
```

### Alert Stream (Kafka Topic: `patient-alerts`)

```json
{
  "alert_id": "ALERT-20251104-001",
  "patient_id": "PT-001",
  "timestamp": "2025-11-04T10:30:45.123Z",
  "alert_type": "ANOMALY_DETECTED",
  "severity": "HIGH",
  "details": {
    "anomaly_score": 0.85,
    "affected_vitals": ["heart_rate", "spo2"],
    "predicted_risk": "CARDIAC_DISTRESS"
  },
  "model_version": "v1.2.0"
}
```

---

## 🎲 Data Generation Strategy for Your Project

### Approach 1: Simple Random Walk (Quick Start)

```python
# Each vital sign follows realistic ranges
# Add Gaussian noise
# Occasionally inject anomalies
```

### Approach 2: Physiologically-Accurate Simulation (Better)

```python
# Model correlations between vitals
# Heart rate affects blood pressure
# SpO2 relates to respiratory rate
# Add realistic temporal patterns
```

### Approach 3: Scenario-Based Generation (Best for Demo)

```python
# Define patient profiles:
Profile 1: Healthy post-surgery (stable)
Profile 2: Sepsis patient (deteriorating)
Profile 3: Cardiac arrest (critical events)
Profile 4: COPD patient (chronic instability)
```

---

## 📈 Big Data Characteristics to Demonstrate

### Volume

- Generate 100+ patients × 1 reading/second × 24 hours = 8.64M records/day
- Store in InfluxDB (time-series) + PostgreSQL (alerts)

### Velocity

- Real-time streaming via Kafka
- Process within 100ms of data arrival
- ML inference in near real-time

### Variety

- Structured: Vital signs numeric data
- Semi-structured: JSON messages
- Time-series: Continuous measurements

### Veracity

- Add realistic noise and missing data
- Handle out-of-range values
- Quality indicators

---

## 🚀 Next Steps for Data

1. **Create synthetic data generator**
2. **Set up Kafka topics** for streaming
3. **Define patient profiles** with different conditions
4. **Generate baseline dataset** for ML model training
5. **Stream data in real-time** for testing

---

## 📚 Additional Resources

### Free Healthcare Datasets:

- **Kaggle**: Heart Disease, Diabetes, ICU datasets
- **UCI ML Repository**: Healthcare section
- **Data.gov**: Public health data
- **WHO**: Global health statistics

### Data Generation Tools:

- **Synthea**: Synthetic patient generator
- **Mockaroo**: Custom data generation
- **Faker**: Python library for fake data

---

## ✅ Recommended Data Sources FOR YOUR PROJECT:

1. **Primary**: Custom synthetic data generator (we build this)
2. **Training**: PhysioNet or Kaggle healthcare datasets
3. **Validation**: Mix synthetic + real patterns
4. **Demo**: Multi-patient concurrent simulation

This approach gives you:

- ✅ No privacy/legal issues
- ✅ Unlimited data for testing
- ✅ Control over scenarios
- ✅ Demonstrates big data skills
- ✅ Realistic for university project

---
