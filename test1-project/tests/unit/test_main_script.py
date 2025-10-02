"""
Unit tests for main monitoring script error handling.
"""
import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
from src.monitor.main import (
    setup_logging, monitor_services, monitor_rbcapp1, 
    print_monitoring_summary, main
)
from src.monitor.models import ServiceStatus


class TestSetupLogging:
    """Test cases for logging setup."""
    
    @patch('src.monitor.main.logging.basicConfig')
    def test_setup_logging_default(self, mock_basic_config):
        """Test logging setup with default parameters."""
        setup_logging()
        
        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args[1]
        assert call_args['level'] == 20  # INFO level
        assert 'format' in call_args
        assert 'datefmt' in call_args
        assert 'filename' not in call_args
    
    @patch('src.monitor.main.logging.basicConfig')
    def test_setup_logging_with_file(self, mock_basic_config):
        """Test logging setup with log file."""
        setup_logging(log_level="DEBUG", log_file="/tmp/test.log")
        
        mock_basic_config.assert_called_once()
        call_args = mock_basic_config.call_args[1]
        assert call_args['level'] == 10  # DEBUG level
        assert call_args['filename'] == "/tmp/test.log"
        assert call_args['filemode'] == 'a'
    
    @patch('src.monitor.main.logging.basicConfig')
    def test_setup_logging_invalid_level(self, mock_basic_config):
        """Test logging setup with invalid log level."""
        with pytest.raises(AttributeError):
            setup_logging(log_level="INVALID")


class TestMonitorServices:
    """Test cases for monitor_services function."""
    
    @patch('src.monitor.main.ApplicationMonitor')
    @patch('src.monitor.main.ServiceChecker')
    def test_monitor_services_success(self, mock_service_checker_class, mock_app_monitor_class):
        """Test successful service monitoring."""
        # Mock service checker
        mock_service_checker = Mock()
        mock_service_checker.get_current_timestamp.return_value = "2024-01-15T10:30:00Z"
        mock_service_checker.get_hostname.return_value = "test-host"
        mock_service_checker_class.return_value = mock_service_checker
        
        # Mock application monitor
        mock_monitor = Mock()
        mock_monitor.check_service_statuses.return_value = {"httpd": "UP", "rabbitmq": "DOWN"}
        mock_monitor.create_service_status_objects.return_value = [
            ServiceStatus("httpd", "UP", "test-host", "2024-01-15T10:30:00Z"),
            ServiceStatus("rabbitmq", "DOWN", "test-host", "2024-01-15T10:30:00Z")
        ]
        mock_monitor.write_multiple_status_files.return_value = [
            "data/httpd-status-2024-01-15T10-30-00Z.json",
            "data/rabbitmq-status-2024-01-15T10-30-00Z.json"
        ]
        mock_app_monitor_class.return_value = mock_monitor
        
        services = ["httpd", "rabbitmq"]
        report = monitor_services(services, "data", write_files=True)
        
        # Verify report structure
        assert report["services_monitored"] == services
        assert report["service_statuses"] == {"httpd": "UP", "rabbitmq": "DOWN"}
        assert len(report["status_objects"]) == 2
        assert len(report["written_files"]) == 2
        assert "timestamp" in report
        assert "hostname" in report
    
    @patch('src.monitor.main.ApplicationMonitor')
    @patch('src.monitor.main.ServiceChecker')
    def test_monitor_services_no_files(self, mock_service_checker_class, mock_app_monitor_class):
        """Test service monitoring without writing files."""
        # Mock service checker
        mock_service_checker = Mock()
        mock_service_checker.get_current_timestamp.return_value = "2024-01-15T10:30:00Z"
        mock_service_checker.get_hostname.return_value = "test-host"
        mock_service_checker_class.return_value = mock_service_checker
        
        # Mock application monitor
        mock_monitor = Mock()
        mock_monitor.check_service_statuses.return_value = {"httpd": "UP"}
        mock_monitor.create_service_status_objects.return_value = [
            ServiceStatus("httpd", "UP", "test-host", "2024-01-15T10:30:00Z")
        ]
        mock_app_monitor_class.return_value = mock_monitor
        
        report = monitor_services(["httpd"], "data", write_files=False)
        
        # Should not write files
        assert report["written_files"] == []
        mock_monitor.write_multiple_status_files.assert_not_called()
    
    @patch('src.monitor.main.ApplicationMonitor')
    @patch('src.monitor.main.ServiceChecker')
    def test_monitor_services_exception(self, mock_service_checker_class, mock_app_monitor_class):
        """Test service monitoring when exception occurs."""
        # Mock service checker
        mock_service_checker_class.return_value = Mock()
        
        # Mock application monitor to raise exception
        mock_monitor = Mock()
        mock_monitor.check_service_statuses.side_effect = Exception("Monitoring failed")
        mock_app_monitor_class.return_value = mock_monitor
        
        with pytest.raises(Exception, match="Monitoring failed"):
            monitor_services(["httpd"], "data")


