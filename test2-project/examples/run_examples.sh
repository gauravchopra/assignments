#!/bin/bash
# Example execution commands for rbcapp1 Infrastructure Management

echo "rbcapp1 Infrastructure Management - Example Commands"
echo "===================================================="

# Set common variables
INVENTORY="inventory"
PLAYBOOK="assignment.yml"

echo ""
echo "1. Display Help and Available Actions:"
echo "   ansible-playbook $PLAYBOOK -i $INVENTORY -e action=help"
echo ""

echo "2. Verify and Install Services:"
echo "   ansible-playbook $PLAYBOOK -i $INVENTORY -e action=verify_install"
echo ""

echo "3. Check Disk Usage (with email alerts):"
echo "   ansible-playbook $PLAYBOOK -i $INVENTORY -e action=check-disk"
echo ""

echo "4. Check rbcapp1 Application Status:"
echo "   ansible-playbook $PLAYBOOK -i $INVENTORY -e action=check-status"
echo ""

echo "Advanced Examples:"
echo "=================="
echo ""

echo "5. Target Specific Host Groups:"
echo "   ansible-playbook $PLAYBOOK -i $INVENTORY -e action=verify_install -e target_hosts=webservers"
echo "   ansible-playbook $PLAYBOOK -i $INVENTORY -e action=check-disk -e target_hosts=database"
echo ""

echo "6. Custom Disk Usage Threshold:"
echo "   ansible-playbook $PLAYBOOK -i $INVENTORY -e action=check-disk -e disk_usage_threshold=90"
echo ""

echo "7. Dry Run (Check Mode):"
echo "   ansible-playbook $PLAYBOOK -i $INVENTORY -e action=verify_install --check --diff"
echo ""

echo "8. Verbose Output:"
echo "   ansible-playbook $PLAYBOOK -i $INVENTORY -e action=check-status -vvv"
echo ""

echo "9. Test with Local Inventory:"
echo "   ansible-playbook $PLAYBOOK -i test_inventory -e action=help"
echo ""

echo "Validation Commands:"
echo "==================="
echo ""

echo "10. Syntax Check:"
echo "    ansible-playbook $PLAYBOOK -i $INVENTORY --syntax-check"
echo ""

echo "11. Test SSH Connectivity:"
echo "    ansible all -i $INVENTORY -m ping"
echo ""

echo "12. Test Privilege Escalation:"
echo "    ansible all -i $INVENTORY -m shell -a 'sudo whoami'"
echo ""

echo "13. Verify Test 1 API Connectivity:"
echo "    curl http://localhost:5000/healthcheck"
echo ""

echo "Production Considerations:"
echo "========================="
echo ""

echo "14. Use Ansible Vault for Sensitive Data:"
echo "    ansible-vault create group_vars/vault.yml"
echo "    ansible-playbook $PLAYBOOK -i $INVENTORY -e action=check-disk --ask-vault-pass"
echo ""

echo "15. Schedule Regular Monitoring:"
echo "    # Add to crontab:"
echo "    # */15 * * * * cd /path/to/test2-project && ansible-playbook $PLAYBOOK -i $INVENTORY -e action=check-disk"
echo ""

echo "16. Integration with Monitoring Systems:"
echo "    # Export results to monitoring system"
echo "    ansible-playbook $PLAYBOOK -i $INVENTORY -e action=check-status --extra-vars '{\"output_format\": \"json\"}'"
echo ""

echo ""
echo "For more information, see README.md or run:"
echo "ansible-playbook $PLAYBOOK -i $INVENTORY -e action=help"