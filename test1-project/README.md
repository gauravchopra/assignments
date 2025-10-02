# rbcapp1 Monitoring System

A comprehensive monitoring system for the critical "rbcapp1" application and its dependent services. The system monitors three dependent services (httpd, rabbitMQ, and postgreSQL) running on Linux machines and provides status reporting through JSON files and a REST API with Elasticsearch integration.

## Table of Contents

- [Overview](#overview)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Monitoring Script](#monitoring-script)
- [File Formats](#file-formats)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## Overview

The rbcapp1 monitoring system consists of two main components:

1. **Monitoring Script**: Checks Linux service status using systemctl and generates timestamped JSON status files
2. **REST API**: Manages status data in Elasticsearch and provides health check endpoints

### Key Features

- Real-time monitoring of Linux services (httpd, rabbitMQ, postgreSQL)
- Application status determination based on service dependencies
- JSON file generation with timestamps
- REST API for data management and retrieval
- Elasticsearch integration for historical data storage
- Comprehensive error handling and logging
- Command-line interface with flexible options

## System Requirements

### Operating System
- Linux (systemctl required for service monitoring)
- Tested on CentOS, RHEL, Ubuntu, and Debian

### Software Dependencies
- Python 3.8 or higher
- systemctl (systemd)
- Elasticsearch 8.x (for API functionality)

### Hardware Requirements
- Minimum 512MB RAM
- 100MB disk space for application
- Additional space for JSON files and logs

### Network Requirements
- Access to Elasticsearch cluster (default: localhost:9200)
- Network connectivity for API endpoints (default: port 5000)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd rbcapp1-monitoring
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Or install using setup.py
pip install -e .

# For development (includes testing tools)
pip install -e ".[dev]"
```

### 4. Create Data Directory

```bash
mkdir -p data
chmod 755 data
```

### 5. Verify Installation

```bash
# Test monitoring script
python -m src.monitor.main --help

# Test API (requires Elasticsearch)
python -m src.api.app
```

## Configuration

### Environment Variables

The system can be configured using environment variables:

```bash
# Elasticsearch Configuration
export ELASTICSEARCH_HOST=localhost
export ELASTICSEARCH_PORT=9200
export ELASTICSEARCH_INDEX=service-monitoring

# API Configuration
export API_HOST=0.0.0.0
export API_PORT=5000
export API_DEBUG=false

# File System Configuration
export DATA_DIR=data
```

### Elasticsearch Setup

#### Option 1: Docker (Recommended for Development)

```bash
# Start Elasticsearch with Docker
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  elasticsearch:8.10.0

# Verify Elasticsearch is running
curl http://localhost:9200
```

#### Option 2: Native Installation

```bash
# Download and install Elasticsearch (example for Linux)
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.10.0-linux-x86_64.tar.gz
tar -xzf elasticsearch-8.10.0-linux-x86_64.tar.gz
cd elasticsearch-8.10.0/

# Start Elasticsearch
./bin/elasticsearch
```

#### Option 3: Package Manager

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install elasticsearch

# CentOS/RHEL
sudo yum install elasticsearch

# Start service
sudo systemctl start elasticsearch
sudo systemctl enable elasticsearch
```

### Index Configuration

The system automatically creates the required Elasticsearch index. For manual setup:

```bash
# Create index with mapping
curl -X PUT "localhost:9200/service-monitoring" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "service_name": {"type": "keyword"},
      "service_status": {"type": "keyword"},
      "host_name": {"type": "keyword"},
      "timestamp": {"type": "date"}
    }
  }
}
'
```

### Service Configuration

Ensure the monitored services are properly configured:

```bash
# Check if services exist and are configured
systemctl status httpd
systemctl status rabbitmq-server  # Note: actual service name may vary
systemctl status postgresql

# Enable services to start on boot
sudo systemctl enable httpd rabbitmq-server postgresql
```

## Usage

### Quick Start

1. **Start Elasticsearch** (if not already running):
   ```bash
   docker run -d --name elasticsearch -p 9200:9200 -e "discovery.type=single-node" elasticsearch:8.10.0
   ```

2. **Run monitoring script**:
   ```bash
   python -m src.monitor.main
   ```

3. **Start API server**:
   ```bash
   python -m src.api.app
   ```

4. **Check API health**:
   ```bash
   curl http://localhost:5000/healthcheck
   ```

### Monitoring Script Usage

#### Basic Monitoring

```bash
# Monitor rbcapp1 and all dependent services
python -m src.monitor.main

# Monitor specific services only
python -m src.monitor.main --services httpd rabbitmq

# Monitor without writing JSON files
python -m src.monitor.main --no-files
```

#### Advanced Options

```bash
# Custom output directory and logging
python -m src.monitor.main \
  --output-dir /var/log/monitoring \
  --log-level DEBUG \
  --log-file /var/log/monitoring.log

# Quiet mode (minimal output)
python -m src.monitor.main --quiet

# Monitor rbcapp1 status only
python -m src.monitor.main --rbcapp1-only
```

### API Server Usage

#### Starting the API Server

```bash
# Development mode
python -m src.api.app

# Production mode with gunicorn
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 src.api.app:create_app()

# With custom configuration
export API_HOST=0.0.0.0
export API_PORT=8080
python -m src.api.app
```

### Cron Job Setup

For automated monitoring, set up a cron job:

```bash
# Edit crontab
crontab -e

# Add monitoring job (runs every 5 minutes)
*/5 * * * * /path/to/venv/bin/python -m src.monitor.main --output-dir /var/log/monitoring --quiet

# Add daily cleanup job (optional)
0 2 * * * find /var/log/monitoring -name "*.json" -mtime +7 -delete
```

Example cron configurations:

```bash
# Every minute
* * * * * /usr/local/bin/rbcapp1-monitor --quiet

# Every 5 minutes
*/5 * * * * /usr/local/bin/rbcapp1-monitor --output-dir /var/monitoring

# Every hour with logging
0 * * * * /usr/local/bin/rbcapp1-monitor --log-file /var/log/rbcapp1-monitor.log

# Business hours only (9 AM to 5 PM, Monday to Friday)
*/15 9-17 * * 1-5 /usr/local/bin/rbcapp1-monitor
```

## API Documentation

### Base URL
```
http://localhost:5000
```

### Endpoints

#### POST /add
Store service status data in Elasticsearch.

**Request:**
```bash
curl -X POST http://localhost:5000/add \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "httpd",
    "service_status": "UP",
    "host_name": "server01",
    "timestamp": "2024-01-15T10:30:00Z"
  }'
```

**Response (201 Created):**
```json
{
  "message": "Status data successfully stored",
  "service_name": "httpd",
  "timestamp": "2024-01-15T10:30:15Z"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "bad_request",
  "message": "Missing required fields: service_name",
  "timestamp": "2024-01-15T10:30:15Z"
}
```

#### GET /healthcheck
Retrieve status of all applications.

**Request:**
```bash
curl http://localhost:5000/healthcheck
```

**Response (200 OK):**
```json
{
  "services": {
    "httpd": "UP",
    "rabbitmq": "DOWN",
    "postgresql": "UP",
    "rbcapp1": "DOWN"
  },
  "timestamp": "2024-01-15T10:30:15Z"
}
```

#### GET /healthcheck/{serviceName}
Retrieve status of a specific service.

**Request:**
```bash
curl http://localhost:5000/healthcheck/httpd
```

**Response (200 OK):**
```json
{
  "service_name": "httpd",
  "service_status": "UP",
  "host_name": "server01",
  "last_updated": "2024-01-15T10:25:00Z",
  "timestamp": "2024-01-15T10:30:15Z"
}
```

**Error Response (404 Not Found):**
```json
{
  "error": "not_found",
  "message": "Service \"nonexistent\" not found",
  "timestamp": "2024-01-15T10:30:15Z"
}
```

### Error Codes

| Code | Description |
|------|-------------|
| 400  | Bad Request - Invalid JSON or missing required fields |
| 404  | Not Found - Service does not exist |
| 500  | Internal Server Error - Unexpected server error |
| 503  | Service Unavailable - Elasticsearch is not available |

## Monitoring Script

### Command Line Options

```
usage: main.py [-h] [--services SERVICES [SERVICES ...]] [--output-dir OUTPUT_DIR]
               [--no-files] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
               [--log-file LOG_FILE] [--quiet] [--rbcapp1-only]

Monitor rbcapp1 and its dependent services

optional arguments:
  -h, --help            show this help message and exit
  --services SERVICES [SERVICES ...]
                        Specific services to monitor (default: all rbcapp1 dependencies)
  --output-dir OUTPUT_DIR
                        Directory to write JSON status files (default: data)
  --no-files            Skip writing JSON status files
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Logging level (default: INFO)
  --log-file LOG_FILE   Log file path (default: log to console)
  --quiet               Suppress console output (except errors)
  --rbcapp1-only        Monitor rbcapp1 application status only (includes dependent services)
```

### Exit Codes

| Code | Description |
|------|-------------|
| 0    | Success - All monitored services are UP |
| 1    | Failure - One or more services are DOWN or error occurred |

### Examples

```bash
# Basic monitoring with output
python -m src.monitor.main

# Monitor specific services
python -m src.monitor.main --services httpd postgresql

# Production monitoring with logging
python -m src.monitor.main \
  --output-dir /var/monitoring \
  --log-file /var/log/rbcapp1-monitor.log \
  --log-level INFO \
  --quiet

# Check only rbcapp1 status
python -m src.monitor.main --rbcapp1-only --no-files
```

## File Formats

### JSON Status File Format

Generated files follow the naming convention: `{serviceName}-status-{timestamp}.json`

**Example filename:** `httpd-status-20240115T103000Z.json`

**File content:**
```json
{
  "service_name": "httpd",
  "service_status": "UP",
  "host_name": "server01",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Elasticsearch Document Structure

```json
{
  "_index": "service-monitoring",
  "_id": "auto-generated",
  "_source": {
    "service_name": "httpd",
    "service_status": "UP",
    "host_name": "server01",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Sample Elasticsearch Queries

```bash
# Get all documents
curl "localhost:9200/service-monitoring/_search?pretty"

# Get latest status for a specific service
curl "localhost:9200/service-monitoring/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "term": {"service_name": "httpd"}
  },
  "sort": [{"timestamp": {"order": "desc"}}],
  "size": 1
}
'

# Get all DOWN services
curl "localhost:9200/service-monitoring/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "term": {"service_status": "DOWN"}
  }
}
'

# Get services from specific host
curl "localhost:9200/service-monitoring/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "term": {"host_name": "server01"}
  }
}
'
```

## Troubleshooting

### Common Issues

#### 1. Permission Denied Errors

```bash
# Error: Permission denied when checking service status
sudo usermod -a -G systemd-journal $USER
# Or run with appropriate permissions
sudo python -m src.monitor.main
```

#### 2. Elasticsearch Connection Failed

```bash
# Check if Elasticsearch is running
curl http://localhost:9200

# Check Elasticsearch logs
docker logs elasticsearch

# Verify network connectivity
telnet localhost 9200
```

#### 3. Service Not Found

```bash
# List available services
systemctl list-units --type=service

# Check specific service name
systemctl status httpd
systemctl status apache2  # Alternative name
```

#### 4. JSON File Write Errors

```bash
# Check directory permissions
ls -la data/
chmod 755 data/

# Check disk space
df -h
```

### Logging and Debugging

#### Enable Debug Logging

```bash
# Console debug output
python -m src.monitor.main --log-level DEBUG

# File debug output
python -m src.monitor.main --log-level DEBUG --log-file debug.log
```

#### API Debug Mode

```bash
# Enable Flask debug mode
export API_DEBUG=true
python -m src.api.app
```

#### Check System Status

```bash
# Verify system dependencies
python -c "import subprocess; print(subprocess.run(['systemctl', '--version'], capture_output=True, text=True).stdout)"

# Check Python version
python --version

# Verify package installation
pip list | grep -E "(flask|elasticsearch|requests)"
```

### Performance Considerations

#### Monitoring Script Performance

- Service checks typically take 100-500ms per service
- JSON file writes are minimal overhead
- Memory usage is typically under 50MB

#### API Performance

- Elasticsearch queries are cached for 30 seconds
- Concurrent request handling with Flask
- Memory usage scales with request volume

#### Elasticsearch Performance

- Index size grows approximately 1KB per status record
- Query performance depends on index size and hardware
- Consider index lifecycle management for large deployments

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

### Code Quality

```bash
# Install development tools
pip install black flake8 mypy

# Format code
black src/ tests/

# Check code style
flake8 src/ tests/

# Type checking
mypy src/
```

### Project Structure

```
rbcapp1-monitoring/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py                 # Flask application
│   │   ├── config.py              # API configuration
│   │   └── elasticsearch_client.py # Elasticsearch wrapper
│   └── monitor/
│       ├── __init__.py
│       ├── main.py                # Main monitoring script
│       ├── app_monitor.py         # Application monitoring logic
│       ├── service_checker.py     # Service status checking
│       └── models.py              # Data models
├── tests/
│   ├── unit/                      # Unit tests
│   └── integration/               # Integration tests
├── data/                          # JSON output directory
├── config.py                      # Global configuration
├── requirements.txt               # Python dependencies
├── setup.py                       # Package setup
└── README.md                      # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run the test suite
5. Submit a pull request

For questions or support, please refer to the project documentation or contact the development team.

## Advanced Usage Examples

### Integration with External Systems

#### Nagios Integration

Create a Nagios check script:

```bash
#!/bin/bash
# /usr/local/nagios/libexec/check_rbcapp1.sh

cd /path/to/rbcapp1-monitoring
source venv/bin/activate

# Run monitoring and capture exit code
python -m src.monitor.main --quiet --no-files
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "OK - rbcapp1 and all dependencies are UP"
    exit 0
else
    echo "CRITICAL - rbcapp1 or dependencies are DOWN"
    exit 2
fi
```

Nagios command definition:
```
define command{
    command_name    check_rbcapp1
    command_line    /usr/local/nagios/libexec/check_rbcapp1.sh
}

define service{
    use                     generic-service
    host_name               production-server
    service_description     rbcapp1 Application Status
    check_command           check_rbcapp1
    check_interval          5
    retry_interval          1
}
```

#### Prometheus Integration

Create a Prometheus exporter script:

```python
#!/usr/bin/env python3
# prometheus_exporter.py

import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from monitor.main import monitor_rbcapp1
from http.server import HTTPServer, BaseHTTPRequestHandler

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            try:
                report = monitor_rbcapp1(output_dir='data', write_files=False)
                
                metrics = []
                metrics.append('# HELP rbcapp1_service_status Service status (1=UP, 0=DOWN)')
                metrics.append('# TYPE rbcapp1_service_status gauge')
                
                for service, status in report.get('service_statuses', {}).items():
                    value = 1 if status == 'UP' else 0
                    metrics.append(f'rbcapp1_service_status{{service="{service}"}} {value}')
                
                if 'app_status' in report:
                    app_value = 1 if report['app_status'] == 'UP' else 0
                    metrics.append(f'rbcapp1_service_status{{service="rbcapp1"}} {app_value}')
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write('\n'.join(metrics).encode())
                
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f'Error: {e}'.encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), MetricsHandler)
    print("Prometheus exporter running on :8080/metrics")
    server.serve_forever()
```

#### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "rbcapp1 Monitoring Dashboard",
    "panels": [
      {
        "title": "Service Status",
        "type": "stat",
        "targets": [
          {
            "expr": "rbcapp1_service_status",
            "legendFormat": "{{service}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "mappings": [
              {"options": {"0": {"text": "DOWN", "color": "red"}}},
              {"options": {"1": {"text": "UP", "color": "green"}}}
            ]
          }
        }
      }
    ]
  }
}
```

### Load Balancer Health Checks

#### HAProxy Configuration

```
backend rbcapp1_backend
    balance roundrobin
    option httpchk GET /healthcheck/rbcapp1
    http-check expect status 200
    server app1 192.168.1.10:5000 check
    server app2 192.168.1.11:5000 check
```

#### NGINX Configuration

```nginx
upstream rbcapp1_api {
    server 192.168.1.10:5000;
    server 192.168.1.11:5000;
}

server {
    listen 80;
    server_name monitoring.example.com;
    
    location /health {
        proxy_pass http://rbcapp1_api/healthcheck;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://rbcapp1_api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Automated Deployment Scripts

#### Systemd Service Files

Create `/etc/systemd/system/rbcapp1-monitor.service`:
```ini
[Unit]
Description=rbcapp1 Monitoring Service
After=network.target elasticsearch.service

[Service]
Type=simple
User=monitoring
Group=monitoring
WorkingDirectory=/opt/rbcapp1-monitoring
Environment=PATH=/opt/rbcapp1-monitoring/venv/bin
ExecStart=/opt/rbcapp1-monitoring/venv/bin/python -m src.api.app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/rbcapp1-monitor.timer`:
```ini
[Unit]
Description=rbcapp1 Monitoring Timer
Requires=rbcapp1-monitor.service

[Timer]
OnCalendar=*:0/5
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable rbcapp1-monitor.service
sudo systemctl enable rbcapp1-monitor.timer
sudo systemctl start rbcapp1-monitor.service
sudo systemctl start rbcapp1-monitor.timer
```

#### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    systemctl \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY config.py .

# Create data directory
RUN mkdir -p data && chmod 755 data

# Expose API port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/healthcheck || exit 1

# Default command
CMD ["python", "-m", "src.api.app"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  elasticsearch:
    image: elasticsearch:8.10.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200 || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  rbcapp1-api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - ELASTICSEARCH_HOST=elasticsearch
      - ELASTICSEARCH_PORT=9200
    depends_on:
      elasticsearch:
        condition: service_healthy
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  rbcapp1-monitor:
    build: .
    command: >
      sh -c "while true; do
        python -m src.monitor.main --output-dir /app/data --quiet;
        sleep 300;
      done"
    volumes:
      - ./data:/app/data
      - /var/run/docker.sock:/var/run/docker.sock:ro
    restart: unless-stopped

volumes:
  es_data:
```

Deploy with Docker Compose:
```bash
docker-compose up -d
docker-compose logs -f
```

## Complete API Reference

### Authentication

Currently, the API does not implement authentication. For production deployments, consider adding:

- API key authentication
- JWT token validation
- OAuth2 integration
- IP whitelisting

### Rate Limiting

Implement rate limiting for production:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/healthcheck')
@limiter.limit("10 per minute")
def healthcheck():
    # ... existing code
```

### API Response Examples

#### Successful Responses

**POST /add - Success**
```json
{
  "message": "Status data successfully stored",
  "service_name": "httpd",
  "timestamp": "2024-01-15T10:30:15Z"
}
```

**GET /healthcheck - All Services**
```json
{
  "services": {
    "httpd": "UP",
    "rabbitmq": "UP", 
    "postgresql": "UP",
    "rbcapp1": "UP"
  },
  "timestamp": "2024-01-15T10:30:15Z"
}
```

**GET /healthcheck/httpd - Specific Service**
```json
{
  "service_name": "httpd",
  "service_status": "UP",
  "host_name": "server01",
  "last_updated": "2024-01-15T10:25:00Z",
  "timestamp": "2024-01-15T10:30:15Z"
}
```

#### Error Responses

**400 Bad Request - Missing Fields**
```json
{
  "error": "bad_request",
  "message": "Missing required fields: service_name, service_status",
  "timestamp": "2024-01-15T10:30:15Z"
}
```

**400 Bad Request - Invalid Status**
```json
{
  "error": "bad_request",
  "message": "service_status must be one of: UP, DOWN",
  "timestamp": "2024-01-15T10:30:15Z"
}
```

**404 Not Found - Service Not Found**
```json
{
  "error": "not_found",
  "message": "Service \"nonexistent\" not found",
  "timestamp": "2024-01-15T10:30:15Z"
}
```

**503 Service Unavailable - Elasticsearch Down**
```json
{
  "error": "service_unavailable",
  "message": "Elasticsearch service is not available",
  "timestamp": "2024-01-15T10:30:15Z"
}
```

### Bulk Operations

For high-volume scenarios, consider implementing bulk endpoints:

```bash
# Bulk status update
curl -X POST http://localhost:5000/add/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "statuses": [
      {
        "service_name": "httpd",
        "service_status": "UP",
        "host_name": "server01",
        "timestamp": "2024-01-15T10:30:00Z"
      },
      {
        "service_name": "rabbitmq",
        "service_status": "DOWN",
        "host_name": "server01", 
        "timestamp": "2024-01-15T10:30:00Z"
      }
    ]
  }'