class TestMonitorRbcapp1:
    """Test cases for monitor_rbcapp1 function."""
    
    @patch('src.monitor.main.ApplicationMonitor')
    @patch('src.monitor.main.ServiceChecker')
    def test_monitor_rbcapp1_success(self, mock_service_checker_class, mock_app_monitor_class):
        """Test successful rbcapp1 monitoring."""
        # Mock service checker
        mock_service_checker = Mock()
        mock_service_checker_class.return_value = mock_service_checker
        
        # Mock application monitor
        mock_monitor = Mock()
        mock_report = {
            "service_statuses": {"httpd": "UP", "rabbitmq": "UP", "postgresql": "UP"},
            "app_status": "UP",
            "service_objects": [
                ServiceStatus("httpd", "UP", "test-host", "2024-01-15T10:30:00Z"),
                ServiceStatus("rabbitmq", "UP", "test-host", "2024-01-15T10:30:00Z"),
                ServiceStatus("postgresql", "UP", "test-host", "2024-01-15T10:30:00Z")
            ],
            "app_object": ServiceStatus("rbcapp1", "UP", "test-host", "2024-01-15T10:30:00Z"),
            "timestamp": "2024-01-15T10:30:00Z"
        }
        mock_monitor.get_full_monitoring_report.return_value = mock_report
        mock_monitor.write_multiple_status_files.return_value = [
            "data/httpd-status-2024-01-15T10-30-00Z.json",
            "data/rabbitmq-status-2024-01-15T10-30-00Z.json",
            "data/postgresql-status-2024-01-15T10-30-00Z.json"
        ]
        mock_monitor.write_status_file.return_value = "data/rbcapp1-status-2024-01-15T10-30-00Z.json"
        mock_app_monitor_class.return_value = mock_monitor
        
        report = monitor_rbcapp1("data", write_files=True)
        
        # Verify report structure
        assert report["service_statuses"] == {"httpd": "UP", "rabbitmq": "UP", "postgresql": "UP"}
        assert report["app_status"] == "UP"
        assert len(report["written_files"]) == 4  # 3 services + 1 app
    
    @patch('src.monitor.main.ApplicationMonitor')
    @patch('src.monitor.main.ServiceChecker')
    def test_monitor_rbcapp1_exception(self, mock_service_checker_class, mock_app_monitor_class):
        """Test rbcapp1 monitoring when exception occurs."""
        # Mock service checker
        mock_service_checker_class.return_value = Mock()
        
        # Mock application monitor to raise exception
        mock_monitor = Mock()
        mock_monitor.get_full_monitoring_report.side_effect = Exception("Monitoring failed")
        mock_app_monitor_class.return_value = mock_monitor
        
        with pytest.raises(Exception, match="Monitoring failed"):
            monitor_rbcapp1("data")


class TestPrintMonitoringSummary:
    """Test cases for print_monitoring_summary function."""
    
    def test_print_monitoring_summary_complete_report(self, capsys):
        """Test printing complete monitoring summary."""
        report = {
            "timestamp": "2024-01-15T10:30:00Z",
            "hostname": "test-host",
            "service_statuses": {"httpd": "UP", "rabbitmq": "DOWN"},
            "app_status": "DOWN",
            "written_files": ["data/httpd-status.json", "data/rbcapp1-status.json"]
        }
        
        print_monitoring_summary(report)
        
        captured = capsys.readouterr()
        assert "MONITORING SUMMARY" in captured.out
        assert "test-host" in captured.out
        assert "2024-01-15T10:30:00Z" in captured.out
        assert "✓ httpd: UP" in captured.out
        assert "✗ rabbitmq: DOWN" in captured.out
        assert "✗ rbcapp1: DOWN" in captured.out
        assert "data/httpd-status.json" in captured.out
    
    def test_print_monitoring_summary_minimal_report(self, capsys):
        """Test printing minimal monitoring summary."""
        report = {
            "timestamp": "Unknown",
            "hostname": "Unknown"
        }
        
        print_monitoring_summary(report)
        
        captured = capsys.readouterr()
        assert "MONITORING SUMMARY" in captured.out
        assert "Unknown" in captured.out
    
    def test_print_monitoring_summary_with_error(self, capsys):
        """Test printing monitoring summary with error."""
        report = {
            "timestamp": "2024-01-15T10:30:00Z",
            "hostname": "test-host",
            "error": "System failure"
        }
        
        print_monitoring_summary(report)
        
        captured = capsys.readouterr()
        assert "Error: System failure" in captured.out


