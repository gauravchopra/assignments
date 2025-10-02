"""
Unit tests for Flask application factory and configuration.
"""
import pytest
import json
from unittest.mock import Mock, patch
from src.api import create_app
from src.api.config import DevelopmentConfig, TestingConfig, ProductionConfig
from src.api.elasticsearch_client import ElasticsearchConnectionError


class TestFlaskAppFactory:
    """Test cases for Flask application factory."""
    
    def test_create_app_default_config(self):
        """Test creating app with default configuration."""
        app = create_app()
        
        assert app is not None
        assert app.config['JSON_SORT_KEYS'] is False
        assert app.config['JSONIFY_PRETTYPRINT_REGULAR'] is True
    
    def test_create_app_with_custom_config(self):
        """Test creating app with custom configuration."""
        custom_config = {
            'TESTING': True,
            'DEBUG': False,
            'CUSTOM_SETTING': 'test_value'
        }
        
        app = create_app(config=custom_config)
        
        assert app.config['TESTING'] is True
        assert app.config['DEBUG'] is False
        assert app.config['CUSTOM_SETTING'] == 'test_value'
    
    def test_create_app_testing_mode(self):
        """Test creating app in testing mode."""
        app = create_app(config={'TESTING': True})
        
        assert app.testing is True
        assert app.config['TESTING'] is True


class TestErrorHandlers:
    """Test cases for error handlers."""
    
    @pytest.fixture
    def app(self):
        """Create test app fixture."""
        return create_app(config={'TESTING': True})
    
    @pytest.fixture
    def client(self, app):
        """Create test client fixture."""
        return app.test_client()
    
    def test_404_error_handler(self, client):
        """Test 404 error handler."""
        response = client.get('/nonexistent-endpoint')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'not_found'
        assert data['message'] == 'Resource not found'
        assert 'timestamp' in data
    
    def test_error_response_format(self, client):
        """Test that error responses follow the expected format."""
        response = client.get('/nonexistent-endpoint')
        
        assert response.status_code == 404
        assert response.content_type == 'application/json'
        
        data = json.loads(response.data)
        required_fields = ['error', 'message', 'timestamp']
        
        for field in required_fields:
            assert field in data
        
        # Verify timestamp format (ISO 8601 with Z suffix)
        assert data['timestamp'].endswith('Z')
        assert 'T' in data['timestamp']


class TestAppConfiguration:
    """Test cases for application configuration."""
    
    def test_development_config(self):
        """Test development configuration."""
        config = DevelopmentConfig()
        
        assert config.DEBUG is True
        assert config.TESTING is False
        assert config.ELASTICSEARCH_URL == 'http://localhost:9200'
        assert config.ELASTICSEARCH_INDEX == 'service-monitoring'
    
    def test_testing_config(self):
        """Test testing configuration."""
        config = TestingConfig()
        
        assert config.DEBUG is False
        assert config.TESTING is True
        assert config.ELASTICSEARCH_INDEX == 'test-service-monitoring'
    
    def test_production_config_without_secret_key(self):
        """Test production config raises error without SECRET_KEY."""
        import os
        
        # Ensure SECRET_KEY is not set
        if 'SECRET_KEY' in os.environ:
            del os.environ['SECRET_KEY']
        
        with pytest.raises(ValueError, match="SECRET_KEY environment variable must be set"):
            ProductionConfig()
    
    def test_app_with_development_config(self):
        """Test app creation with development config."""
        from src.api.config import config
        
        app = create_app(config=config['development'].__dict__)
        
        assert app.config['DEBUG'] is True
        assert app.config['TESTING'] is False


class TestAppInitialization:
    """Test cases for app initialization."""
    
    def test_app_has_error_handlers(self):
        """Test that app has registered error handlers."""
        app = create_app()
        
        # Check that error handlers are registered
        assert 400 in app.error_handler_spec[None]
        assert 404 in app.error_handler_spec[None]
        assert 500 in app.error_handler_spec[None]
        assert 503 in app.error_handler_spec[None]
    
    def test_app_json_configuration(self):
        """Test JSON-related configuration."""
        app = create_app()
        
        assert app.config['JSON_SORT_KEYS'] is False
        assert app.config['JSONIFY_PRETTYPRINT_REGULAR'] is True
    
    def test_app_instance_type(self):
        """Test that create_app returns Flask instance."""
        from flask import Flask
        
        app = create_app()
        assert isinstance(app, Flask)
        assert app.name == 'src.api.app'


