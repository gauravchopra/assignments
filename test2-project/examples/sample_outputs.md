# Sample Outputs - rbcapp1 Infrastructure Management

This document shows example outputs for each action supported by the Ansible playbook.

## 1. Help Action

**Command**: `ansible-playbook assignment.yml -i inventory -e action=help`

**Sample Output**:
```
PLAY [rbcapp1 Infrastructure Management] **************************************

TASK [Display playbook header] ************************************************
ok: [host1 -> localhost] => 
  msg: |
    =====================================
    rbcapp1 Infrastructure Management
    =====================================
    Action: help
    Target Hosts: host1, host2, host3
    =====================================

TASK [Display help information] ***********************************************
ok: [host1 -> localhost] => 
  msg: |
    rbcapp1 Infrastructure Management Playbook
    ==========================================
    
    Available Actions:
    
    1. verify_install
       - Verifies services are installed on their designated hosts
       - Installs missing services (demonstrates with httpd)
       - Usage: ansible-playbook assignment.yml -i inventory -e action=verify_install
    
    2. check-disk
       - Checks disk space on all servers
       - Sends email alerts for disk usage > 80%
       - Usage: ansible-playbook assignment.yml -i inventory -e action=check-disk
    
    3. check-status
       - Returns rbcapp1 application status
       - Lists services that are down using REST API from Test 1
       - Usage: ansible-playbook assignment.yml -i inventory -e action=check-status
    
    4. help
       - Displays this help message
       - Usage: ansible-playbook assignment.yml -i inventory -e action=help

PLAY RECAP *********************************************************************
host1                      : ok=2    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
host2                      : ok=0    changed=0    unreachable=0    failed=0    skipped=2    rescued=0    ignored=0
host3                      : ok=0    changed=0    unreachable=0    failed=0    skipped=2    rescued=0    ignored=0
```

## 2. Service Verification and Installation

**Command**: `ansible-playbook assignment.yml -i inventory -e action=verify_install`

**Sample Output**:
```
PLAY [rbcapp1 Infrastructure Management] **************************************

TASK [Display service verification header] ************************************
ok: [host1] => 
  msg: |
    =====================================
    Service Verification and Installation
    =====================================
    Host: host1
    Service: httpd
    Package: httpd
    =====================================

TASK [Check if service package is installed] **********************************
ok: [host1]
ok: [host2]
ok: [host3]

TASK [Display current service installation status] ****************************
ok: [host1] => 
  msg: |
    Service Status Check:
    - Host: host1
    - Service: httpd
    - Package: httpd
    - Installed: true

TASK [Install httpd package] ***************************************************
ok: [host1] => (item=httpd)

TASK [Display httpd installation results] *************************************
ok: [host1] => 
  msg: |
    httpd Installation Results:
    - Installation: Already installed
    - Service Active: active
    - Service Enabled: enabled
    - Process ID: 1234

TASK [Display service verification summary] ***********************************
ok: [host1 -> localhost] => 
  msg: |
    =====================================
    Service Verification Summary
    =====================================
    Host: host1
      Service: httpd
      Package: httpd
      Installed: true
      Running: active
      Enabled: enabled
    Host: host2
      Service: rabbitmq-server
      Package: rabbitmq-server
      Installed: false
      Running: not_installed
      Enabled: not_installed
    Host: host3
      Service: postgresql
      Package: postgresql-server
      Installed: true
      Running: active
      Enabled: enabled
    =====================================

PLAY RECAP *********************************************************************
host1                      : ok=8    changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
host2                      : ok=6    changed=0    unreachable=0    failed=0    skipped=3    rescued=0    ignored=0
host3                      : ok=6    changed=0    unreachable=0    failed=0    skipped=3    rescued=0    ignored=0
```

## 3. Disk Space Monitoring

**Command**: `ansible-playbook assignment.yml -i inventory -e action=check-disk`

