# Assignment Workspace - Three Test Projects

This workspace contains three separate test assignments, each demonstrating different technical skills and implementations.

## Project Structure

```
assignment-workspace/
├── test1-project/          # TEST 1 - rbcapp1 Monitoring System
├── test2-project/          # TEST 2 - Ansible Automation
├── test3-project/          # TEST 3 - Real Estate Data Analysis
└── README.md              # This file
```

## Test Projects Overview

### 🔧 Test 1 - rbcapp1 Monitoring System
**Location**: `test1-project/`  
**Technology**: Python, Flask, Elasticsearch  
**Purpose**: Monitoring system for rbcapp1 application and its dependent services

**Key Features**:
- Service status monitoring (httpd, rabbitMQ, postgreSQL)
- JSON status file generation with timestamps
- REST API with health check endpoints
- Elasticsearch integration for data storage
- Comprehensive error handling and logging

**Quick Start**:
```bash
cd test1-project
pip install -r requirements.txt
python -m src.monitor.main
python -m src.api.app
```

### 🚀 Test 2 - Ansible Automation
**Location**: `test2-project/`  
**Technology**: Ansible, YAML, Shell Scripting  
**Purpose**: Infrastructure automation for rbcapp1 services across multiple RHEL servers

**Key Features**:
- Multi-host service management (httpd on host1, rabbitMQ on host2, postgreSQL on host3)
- Action-based playbook execution (`verify_install`, `check-disk`, `check-status`)
- Automated service installation and verification
- Disk space monitoring with email alerts
- Integration with Test 1 REST API for status checking

**Quick Start**:
```bash
cd test2-project
ansible-playbook assignment.yml -i inventory -e action=help
ansible-playbook assignment.yml -i inventory -e action=verify_install
```

### 📊 Test 3 - Real Estate Data Analysis
**Location**: `test3-project/`  
**Technology**: Python, Pandas, NumPy  
**Purpose**: Analyze real estate sales data and filter properties by price per square foot

**Key Features**:
- CSV data processing and validation
- Price per square foot calculations
- Statistical analysis (average, min, max, median)
- Property filtering based on below-average criteria
- Automated output generation with timestamps
- Comprehensive data quality reporting

**Quick Start**:
```bash
cd test3-project
pip install -r requirements.txt
python run_analysis.py
```

## Getting Started

Each test project is self-contained with its own README, dependencies, and setup instructions. Navigate to the specific project directory and follow the Quick Start guide above.

### Prerequisites
- Python 3.8+ (for Test 1 and Test 3)
- Ansible (for Test 2)
- Elasticsearch (for Test 1 API functionality)


### Installation
Each project has its own `requirements.txt` or dependency management. See individual project READMEs for detailed setup instructions.
