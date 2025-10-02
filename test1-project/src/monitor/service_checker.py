"""
Service status checking functionality for Linux services.
"""
import subprocess
import socket
import logging
from typing import Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class ServiceChecker:
    """
    Handles checking the status of Linux services using systemctl.
    """
    
    def __init__(self):
        """Initialize the service checker."""
        self.hostname = self._get_hostname()
    
    def _get_hostname(self) -> str:
        """
        Get the hostname of the current machine.
        
        Returns:
            str: The hostname of the machine
        """
        try:
            return socket.gethostname()
        except Exception as e:
            logger.error(f"Failed to get hostname: {e}")
            return "unknown-host"
    
    def check_service_status(self, service_name: str) -> str:
        """
        Check if a Linux service is active using systemctl.
        
        Args:
            service_name: Name of the service to check
            
        Returns:
            str: "UP" if service is active, "DOWN" otherwise
            
        Raises:
            ValueError: If service_name is empty or None
        """
        if not service_name or not isinstance(service_name, str):
            raise ValueError("service_name must be a non-empty string")
        
        try:
            # Use systemctl to check if service is active
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # systemctl is-active returns 0 if service is active
            if result.returncode == 0 and result.stdout.strip() == 'active':
                logger.info(f"Service {service_name} is UP")
                return "UP"
            else:
                logger.warning(f"Service {service_name} is DOWN (status: {result.stdout.strip()})")
                return "DOWN"
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout checking service {service_name}")
            return "DOWN"
        except subprocess.CalledProcessError as e:
            logger.error(f"Error checking service {service_name}: {e}")
            return "DOWN"
        except FileNotFoundError:
            logger.error("systemctl command not found - not running on a systemd system")
            return "DOWN"
        except Exception as e:
            logger.error(f"Unexpected error checking service {service_name}: {e}")
            return "DOWN"
    
    def get_hostname(self) -> str:
        """
        Get the hostname of the current machine.
        
        Returns:
            str: The hostname of the machine
        """
        return self.hostname
    
    def get_current_timestamp(self) -> str:
        """
        Get the current timestamp in ISO format.
        
        Returns:
            str: Current timestamp in ISO 8601 format with Z suffix
        """
        return datetime.utcnow().isoformat() + 'Z'