class TestMainFunction:
    """Test cases for main function."""
    
    @patch('src.monitor.main.monitor_rbcapp1')
    @patch('src.monitor.main.setup_logging')
    def test_main_default_rbcapp1_monitoring(self, mock_setup_logging, mock_monitor_rbcapp1):
        """Test main function with default rbcapp1 monitoring."""
        mock_monitor_rbcapp1.return_value = {
            "app_status": "UP",
            "service_statuses": {"httpd": "UP", "rabbitmq": "UP", "postgresql": "UP"}
        }
        
        with patch('sys.argv', ['main.py']):
            exit_code = main()
        
        assert exit_code == 0
        mock_setup_logging.assert_called_once()
        mock_monitor_rbcapp1.assert_called_once_with(output_dir="data", write_files=True)
    
    @patch('src.monitor.main.monitor_services')
    @patch('src.monitor.main.setup_logging')
    def test_main_specific_services(self, mock_setup_logging, mock_monitor_services):
        """Test main function with specific services."""
        mock_monitor_services.return_value = {
            "service_statuses": {"httpd": "UP", "nginx": "DOWN"}
        }
        
        with patch('sys.argv', ['main.py', '--services', 'httpd', 'nginx']):
            exit_code = main()
        
        assert exit_code == 1  # Exit with error due to nginx being DOWN
        mock_monitor_services.assert_called_once_with(
            services=['httpd', 'nginx'],
            output_dir="data",
            write_files=True
        )
    
    @patch('src.monitor.main.monitor_rbcapp1')
    @patch('src.monitor.main.setup_logging')
    def test_main_app_down_exit_code(self, mock_setup_logging, mock_monitor_rbcapp1):
        """Test main function exit code when app is down."""
        mock_monitor_rbcapp1.return_value = {
            "app_status": "DOWN",
            "service_statuses": {"httpd": "UP", "rabbitmq": "DOWN", "postgresql": "UP"}
        }
        
        with patch('sys.argv', ['main.py']):
            exit_code = main()
        
        assert exit_code == 1
    
    @patch('src.monitor.main.monitor_rbcapp1')
    @patch('src.monitor.main.setup_logging')
    def test_main_no_files_option(self, mock_setup_logging, mock_monitor_rbcapp1):
        """Test main function with --no-files option."""
        mock_monitor_rbcapp1.return_value = {
            "app_status": "UP",
            "service_statuses": {"httpd": "UP", "rabbitmq": "UP", "postgresql": "UP"}
        }
        
        with patch('sys.argv', ['main.py', '--no-files']):
            exit_code = main()
        
        assert exit_code == 0
        mock_monitor_rbcapp1.assert_called_once_with(output_dir="data", write_files=False)
    
    @patch('src.monitor.main.monitor_rbcapp1')
    @patch('src.monitor.main.setup_logging')
    def test_main_custom_output_dir(self, mock_setup_logging, mock_monitor_rbcapp1):
        """Test main function with custom output directory."""
        mock_monitor_rbcapp1.return_value = {
            "app_status": "UP",
            "service_statuses": {"httpd": "UP", "rabbitmq": "UP", "postgresql": "UP"}
        }
        
        with patch('sys.argv', ['main.py', '--output-dir', '/tmp/monitoring']):
            exit_code = main()
        
        assert exit_code == 0
        mock_monitor_rbcapp1.assert_called_once_with(output_dir="/tmp/monitoring", write_files=True)
    
    @patch('src.monitor.main.monitor_rbcapp1')
    @patch('src.monitor.main.setup_logging')
    def test_main_quiet_mode(self, mock_setup_logging, mock_monitor_rbcapp1, capsys):
        """Test main function in quiet mode."""
        mock_monitor_rbcapp1.return_value = {
            "app_status": "UP",
            "service_statuses": {"httpd": "UP", "rabbitmq": "UP", "postgresql": "UP"}
        }
        
        with patch('sys.argv', ['main.py', '--quiet']):
            exit_code = main()
        
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "MONITORING SUMMARY" not in captured.out
    
    @patch('src.monitor.main.monitor_rbcapp1')
    @patch('src.monitor.main.setup_logging')
    def test_main_keyboard_interrupt(self, mock_setup_logging, mock_monitor_rbcapp1, capsys):
        """Test main function handling keyboard interrupt."""
        mock_monitor_rbcapp1.side_effect = KeyboardInterrupt()
        
        with patch('sys.argv', ['main.py']):
            exit_code = main()
        
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "interrupted by user" in captured.out
    
    @patch('src.monitor.main.monitor_rbcapp1')
    @patch('src.monitor.main.setup_logging')
    def test_main_exception_handling(self, mock_setup_logging, mock_monitor_rbcapp1, capsys):
        """Test main function handling unexpected exceptions."""
        mock_monitor_rbcapp1.side_effect = Exception("System failure")
        
        with patch('sys.argv', ['main.py']):
            exit_code = main()
        
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Error: System failure" in captured.out
    
    @patch('src.monitor.main.monitor_rbcapp1')
    @patch('src.monitor.main.setup_logging')
    def test_main_log_level_and_file(self, mock_setup_logging, mock_monitor_rbcapp1):
        """Test main function with custom log level and file."""
        mock_monitor_rbcapp1.return_value = {
            "app_status": "UP",
            "service_statuses": {"httpd": "UP", "rabbitmq": "UP", "postgresql": "UP"}
        }
        
        with patch('sys.argv', ['main.py', '--log-level', 'DEBUG', '--log-file', '/tmp/test.log']):
            exit_code = main()
        
        assert exit_code == 0
        mock_setup_logging.assert_called_once_with('DEBUG', '/tmp/test.log')