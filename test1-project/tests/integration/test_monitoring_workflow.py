"""
Integration tests for the complete monitoring workflow.
Tests end-to-end functionality including monitoring script, JSON file generation,
API endpoints, and Elasticsearch integration.
"""
import json
import tempfile
import pytest
import os
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch, call, MagicMock
from src.monitor.main import (
    monitor_services, 
    monitor_rbcapp1, 
    print_monitoring_summary,
    setup_logging,
    main
)
from src.monitor.models import ServiceStatus
from src.api.app import create_app
from src.api.elasticsearch_client import ElasticsearchClient, ElasticsearchConnectionError


class TestMonitoringWorkflow:
    """Integration tests for the monitoring workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.monitor.main.ServiceChecker')
    @patch('src.monitor.main.ApplicationMonitor')
    def test_monitor_services_success(self, mock_monitor_class, mock_checker_class):
        """Test successful service monitoring workflow."""
        # Mock service checker
        mock_checker = Mock()
        mock_checker.get_current_timestamp.return_value = "2024-01-15T10:30:00Z"
        mock_checker.get_hostname.return_value = "test-host"
        mock_checker_class.return_value = mock_checker
        
        # Mock application monitor
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        # Mock service status check
        mock_monitor.check_service_statuses.return_value = {
            "httpd": "UP",
            "rabbitmq": "DOWN"
        }
        
        # Mock ServiceStatus objects
        status_objects = [
            ServiceStatus("httpd", "UP", "test-host", "2024-01-15T10:30:00Z"),
            ServiceStatus("rabbitmq", "DOWN", "test-host", "2024-01-15T10:30:00Z")
        ]
        mock_monitor.create_service_status_objects.return_value = status_objects
        
        # Mock file writing
        mock_monitor.write_multiple_status_files.return_value = [
            "data/httpd-status-2024-01-15T10-30-00Z.json",
            "data/rabbitmq-status-2024-01-15T10-30-00Z.json"
        ]
        
        # Run monitoring
        services = ["httpd", "rabbitmq"]
        report = monitor_services(services, self.temp_dir, write_files=True)
        
        # Verify report structure
        assert report["services_monitored"] == services
        assert report["service_statuses"] == {"httpd": "UP", "rabbitmq": "DOWN"}
        assert report["status_objects"] == status_objects
        assert len(report["written_files"]) == 2
        assert report["timestamp"] == "2024-01-15T10:30:00Z"
        assert report["hostname"] == "test-host"
        
        # Verify method calls
        mock_monitor.check_service_statuses.assert_called_once_with(services)
        mock_monitor.create_service_status_objects.assert_called_once()
        mock_monitor.write_multiple_status_files.assert_called_once_with(
            status_objects, self.temp_dir
        )
    
    @patch('src.monitor.main.ServiceChecker')
    @patch('src.monitor.main.ApplicationMonitor')
    def test_monitor_services_no_files(self, mock_monitor_class, mock_checker_class):
        """Test service monitoring without writing files."""
        # Mock service checker
        mock_checker = Mock()
        mock_checker.get_current_timestamp.return_value = "2024-01-15T10:30:00Z"
        mock_checker.get_hostname.return_value = "test-host"
        mock_checker_class.return_value = mock_checker
        
        # Mock application monitor
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        # Mock service status check
        mock_monitor.check_service_statuses.return_value = {"httpd": "UP"}
        
        # Mock ServiceStatus objects
        status_objects = [ServiceStatus("httpd", "UP", "test-host", "2024-01-15T10:30:00Z")]
        mock_monitor.create_service_status_objects.return_value = status_objects
        
        # Run monitoring without writing files
        report = monitor_services(["httpd"], self.temp_dir, write_files=False)
        
        # Verify no files were written
        assert report["written_files"] == []
        
        # Verify file writing was not called
        mock_monitor.write_multiple_status_files.assert_not_called()
    
    @patch('src.monitor.main.ServiceChecker')
    @patch('src.monitor.main.ApplicationMonitor')
    def test_monitor_rbcapp1_success(self, mock_monitor_class, mock_checker_class):
        """Test successful rbcapp1 monitoring workflow."""
        # Mock service checker
        mock_checker = Mock()
        mock_checker_class.return_value = mock_checker
        
        # Mock application monitor
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        # Mock full monitoring report
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
        
        # Mock file writing
        mock_monitor.write_multiple_status_files.return_value = [
            "data/httpd-status-2024-01-15T10-30-00Z.json",
            "data/rabbitmq-status-2024-01-15T10-30-00Z.json",
            "data/postgresql-status-2024-01-15T10-30-00Z.json"
        ]
        mock_monitor.write_status_file.return_value = "data/rbcapp1-status-2024-01-15T10-30-00Z.json"
        
        # Run rbcapp1 monitoring
        report = monitor_rbcapp1(self.temp_dir, write_files=True)
        
        # Verify report structure
        assert report["service_statuses"] == {"httpd": "UP", "rabbitmq": "UP", "postgresql": "UP"}
        assert report["app_status"] == "UP"
        assert report["service_objects"] == service_objects
        assert report["app_object"] == app_object
        assert len(report["written_files"]) == 4  # 3 services + 1 app
        
        # Verify method calls
        mock_monitor.get_full_monitoring_report.assert_called_once()
        mock_monitor.write_multiple_status_files.assert_called_once_with(
            service_objects, self.temp_dir
        )
        mock_monitor.write_status_file.assert_called_once_with(app_object, self.temp_dir)
    
    @patch('src.monitor.main.ServiceChecker')
    @patch('src.monitor.main.ApplicationMonitor')
    def test_monitor_rbcapp1_with_failure(self, mock_monitor_class, mock_checker_class):
        """Test rbcapp1 monitoring when services are down."""
        # Mock service checker
        mock_checker = Mock()
        mock_checker_class.return_value = mock_checker
        
        # Mock application monitor
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        # Mock full monitoring report with failure
        service_objects = [
            ServiceStatus("httpd", "UP", "test-host", "2024-01-15T10:30:00Z"),
            ServiceStatus("rabbitmq", "DOWN", "test-host", "2024-01-15T10:30:00Z"),
            ServiceStatus("postgresql", "UP", "test-host", "2024-01-15T10:30:00Z")
        ]
        app_object = ServiceStatus("rbcapp1", "DOWN", "test-host", "2024-01-15T10:30:00Z")
        
        mock_report = {
            "service_statuses": {"httpd": "UP", "rabbitmq": "DOWN", "postgresql": "UP"},
            "app_status": "DOWN",
            "service_objects": service_objects,
            "app_object": app_object,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        mock_monitor.get_full_monitoring_report.return_value = mock_report
        
        # Mock file writing
        mock_monitor.write_multiple_status_files.return_value = [
            "data/httpd-status-2024-01-15T10-30-00Z.json",
            "data/rabbitmq-status-2024-01-15T10-30-00Z.json",
            "data/postgresql-status-2024-01-15T10-30-00Z.json"
        ]
        mock_monitor.write_status_file.return_value = "data/rbcapp1-status-2024-01-15T10-30-00Z.json"
        
        # Run rbcapp1 monitoring
        report = monitor_rbcapp1(self.temp_dir, write_files=True)
        
        # Verify app is down due to rabbitmq failure
        assert report["app_status"] == "DOWN"
        assert report["service_statuses"]["rabbitmq"] == "DOWN"
    
    @patch('builtins.print')
    def test_print_monitoring_summary(self, mock_print):
        """Test printing monitoring summary."""
        report = {
            "timestamp": "2024-01-15T10:30:00Z",
            "hostname": "test-host",
            "service_statuses": {
                "httpd": "UP",
                "rabbitmq": "DOWN",
                "postgresql": "UP"
            },
            "app_status": "DOWN",
            "written_files": [
                "data/httpd-status-2024-01-15T10-30-00Z.json",
                "data/rabbitmq-status-2024-01-15T10-30-00Z.json"
            ]
        }
        
        print_monitoring_summary(report)
        
        # Verify print was called with expected content
        assert mock_print.call_count > 0
        
        # Check that key information was printed
        printed_text = " ".join([str(call.args[0]) for call in mock_print.call_args_list if call.args])
        assert "test-host" in printed_text
        assert "2024-01-15T10:30:00Z" in printed_text
        assert "httpd: UP" in printed_text
        assert "rabbitmq: DOWN" in printed_text
        assert "rbcapp1: DOWN" in printed_text
    
    @patch('src.monitor.main.logging.basicConfig')
    def test_setup_logging_console(self, mock_basic_config):
        """Test logging setup for console output."""
        setup_logging("DEBUG", None)
        
        mock_basic_config.assert_called_once()
        config_args = mock_basic_config.call_args[1]
        
        assert config_args['level'] == 10  # DEBUG level
        assert 'filename' not in config_args
    
    @patch('src.monitor.main.logging.basicConfig')
    def test_setup_logging_file(self, mock_basic_config):
        """Test logging setup for file output."""
        log_file = str(self.temp_path / "test.log")
        setup_logging("INFO", log_file)
        
        mock_basic_config.assert_called_once()
        config_args = mock_basic_config.call_args[1]
        
        assert config_args['level'] == 20  # INFO level
        assert config_args['filename'] == log_file
        assert config_args['filemode'] == 'a'
    
    @patch('src.monitor.main.monitor_rbcapp1')
    @patch('src.monitor.main.setup_logging')
    @patch('sys.argv', ['main.py'])
    def test_main_default_behavior(self, mock_setup_logging, mock_monitor_rbcapp1):
        """Test main function with default arguments."""
        # Mock successful monitoring
        mock_monitor_rbcapp1.return_value = {
            "app_status": "UP",
            "service_statuses": {"httpd": "UP", "rabbitmq": "UP", "postgresql": "UP"},
            "written_files": []
        }
        
        with patch('src.monitor.main.print_monitoring_summary') as mock_print_summary:
            exit_code = main()
        
        # Verify successful execution
        assert exit_code == 0
        
        # Verify setup and monitoring calls
        mock_setup_logging.assert_called_once_with("INFO", None)
        mock_monitor_rbcapp1.assert_called_once_with(
            output_dir="data",
            write_files=True
        )
        mock_print_summary.assert_called_once()
    
    @patch('src.monitor.main.monitor_services')
    @patch('src.monitor.main.setup_logging')
    @patch('sys.argv', ['main.py', '--services', 'httpd', 'nginx'])
    def test_main_specific_services(self, mock_setup_logging, mock_monitor_services):
        """Test main function with specific services."""
        # Mock successful monitoring
        mock_monitor_services.return_value = {
            "service_statuses": {"httpd": "UP", "nginx": "UP"},
            "written_files": []
        }
        
        with patch('src.monitor.main.print_monitoring_summary') as mock_print_summary:
            exit_code = main()
        
        # Verify successful execution
        assert exit_code == 0
        
        # Verify monitoring call with specific services
        mock_monitor_services.assert_called_once_with(
            services=['httpd', 'nginx'],
            output_dir="data",
            write_files=True
        )
    
    @patch('src.monitor.main.monitor_rbcapp1')
    @patch('src.monitor.main.setup_logging')
    @patch('sys.argv', ['main.py', '--no-files', '--quiet'])
    def test_main_no_files_quiet(self, mock_setup_logging, mock_monitor_rbcapp1):
        """Test main function with no files and quiet mode."""
        # Mock successful monitoring
        mock_monitor_rbcapp1.return_value = {
            "app_status": "UP",
            "service_statuses": {"httpd": "UP", "rabbitmq": "UP", "postgresql": "UP"},
            "written_files": []
        }
        
        with patch('src.monitor.main.print_monitoring_summary') as mock_print_summary:
            exit_code = main()
        
        # Verify successful execution
        assert exit_code == 0
        
        # Verify monitoring call without file writing
        mock_monitor_rbcapp1.assert_called_once_with(
            output_dir="data",
            write_files=False
        )
        
        # Verify summary was not printed (quiet mode)
        mock_print_summary.assert_not_called()
    
    @patch('src.monitor.main.monitor_rbcapp1')
    @patch('src.monitor.main.setup_logging')
    @patch('sys.argv', ['main.py'])
    def test_main_app_down_exit_code(self, mock_setup_logging, mock_monitor_rbcapp1):
        """Test main function returns error code when app is down."""
        # Mock monitoring with app down
        mock_monitor_rbcapp1.return_value = {
            "app_status": "DOWN",
            "service_statuses": {"httpd": "UP", "rabbitmq": "DOWN", "postgresql": "UP"},
            "written_files": []
        }
        
        with patch('src.monitor.main.print_monitoring_summary'):
            exit_code = main()
        
        # Verify error exit code
        assert exit_code == 1
    
    @patch('src.monitor.main.monitor_rbcapp1')
    @patch('src.monitor.main.setup_logging')
    @patch('sys.argv', ['main.py'])
    def test_main_exception_handling(self, mock_setup_logging, mock_monitor_rbcapp1):
        """Test main function handles exceptions properly."""
        # Mock monitoring to raise exception
        mock_monitor_rbcapp1.side_effect = Exception("Monitoring failed")
        
        with patch('builtins.print') as mock_print:
            exit_code = main()
        
        # Verify error exit code
        assert exit_code == 1
        
        # Verify error was printed
        mock_print.assert_called_with("Error: Monitoring failed")


class TestEndToEndWorkflow:
    """Integration tests for complete end-to-end monitoring workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.monitor.main.ServiceChecker')
    @patch('src.monitor.main.ApplicationMonitor')
    def test_monitoring_script_to_json_files(self, mock_monitor_class, mock_checker_class):
        """Test complete workflow from monitoring script to JSON file generation."""
        # Mock service checker
        mock_checker = Mock()
        mock_checker.get_current_timestamp.return_value = "2024-01-15T10:30:00Z"
        mock_checker.get_hostname.return_value = "test-host"
        mock_checker_class.return_value = mock_checker
        
        # Mock application monitor
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        # Create test service status objects
        service_objects = [
            ServiceStatus("httpd", "UP", "test-host", "2024-01-15T10:30:00Z"),
            ServiceStatus("rabbitmq", "DOWN", "test-host", "2024-01-15T10:30:00Z"),
            ServiceStatus("postgresql", "UP", "test-host", "2024-01-15T10:30:00Z")
        ]
        app_object = ServiceStatus("rbcapp1", "DOWN", "test-host", "2024-01-15T10:30:00Z")
        
        # Mock full monitoring report
        mock_report = {
            "service_statuses": {"httpd": "UP", "rabbitmq": "DOWN", "postgresql": "UP"},
            "app_status": "DOWN",
            "service_objects": service_objects,
            "app_object": app_object,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        mock_monitor.get_full_monitoring_report.return_value = mock_report
        
        # Create actual JSON files for testing
        json_files = []
        def mock_write_multiple_files(objects, output_dir):
            files = []
            for obj in objects:
                filename = f"{obj.service_name}-status-{obj.timestamp.replace(':', '-')}.json"
                filepath = Path(output_dir) / filename
                filepath.parent.mkdir(parents=True, exist_ok=True)
                with open(filepath, 'w') as f:
                    json.dump(obj.to_dict(), f, indent=2)
                files.append(str(filepath))
                json_files.append(str(filepath))
            return files
        
        def mock_write_single_file(obj, output_dir):
            filename = f"{obj.service_name}-status-{obj.timestamp.replace(':', '-')}.json"
            filepath = Path(output_dir) / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(obj.to_dict(), f, indent=2)
            json_files.append(str(filepath))
            return str(filepath)
        
        mock_monitor.write_multiple_status_files.side_effect = mock_write_multiple_files
        mock_monitor.write_status_file.side_effect = mock_write_single_file
        
        # Run monitoring
        report = monitor_rbcapp1(self.temp_dir, write_files=True)
        
        # Verify JSON files were created
        assert len(json_files) == 4  # 3 services + 1 app
        
        # Verify JSON file contents
        for json_file in json_files:
            assert os.path.exists(json_file)
            with open(json_file, 'r') as f:
                data = json.load(f)
                assert 'service_name' in data
                assert 'service_status' in data
                assert 'host_name' in data
                assert 'timestamp' in data
                assert data['host_name'] == 'test-host'
                assert data['timestamp'] == '2024-01-15T10:30:00Z'
        
        # Verify report structure
        assert report["app_status"] == "DOWN"
        assert report["service_statuses"]["rabbitmq"] == "DOWN"
        assert len(report["written_files"]) == 4
    
    def test_api_endpoints_with_real_json_files(self):
        """Test API endpoints with actual JSON file inputs."""
        # Create test JSON files
        test_data = [
            {
                "service_name": "httpd",
                "service_status": "UP",
                "host_name": "test-host",
                "timestamp": "2024-01-15T10:30:00Z"
            },
            {
                "service_name": "rabbitmq",
                "service_status": "DOWN",
                "host_name": "test-host",
                "timestamp": "2024-01-15T10:30:00Z"
            },
            {
                "service_name": "rbcapp1",
                "service_status": "DOWN",
                "host_name": "test-host",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        ]
        
        json_files = []
        for data in test_data:
            filename = f"{data['service_name']}-status-{data['timestamp'].replace(':', '-')}.json"
            filepath = self.temp_path / filename
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            json_files.append(str(filepath))
        
        # Mock Elasticsearch client for API testing
        with patch('src.api.app.ElasticsearchClient') as mock_es_class:
            mock_es_client = Mock()
            mock_es_class.return_value = mock_es_client
            
            # Mock successful indexing
            mock_es_client.index_document.return_value = True
            
            # Mock service status retrieval
            mock_es_client.get_all_service_statuses.return_value = {
                'httpd': 'UP',
                'rabbitmq': 'DOWN',
                'rbcapp1': 'DOWN'
            }
            
            mock_es_client.get_service_status.return_value = {
                'service_name': 'httpd',
                'service_status': 'UP',
                'host_name': 'test-host',
                'timestamp': '2024-01-15T10:30:00Z'
            }
            
            # Create Flask app
            app = create_app(config={'TESTING': True})
            
            with app.test_client() as client:
                # Test POST /add endpoint with JSON file data
                for data in test_data:
                    response = client.post('/add',
                                         data=json.dumps(data),
                                         content_type='application/json')
                    assert response.status_code == 201
                    response_data = json.loads(response.data)
                    assert response_data['service_name'] == data['service_name']
                
                # Test GET /healthcheck endpoint
                response = client.get('/healthcheck')
                assert response.status_code == 200
                response_data = json.loads(response.data)
                assert 'services' in response_data
                assert response_data['services']['httpd'] == 'UP'
                assert response_data['services']['rabbitmq'] == 'DOWN'
                
                # Test GET /healthcheck/{serviceName} endpoint
                response = client.get('/healthcheck/httpd')
                assert response.status_code == 200
                response_data = json.loads(response.data)
                assert response_data['service_name'] == 'httpd'
                assert response_data['service_status'] == 'UP'
        
        # Verify JSON files still exist and are readable
        for json_file in json_files:
            assert os.path.exists(json_file)
            with open(json_file, 'r') as f:
                data = json.load(f)
                assert data in test_data
    
    def test_elasticsearch_integration_with_test_data(self):
        """Test Elasticsearch integration with test monitoring data."""
        # Mock Elasticsearch client with realistic behavior
        with patch('src.api.elasticsearch_client.Elasticsearch') as mock_es:
            mock_client = Mock()
            mock_es.return_value = mock_client
            
            # Mock index existence check
            mock_client.indices.exists.return_value = True
            
            # Mock successful document indexing
            mock_client.index.return_value = {"_id": "test-id", "result": "created"}
            
            # Mock search responses for different scenarios
            def mock_search(*args, **kwargs):
                body = kwargs.get('body', {})
                
                # Check if it's an aggregation query (for all services)
                if 'aggs' in body:
                    return {
                        "aggregations": {
                            "services": {
                                "buckets": [
                                    {
                                        "key": "httpd",
                                        "latest": {
                                            "hits": {
                                                "hits": [
                                                    {
                                                        "_source": {
                                                            "service_name": "httpd",
                                                            "service_status": "UP",
                                                            "host_name": "test-host",
                                                            "timestamp": "2024-01-15T10:30:00Z"
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    },
                                    {
                                        "key": "rabbitmq",
                                        "latest": {
                                            "hits": {
                                                "hits": [
                                                    {
                                                        "_source": {
                                                            "service_name": "rabbitmq",
                                                            "service_status": "DOWN",
                                                            "host_name": "test-host",
                                                            "timestamp": "2024-01-15T10:30:00Z"
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    }
                else:
                    # Single service query
                    query = body.get('query', {})
                    if 'term' in query and 'service_name' in query['term']:
                        service_name = query['term']['service_name']
                        if service_name == 'httpd':
                            return {
                                "hits": {
                                    "hits": [
                                        {
                                            "_source": {
                                                "service_name": "httpd",
                                                "service_status": "UP",
                                                "host_name": "test-host",
                                                "timestamp": "2024-01-15T10:30:00Z"
                                            }
                                        }
                                    ]
                                }
                            }
                    return {"hits": {"hits": []}}
            
            mock_client.search.side_effect = mock_search
            
            # Test ElasticsearchClient functionality
            es_client = ElasticsearchClient()
            
            # Test document indexing
            test_document = {
                "service_name": "httpd",
                "service_status": "UP",
                "host_name": "test-host"
            }
            
            result = es_client.index_document(test_document)
            assert result is True
            
            # Verify index was called with correct parameters
            mock_client.index.assert_called()
            call_args = mock_client.index.call_args
            assert call_args[1]['index'] == 'service-monitoring'
            assert 'timestamp' in call_args[1]['body']
            
            # Test querying all service statuses
            all_statuses = es_client.get_all_service_statuses()
            assert isinstance(all_statuses, dict)
            assert all_statuses['httpd'] == 'UP'
            assert all_statuses['rabbitmq'] == 'DOWN'
            
            # Test querying specific service status
            httpd_status = es_client.get_service_status('httpd')
            assert httpd_status is not None
            assert httpd_status['service_name'] == 'httpd'
            assert httpd_status['service_status'] == 'UP'
            
            # Test querying non-existent service
            nonexistent_status = es_client.get_service_status('nonexistent')
            assert nonexistent_status is None
    
    @patch('src.monitor.main.ServiceChecker')
    @patch('src.monitor.main.ApplicationMonitor')
    def test_complete_monitoring_to_api_workflow(self, mock_monitor_class, mock_checker_class):
        """Test complete workflow from monitoring script through API to Elasticsearch."""
        # Setup monitoring mocks
        mock_checker = Mock()
        mock_checker.get_current_timestamp.return_value = "2024-01-15T10:30:00Z"
        mock_checker.get_hostname.return_value = "integration-test-host"
        mock_checker_class.return_value = mock_checker
        
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        # Create realistic service status data
        service_objects = [
            ServiceStatus("httpd", "UP", "integration-test-host", "2024-01-15T10:30:00Z"),
            ServiceStatus("rabbitmq", "UP", "integration-test-host", "2024-01-15T10:30:00Z"),
            ServiceStatus("postgresql", "UP", "integration-test-host", "2024-01-15T10:30:00Z")
        ]
        app_object = ServiceStatus("rbcapp1", "UP", "integration-test-host", "2024-01-15T10:30:00Z")
        
        mock_report = {
            "service_statuses": {"httpd": "UP", "rabbitmq": "UP", "postgresql": "UP"},
            "app_status": "UP",
            "service_objects": service_objects,
            "app_object": app_object,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        mock_monitor.get_full_monitoring_report.return_value = mock_report
        
        # Create JSON files that would be generated by monitoring
        json_files = []
        def mock_write_files(objects, output_dir):
            files = []
            for obj in objects:
                filename = f"{obj.service_name}-status-{obj.timestamp.replace(':', '-')}.json"
                filepath = Path(output_dir) / filename
                filepath.parent.mkdir(parents=True, exist_ok=True)
                with open(filepath, 'w') as f:
                    json.dump(obj.to_dict(), f, indent=2)
                files.append(str(filepath))
                json_files.append(str(filepath))
            return files
        
        def mock_write_single_file(obj, output_dir):
            filename = f"{obj.service_name}-status-{obj.timestamp.replace(':', '-')}.json"
            filepath = Path(output_dir) / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(obj.to_dict(), f, indent=2)
            json_files.append(str(filepath))
            return str(filepath)
        
        mock_monitor.write_multiple_status_files.side_effect = mock_write_files
        mock_monitor.write_status_file.side_effect = mock_write_single_file
        
        # Step 1: Run monitoring script
        monitoring_report = monitor_rbcapp1(self.temp_dir, write_files=True)
        
        # Verify monitoring completed successfully
        assert monitoring_report["app_status"] == "UP"
        assert len(monitoring_report["written_files"]) == 4
        
        # Step 2: Simulate reading JSON files and sending to API
        with patch('src.api.app.ElasticsearchClient') as mock_es_class:
            mock_es_client = Mock()
            mock_es_class.return_value = mock_es_client
            mock_es_client.index_document.return_value = True
            
            # Create Flask app
            app = create_app(config={'TESTING': True})
            
            with app.test_client() as client:
                # Send each JSON file's data to the API
                indexed_data = []
                for json_file in json_files:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    response = client.post('/add',
                                         data=json.dumps(data),
                                         content_type='application/json')
                    
                    assert response.status_code == 201
                    response_data = json.loads(response.data)
                    assert response_data['service_name'] == data['service_name']
                    indexed_data.append(data)
                
                # Verify all data was indexed
                assert len(indexed_data) == 4
                assert mock_es_client.index_document.call_count == 4
                
                # Verify the indexed data includes all services
                indexed_services = [data['service_name'] for data in indexed_data]
                assert 'httpd' in indexed_services
                assert 'rabbitmq' in indexed_services
                assert 'postgresql' in indexed_services
                assert 'rbcapp1' in indexed_services
        
        # Step 3: Verify JSON files are properly formatted
        for json_file in json_files:
            with open(json_file, 'r') as f:
                data = json.load(f)
                
            # Verify required fields
            required_fields = ['service_name', 'service_status', 'host_name', 'timestamp']
            for field in required_fields:
                assert field in data, f"Missing field {field} in {json_file}"
            
            # Verify data types and values
            assert isinstance(data['service_name'], str)
            assert data['service_status'] in ['UP', 'DOWN']
            assert isinstance(data['host_name'], str)
            assert data['host_name'] == 'integration-test-host'
            assert data['timestamp'] == '2024-01-15T10:30:00Z'
    
    def test_error_handling_in_workflow(self):
        """Test error handling throughout the complete workflow."""
        # Test monitoring script error handling
        with patch('src.monitor.main.ServiceChecker') as mock_checker_class:
            mock_checker_class.side_effect = Exception("Service checker initialization failed")
            
            with pytest.raises(Exception, match="Service checker initialization failed"):
                monitor_rbcapp1(self.temp_dir, write_files=True)
        
        # Test API error handling with invalid JSON files
        with patch('src.api.app.ElasticsearchClient') as mock_es_class:
            mock_es_client = Mock()
            mock_es_class.return_value = mock_es_client
            
            app = create_app(config={'TESTING': True})
            
            with app.test_client() as client:
                # Test with invalid JSON payload
                response = client.post('/add',
                                     data='{"invalid": "json", "missing": "required_fields"}',
                                     content_type='application/json')
                
                assert response.status_code == 400
                response_data = json.loads(response.data)
                assert response_data['error'] == 'bad_request'
                assert 'Missing required fields' in response_data['message']
        
        # Test Elasticsearch connection error handling
        with patch('src.api.app.ElasticsearchClient') as mock_es_class:
            mock_es_class.side_effect = ElasticsearchConnectionError("Connection failed")
            
            app = create_app(config={'TESTING': True})
            
            with app.test_client() as client:
                response = client.get('/healthcheck')
                
                assert response.status_code == 503
                response_data = json.loads(response.data)
                assert response_data['error'] == 'service_unavailable'
                assert 'Elasticsearch service is not available' in response_data['message']