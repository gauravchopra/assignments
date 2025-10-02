# Test 2 - Ansible Automation for rbcapp1 Infrastructure

This is the second test assignment implementing Ansible automation for managing rbcapp1 services distributed across multiple RHEL servers.

## Overview

This project provides Ansible-based automation for the rbcapp1 infrastructure with three main capabilities:

1. **Service Verification & Installation** (`verify_install`) - Verifies and installs services on designated hosts
2. **Disk Space Monitoring** (`check-disk`) - Monitors disk usage and sends email alerts for >80% usage  
3. **Application Status Checking** (`check-status`) - Integrates with Test 1 REST API to check rbcapp1 status

## Architecture

The rbcapp1 services are distributed across three RHEL servers:
- **host1**: httpd service
- **host2**: rabbitmq-server service  
- **host3**: postgresql service

## Project Structure

```
test2-project/
├── assignment.yml              # Main Ansible playbook
├── inventory                   # Production inventory file
├── test_inventory             # Test inventory for development
├── ansible.cfg                # Ansible configuration
├── tasks/                     # Task files
│   ├── verify_install.yml     # Service verification and installation
│   ├── check_disk.yml         # Disk monitoring and alerting
│   └── check_status.yml       # rbcapp1 status checking
├── group_vars/
│   └── all.yml                # Global variables
├── templates/
│   └── disk_alert_email.j2    # Email alert template
├── examples/
│   ├── run_examples.sh        # Example commands
│   └── sample_outputs.md      # Sample execution outputs
├── .kiro/specs/               # Kiro specifications
└── README.md                  # This file
```

## Quick Start

### Prerequisites

1. **Ansible Installation**:
   ```bash
   pip install ansible
   ```

2. **SSH Access**: Ensure SSH key-based access to target hosts
   ```bash
   ssh-keygen -t rsa -b 4096
   ssh-copy-id ansible@host1
   ssh-copy-id ansible@host2  
   ssh-copy-id ansible@host3
   ```

3. **Test 1 API**: Ensure rbcapp1 monitoring API from Test 1 is running

### Basic Usage

1. **Help and Available Actions**:
   ```bash
   ansible-playbook assignment.yml -i inventory -e action=help
   ```

2. **Verify and Install Services**:
   ```bash
   ansible-playbook assignment.yml -i inventory -e action=verify_install
   ```

3. **Check Disk Usage**:
   ```bash
   ansible-playbook assignment.yml -i inventory -e action=check-disk
   ```

4. **Check rbcapp1 Status**:
   ```bash
   ansible-playbook assignment.yml -i inventory -e action=check-status
   ```

## Configuration

### Inventory Configuration

Edit the `inventory` file to match your environment:

```ini
[webservers]
host1 ansible_host=192.168.1.10 service_name=httpd

[messagequeue]  
host2 ansible_host=192.168.1.11 service_name=rabbitmq-server

[database]
host3 ansible_host=192.168.1.12 service_name=postgresql
```

### Global Variables

Configure settings in `group_vars/all.yml`:

```yaml
# Monitoring thresholds
disk_usage_threshold: 80

# Email alerts
alert_email: "admin@example.com"
smtp_server: "smtp.example.com"
smtp_port: 587
smtp_username: "monitoring@example.com"

# rbcapp1 API (from Test 1)
rbcapp1_api_host: "localhost"
rbcapp1_api_port: 5000
```

### Secure Credentials

For production, use ansible-vault for sensitive data:

```bash
# Create encrypted variables file
ansible-vault create group_vars/vault.yml

# Add encrypted variables
vault_smtp_password: "your_secure_password"
```

## Detailed Usage

### 1. Service Verification and Installation

**Purpose**: Verifies services are installed on designated hosts and installs missing services.

```bash
ansible-playbook assignment.yml -i inventory -e action=verify_install
```

**Features**:
- Checks if services are installed on their designated hosts
- Demonstrates installation with httpd service (includes package installation, service enablement, and startup)
- Reports installation status for all services
- Handles installation failures gracefully

**Example Output**:
```
Service Status Check:
- Host: host1
- Service: httpd  
- Package: httpd
- Installed: true

httpd Installation Results:
- Installation: Already installed
- Service Active: active
- Service Enabled: enabled
```

### 2. Disk Space Monitoring

**Purpose**: Monitors disk usage across all servers and sends email alerts for usage >80%.

```bash
ansible-playbook assignment.yml -i inventory -e action=check-disk
```

**Features**:
- Checks disk usage on all mounted filesystems
- Identifies filesystems exceeding 80% threshold
- Sends detailed email alerts to configured recipients
- Provides comprehensive disk usage reports

**Example Output**:
```
Disk Usage Report for host1:

Mount Point: /
  Device: /dev/sda1
  Total Size: 20.0 GB
  Used Space: 16.5 GB  
  Available: 3.5 GB
  Usage: 82.5%
  Alert Required: true
```

**Email Alert**: Automatically sent when high usage detected, includes:
- List of affected hosts and filesystems
- Detailed usage statistics
- Recommended actions

### 3. Application Status Checking

**Purpose**: Checks rbcapp1 application status using the REST API from Test 1.