**Sample Output**:
```
PLAY [rbcapp1 Infrastructure Management] **************************************

TASK [Display disk monitoring header] *****************************************
ok: [host1] => 
  msg: |
    =====================================
    Disk Space Monitoring
    =====================================
    Host: host1
    Threshold: 80%
    =====================================

TASK [Display disk usage for all mount points] ********************************
ok: [host1] => 
  msg: |
    Disk Usage Report for host1:
    
    Mount Point: /
      Device: /dev/sda1
      Filesystem: ext4
      Total Size: 20.0 GB
      Used Space: 16.5 GB
      Available: 3.5 GB
      Usage: 82.5%
      Alert Required: true
    
    Mount Point: /var
      Device: /dev/sda2
      Filesystem: ext4
      Total Size: 10.0 GB
      Used Space: 6.2 GB
      Available: 3.8 GB
      Usage: 62.0%
      Alert Required: false

TASK [Display high usage alert] ***********************************************
ok: [host1] => 
  msg: |
    ⚠️  HIGH DISK USAGE ALERT ⚠️
    Host: host1
    
    Critical filesystems (>80%):
    - /: 82.5% used (16.5/20.0 GB)

TASK [Send email alert for high disk usage] ***********************************
ok: [host1 -> localhost]

TASK [Display email sending result] *******************************************
ok: [host1 -> localhost] => 
  msg: |
    Email Alert Status:
    ✅ Email alert sent successfully to admin@example.com
    Subject: 🚨 Disk Usage Alert - 1 hosts with high disk usage
    Recipients notified about 1 hosts with high disk usage

TASK [Display disk monitoring summary] ****************************************
ok: [host1 -> localhost] => 
  msg: |
    =====================================
    Disk Monitoring Summary
    =====================================
    Total Hosts Monitored: 3
    Hosts with Alerts: 1
    Total Critical Filesystems: 1
    Alert Threshold: 80%
    
    Per-Host Summary:
    host1: 1/2 critical
    host2: 0/3 critical
    host3: 0/2 critical
    =====================================

PLAY RECAP *********************************************************************
host1                      : ok=8    changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
host2                      : ok=6    changed=0    unreachable=0    failed=0    skipped=3    rescued=0    ignored=0
host3                      : ok=6    changed=0    unreachable=0    failed=0    skipped=3    rescued=0    ignored=0
```

## 4. Application Status Checking

**Command**: `ansible-playbook assignment.yml -i inventory -e action=check-status`

**Sample Output**:
```
PLAY [rbcapp1 Infrastructure Management] **************************************

TASK [Display status checking header] *****************************************
ok: [host1 -> localhost] => 
  msg: |
    =====================================
    rbcapp1 Application Status Check
    =====================================
    API Base URL: http://localhost:5000
    Checking via REST API from Test 1
    =====================================

TASK [Check rbcapp1 API connectivity] *****************************************
ok: [host1 -> localhost]

TASK [Display API connectivity status] ****************************************
ok: [host1 -> localhost] => 
  msg: |
    API Connectivity Check:
    ✅ rbcapp1 API is reachable
    - URL: http://localhost:5000/healthcheck
    - Status Code: 200
    - Response Time: 0.045s

TASK [Query rbcapp1 application status] ***************************************
ok: [host1 -> localhost]

TASK [Display rbcapp1 application status] *************************************
ok: [host1 -> localhost] => 
  msg: |
    =====================================
    rbcapp1 Application Status Report
    =====================================
    
    🔗 API Status: Connected
    📊 Overall Application Status: 
    
    Services Summary:
    ✅ httpd: UP
    ❌ rabbitmq: DOWN
    ✅ postgresql: UP
    ✅ rbcapp1: DOWN
    
    🚨 Services Currently DOWN:
    - rabbitmq
    - rbcapp1
    
    ✅ Services Currently UP: 2
    
    =====================================

TASK [Display detailed service information] ***********************************
ok: [host1 -> localhost] => 
  msg: |
    =====================================
    Detailed Service Status Information
    =====================================
    
    Service: httpd
    - Status: UP
    - Host: host1
    - Last Updated: 2024-01-15T10:30:00Z
    
    Service: rabbitmq
    - Status: DOWN
    - Host: host2
    - Last Updated: 2024-01-15T09:45:00Z
    
    Service: postgresql
    - Status: UP
    - Host: host3
    - Last Updated: 2024-01-15T10:28:00Z
    
    Service: rbcapp1
    - Status: DOWN
    - Error: Service not found
    =====================================

TASK [Display status check summary] *******************************************
ok: [host1 -> localhost] => 
  msg: |
    =====================================
    Status Check Summary
    =====================================
    Timestamp: 2024-01-15T10:30:15Z
    API Accessible: true
    Overall Status: DEGRADED
    
    Service Counts:
    - Total Services: 4
    - Services UP: 2
    - Services DOWN: 2
    
    Services Requiring Attention:
    - rabbitmq
    - rbcapp1
    =====================================

PLAY RECAP *********************************************************************
host1                      : ok=9    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
host2                      : ok=1    changed=0    unreachable=0    failed=0    skipped=8    rescued=0    ignored=0
host3                      : ok=1    changed=0    unreachable=0    failed=0    skipped=8    rescued=0    ignored=0
```