```

## Monitoring Script Advanced Examples

### Custom Service Lists

```bash
# Monitor web services only
python -m src.monitor.main --services httpd nginx apache2

# Monitor database services
python -m src.monitor.main --services postgresql mysql mongodb

# Monitor message queues
python -m src.monitor.main --services rabbitmq redis kafka
```

### Output Formatting

```bash
# JSON output for parsing
python -m src.monitor.main --quiet --no-files 2>/dev/null | jq '.service_statuses'

# CSV format (custom script)
python -m src.monitor.main --quiet --no-files | python -c "
import json, sys, csv
data = json.load(sys.stdin)
writer = csv.writer(sys.stdout)
writer.writerow(['Service', 'Status', 'Timestamp'])
for service, status in data['service_statuses'].items():
    writer.writerow([service, status, data['timestamp']])
"
```

### Integration with Configuration Management

#### Ansible Playbook

```yaml
---
- name: Deploy rbcapp1 monitoring
  hosts: monitoring_servers
  become: yes
  
  vars:
    app_dir: /opt/rbcapp1-monitoring
    app_user: monitoring
    
  tasks:
    - name: Create monitoring user
      user:
        name: "{{ app_user }}"
        system: yes
        shell: /bin/bash
        home: "{{ app_dir }}"
        
    - name: Clone repository
      git:
        repo: https://github.com/example/rbcapp1-monitoring.git
        dest: "{{ app_dir }}"
        version: main
      become_user: "{{ app_user }}"
      
    - name: Install Python dependencies
      pip:
        requirements: "{{ app_dir }}/requirements.txt"
        virtualenv: "{{ app_dir }}/venv"
      become_user: "{{ app_user }}"
      
    - name: Create data directory
      file:
        path: "{{ app_dir }}/data"
        state: directory
        owner: "{{ app_user }}"
        group: "{{ app_user }}"
        mode: '0755'
        
    - name: Install systemd service
      template:
        src: rbcapp1-monitor.service.j2
        dest: /etc/systemd/system/rbcapp1-monitor.service
      notify: restart rbcapp1-monitor
      
    - name: Install monitoring cron job
      cron:
        name: "rbcapp1 monitoring"
        minute: "*/5"
        user: "{{ app_user }}"
        job: "cd {{ app_dir }} && ./venv/bin/python -m src.monitor.main --quiet"
        
  handlers:
    - name: restart rbcapp1-monitor
      systemd:
        name: rbcapp1-monitor
        state: restarted
        daemon_reload: yes
        enabled: yes
