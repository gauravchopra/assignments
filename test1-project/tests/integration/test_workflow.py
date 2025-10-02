"""
Simplified integration tests for monitoring workflow.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from src.monitor.main import monitor_services, monitor_rbcapp1, main
from src.monitor.models import ServiceStatus


class TestMonitoringWorkflow:
    """Integration tests for monitoring workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.monitor.main.ServiceChecker')
    @patch('src.monitor.main.ApplicationMonitor')
    def test_monitor_services_workflow(self, mock_monitor_class, mock_checker_class):
        """Test complete service monitoring workflow."""
        # Setup mocks
        mock_checker = Mock()
        mock_checker.get_current_timestamp.return_value = "2024-01-15T10:30:00Z"
        mock_checker.get_hostname.return_value = "test-host"
        mock_checker_class.return_value = mock_checker
        
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        mock_monitor.check_service_statuses.return_value = {"httpd": "UP", "rabbitmq": "DOWN"}
        mock_monitor.create_service_status_objects.return_value = [
            ServiceStatus("httpd", "UP", "test-host", "2024-01-15T10:30:00Z"),
            ServiceStatus("rabbitmq", "DOWN", "test-host", "2024-01-15T10:30:00Z")
        ]
        mock_monitor.write_multiple_status_files.return_value = [
            "data/httpd-status.json",
            "data/rabbitmq-status.json"
        ]
        
        # Run monitoring
        services = ["httpd", "rabbitmq"]
        report = monitor_services(services, self.temp_dir, write_files=True)
        
        # Verify results
        assert report["services_monitored"] == services
        assert report["service_statuses"] == {"httpd": "UP", "rabbitmq": "DOWN"}
        assert len(report["status_objects"]) == 2
        assert len(report["written_files"]) == 2
    
    @patch('src.monitor.main.ServiceChecker')
    @patch('src.monitor.main.ApplicationMonitor')
    def test_monitor_rbcapp1_workflow(self, mock_monitor_class, mock_checker_class):
        """Test rbcapp1 monitoring workflow."""
        # Setup mocks
        mock_checker_class.return_value = Mock()
        
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        service_objects = [
            ServiceStatus("httpd", "UP", "test-host", "2024-01-15T10:30:00Z"),
            ServiceStatus("rabbitmq", "UP", "test-host", "2024-01-15T10:30:00Z"),
            ServiceStatus("postgresql", "UP", "test-host", "2024-01-15T10:30:00Z")
        ]
        app_object = ServiceStatus("rbcapp1", "UP", "test-host", "2024-01-15T10:30:00Z")
        
        mock_report = {
            "service_statuses": {"httpd": "UP", "rabbitmq": "UP", "postgresql": "UP"},
            "app_status": "UP",
            "service_objects": service_objects,
            "app_object": app_object,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        mock_monitor.get_full_monitoring_report.return_value = mock_report
        mock_monitor.write_multiple_status_files.return_value = ["file1.json", "file2.json", "file3.json"]
        mock_monitor.write_status_file.return_value = "rbcapp1.json"
        
        # Run monitoring
        report = monitor_rbcapp1(self.temp_dir, write_files=True)
        
        # Verify results
        assert report["app_status"] == "UP"
        assert len(report["written_files"]) == 4  # 3 services + 1 app
    
    @patch('src.monitor.main.monitor_rbcapp1')
    @patch('src.monitor.main.setup_logging')
    def test_main_function_success(self, mock_setup_logging, mock_monitor_rbcapp1):
        """Test main function with successful monitoring."""
        mock_monitor_rbcapp1.return_value = {
            "app_status": "UP",
            "service_statuses": {"httpd": "UP", "rabbitmq": "UP", "postgresql": "UP"}
        }
        
        with patch('sys.argv', ['main.py']):
            exit_code = main()
        
        assert exit_code == 0
        mock_monitor_rbcapp1.assert_called_once()
    
    @patch('src.monitor.main.monitor_rbcapp1')
    @patch('src.monitor.main.setup_logging')
    def test_main_function_failure(self, mock_setup_logging, mock_monitor_rbcapp1):
        """Test main function with monitoring failure."""
        mock_monitor_rbcapp1.return_value = {
            "app_status": "DOWN",
            "service_statuses": {"httpd": "UP", "rabbitmq": "DOWN", "postgresql": "UP"}
        }
        
        with patch('sys.argv', ['main.py']):
            exit_code = main()
        
        assert exit_code == 1