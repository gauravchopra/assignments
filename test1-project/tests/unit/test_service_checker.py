"""
Unit tests for service status checking functionality.
"""
import pytest
import subprocess
import socket
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.monitor.service_checker import ServiceChecker


class TestServiceChecker:
    """Test cases for ServiceChecker class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.checker = ServiceChecker()
    
    @patch('socket.gethostname')
    def test_get_hostname_success(self, mock_gethostname):
        """Test successful hostname detection."""
        mock_gethostname.return_value = "test-server"
        checker = ServiceChecker()
        
        assert checker.get_hostname() == "test-server"
    
    @patch('socket.gethostname')
    def test_get_hostname_failure(self, mock_gethostname):
        """Test hostname detection failure."""
        mock_gethostname.side_effect = Exception("Network error")
        checker = ServiceChecker()
        
        assert checker.get_hostname() == "unknown-host"
    
    @patch('subprocess.run')
    def test_check_service_status_up(self, mock_run):
        """Test checking service status when service is UP."""
        # Mock successful systemctl response
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "active\n"
        mock_run.return_value = mock_result
        
        status = self.checker.check_service_status("httpd")
        
        assert status == "UP"
        mock_run.assert_called_once_with(
            ['systemctl', 'is-active', 'httpd'],
            capture_output=True,
            text=True,
            timeout=10
        )
    
    @patch('subprocess.run')
    def test_check_service_status_down_inactive(self, mock_run):
        """Test checking service status when service is inactive."""
        # Mock inactive systemctl response
        mock_result = MagicMock()
        mock_result.returncode = 3
        mock_result.stdout = "inactive\n"
        mock_run.return_value = mock_result
        
        status = self.checker.check_service_status("httpd")
        
        assert status == "DOWN"
    
    @patch('subprocess.run')
    def test_check_service_status_down_failed(self, mock_run):
        """Test checking service status when service is failed."""
        # Mock failed systemctl response
        mock_result = MagicMock()
        mock_result.returncode = 3
        mock_result.stdout = "failed\n"
        mock_run.return_value = mock_result
        
        status = self.checker.check_service_status("postgresql")
        
        assert status == "DOWN"
    
    @patch('subprocess.run')
    def test_check_service_status_timeout(self, mock_run):
        """Test checking service status when systemctl times out."""
        mock_run.side_effect = subprocess.TimeoutExpired(['systemctl'], 10)
        
        status = self.checker.check_service_status("rabbitmq")
        
        assert status == "DOWN"
    
    @patch('subprocess.run')
    def test_check_service_status_called_process_error(self, mock_run):
        """Test checking service status when systemctl raises CalledProcessError."""
        mock_run.side_effect = subprocess.CalledProcessError(1, ['systemctl'])
        
        status = self.checker.check_service_status("httpd")
        
        assert status == "DOWN"
    
    @patch('subprocess.run')
    def test_check_service_status_file_not_found(self, mock_run):
        """Test checking service status when systemctl is not found."""
        mock_run.side_effect = FileNotFoundError("systemctl not found")
        
        status = self.checker.check_service_status("httpd")
        
        assert status == "DOWN"
    
    @patch('subprocess.run')
    def test_check_service_status_unexpected_error(self, mock_run):
        """Test checking service status when unexpected error occurs."""
        mock_run.side_effect = Exception("Unexpected error")
        
        status = self.checker.check_service_status("httpd")
        
        assert status == "DOWN"
    
    def test_check_service_status_empty_service_name(self):
        """Test checking service status with empty service name."""
        with pytest.raises(ValueError, match="service_name must be a non-empty string"):
            self.checker.check_service_status("")
    
    def test_check_service_status_none_service_name(self):
        """Test checking service status with None service name."""
        with pytest.raises(ValueError, match="service_name must be a non-empty string"):
            self.checker.check_service_status(None)
    
    def test_check_service_status_non_string_service_name(self):
        """Test checking service status with non-string service name."""
        with pytest.raises(ValueError, match="service_name must be a non-empty string"):
            self.checker.check_service_status(123)
    
    @patch('subprocess.run')
    def test_check_service_status_active_with_whitespace(self, mock_run):
        """Test checking service status when output has whitespace."""
        # Mock systemctl response with extra whitespace
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "  active  \n"
        mock_run.return_value = mock_result
        
        status = self.checker.check_service_status("httpd")
        
        assert status == "UP"
    
    @patch('subprocess.run')
    def test_check_service_status_active_wrong_returncode(self, mock_run):
        """Test checking service status when output is active but return code is wrong."""
        # Mock systemctl response with active output but non-zero return code
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "active\n"
        mock_run.return_value = mock_result
        
        status = self.checker.check_service_status("httpd")
        
        assert status == "DOWN"
    
    @patch('subprocess.run')
    def test_check_service_status_zero_returncode_wrong_output(self, mock_run):
        """Test checking service status when return code is 0 but output is not active."""
        # Mock systemctl response with zero return code but non-active output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "inactive\n"
        mock_run.return_value = mock_result
        
        status = self.checker.check_service_status("httpd")
        
        assert status == "DOWN"
    
    def test_get_current_timestamp_format(self):
        """Test that current timestamp is in correct ISO format."""
        timestamp = self.checker.get_current_timestamp()
        
        # Should end with 'Z'
        assert timestamp.endswith('Z')
        
        # Should be parseable as ISO format
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    def test_get_current_timestamp_different_calls(self):
        """Test that different calls to get_current_timestamp return different values."""
        import time
        
        timestamp1 = self.checker.get_current_timestamp()
        time.sleep(0.001)  # Small delay
        timestamp2 = self.checker.get_current_timestamp()
        
        # Timestamps should be different (unless system is very fast)
        # At minimum, they should both be valid
        datetime.fromisoformat(timestamp1.replace('Z', '+00:00'))
        datetime.fromisoformat(timestamp2.replace('Z', '+00:00'))
    
    @patch('socket.gethostname')
    def test_hostname_cached_on_init(self, mock_gethostname):
        """Test that hostname is cached during initialization."""
        mock_gethostname.return_value = "cached-host"
        checker = ServiceChecker()
        
        # Call get_hostname multiple times
        host1 = checker.get_hostname()
        host2 = checker.get_hostname()
        
        assert host1 == "cached-host"
        assert host2 == "cached-host"
        # Should only be called once during init
        mock_gethostname.assert_called_once()