```

#### Chef Recipe

```ruby
# recipes/default.rb

app_dir = '/opt/rbcapp1-monitoring'
app_user = 'monitoring'

user app_user do
  system true
  shell '/bin/bash'
  home app_dir
  manage_home true
end

git app_dir do
  repository 'https://github.com/example/rbcapp1-monitoring.git'
  revision 'main'
  user app_user
  group app_user
end

python_virtualenv "#{app_dir}/venv" do
  user app_user
  group app_user
end

pip_requirements "#{app_dir}/requirements.txt" do
  virtualenv "#{app_dir}/venv"
  user app_user
  group app_user
end

directory "#{app_dir}/data" do
  owner app_user
  group app_user
  mode '0755'
end

cron 'rbcapp1-monitoring' do
  minute '*/5'
  user app_user
  command "cd #{app_dir} && ./venv/bin/python -m src.monitor.main --quiet"
end
```

## Sample Cron Job Configurations

### Basic Monitoring

```bash
# Every 5 minutes - basic monitoring
*/5 * * * * /opt/rbcapp1-monitoring/venv/bin/python -m src.monitor.main --quiet

# Every minute - high frequency monitoring
* * * * * /opt/rbcapp1-monitoring/venv/bin/python -m src.monitor.main --output-dir /var/monitoring --quiet

