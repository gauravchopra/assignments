"""
Data models for the monitoring system.
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any
import json


@dataclass
class ServiceStatus:
    """
    Data model for service status information.
    
    Attributes:
        service_name: Name of the service being monitored
        service_status: Status of the service ("UP" or "DOWN")
        host_name: Hostname where the service is running
        timestamp: ISO format timestamp when status was checked
    """
    service_name: str
    service_status: str
    host_name: str
    timestamp: str
    
    def __post_init__(self):
        """Validate the data after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate the service status data."""
        if not self.service_name or not isinstance(self.service_name, str):
            raise ValueError("service_name must be a non-empty string")
        
        if self.service_status not in ["UP", "DOWN"]:
            raise ValueError("service_status must be either 'UP' or 'DOWN'")
        
        if not self.host_name or not isinstance(self.host_name, str):
            raise ValueError("host_name must be a non-empty string")
        
        if not self.timestamp or not isinstance(self.timestamp, str):
            raise ValueError("timestamp must be a non-empty string")
        
        # Validate timestamp format (ISO 8601)
        try:
            datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("timestamp must be in ISO 8601 format")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the ServiceStatus to a dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert the ServiceStatus to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceStatus':
        """Create a ServiceStatus instance from a dictionary."""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ServiceStatus':
        """Create a ServiceStatus instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)