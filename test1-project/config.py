"""Configuration settings for rbcapp1 monitoring system."""
import os
from dataclasses import dataclass
from typing import List


@dataclass
class MonitoringConfig:
    """Configuration for the monitoring system."""
    
    # Services to monitor
    MONITORED_SERVICES: List[str] = None
    
    # File system settings
    DATA_DIR: str = "data"
    JSON_FILE_PATTERN: str = "{service_name}-status-{timestamp}.json"
    
    # Elasticsearch settings
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_INDEX: str = "service-monitoring"
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 5000
    API_DEBUG: bool = False
    
    def __post_init__(self):
        if self.MONITORED_SERVICES is None:
            self.MONITORED_SERVICES = ["httpd", "rabbitMQ", "postgreSQL"]
        
        # Override with environment variables if present
        self.ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", self.ELASTICSEARCH_HOST)
        self.ELASTICSEARCH_PORT = int(os.getenv("ELASTICSEARCH_PORT", self.ELASTICSEARCH_PORT))
        self.ELASTICSEARCH_INDEX = os.getenv("ELASTICSEARCH_INDEX", self.ELASTICSEARCH_INDEX)
        self.API_HOST = os.getenv("API_HOST", self.API_HOST)
        self.API_PORT = int(os.getenv("API_PORT", self.API_PORT))
        self.API_DEBUG = os.getenv("API_DEBUG", "false").lower() == "true"
        self.DATA_DIR = os.getenv("DATA_DIR", self.DATA_DIR)


# Global configuration instance
config = MonitoringConfig()