"""
Application monitoring functionality for rbcapp1.
"""
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from .service_checker import ServiceChecker
from .models import ServiceStatus


logger = logging.getLogger(__name__)


class ApplicationMonitor:
    """
    Monitors the rbcapp1 application by checking its dependent services.
    """
    
    # Required services for rbcapp1 to be considered UP
    REQUIRED_SERVICES = ["httpd", "rabbitmq", "postgresql"]
    
    def __init__(self, service_checker: ServiceChecker = None):
        """
        Initialize the application monitor.
        
        Args:
            service_checker: ServiceChecker instance (optional, creates new if None)
        """
        self.service_checker = service_checker or ServiceChecker()
    
    def check_service_statuses(self, services: List[str] = None) -> Dict[str, str]:
        """
        Check the status of multiple services.
        
        Args:
            services: List of service names to check (defaults to REQUIRED_SERVICES)
            
        Returns:
            Dict mapping service names to their status ("UP" or "DOWN")
        """
        if services is None:
            services = self.REQUIRED_SERVICES.copy()
        
        if not services:
            raise ValueError("services list cannot be empty")
        
        statuses = {}
        for service in services:
            try:
                status = self.service_checker.check_service_status(service)
                statuses[service] = status
                logger.info(f"Service {service}: {status}")
            except Exception as e:
                logger.error(f"Error checking service {service}: {e}")
                statuses[service] = "DOWN"
        
        return statuses
    
    def determine_app_status(self, service_statuses: Dict[str, str]) -> str:
        """
        Determine rbcapp1 application status based on dependent service statuses.
        
        Args:
            service_statuses: Dictionary mapping service names to their status
            
        Returns:
            str: "UP" if all required services are UP, "DOWN" otherwise
        """
        if not service_statuses:
            logger.warning("No service statuses provided, considering app DOWN")
            return "DOWN"
        
        # Check if all required services are present and UP
        for service in self.REQUIRED_SERVICES:
            if service not in service_statuses:
                logger.warning(f"Required service {service} not found in status check")
                return "DOWN"
            
            if service_statuses[service] != "UP":
                logger.warning(f"Required service {service} is {service_statuses[service]}, app is DOWN")
                return "DOWN"
        
        logger.info("All required services are UP, app is UP")
        return "UP"
    
    def get_rbcapp1_status(self) -> str:
        """
        Get the current status of rbcapp1 application.
        
        Returns:
            str: "UP" if all dependent services are UP, "DOWN" otherwise
        """
        try:
            service_statuses = self.check_service_statuses()
            return self.determine_app_status(service_statuses)
        except Exception as e:
            logger.error(f"Error determining rbcapp1 status: {e}")
            return "DOWN"
    
    def create_service_status_objects(self, service_statuses: Dict[str, str]) -> List[ServiceStatus]:
        """
        Create ServiceStatus objects for each service.
        
        Args:
            service_statuses: Dictionary mapping service names to their status
            
        Returns:
            List of ServiceStatus objects
        """
        status_objects = []
        hostname = self.service_checker.get_hostname()
        timestamp = self.service_checker.get_current_timestamp()
        
        for service_name, status in service_statuses.items():
            try:
                service_status = ServiceStatus(
                    service_name=service_name,
                    service_status=status,
                    host_name=hostname,
                    timestamp=timestamp
                )
                status_objects.append(service_status)
            except Exception as e:
                logger.error(f"Error creating ServiceStatus for {service_name}: {e}")
        
        return status_objects
    
    def create_rbcapp1_status_object(self, app_status: str) -> ServiceStatus:
        """
        Create a ServiceStatus object for rbcapp1 application.
        
        Args:
            app_status: Status of rbcapp1 ("UP" or "DOWN")
            
        Returns:
            ServiceStatus object for rbcapp1
        """
        hostname = self.service_checker.get_hostname()
        timestamp = self.service_checker.get_current_timestamp()
        
        return ServiceStatus(
            service_name="rbcapp1",
            service_status=app_status,
            host_name=hostname,
            timestamp=timestamp
        )
    
    def get_full_monitoring_report(self) -> Dict[str, Any]:
        """
        Get a complete monitoring report including all services and rbcapp1 status.
        
        Returns:
            Dictionary containing service statuses, app status, and ServiceStatus objects
        """
        try:
            # Check all required services
            service_statuses = self.check_service_statuses()
            
            # Determine rbcapp1 status
            app_status = self.determine_app_status(service_statuses)
            
            # Create ServiceStatus objects
            service_objects = self.create_service_status_objects(service_statuses)
            app_object = self.create_rbcapp1_status_object(app_status)
            
            return {
                "service_statuses": service_statuses,
                "app_status": app_status,
                "service_objects": service_objects,
                "app_object": app_object,
                "timestamp": self.service_checker.get_current_timestamp()
            }
        except Exception as e:
            logger.error(f"Error generating monitoring report: {e}")
            # Return minimal error report
            return {
                "service_statuses": {},
                "app_status": "DOWN",
                "service_objects": [],
                "app_object": self.create_rbcapp1_status_object("DOWN"),
                "timestamp": self.service_checker.get_current_timestamp(),
                "error": str(e)
            }
    
    def generate_json_filename(self, service_name: str, timestamp: str = None) -> str:
        """
        Generate a timestamped filename for JSON status files.
        
        Args:
            service_name: Name of the service
            timestamp: Optional timestamp (uses current time if None)
            
        Returns:
            str: Filename in format {serviceName}-status-{@timestamp}.json
        """
        if not service_name or not isinstance(service_name, str):
            raise ValueError("service_name must be a non-empty string")
        
        if timestamp is None:
            timestamp = self.service_checker.get_current_timestamp()
        
        # Convert timestamp to filename-safe format
        # Replace colons and other problematic characters
        safe_timestamp = timestamp.replace(':', '-').replace('.', '-')
        
        return f"{service_name}-status-{safe_timestamp}.json"
    
    def write_status_file(self, service_status: ServiceStatus, output_dir: str = "data") -> str:
        """
        Write a ServiceStatus object to a timestamped JSON file.
        
        Args:
            service_status: ServiceStatus object to write
            output_dir: Directory to write the file to (default: "data")
            
        Returns:
            str: Path to the written file
            
        Raises:
            OSError: If file cannot be written
            ValueError: If service_status is invalid
        """
        if not isinstance(service_status, ServiceStatus):
            raise ValueError("service_status must be a ServiceStatus instance")
        
        try:
            # Ensure output directory exists
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename = self.generate_json_filename(
                service_status.service_name, 
                service_status.timestamp
            )
            
            # Full file path
            file_path = output_path / filename
            
            # Write JSON data to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(service_status.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully wrote status file: {file_path}")
            return str(file_path)
            
        except OSError as e:
            logger.error(f"Failed to write status file for {service_status.service_name}: {e}")
            raise OSError(f"Cannot write status file: {e}")
        except Exception as e:
            logger.error(f"Unexpected error writing status file for {service_status.service_name}: {e}")
            raise
    
    def write_multiple_status_files(self, service_statuses: List[ServiceStatus], output_dir: str = "data") -> List[str]:
        """
        Write multiple ServiceStatus objects to timestamped JSON files.
        
        Args:
            service_statuses: List of ServiceStatus objects to write
            output_dir: Directory to write the files to (default: "data")
            
        Returns:
            List[str]: Paths to the written files
        """
        if not isinstance(service_statuses, list):
            raise ValueError("service_statuses must be a list")
        
        written_files = []
        errors = []
        
        for service_status in service_statuses:
            try:
                file_path = self.write_status_file(service_status, output_dir)
                written_files.append(file_path)
            except Exception as e:
                error_msg = f"Failed to write file for {service_status.service_name}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        if errors:
            logger.warning(f"Encountered {len(errors)} errors while writing status files")
        
        return written_files