# Every 15 minutes with logging
*/15 * * * * /opt/rbcapp1-monitoring/venv/bin/python -m src.monitor.main --log-file /var/log/rbcapp1.log --quiet
```

### Advanced Scheduling

```bash
# Business hours only (9 AM to 5 PM, Monday to Friday)
*/5 9-17 * * 1-5 /opt/rbcapp1-monitoring/venv/bin/python -m src.monitor.main --quiet

# Different frequencies for different times
# Every minute during business hours
* 9-17 * * 1-5 /opt/rbcapp1-monitoring/venv/bin/python -m src.monitor.main --quiet
# Every 15 minutes outside business hours
*/15 0-8,18-23 * * * /opt/rbcapp1-monitoring/venv/bin/python -m src.monitor.main --quiet
*/15 * * * 0,6 /opt/rbcapp1-monitoring/venv/bin/python -m src.monitor.main --quiet

# Maintenance window exclusion (skip monitoring during maintenance)
*/5 * * * * [ "$(date +\%H)" != "02" ] && /opt/rbcapp1-monitoring/venv/bin/python -m src.monitor.main --quiet
```

### Error Handling in Cron

```bash
# With error notification
*/5 * * * * /opt/rbcapp1-monitoring/venv/bin/python -m src.monitor.main --quiet || echo "rbcapp1 monitoring failed at $(date)" | mail -s "Monitoring Alert" admin@example.com

