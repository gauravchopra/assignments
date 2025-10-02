# Test 2 - Ansible Automation for rbcapp1

Ansible automation for managing rbcapp1 services across multiple RHEL servers.

## Quick Start

1. **Install Ansible:**
   ```bash
   pip install ansible
   ```

2. **Configure SSH access** to target hosts

3. **Update inventory** with your server details

4. **Run playbook:**
   ```bash
   ansible-playbook assignment.yml -i inventory -e action=help
   ```

## Available Actions

```bash
# Verify and install services
ansible-playbook assignment.yml -i inventory -e action=verify_install

# Check disk usage (alerts if >80%)
ansible-playbook assignment.yml -i inventory -e action=check-disk

# Check rbcapp1 status (requires Test 1 API)
ansible-playbook assignment.yml -i inventory -e action=check-status
```

## Configuration

### Inventory Setup
Edit `inventory` file with your server details:
```ini
[webservers]
host1 ansible_host=192.168.1.10 service_name=httpd

[messagequeue]  
host2 ansible_host=192.168.1.11 service_name=rabbitmq-server

[database]
host3 ansible_host=192.168.1.12 service_name=postgresql
```

### Variables
Configure settings in `group_vars/all.yml`:
- Disk usage threshold (default: 80%)
- Email alert settings
- rbcapp1 API connection details

## Project Structure

```
tasks/
├── verify_install.yml     # Service verification and installation
├── check_disk.yml         # Disk monitoring and alerting
└── check_status.yml       # rbcapp1 status checking
templates/
└── disk_alert_email.j2    # Email alert template
```

## Integration with Test 1

The `check-status` action requires the rbcapp1 monitoring API from Test 1 to be running:
```bash
# Start Test 1 API first
cd ../test1-project
python -m src.api.app
```