```bash
ansible-playbook assignment.yml -i inventory -e action=check-status
```

**Features**:
- Queries rbcapp1 REST API `/healthcheck` endpoint
- Reports overall application status
- Lists services that are down
- Provides detailed service information
- Handles API connectivity issues

**Example Output**:
```
rbcapp1 Application Status Report
=================================

🔗 API Status: Connected
📊 Overall Application Status:

Services Summary:
✅ httpd: UP
❌ rabbitmq: DOWN  
✅ postgresql: UP
✅ rbcapp1: UP

🚨 Services Currently DOWN:
- rabbitmq
```

## Advanced Usage

### Custom Host Targeting

Target specific host groups:
```bash
# Only web servers
ansible-playbook assignment.yml -i inventory -e action=verify_install -e target_hosts=webservers

# Only database servers  
ansible-playbook assignment.yml -i inventory -e action=check-disk -e target_hosts=database
```

### Custom Thresholds

Override default disk usage threshold:
```bash
ansible-playbook assignment.yml -i inventory -e action=check-disk -e disk_usage_threshold=90
```

### Dry Run Mode

Test playbook without making changes:
```bash
ansible-playbook assignment.yml -i inventory -e action=verify_install --check --diff
```

### Verbose Output

Enable detailed logging:
```bash
ansible-playbook assignment.yml -i inventory -e action=check-status -vvv
```

## Integration with Test 1

The `check-status` action integrates with the rbcapp1 monitoring API from Test 1:

- **API Endpoint**: `http://localhost:5000/healthcheck`
- **Authentication**: None (as per Test 1 implementation)
- **Response Format**: JSON with service statuses
- **Timeout**: 10 seconds (configurable)

Ensure Test 1 API is running before using `check-status`:
```bash
# Start Test 1 API
cd ../rbcapp1-monitoring
python -m src.api.app

# Verify API is accessible
curl http://localhost:5000/healthcheck
```

## Error Handling

The playbook includes comprehensive error handling:

- **SSH Connection Failures**: Reports connectivity issues per host
- **Service Installation Errors**: Continues with other hosts, logs failures
- **API Unavailability**: Provides troubleshooting guidance
- **Email Delivery Failures**: Logs errors but continues execution
- **Invalid Actions**: Displays help and available options

## Testing

### Test Inventory

A test inventory is provided for development:
```bash
# Use test inventory with local connections
ansible-playbook assignment.yml -i test_inventory -e action=help
```

### Validation

Validate playbook syntax:
```bash
ansible-playbook assignment.yml -i inventory --syntax-check
```

### Dry Run Testing

Test without making changes:
```bash
ansible-playbook assignment.yml -i inventory -e action=verify_install --check
```

## Troubleshooting

### Common Issues

1. **SSH Connection Failed**:
   ```bash
   # Test SSH connectivity
   ansible all -i inventory -m ping
   
   # Check SSH key permissions
   chmod 600 ~/.ssh/id_rsa
   ```

2. **Privilege Escalation Failed**:
   ```bash
   # Test sudo access
   ansible all -i inventory -m shell -a "sudo whoami" --ask-become-pass
   ```

3. **API Not Accessible**:
   ```bash
   # Verify Test 1 API is running
   curl http://localhost:5000/healthcheck
   
   # Check firewall rules
   sudo firewall-cmd --list-ports
   ```

4. **Email Delivery Failed**:
   - Verify SMTP server settings in `group_vars/all.yml`
   - Check SMTP authentication credentials
   - Test SMTP connectivity: `telnet smtp.example.com 587`

### Debug Mode

Enable debug output:
```bash
ansible-playbook assignment.yml -i inventory -e action=check-disk -e enable_debug=true -vvv
```

### Log Files

Check Ansible logs:
```bash
tail -f ansible.log
```

## Security Considerations

1. **SSH Keys**: Use dedicated SSH keys for Ansible automation
2. **Privilege Escalation**: Limit sudo access to required commands only
3. **Sensitive Data**: Use ansible-vault for passwords and credentials
4. **Network Security**: Ensure proper firewall rules for required ports
5. **API Security**: Consider implementing authentication for production API access

## Performance Optimization

- **Parallel Execution**: Configured for 5 concurrent hosts (adjustable in ansible.cfg)
- **SSH Multiplexing**: Enabled for faster connections
- **Fact Caching**: Reduces fact gathering overhead
- **Pipelining**: Enabled for improved performance

## Production Deployment

For production use:

1. **Update Inventory**: Replace example IPs with actual server addresses
2. **Configure SMTP**: Set up proper email server credentials
3. **Secure Credentials**: Use ansible-vault for all sensitive data
4. **Monitoring Integration**: Consider integrating with existing monitoring systems
5. **Backup Strategy**: Implement configuration backup before changes
6. **Change Management**: Use version control for playbook changes

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Ansible logs in `ansible.log`
3. Verify Test 1 API connectivity for status checking
4. Ensure proper SSH access to all target hosts

---

**Note**: This is Test 2 - Ansible automation for rbcapp1 infrastructure, integrating with the monitoring system from Test 1.