# With retry logic
*/5 * * * * /opt/rbcapp1-monitoring/scripts/monitor_with_retry.sh

# With lock file to prevent overlapping runs
*/5 * * * * /usr/bin/flock -n /tmp/rbcapp1-monitor.lock /opt/rbcapp1-monitoring/venv/bin/python -m src.monitor.main --quiet
```

Create `/opt/rbcapp1-monitoring/scripts/monitor_with_retry.sh`:
```bash
#!/bin/bash

SCRIPT_DIR="/opt/rbcapp1-monitoring"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"
MAX_RETRIES=3
RETRY_DELAY=30

cd "$SCRIPT_DIR"

for i in $(seq 1 $MAX_RETRIES); do
    if $VENV_PYTHON -m src.monitor.main --quiet; then
        exit 0
    else
        echo "Monitoring attempt $i failed, retrying in ${RETRY_DELAY}s..."
        sleep $RETRY_DELAY
    fi
done

echo "Monitoring failed after $MAX_RETRIES attempts"
exit 1
```

### Log Rotation for Cron Jobs

```bash
# Add to /etc/logrotate.d/rbcapp1-monitoring
/var/log/rbcapp1*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 monitoring monitoring
    postrotate
        /bin/kill -HUP $(cat /var/run/rsyslogd.pid 2>/dev/null) 2>/dev/null || true
    endscript
}
```

## Performance Tuning

### Elasticsearch Optimization

```bash
# Index template for better performance
curl -X PUT "localhost:9200/_index_template/service-monitoring" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["service-monitoring*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 0,
      "refresh_interval": "30s",
      "index.codec": "best_compression"
    },
    "mappings": {
      "properties": {
        "service_name": {"type": "keyword"},
        "service_status": {"type": "keyword"},
        "host_name": {"type": "keyword"},
        "timestamp": {"type": "date", "format": "strict_date_optional_time||epoch_millis"}
      }
    }
  }
}
'

# Index lifecycle management
curl -X PUT "localhost:9200/_ilm/policy/service-monitoring-policy" -H 'Content-Type: application/json' -d'
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_size": "50GB",
            "max_age": "30d"
          }
        }
      },
      "delete": {
        "min_age": "90d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
'
```

### Monitoring Script Optimization

```bash
# Parallel service checking
python -m src.monitor.main --services httpd rabbitmq postgresql --parallel

# Reduced output for high-frequency monitoring
python -m src.monitor.main --quiet --no-files --minimal-logging
```

### API Performance Tuning

```python
# Add caching to Flask app
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/healthcheck')
@cache.cached(timeout=30)  # Cache for 30 seconds
def healthcheck():
    # ... existing code
```

This completes the comprehensive documentation for the rbcapp1 monitoring system, covering all requirements for task 8.2 including detailed API documentation, usage examples, cron job configurations, and sample JSON formats and Elasticsearch queries.