## 5. API Unavailable Scenario

**Command**: `ansible-playbook assignment.yml -i inventory -e action=check-status` (when Test 1 API is down)

**Sample Output**:
```
TASK [Display API unavailable message] ****************************************
ok: [host1 -> localhost] => 
  msg: |
    =====================================
    rbcapp1 API Unavailable
    =====================================
    
    ❌ Cannot connect to rbcapp1 monitoring API
    
    API Details:
    - URL: http://localhost:5000
    - Error: Connection refused
    
    Possible Causes:
    - rbcapp1 monitoring API (Test 1) is not running
    - Network connectivity issues
    - Firewall blocking access to port 5000
    - API host localhost is incorrect
    
    Troubleshooting Steps:
    1. Verify rbcapp1 API is running: curl http://localhost:5000/healthcheck
    2. Check network connectivity to localhost:5000
    3. Verify firewall rules allow access to port 5000
    4. Check API logs for errors
    
    =====================================
```

## 6. Invalid Action

**Command**: `ansible-playbook assignment.yml -i inventory -e action=invalid_action`

**Sample Output**:
```
TASK [Validate action parameter] **********************************************
fatal: [host1 -> localhost]: FAILED! => 
  msg: |
    Invalid action: invalid_action
    
    Valid actions are:
      - verify_install: Verify and install services on designated hosts
      - check-disk: Check disk usage and send alerts for >80% usage
      - check-status: Check rbcapp1 application status via REST API
      - help: Display this help message
    
    Usage: ansible-playbook assignment.yml -i inventory -e action=<action_name>
```

## 7. Syntax Check

**Command**: `ansible-playbook assignment.yml -i inventory --syntax-check`

**Sample Output**:
```
playbook: assignment.yml
```

## 8. Connectivity Test

**Command**: `ansible all -i inventory -m ping`

**Sample Output**:
```
host1 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3"
    },
    "changed": false,
    "ping": "pong"
}
host2 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3"
    },
    "changed": false,
    "ping": "pong"
}
host3 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3"
    },
    "changed": false,
    "ping": "pong"
}
```

## 9. Email Alert Sample

**Subject**: 🚨 Disk Usage Alert - rbcapp1 Infrastructure

**Body**:
```
Disk Usage Alert Report
========================

Alert Details:
- Alert Threshold: 80%
- Total Hosts Checked: 3
- Hosts with Alerts: 1
- Total Critical Filesystems: 1
- Generated: 2024-01-15T10:30:15Z

Critical Hosts:

Host: host1
Critical Filesystems: 1
  📁 / (/dev/sda1)
     Usage: 82.5% (16.5/20.0 GB)
     Available: 3.5 GB
     Filesystem: ext4

All Hosts Summary:
host1: 1/2 filesystems critical
host2: 0/3 filesystems critical
host3: 0/2 filesystems critical

Recommended Actions:
1. Immediately investigate hosts with >90% usage
2. Clean up temporary files and logs
3. Archive or remove old data
4. Consider expanding storage capacity
5. Implement automated cleanup policies

This alert was generated by the rbcapp1 Infrastructure Management system.
For support, contact the system administration team.

---
rbcapp1 Infrastructure Management
Ansible Automation System
```

These sample outputs demonstrate the comprehensive reporting and error handling capabilities of the Ansible automation system.