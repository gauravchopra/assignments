#!/usr/bin/env python3
"""
Main monitoring script for rbcapp1 and its dependent services.

This script orchestrates service status checks, generates JSON status files,
and provides a command-line interface for monitoring operations.
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from .app_monitor import ApplicationMonitor
from .service_checker import ServiceChecker
from .models import ServiceStatus


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path (logs to console if None)
    """
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Set up logging configuration
    logging_config = {
        'level': getattr(logging, log_level.upper()),
        'format': log_format,
        'datefmt': '%Y-%m-%d %H:%M:%S'
    }
    
    if log_file:
        logging_config['filename'] = log_file
        logging_config['filemode'] = 'a'
    
    logging.basicConfig(**logging_config)
    
    # Set up logger for this module
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized at {log_level} level")


def monitor_services(services: List[str], output_dir: str, write_files: bool = True) -> dict:
    """
    Monitor specified services and optionally write status files.
    
    Args:
        services: List of service names to monitor
        output_dir: Directory to write JSON status files
        write_files: Whether to write JSON status files
        
    Returns:
        dict: Monitoring report with service statuses and file paths
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize monitoring components
        service_checker = ServiceChecker()
        monitor = ApplicationMonitor(service_checker)
        
        logger.info(f"Starting monitoring for services: {services}")
        
        # Check service statuses
        service_statuses = monitor.check_service_statuses(services)
        
        # Create ServiceStatus objects
        status_objects = monitor.create_service_status_objects(service_statuses)
        
        # Write status files if requested
        written_files = []
        if write_files and status_objects:
            logger.info(f"Writing status files to {output_dir}")
            written_files = monitor.write_multiple_status_files(status_objects, output_dir)
            logger.info(f"Successfully wrote {len(written_files)} status files")
        
        # Create monitoring report
        report = {
            "services_monitored": services,
            "service_statuses": service_statuses,
            "status_objects": status_objects,
            "written_files": written_files,
            "timestamp": service_checker.get_current_timestamp(),
            "hostname": service_checker.get_hostname()
        }
        
        logger.info("Monitoring completed successfully")
        return report
        
    except Exception as e:
        logger.error(f"Error during monitoring: {e}")
        raise


def monitor_rbcapp1(output_dir: str, write_files: bool = True) -> dict:
    """
    Monitor rbcapp1 application and its dependent services.
    
    Args:
        output_dir: Directory to write JSON status files
        write_files: Whether to write JSON status files
        
    Returns:
        dict: Complete monitoring report including app status
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize monitoring components
        service_checker = ServiceChecker()
        monitor = ApplicationMonitor(service_checker)
        
        logger.info("Starting rbcapp1 monitoring")
        
        # Get full monitoring report
        report = monitor.get_full_monitoring_report()
        
        # Write status files if requested
        written_files = []
        if write_files:
            logger.info(f"Writing status files to {output_dir}")
            
            # Write individual service status files
            if report["service_objects"]:
                service_files = monitor.write_multiple_status_files(
                    report["service_objects"], output_dir
                )
                written_files.extend(service_files)
            
            # Write rbcapp1 status file
            if report["app_object"]:
                app_file = monitor.write_status_file(report["app_object"], output_dir)
                written_files.append(app_file)
            
            logger.info(f"Successfully wrote {len(written_files)} status files")
        
        # Add file information to report
        report["written_files"] = written_files
        
        # Log summary
        logger.info(f"rbcapp1 status: {report['app_status']}")
        for service, status in report["service_statuses"].items():
            logger.info(f"  {service}: {status}")
        
        return report
        
    except Exception as e:
        logger.error(f"Error during rbcapp1 monitoring: {e}")
        raise


def print_monitoring_summary(report: dict) -> None:
    """
    Print a summary of the monitoring results to console.
    
    Args:
        report: Monitoring report dictionary
    """
    print("\n" + "="*50)
    print("MONITORING SUMMARY")
    print("="*50)
    
    # Print timestamp and hostname
    print(f"Timestamp: {report.get('timestamp', 'Unknown')}")
    print(f"Hostname: {report.get('hostname', 'Unknown')}")
    print()
    
    # Print service statuses
    if "service_statuses" in report:
        print("Service Statuses:")
        for service, status in report["service_statuses"].items():
            status_symbol = "✓" if status == "UP" else "✗"
            print(f"  {status_symbol} {service}: {status}")
        print()
    
    # Print app status if available
    if "app_status" in report:
        app_symbol = "✓" if report["app_status"] == "UP" else "✗"
        print(f"Application Status:")
        print(f"  {app_symbol} rbcapp1: {report['app_status']}")
        print()
    
    # Print written files
    if "written_files" in report and report["written_files"]:
        print("Status Files Written:")
        for file_path in report["written_files"]:
            print(f"  - {file_path}")
        print()
    
    # Print errors if any
    if "error" in report:
        print(f"Error: {report['error']}")
        print()
    
    print("="*50)


def main() -> int:
    """
    Main entry point for the monitoring script.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Monitor rbcapp1 and its dependent services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor rbcapp1 and all dependent services
  python -m src.monitor.main

  # Monitor specific services only
  python -m src.monitor.main --services httpd rabbitmq

  # Monitor without writing files
  python -m src.monitor.main --no-files

  # Monitor with custom output directory and logging
  python -m src.monitor.main --output-dir /tmp/monitoring --log-level DEBUG
        """
    )
    
    parser.add_argument(
        "--services",
        nargs="+",
        help="Specific services to monitor (default: all rbcapp1 dependencies)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="data",
        help="Directory to write JSON status files (default: data)"
    )
    
    parser.add_argument(
        "--no-files",
        action="store_true",
        help="Skip writing JSON status files"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        help="Log file path (default: log to console)"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output (except errors)"
    )
    
    parser.add_argument(
        "--rbcapp1-only",
        action="store_true",
        help="Monitor rbcapp1 application status only (includes dependent services)"
    )
    
    args = parser.parse_args()
    
    try:
        # Set up logging
        setup_logging(args.log_level, args.log_file)
        logger = logging.getLogger(__name__)
        
        # Determine what to monitor
        if args.services:
            # Monitor specific services
            logger.info(f"Monitoring specific services: {args.services}")
            report = monitor_services(
                services=args.services,
                output_dir=args.output_dir,
                write_files=not args.no_files
            )
        else:
            # Monitor rbcapp1 and all dependencies
            logger.info("Monitoring rbcapp1 application")
            report = monitor_rbcapp1(
                output_dir=args.output_dir,
                write_files=not args.no_files
            )
        
        # Print summary unless quiet mode
        if not args.quiet:
            print_monitoring_summary(report)
        
        # Determine exit code based on results
        if "app_status" in report:
            # rbcapp1 monitoring - exit with error if app is down
            exit_code = 0 if report["app_status"] == "UP" else 1
        else:
            # Service monitoring - exit with error if any service is down
            service_statuses = report.get("service_statuses", {})
            exit_code = 0 if all(status == "UP" for status in service_statuses.values()) else 1
        
        if exit_code != 0:
            logger.warning("Monitoring detected issues - exiting with error code")
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        if not args.quiet:
            print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())