class TestAddEndpoint:
    """Test cases for POST /add endpoint."""
    
    @pytest.fixture
    def app(self):
        """Create test app fixture with mocked Elasticsearch."""
        with patch('src.api.app.ElasticsearchClient') as mock_es_class:
            mock_es_client = Mock()
            mock_es_class.return_value = mock_es_client
            
            app = create_app(config={'TESTING': True})
            app.es_client = mock_es_client
            return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client fixture."""
        return app.test_client()
    
    @pytest.fixture
    def valid_payload(self):
        """Valid JSON payload for testing."""
        return {
            "service_name": "httpd",
            "service_status": "UP",
            "host_name": "test-host"
        }
    
    def test_add_endpoint_success(self, client, app, valid_payload):
        """Test successful POST to /add endpoint."""
        app.es_client.index_document.return_value = True
        
        response = client.post('/add', 
                             data=json.dumps(valid_payload),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'Status data successfully stored'
        assert data['service_name'] == 'httpd'
        assert 'timestamp' in data
        
        # Verify Elasticsearch client was called
        app.es_client.index_document.assert_called_once_with(valid_payload)
    
    def test_add_endpoint_missing_content_type(self, client, valid_payload):
        """Test POST /add with missing content type."""
        response = client.post('/add', data=json.dumps(valid_payload))
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'bad_request'
        assert data['message'] == 'Request must be JSON'
    
    def test_add_endpoint_empty_payload(self, client):
        """Test POST /add with empty JSON payload."""
        response = client.post('/add',
                             data='{}',
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'bad_request'
        assert data['message'] == 'Empty JSON payload'
    
    def test_add_endpoint_missing_required_fields(self, client):
        """Test POST /add with missing required fields."""
        incomplete_payload = {
            "service_name": "httpd"
            # Missing service_status and host_name
        }
        
        response = client.post('/add',
                             data=json.dumps(incomplete_payload),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'bad_request'
        assert 'Missing required fields' in data['message']
        assert 'service_status' in data['message']
        assert 'host_name' in data['message']
    
    def test_add_endpoint_invalid_service_status(self, client, valid_payload):
        """Test POST /add with invalid service_status value."""
        valid_payload['service_status'] = 'INVALID'
        
        response = client.post('/add',
                             data=json.dumps(valid_payload),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'bad_request'
        assert 'service_status must be one of: UP, DOWN' in data['message']
    
    def test_add_endpoint_elasticsearch_unavailable(self, client, valid_payload):
        """Test POST /add when Elasticsearch is unavailable."""
        with patch('src.api.app.ElasticsearchClient') as mock_es_class:
            mock_es_class.side_effect = ElasticsearchConnectionError("Connection failed")
            
            app = create_app(config={'TESTING': True})
            
            with app.test_client() as test_client:
                response = test_client.post('/add',
                                          data=json.dumps(valid_payload),
                                          content_type='application/json')
                
                assert response.status_code == 503
                data = json.loads(response.data)
                assert data['error'] == 'service_unavailable'
                assert 'Elasticsearch service is not available' in data['message']
    
    def test_add_endpoint_elasticsearch_connection_error(self, client, app, valid_payload):
        """Test POST /add when Elasticsearch connection fails during operation."""
        app.es_client.index_document.side_effect = ElasticsearchConnectionError("Connection lost")
        
        response = client.post('/add',
                             data=json.dumps(valid_payload),
                             content_type='application/json')
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['error'] == 'service_unavailable'
        assert data['message'] == 'Elasticsearch service is unavailable'
    
    def test_add_endpoint_elasticsearch_validation_error(self, client, app, valid_payload):
        """Test POST /add when Elasticsearch validation fails."""
        app.es_client.index_document.side_effect = ValueError("Invalid document format")
        
        response = client.post('/add',
                             data=json.dumps(valid_payload),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'bad_request'
        assert 'Invalid document format' in data['message']
    
    def test_add_endpoint_with_timestamp(self, client, app, valid_payload):
        """Test POST /add with custom timestamp."""
        valid_payload['timestamp'] = '2024-01-15T10:30:00Z'
        app.es_client.index_document.return_value = True
        
        response = client.post('/add',
                             data=json.dumps(valid_payload),
                             content_type='application/json')
        
        assert response.status_code == 201
        app.es_client.index_document.assert_called_once_with(valid_payload)
    
    def test_add_endpoint_empty_field_values(self, client):
        """Test POST /add with empty field values."""
        payload_with_empty_values = {
            "service_name": "",
            "service_status": "UP",
            "host_name": "test-host"
        }
        
        response = client.post('/add',
                             data=json.dumps(payload_with_empty_values),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'bad_request'
        assert 'Missing required fields' in data['message']
        assert 'service_name' in data['message']


class TestHealthcheckEndpoint:
    """Test cases for GET /healthcheck endpoint."""
    
    @pytest.fixture
    def app(self):
        """Create test app fixture with mocked Elasticsearch."""
        with patch('src.api.app.ElasticsearchClient') as mock_es_class:
            mock_es_client = Mock()
            mock_es_class.return_value = mock_es_client
            
            app = create_app(config={'TESTING': True})
            app.es_client = mock_es_client
            return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client fixture."""
        return app.test_client()
    
    def test_healthcheck_success(self, client, app):
        """Test successful GET /healthcheck endpoint."""
        mock_statuses = {
            'httpd': 'UP',
            'rabbitMQ': 'UP',
            'postgreSQL': 'DOWN',
            'rbcapp1': 'DOWN'
        }
        app.es_client.get_all_service_statuses.return_value = mock_statuses
        
        response = client.get('/healthcheck')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'services' in data
        assert 'timestamp' in data
        assert data['services'] == mock_statuses
        
        # Verify Elasticsearch client was called
        app.es_client.get_all_service_statuses.assert_called_once()
    
    def test_healthcheck_empty_services(self, client, app):
        """Test GET /healthcheck with no services in Elasticsearch."""
        app.es_client.get_all_service_statuses.return_value = {}
        
        response = client.get('/healthcheck')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['services'] == {}
        assert 'timestamp' in data
    
    def test_healthcheck_elasticsearch_unavailable(self, client):
        """Test GET /healthcheck when Elasticsearch is unavailable."""
        with patch('src.api.app.ElasticsearchClient') as mock_es_class:
            mock_es_class.side_effect = ElasticsearchConnectionError("Connection failed")
            
            app = create_app(config={'TESTING': True})
            
            with app.test_client() as test_client:
                response = test_client.get('/healthcheck')
                
                assert response.status_code == 503
                data = json.loads(response.data)
                assert data['error'] == 'service_unavailable'
                assert 'Elasticsearch service is not available' in data['message']
    
    def test_healthcheck_elasticsearch_connection_error(self, client, app):
        """Test GET /healthcheck when Elasticsearch connection fails during operation."""
        app.es_client.get_all_service_statuses.side_effect = ElasticsearchConnectionError("Connection lost")
        
        response = client.get('/healthcheck')
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['error'] == 'service_unavailable'
        assert data['message'] == 'Elasticsearch service is unavailable'
    
    def test_healthcheck_unexpected_error(self, client, app):
        """Test GET /healthcheck with unexpected error."""
        app.es_client.get_all_service_statuses.side_effect = Exception("Unexpected error")
        
        response = client.get('/healthcheck')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['error'] == 'internal_server_error'
        assert data['message'] == 'An unexpected error occurred'
    
    def test_healthcheck_response_format(self, client, app):
        """Test that healthcheck response follows expected format."""
        mock_statuses = {'httpd': 'UP', 'rabbitMQ': 'DOWN'}
        app.es_client.get_all_service_statuses.return_value = mock_statuses
        
        response = client.get('/healthcheck')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = json.loads(response.data)
        required_fields = ['services', 'timestamp']
        
        for field in required_fields:
            assert field in data
        
        # Verify timestamp format (ISO 8601 with Z suffix)
        assert data['timestamp'].endswith('Z')
        assert 'T' in data['timestamp']


