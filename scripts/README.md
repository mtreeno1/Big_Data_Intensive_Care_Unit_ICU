# README - Scripts Directory

## 🛠️ Utility Scripts

This directory contains utility scripts to help manage the ICU Monitoring System.

### Available Scripts

#### `setup.sh` - Initial Setup

Complete setup for first-time installation:

- Creates Python virtual environment
- Installs all dependencies
- Creates configuration files
- Starts Docker infrastructure

**Usage:**

```bash
cd /home/hdoop/UET/BigData/ICU
./scripts/setup.sh
```

#### `start.sh` - Start Services

Starts all infrastructure services (Kafka, PostgreSQL, InfluxDB):

**Usage:**

```bash
./scripts/start.sh
```

#### `stop.sh` - Stop Services

Stops all running services:

**Usage:**

```bash
./scripts/stop.sh
```

#### `status.sh` - Check Status

Displays status of all services and components:

**Usage:**

```bash
./scripts/status.sh
```

---

## 📝 Quick Reference

```bash
# First time setup
./scripts/setup.sh

# Start services
./scripts/start.sh

# Check if everything is running
./scripts/status.sh

# Stop services when done
./scripts/stop.sh
```

---

## 🔍 Troubleshooting

If scripts fail:

1. Check if you have execution permissions: `ls -l scripts/`
2. Make executable: `chmod +x scripts/*.sh`
3. Check if Docker is running: `docker ps`
4. Check logs: `docker-compose logs`
