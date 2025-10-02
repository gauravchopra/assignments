"""
Consolidated API tests.
"""
import pytest
import json
from unittest.mock import Mock, patch
from src.api import create_app
from src.api.elasticsearch_client import ElasticsearchClient, ElasticsearchConnectionError


class TestFlaskAPI:
    """Essential API endpoint tests."""
    
    @pytest.fixture
    def app(self):
        """Create test app with mocked Elasticsearch."""
        with patch('src.api.app.ElasticsearchClient') as mock_es_class:
            mock_es_client = Mock()
            mock_es_class.return_value = mock_es_client
            
            app = create_app(config={'TESTING': True})
            app.es_client = mock_es_client
            return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_add_endpoint_success(self, client, app):
        """Test successful POST to /add."""
        app.es_client.index_document.return_value = True
        
        payload = {
            "service_name": "httpd",
            "service_status": "UP",
            "host_name": "test-host"
        }
        
        response = client.post('/add', 
                             data=json.dumps(payload),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['service_name'] == 'httpd'
    
    def test_add_endpoint_missing_fields(self, client):
        """Test POST /add with missing fields."""
        payload = {"service_name": "httpd"}  # Missing required fields
        
        response = client.post('/add',
                             data=json.dumps(payload),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Missing required fields' in data['message']
    
    def test_healthcheck_endpoint(self, client, app):
        """Test GET /healthcheck."""
        mock_statuses = {'httpd': 'UP', 'rabbitmq': 'DOWN'}
        app.es_client.get_all_service_statuses.return_value = mock_statuses
        
        response = client.get('/healthcheck')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['services'] == mock_statuses
    
    def test_healthcheck_service_endpoint(self, client, app):
        """Test GET /healthcheck/{serviceName}."""
        service_doc = {
            'service_name': 'httpd',
            'service_status': 'UP',
            'host_name': 'test-host',
            'timestamp': '2024-01-15T10:30:00Z'
        }
        app.es_client.get_service_status.return_value = service_doc
        
        response = client.get('/healthcheck/httpd')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['service_name'] == 'httpd'
        assert data['service_status'] == 'UP'
    
    def test_elasticsearch_unavailable(self, client):
        """Test API when Elasticsearch is unavailable."""
        with patch('src.api.app.ElasticsearchClient') as mock_es_class:
            mock_es_class.side_effect = ElasticsearchConnectionError("Connection failed")
            
            app = create_app(config={'TESTING': True})
            
            with app.test_client() as test_client:
                response = test_client.get('/healthcheck')
                
                assert response.status_code == 503
                data = json.loads(response.data)
                assert data['error'] == 'service_unavailable'


class TestElasticsearchClient:
    """Essential Elasticsearch client tests."""
    
    @patch('src.api.elasticsearch_client.Elasticsearch')
    def test_index_document_success(self, mock_elasticsearch):
        """Test successful document indexing."""
        mock_client = Mock()
        mock_client.indices.exists.return_value = True
        mock_client.index.return_value = {"_id": "test-id", "result": "created"}
        mock_elasticsearch.return_value = mock_client
        
        client = ElasticsearchClient()
        document = {
            "service_name": "httpd",
            "service_status": "UP",
            "host_name": "test-host"
        }
        
        result = client.index_document(document)
        assert result is True
    
    @patch('src.api.elasticsearch_client.Elasticsearch')
    def test_get_service_status(self, mock_elasticsearch):
        """Test getting service status."""
        mock_client = Mock()
        mock_client.indices.exists.return_value = True
        mock_response = {
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
        mock_client.search.return_value = mock_response
        mock_elasticsearch.return_value = mock_client
        
        client = ElasticsearchClient()
        result = client.get_service_status("httpd")
        
        assert result is not None
        assert result["service_name"] == "httpd"
        assert result["service_status"] == "UP"