class TestHealthcheckServiceEndpoint:
    """Test cases for GET /healthcheck/{serviceName} endpoint."""
    
    @pytest.fixture
    def app(self):
        """Create test app fixture with mocked Elasticsearch."""
        with patch('src.api.app.ElasticsearchClient') as mock_es_class:
            mock_es_client = Mock()
            mock_es_class.return_value = mock_es_client
            
            app = create_app(config={'TESTING': True})
            app.es_client = mock_es_client
            return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client fixture."""
        return app.test_client()
    
    @pytest.fixture
    def sample_service_doc(self):
        """Sample service status document."""
        return {
            'service_name': 'httpd',
            'service_status': 'UP',
            'host_name': 'test-host',
            'timestamp': '2024-01-15T10:30:00Z'
        }
    
    def test_healthcheck_service_success(self, client, app, sample_service_doc):
        """Test successful GET /healthcheck/{serviceName} endpoint."""
        app.es_client.get_service_status.return_value = sample_service_doc
        
        response = client.get('/healthcheck/httpd')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['service_name'] == 'httpd'
        assert data['service_status'] == 'UP'
        assert data['host_name'] == 'test-host'
        assert data['last_updated'] == '2024-01-15T10:30:00Z'
        assert 'timestamp' in data
        
        # Verify Elasticsearch client was called with correct service name
        app.es_client.get_service_status.assert_called_once_with('httpd')
    
    def test_healthcheck_service_not_found(self, client, app):
        """Test GET /healthcheck/{serviceName} for non-existent service."""
        app.es_client.get_service_status.return_value = None
        
        response = client.get('/healthcheck/nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'not_found'
        assert 'Service "nonexistent" not found' in data['message']
        assert 'timestamp' in data
    
    def test_healthcheck_service_empty_name(self, client, app):
        """Test GET /healthcheck/{serviceName} with empty service name."""
        response = client.get('/healthcheck/ ')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'bad_request'
        assert data['message'] == 'Service name cannot be empty'
    
    def test_healthcheck_service_with_whitespace(self, client, app, sample_service_doc):
        """Test GET /healthcheck/{serviceName} with whitespace in service name."""
        app.es_client.get_service_status.return_value = sample_service_doc
        
        response = client.get('/healthcheck/ httpd ')
        
        assert response.status_code == 200
        # Verify that whitespace was stripped
        app.es_client.get_service_status.assert_called_once_with('httpd')
    
    def test_healthcheck_service_elasticsearch_unavailable(self, client):
        """Test GET /healthcheck/{serviceName} when Elasticsearch is unavailable."""
        with patch('src.api.app.ElasticsearchClient') as mock_es_class:
            mock_es_class.side_effect = ElasticsearchConnectionError("Connection failed")
            
            app = create_app(config={'TESTING': True})
            
            with app.test_client() as test_client:
                response = test_client.get('/healthcheck/httpd')
                
                assert response.status_code == 503
                data = json.loads(response.data)
                assert data['error'] == 'service_unavailable'
                assert 'Elasticsearch service is not available' in data['message']
    
    def test_healthcheck_service_elasticsearch_connection_error(self, client, app):
        """Test GET /healthcheck/{serviceName} when Elasticsearch connection fails during operation."""
        app.es_client.get_service_status.side_effect = ElasticsearchConnectionError("Connection lost")
        
        response = client.get('/healthcheck/httpd')
        
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data['error'] == 'service_unavailable'
        assert data['message'] == 'Elasticsearch service is unavailable'
    
    def test_healthcheck_service_unexpected_error(self, client, app):
        """Test GET /healthcheck/{serviceName} with unexpected error."""
        app.es_client.get_service_status.side_effect = Exception("Unexpected error")
        
        response = client.get('/healthcheck/httpd')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['error'] == 'internal_server_error'
        assert data['message'] == 'An unexpected error occurred'
    
    def test_healthcheck_service_response_format(self, client, app, sample_service_doc):
        """Test that service healthcheck response follows expected format."""
        app.es_client.get_service_status.return_value = sample_service_doc
        
        response = client.get('/healthcheck/httpd')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = json.loads(response.data)
        required_fields = ['service_name', 'service_status', 'host_name', 'last_updated', 'timestamp']
        
        for field in required_fields:
            assert field in data
        
        # Verify timestamp format (ISO 8601 with Z suffix)
        assert data['timestamp'].endswith('Z')
        assert 'T' in data['timestamp']
    
    def test_healthcheck_service_without_timestamp(self, client, app):
        """Test service healthcheck when document doesn't have timestamp."""
        service_doc_no_timestamp = {
            'service_name': 'httpd',
            'service_status': 'UP',
            'host_name': 'test-host'
        }
        app.es_client.get_service_status.return_value = service_doc_no_timestamp
        
        response = client.get('/healthcheck/httpd')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['last_updated'] is None
        assert 'timestamp' in data  # Current timestamp should still be present
    
    def test_healthcheck_service_special_characters(self, client, app, sample_service_doc):
        """Test GET /healthcheck/{serviceName} with special characters in service name."""
        sample_service_doc['service_name'] = 'my-service_v2'
        app.es_client.get_service_status.return_value = sample_service_doc
        
        response = client.get('/healthcheck/my-service_v2')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['service_name'] == 'my-service_v2'
        
        app.es_client.get_service_status.assert_called_once_with('my-service_v2')