"""
Consolidated unit tests for core monitoring functionality.
"""
import pytest
from unittest.mock import Mock, patch
from src.monitor.app_monitor import ApplicationMonitor
from src.monitor.service_checker import ServiceChecker
from src.monitor.models import ServiceStatus


class TestServiceChecker:
    """Essential tests for ServiceChecker."""
    
    @patch('subprocess.run')
    def test_check_service_status_up(self, mock_run):
        """Test service status check when service is UP."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "active\n"
        mock_run.return_value = mock_result
        
        checker = ServiceChecker()
        status = checker.check_service_status("httpd")
        
        assert status == "UP"
    
    @patch('subprocess.run')
    def test_check_service_status_down(self, mock_run):
        """Test service status check when service is DOWN."""
        mock_result = Mock()
        mock_result.returncode = 3
        mock_result.stdout = "inactive\n"
        mock_run.return_value = mock_result
        
        checker = ServiceChecker()
        status = checker.check_service_status("httpd")
        
        assert status == "DOWN"
    
    @patch('subprocess.run')
    def test_check_service_status_exception(self, mock_run):
        """Test service status check handles exceptions."""
        mock_run.side_effect = Exception("System error")
        
        checker = ServiceChecker()
        status = checker.check_service_status("httpd")
        
        assert status == "DOWN"


class TestApplicationMonitor:
    """Essential tests for ApplicationMonitor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_service_checker = Mock(spec=ServiceChecker)
        self.monitor = ApplicationMonitor(self.mock_service_checker)
    
    def test_check_service_statuses(self):
        """Test checking multiple service statuses."""
        self.mock_service_checker.check_service_status.side_effect = ["UP", "DOWN", "UP"]
        
        statuses = self.monitor.check_service_statuses()
        
        expected = {
            "httpd": "UP",
            "rabbitmq": "DOWN", 
            "postgresql": "UP"
        }
        assert statuses == expected
    
    def test_determine_app_status_all_up(self):
        """Test app status when all services are UP."""
        service_statuses = {
            "httpd": "UP",
            "rabbitmq": "UP",
            "postgresql": "UP"
        }
        
        status = self.monitor.determine_app_status(service_statuses)
        assert status == "UP"
    
    def test_determine_app_status_one_down(self):
        """Test app status when one service is DOWN."""
        service_statuses = {
            "httpd": "UP",
            "rabbitmq": "DOWN",
            "postgresql": "UP"
        }
        
        status = self.monitor.determine_app_status(service_statuses)
        assert status == "DOWN"


class TestServiceStatus:
    """Essential tests for ServiceStatus model."""
    
    def test_valid_creation(self):
        """Test creating valid ServiceStatus."""
        status = ServiceStatus(
            service_name="httpd",
            service_status="UP",
            host_name="server1",
            timestamp="2024-01-15T10:30:00Z"
        )
        
        assert status.service_name == "httpd"
        assert status.service_status == "UP"
    
    def test_validation_invalid_status(self):
        """Test validation fails for invalid status."""
        with pytest.raises(ValueError, match="service_status must be either 'UP' or 'DOWN'"):
            ServiceStatus(
                service_name="httpd",
                service_status="INVALID",
                host_name="server1",
                timestamp="2024-01-15T10:30:00Z"
            )
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        status = ServiceStatus(
            service_name="httpd",
            service_status="UP",
            host_name="server1",
            timestamp="2024-01-15T10:30:00Z"
        )
        
        result = status.to_dict()
        expected = {
            "service_name": "httpd",
            "service_status": "UP",
            "host_name": "server1",
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        assert result == expected