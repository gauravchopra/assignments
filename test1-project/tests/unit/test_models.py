"""
Unit tests for monitoring system data models.
"""
import pytest
import json
from datetime import datetime
from src.monitor.models import ServiceStatus


class TestServiceStatus:
    """Test cases for ServiceStatus data model."""
    
    def test_valid_service_status_creation(self):
        """Test creating a valid ServiceStatus instance."""
        timestamp = datetime.now().isoformat() + 'Z'
        status = ServiceStatus(
            service_name="httpd",
            service_status="UP",
            host_name="server1",
            timestamp=timestamp
        )
        
        assert status.service_name == "httpd"
        assert status.service_status == "UP"
        assert status.host_name == "server1"
        assert status.timestamp == timestamp
    
    def test_service_status_validation_empty_service_name(self):
        """Test validation fails for empty service name."""
        timestamp = datetime.now().isoformat() + 'Z'
        
        with pytest.raises(ValueError, match="service_name must be a non-empty string"):
            ServiceStatus(
                service_name="",
                service_status="UP",
                host_name="server1",
                timestamp=timestamp
            )
    
    def test_service_status_validation_none_service_name(self):
        """Test validation fails for None service name."""
        timestamp = datetime.now().isoformat() + 'Z'
        
        with pytest.raises(ValueError, match="service_name must be a non-empty string"):
            ServiceStatus(
                service_name=None,
                service_status="UP",
                host_name="server1",
                timestamp=timestamp
            )
    
    def test_service_status_validation_invalid_status(self):
        """Test validation fails for invalid service status."""
        timestamp = datetime.now().isoformat() + 'Z'
        
        with pytest.raises(ValueError, match="service_status must be either 'UP' or 'DOWN'"):
            ServiceStatus(
                service_name="httpd",
                service_status="UNKNOWN",
                host_name="server1",
                timestamp=timestamp
            )
    
    def test_service_status_validation_empty_host_name(self):
        """Test validation fails for empty host name."""
        timestamp = datetime.now().isoformat() + 'Z'
        
        with pytest.raises(ValueError, match="host_name must be a non-empty string"):
            ServiceStatus(
                service_name="httpd",
                service_status="UP",
                host_name="",
                timestamp=timestamp
            )
    
    def test_service_status_validation_invalid_timestamp_format(self):
        """Test validation fails for invalid timestamp format."""
        with pytest.raises(ValueError, match="timestamp must be in ISO 8601 format"):
            ServiceStatus(
                service_name="httpd",
                service_status="UP",
                host_name="server1",
                timestamp="invalid-timestamp"
            )
    
    def test_service_status_validation_empty_timestamp(self):
        """Test validation fails for empty timestamp."""
        with pytest.raises(ValueError, match="timestamp must be a non-empty string"):
            ServiceStatus(
                service_name="httpd",
                service_status="UP",
                host_name="server1",
                timestamp=""
            )
    
    def test_to_dict_conversion(self):
        """Test converting ServiceStatus to dictionary."""
        timestamp = "2024-01-15T10:30:00Z"
        status = ServiceStatus(
            service_name="httpd",
            service_status="UP",
            host_name="server1",
            timestamp=timestamp
        )
        
        result = status.to_dict()
        expected = {
            "service_name": "httpd",
            "service_status": "UP",
            "host_name": "server1",
            "timestamp": timestamp
        }
        
        assert result == expected
    
    def test_to_json_conversion(self):
        """Test converting ServiceStatus to JSON string."""
        timestamp = "2024-01-15T10:30:00Z"
        status = ServiceStatus(
            service_name="httpd",
            service_status="UP",
            host_name="server1",
            timestamp=timestamp
        )
        
        result = status.to_json()
        parsed = json.loads(result)
        
        expected = {
            "service_name": "httpd",
            "service_status": "UP",
            "host_name": "server1",
            "timestamp": timestamp
        }
        
        assert parsed == expected
    
    def test_from_dict_creation(self):
        """Test creating ServiceStatus from dictionary."""
        timestamp = "2024-01-15T10:30:00Z"
        data = {
            "service_name": "httpd",
            "service_status": "UP",
            "host_name": "server1",
            "timestamp": timestamp
        }
        
        status = ServiceStatus.from_dict(data)
        
        assert status.service_name == "httpd"
        assert status.service_status == "UP"
        assert status.host_name == "server1"
        assert status.timestamp == timestamp
    
    def test_from_json_creation(self):
        """Test creating ServiceStatus from JSON string."""
        timestamp = "2024-01-15T10:30:00Z"
        json_data = json.dumps({
            "service_name": "httpd",
            "service_status": "UP",
            "host_name": "server1",
            "timestamp": timestamp
        })
        
        status = ServiceStatus.from_json(json_data)
        
        assert status.service_name == "httpd"
        assert status.service_status == "UP"
        assert status.host_name == "server1"
        assert status.timestamp == timestamp
    
    def test_from_json_invalid_json(self):
        """Test from_json fails with invalid JSON."""
        with pytest.raises(json.JSONDecodeError):
            ServiceStatus.from_json("invalid json")
    
    def test_from_dict_validation_failure(self):
        """Test from_dict fails when validation fails."""
        data = {
            "service_name": "httpd",
            "service_status": "INVALID",
            "host_name": "server1",
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        with pytest.raises(ValueError, match="service_status must be either 'UP' or 'DOWN'"):
            ServiceStatus.from_dict(data)
    
    def test_down_status_valid(self):
        """Test that DOWN status is valid."""
        timestamp = "2024-01-15T10:30:00Z"
        status = ServiceStatus(
            service_name="postgresql",
            service_status="DOWN",
            host_name="server1",
            timestamp=timestamp
        )
        
        assert status.service_status == "DOWN"
    
    def test_iso_timestamp_with_timezone(self):
        """Test that ISO timestamp with timezone is valid."""
        timestamp = "2024-01-15T10:30:00+05:00"
        status = ServiceStatus(
            service_name="rabbitmq",
            service_status="UP",
            host_name="server1",
            timestamp=timestamp
        )
        
        assert status.timestamp == timestamp