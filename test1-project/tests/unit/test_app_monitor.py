"""
Unit tests for application monitoring functionality.
"""
import pytest
from unittest.mock import Mock, patch
from src.monitor.app_monitor import ApplicationMonitor
from src.monitor.service_checker import ServiceChecker
from src.monitor.models import ServiceStatus


class TestApplicationMonitor:
    """Test cases for ApplicationMonitor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_service_checker = Mock(spec=ServiceChecker)
        self.monitor = ApplicationMonitor(self.mock_service_checker)
    
    def test_init_with_service_checker(self):
        """Test initialization with provided service checker."""
        checker = Mock(spec=ServiceChecker)
        monitor = ApplicationMonitor(checker)
        
        assert monitor.service_checker is checker
    
    def test_init_without_service_checker(self):
        """Test initialization without service checker creates new one."""
        with patch('src.monitor.app_monitor.ServiceChecker') as mock_checker_class:
            monitor = ApplicationMonitor()
            
            mock_checker_class.assert_called_once()
            assert monitor.service_checker is mock_checker_class.return_value
    
    def test_required_services_constant(self):
        """Test that required services are correctly defined."""
        expected_services = ["httpd", "rabbitmq", "postgresql"]
        assert ApplicationMonitor.REQUIRED_SERVICES == expected_services
    
    def test_check_service_statuses_default_services(self):
        """Test checking status of default required services."""
        # Mock service checker responses
        self.mock_service_checker.check_service_status.side_effect = ["UP", "UP", "DOWN"]
        
        statuses = self.monitor.check_service_statuses()
        
        expected = {
            "httpd": "UP",
            "rabbitmq": "UP", 
            "postgresql": "DOWN"
        }
        assert statuses == expected
        
        # Verify all services were checked
        expected_calls = [
            (("httpd",), {}),
            (("rabbitmq",), {}),
            (("postgresql",), {})
        ]
        actual_calls = [call for call in self.mock_service_checker.check_service_status.call_args_list]
        assert actual_calls == expected_calls
    
    def test_check_service_statuses_custom_services(self):
        """Test checking status of custom service list."""
        custom_services = ["nginx", "redis"]
        self.mock_service_checker.check_service_status.side_effect = ["UP", "DOWN"]
        
        statuses = self.monitor.check_service_statuses(custom_services)
        
        expected = {
            "nginx": "UP",
            "redis": "DOWN"
        }
        assert statuses == expected
    
    def test_check_service_statuses_empty_list_error(self):
        """Test that empty services list raises error."""
        with pytest.raises(ValueError, match="services list cannot be empty"):
            self.monitor.check_service_statuses([])
    
    def test_check_service_statuses_with_exception(self):
        """Test handling of exceptions during service status check."""
        # First service succeeds, second fails, third succeeds
        self.mock_service_checker.check_service_status.side_effect = [
            "UP", 
            Exception("Service check failed"),
            "DOWN"
        ]
        
        statuses = self.monitor.check_service_statuses()
        
        expected = {
            "httpd": "UP",
            "rabbitmq": "DOWN",  # Exception should result in DOWN
            "postgresql": "DOWN"
        }
        assert statuses == expected
    
    def test_determine_app_status_all_up(self):
        """Test app status when all required services are UP."""
        service_statuses = {
            "httpd": "UP",
            "rabbitmq": "UP",
            "postgresql": "UP"
        }
        
        status = self.monitor.determine_app_status(service_statuses)
        
        assert status == "UP"
    
    def test_determine_app_status_one_down(self):
        """Test app status when one required service is DOWN."""
        service_statuses = {
            "httpd": "UP",
            "rabbitmq": "DOWN",
            "postgresql": "UP"
        }
        
        status = self.monitor.determine_app_status(service_statuses)
        
        assert status == "DOWN"
    
    def test_determine_app_status_all_down(self):
        """Test app status when all required services are DOWN."""
        service_statuses = {
            "httpd": "DOWN",
            "rabbitmq": "DOWN",
            "postgresql": "DOWN"
        }
        
        status = self.monitor.determine_app_status(service_statuses)
        
        assert status == "DOWN"
    
    def test_determine_app_status_missing_service(self):
        """Test app status when a required service is missing from status check."""
        service_statuses = {
            "httpd": "UP",
            "rabbitmq": "UP"
            # postgresql is missing
        }
        
        status = self.monitor.determine_app_status(service_statuses)
        
        assert status == "DOWN"
    
    def test_determine_app_status_empty_statuses(self):
        """Test app status with empty service statuses."""
        status = self.monitor.determine_app_status({})
        
        assert status == "DOWN"
    
    def test_determine_app_status_extra_services(self):
        """Test app status with extra services beyond required ones."""
        service_statuses = {
            "httpd": "UP",
            "rabbitmq": "UP",
            "postgresql": "UP",
            "nginx": "DOWN",  # Extra service that's down
            "redis": "UP"     # Extra service that's up
        }
        
        status = self.monitor.determine_app_status(service_statuses)
        
        # Should still be UP since all required services are UP
        assert status == "UP"
    
    def test_get_rbcapp1_status_success(self):
        """Test getting rbcapp1 status successfully."""
        self.mock_service_checker.check_service_status.side_effect = ["UP", "UP", "UP"]
        
        status = self.monitor.get_rbcapp1_status()
        
        assert status == "UP"
    
    def test_get_rbcapp1_status_with_failure(self):
        """Test getting rbcapp1 status when service check fails."""
        self.mock_service_checker.check_service_status.side_effect = ["UP", "DOWN", "UP"]
        
        status = self.monitor.get_rbcapp1_status()
        
        assert status == "DOWN"
    
    def test_get_rbcapp1_status_with_exception(self):
        """Test getting rbcapp1 status when exception occurs."""
        self.mock_service_checker.check_service_status.side_effect = Exception("System error")
        
        status = self.monitor.get_rbcapp1_status()
        
        assert status == "DOWN"
    
    def test_create_service_status_objects(self):
        """Test creating ServiceStatus objects from service statuses."""
        self.mock_service_checker.get_hostname.return_value = "test-host"
        self.mock_service_checker.get_current_timestamp.return_value = "2024-01-15T10:30:00Z"
        
        service_statuses = {
            "httpd": "UP",
            "rabbitmq": "DOWN"
        }
        
        objects = self.monitor.create_service_status_objects(service_statuses)
        
        assert len(objects) == 2
        
        # Check first object
        assert objects[0].service_name == "httpd"
        assert objects[0].service_status == "UP"
        assert objects[0].host_name == "test-host"
        assert objects[0].timestamp == "2024-01-15T10:30:00Z"
        
        # Check second object
        assert objects[1].service_name == "rabbitmq"
        assert objects[1].service_status == "DOWN"
        assert objects[1].host_name == "test-host"
        assert objects[1].timestamp == "2024-01-15T10:30:00Z"
    
    def test_create_service_status_objects_with_exception(self):
        """Test creating ServiceStatus objects when validation fails."""
        self.mock_service_checker.get_hostname.return_value = "test-host"
        self.mock_service_checker.get_current_timestamp.return_value = "invalid-timestamp"
        
        service_statuses = {
            "httpd": "UP"
        }
        
        # Should handle validation error gracefully
        objects = self.monitor.create_service_status_objects(service_statuses)
        
        # Should return empty list due to validation error
        assert len(objects) == 0
    
    def test_create_rbcapp1_status_object(self):
        """Test creating ServiceStatus object for rbcapp1."""
        self.mock_service_checker.get_hostname.return_value = "test-host"
        self.mock_service_checker.get_current_timestamp.return_value = "2024-01-15T10:30:00Z"
        
        obj = self.monitor.create_rbcapp1_status_object("UP")
        
        assert obj.service_name == "rbcapp1"
        assert obj.service_status == "UP"
        assert obj.host_name == "test-host"
        assert obj.timestamp == "2024-01-15T10:30:00Z"
    
    def test_get_full_monitoring_report_success(self):
        """Test getting full monitoring report successfully."""
        # Mock service checker responses
        self.mock_service_checker.check_service_status.side_effect = ["UP", "UP", "UP"]
        self.mock_service_checker.get_hostname.return_value = "test-host"
        self.mock_service_checker.get_current_timestamp.return_value = "2024-01-15T10:30:00Z"
        
        report = self.monitor.get_full_monitoring_report()
        
        # Check report structure
        assert "service_statuses" in report
        assert "app_status" in report
        assert "service_objects" in report
        assert "app_object" in report
        assert "timestamp" in report
        assert "error" not in report
        
        # Check service statuses
        expected_statuses = {
            "httpd": "UP",
            "rabbitmq": "UP",
            "postgresql": "UP"
        }
        assert report["service_statuses"] == expected_statuses
        
        # Check app status
        assert report["app_status"] == "UP"
        
        # Check service objects
        assert len(report["service_objects"]) == 3
        
        # Check app object
        assert report["app_object"].service_name == "rbcapp1"
        assert report["app_object"].service_status == "UP"
    
    def test_get_full_monitoring_report_with_failure(self):
        """Test getting full monitoring report when services are down."""
        # Mock service checker responses - one service down
        self.mock_service_checker.check_service_status.side_effect = ["UP", "DOWN", "UP"]
        self.mock_service_checker.get_hostname.return_value = "test-host"
        self.mock_service_checker.get_current_timestamp.return_value = "2024-01-15T10:30:00Z"
        
        report = self.monitor.get_full_monitoring_report()
        
        # App should be DOWN due to one service being down
        assert report["app_status"] == "DOWN"
        assert report["app_object"].service_status == "DOWN"
    
    def test_get_full_monitoring_report_with_exception(self):
        """Test getting full monitoring report when exception occurs."""
        # Mock service checker to raise exception
        self.mock_service_checker.check_service_status.side_effect = Exception("System error")
        self.mock_service_checker.get_hostname.return_value = "test-host"
        self.mock_service_checker.get_current_timestamp.return_value = "2024-01-15T10:30:00Z"
        
        report = self.monitor.get_full_monitoring_report()
        
        # Should return report with services marked as DOWN due to exceptions
        expected_statuses = {
            "httpd": "DOWN",
            "rabbitmq": "DOWN", 
            "postgresql": "DOWN"
        }
        assert report["service_statuses"] == expected_statuses
        assert report["app_status"] == "DOWN"
        assert len(report["service_objects"]) == 3  # Objects created with DOWN status
        assert report["app_object"].service_status == "DOWN"
        assert "error" not in report  # No error in report since service checking handled exceptions gracefully
        
        # Verify all service objects have DOWN status
        for service_obj in report["service_objects"]:
            assert service_obj.service_status == "DOWN"
    
    def test_generate_json_filename_with_timestamp(self):
        """Test generating JSON filename with provided timestamp."""
        filename = self.monitor.generate_json_filename("httpd", "2024-01-15T10:30:00Z")
        
        expected = "httpd-status-2024-01-15T10-30-00Z.json"
        assert filename == expected
    
    def test_generate_json_filename_without_timestamp(self):
        """Test generating JSON filename without timestamp uses current time."""
        self.mock_service_checker.get_current_timestamp.return_value = "2024-01-15T10:30:00Z"
        
        filename = self.monitor.generate_json_filename("rabbitmq")
        
        expected = "rabbitmq-status-2024-01-15T10-30-00Z.json"
        assert filename == expected
    
    def test_generate_json_filename_invalid_service_name(self):
        """Test generating JSON filename with invalid service name."""
        with pytest.raises(ValueError, match="service_name must be a non-empty string"):
            self.monitor.generate_json_filename("")
        
        with pytest.raises(ValueError, match="service_name must be a non-empty string"):
            self.monitor.generate_json_filename(None)
    
    def test_generate_json_filename_special_characters(self):
        """Test generating JSON filename handles special characters in timestamp."""
        filename = self.monitor.generate_json_filename("test-service", "2024-01-15T10:30:45.123Z")
        
        expected = "test-service-status-2024-01-15T10-30-45-123Z.json"
        assert filename == expected
    
    @patch('src.monitor.app_monitor.Path')
    @patch('builtins.open')
    @patch('src.monitor.app_monitor.json.dump')
    def test_write_status_file_success(self, mock_json_dump, mock_open, mock_path):
        """Test successfully writing status file."""
        # Create test ServiceStatus object
        service_status = ServiceStatus(
            service_name="httpd",
            service_status="UP",
            host_name="test-host",
            timestamp="2024-01-15T10:30:00Z"
        )
        
        # Mock Path operations
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.mkdir = Mock()
        mock_path_instance.__truediv__ = Mock(return_value=mock_path_instance)
        mock_path_instance.__str__ = Mock(return_value="data/httpd-status-2024-01-15T10-30-00Z.json")
        
        # Mock file operations
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        result = self.monitor.write_status_file(service_status, "data")
        
        # Verify directory creation
        mock_path_instance.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        
        # Verify file opening
        mock_open.assert_called_once()
        
        # Verify JSON writing
        mock_json_dump.assert_called_once_with(
            service_status.to_dict(), 
            mock_file, 
            indent=2, 
            ensure_ascii=False
        )
        
        # Verify return value
        assert result == "data/httpd-status-2024-01-15T10-30-00Z.json"
    
    def test_write_status_file_invalid_input(self):
        """Test writing status file with invalid input."""
        with pytest.raises(ValueError, match="service_status must be a ServiceStatus instance"):
            self.monitor.write_status_file("not a ServiceStatus object")
        
        with pytest.raises(ValueError, match="service_status must be a ServiceStatus instance"):
            self.monitor.write_status_file(None)
    
    @patch('src.monitor.app_monitor.Path')
    @patch('builtins.open')
    def test_write_status_file_os_error(self, mock_open, mock_path):
        """Test writing status file when OS error occurs."""
        service_status = ServiceStatus(
            service_name="httpd",
            service_status="UP",
            host_name="test-host",
            timestamp="2024-01-15T10:30:00Z"
        )
        
        # Mock Path operations
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.mkdir = Mock()
        mock_path_instance.__truediv__ = Mock(return_value=mock_path_instance)
        
        # Mock file operations to raise OSError
        mock_open.side_effect = OSError("Permission denied")
        
        with pytest.raises(OSError, match="Cannot write status file: Permission denied"):
            self.monitor.write_status_file(service_status)
    
    @patch('src.monitor.app_monitor.ApplicationMonitor.write_status_file')
    def test_write_multiple_status_files_success(self, mock_write_status_file):
        """Test writing multiple status files successfully."""
        # Create test ServiceStatus objects
        service_statuses = [
            ServiceStatus("httpd", "UP", "test-host", "2024-01-15T10:30:00Z"),
            ServiceStatus("rabbitmq", "DOWN", "test-host", "2024-01-15T10:30:00Z")
        ]
        
        # Mock successful file writes
        mock_write_status_file.side_effect = [
            "data/httpd-status-2024-01-15T10-30-00Z.json",
            "data/rabbitmq-status-2024-01-15T10-30-00Z.json"
        ]
        
        result = self.monitor.write_multiple_status_files(service_statuses, "data")
        
        # Verify all files were written
        assert len(result) == 2
        assert result[0] == "data/httpd-status-2024-01-15T10-30-00Z.json"
        assert result[1] == "data/rabbitmq-status-2024-01-15T10-30-00Z.json"
        
        # Verify write_status_file was called for each service
        assert mock_write_status_file.call_count == 2
    
    @patch('src.monitor.app_monitor.ApplicationMonitor.write_status_file')
    def test_write_multiple_status_files_with_errors(self, mock_write_status_file):
        """Test writing multiple status files with some errors."""
        # Create test ServiceStatus objects
        service_statuses = [
            ServiceStatus("httpd", "UP", "test-host", "2024-01-15T10:30:00Z"),
            ServiceStatus("rabbitmq", "DOWN", "test-host", "2024-01-15T10:30:00Z"),
            ServiceStatus("postgresql", "UP", "test-host", "2024-01-15T10:30:00Z")
        ]
        
        # Mock file writes with one error
        mock_write_status_file.side_effect = [
            "data/httpd-status-2024-01-15T10-30-00Z.json",
            OSError("Permission denied"),
            "data/postgresql-status-2024-01-15T10-30-00Z.json"
        ]
        
        result = self.monitor.write_multiple_status_files(service_statuses, "data")
        
        # Should return successful writes only
        assert len(result) == 2
        assert result[0] == "data/httpd-status-2024-01-15T10-30-00Z.json"
        assert result[1] == "data/postgresql-status-2024-01-15T10-30-00Z.json"
        
        # Verify write_status_file was called for each service
        assert mock_write_status_file.call_count == 3
    
    def test_write_multiple_status_files_invalid_input(self):
        """Test writing multiple status files with invalid input."""
        with pytest.raises(ValueError, match="service_statuses must be a list"):
            self.monitor.write_multiple_status_files("not a list")
        
        with pytest.raises(ValueError, match="service_statuses must be a list"):
            self.monitor.write_multiple_status_files(None)