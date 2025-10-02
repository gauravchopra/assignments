# rbcapp1 Monitoring System

A simple monitoring system for the "rbcapp1" application and its dependent services (httpd, rabbitmq, postgresql).

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Elasticsearch (optional for API):**
   ```bash
   docker run -d --name elasticsearch -p 9200:9200 -e "discovery.type=single-node" elasticsearch:8.10.0
   ```

3. **Run monitoring:**
   ```bash
   python -m src.monitor.main
   ```

4. **Start API (optional):**
   ```bash
   python -m src.api.app
   ```

## Usage

### Monitoring Script
```bash
# Monitor all services and generate JSON files
python -m src.monitor.main

# Monitor specific services only
python -m src.monitor.main --services httpd rabbitmq

# Monitor without writing files
python -m src.monitor.main --no-files

# Quiet mode
python -m src.monitor.main --quiet
```

### API Endpoints

- `POST /add` - Store service status data
- `GET /healthcheck` - Get all service statuses  
- `GET /healthcheck/{serviceName}` - Get specific service status

### Example API Usage
```bash
# Add status data
curl -X POST http://localhost:5000/add \
  -H "Content-Type: application/json" \
  -d '{"service_name": "httpd", "service_status": "UP", "host_name": "server01"}'

# Check all services
curl http://localhost:5000/healthcheck

# Check specific service
curl http://localhost:5000/healthcheck/httpd
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v
```

## Project Structure

```
src/
├── api/                    # REST API components
│   ├── app.py             # Flask application
│   ├── config.py          # Configuration
│   └── elasticsearch_client.py
└── monitor/               # Monitoring components
    ├── main.py           # Main script
    ├── app_monitor.py    # Application monitoring
    ├── service_checker.py # Service status checking
    └── models.py         # Data models
tests/                     # Test files
data/                      # JSON output directory
```

## Requirements

- Python 3.8+
- Linux with systemctl
- Elasticsearch 8.x (for API functionality)