"""
Unit tests for Elasticsearch client wrapper.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from elasticsearch.exceptions import ConnectionError as ESConnectionError, NotFoundError, RequestError

from src.api.elasticsearch_client import ElasticsearchClient, ElasticsearchConnectionError


class TestElasticsearchClientInitialization:
    """Test cases for ElasticsearchClient initialization."""
    
    @patch('src.api.elasticsearch_client.Elasticsearch')
    def test_init_success(self, mock_elasticsearch):
        """Test successful initialization."""
        mock_client = Mock()
        mock_client.indices.exists.return_value = True
        mock_elasticsearch.return_value = mock_client
        
        client = ElasticsearchClient()
        
        assert client.url == "http://localhost:9200"
        assert client.index_name == "service-monitoring"
        assert client.client == mock_client
        mock_elasticsearch.assert_called_once_with(["http://localhost:9200"])
    
    @patch('src.api.elasticsearch_client.Elasticsearch')
    def test_init_with_custom_params(self, mock_elasticsearch):
        """Test initialization with custom parameters."""
        mock_client = Mock()
        mock_client.indices.exists.return_value = True
        mock_elasticsearch.return_value = mock_client
        
        custom_url = "http://custom:9200"
        custom_index = "custom-index"
        
        client = ElasticsearchClient(url=custom_url, index_name=custom_index)
        
        assert client.url == custom_url
        assert client.index_name == custom_index
        mock_elasticsearch.assert_called_once_with([custom_url])
    
    @patch('src.api.elasticsearch_client.Elasticsearch')
    def test_init_connection_failure(self, mock_elasticsearch):
        """Test initialization failure due to connection error."""
        mock_elasticsearch.side_effect = Exception("Connection failed")
        
        with pytest.raises(ElasticsearchConnectionError, match="Cannot connect to Elasticsearch"):
            ElasticsearchClient()
    
    @patch('src.api.elasticsearch_client.Elasticsearch')
    def test_ensure_index_creation(self, mock_elasticsearch):
        """Test index creation when it doesn't exist."""
        mock_client = Mock()
        mock_client.indices.exists.return_value = False
        mock_client.indices.create.return_value = {"acknowledged": True}
        mock_elasticsearch.return_value = mock_client
        
        ElasticsearchClient()
        
        mock_client.indices.create.assert_called_once()
        call_args = mock_client.indices.create.call_args
        assert call_args[1]['index'] == 'service-monitoring'
        assert 'mappings' in call_args[1]['body']


class TestElasticsearchClientConnection:
    """Test cases for connection management."""
    
    @patch('src.api.elasticsearch_client.Elasticsearch')
    def test_is_connected_success(self, mock_elasticsearch):
        """Test successful connection check."""
        mock_client = Mock()
        mock_client.indices.exists.return_value = True
        mock_client.ping.return_value = True
        mock_elasticsearch.return_value = mock_client
        
        client = ElasticsearchClient()
        assert client.is_connected() is True
    
    @patch('src.api.elasticsearch_client.Elasticsearch')
    def test_is_connected_failure(self, mock_elasticsearch):
        """Test connection check failure."""
        mock_client = Mock()
        mock_client.indices.exists.return_value = True
        mock_client.ping.side_effect = Exception("Connection failed")
        mock_elasticsearch.return_value = mock_client
        
        client = ElasticsearchClient()
        assert client.is_connected() is False


class TestElasticsearchClientIndexing:
    """Test cases for document indexing."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock Elasticsearch client."""
        with patch('src.api.elasticsearch_client.Elasticsearch') as mock_es:
            mock_client = Mock()
            mock_client.indices.exists.return_value = True
            mock_es.return_value = mock_client
            yield mock_client
    
    def test_index_document_success(self, mock_client):
        """Test successful document indexing."""
        mock_client.index.return_value = {"_id": "test-id", "result": "created"}
        
        client = ElasticsearchClient()
        document = {
            "service_name": "httpd",
            "service_status": "UP",
            "host_name": "test-host"
        }
        
        result = client.index_document(document)
        
        assert result is True
        mock_client.index.assert_called_once()
        call_args = mock_client.index.call_args
        assert call_args[1]['index'] == 'service-monitoring'
        assert 'timestamp' in call_args[1]['body']
    
    def test_index_document_with_timestamp(self, mock_client):
        """Test indexing document that already has timestamp."""
        mock_client.index.return_value = {"_id": "test-id", "result": "created"}
        
        client = ElasticsearchClient()
        timestamp = "2024-01-15T10:30:00Z"
        document = {
            "service_name": "httpd",
            "service_status": "UP",
            "host_name": "test-host",
            "timestamp": timestamp
        }
        
        result = client.index_document(document)
        
        assert result is True
        call_args = mock_client.index.call_args
        assert call_args[1]['body']['timestamp'] == timestamp
    
    def test_index_document_missing_fields(self, mock_client):
        """Test indexing document with missing required fields."""
        client = ElasticsearchClient()
        document = {
            "service_name": "httpd",
            # Missing service_status and host_name
        }
        
        with pytest.raises(ValueError, match="Missing required fields"):
            client.index_document(document)
    
    def test_index_document_connection_error(self, mock_client):
        """Test indexing when Elasticsearch is unavailable."""
        mock_client.index.side_effect = ESConnectionError("Connection failed")
        
        client = ElasticsearchClient()
        document = {
            "service_name": "httpd",
            "service_status": "UP",
            "host_name": "test-host"
        }
        
        with pytest.raises(ElasticsearchConnectionError, match="Elasticsearch service is unavailable"):
            client.index_document(document)


class TestElasticsearchClientQuerying:
    """Test cases for document querying."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock Elasticsearch client."""
        with patch('src.api.elasticsearch_client.Elasticsearch') as mock_es:
            mock_client = Mock()
            mock_client.indices.exists.return_value = True
            mock_es.return_value = mock_client
            yield mock_client
    
    def test_get_latest_status_specific_service(self, mock_client):
        """Test getting latest status for specific service."""
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
        
        client = ElasticsearchClient()
        results = client.get_latest_status("httpd")
        
        assert len(results) == 1
        assert results[0]["service_name"] == "httpd"
        assert results[0]["service_status"] == "UP"
    
    def test_get_latest_status_all_services(self, mock_client):
        """Test getting latest status for all services."""
        mock_response = {
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
                            "key": "rabbitMQ",
                            "latest": {
                                "hits": {
                                    "hits": [
                                        {
                                            "_source": {
                                                "service_name": "rabbitMQ",
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
        mock_client.search.return_value = mock_response
        
        client = ElasticsearchClient()
        results = client.get_latest_status()
        
        assert len(results) == 2
        service_names = [r["service_name"] for r in results]
        assert "httpd" in service_names
        assert "rabbitMQ" in service_names
    
    def test_get_service_status_found(self, mock_client):
        """Test getting status for existing service."""
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
        
        client = ElasticsearchClient()
        result = client.get_service_status("httpd")
        
        assert result is not None
        assert result["service_name"] == "httpd"
        assert result["service_status"] == "UP"
    
    def test_get_service_status_not_found(self, mock_client):
        """Test getting status for non-existent service."""
        mock_response = {"hits": {"hits": []}}
        mock_client.search.return_value = mock_response
        
        client = ElasticsearchClient()
        result = client.get_service_status("nonexistent")
        
        assert result is None
    
    def test_get_all_service_statuses(self, mock_client):
        """Test getting simplified status mapping for all services."""
        mock_response = {
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
                        }
                    ]
                }
            }
        }
        mock_client.search.return_value = mock_response
        
        client = ElasticsearchClient()
        result = client.get_all_service_statuses()
        
        assert isinstance(result, dict)
        assert result["httpd"] == "UP"
    
    def test_query_connection_error(self, mock_client):
        """Test querying when Elasticsearch is unavailable."""
        mock_client.search.side_effect = ESConnectionError("Connection failed")
        
        client = ElasticsearchClient()
        
        with pytest.raises(ElasticsearchConnectionError, match="Elasticsearch service is unavailable"):
            client.get_latest_status("httpd")
    
    def test_query_index_not_found(self, mock_client):
        """Test querying when index doesn't exist."""
        mock_client.search.side_effect = NotFoundError("Index not found", meta={}, body={})
        
        client = ElasticsearchClient()
        result = client.get_latest_status("httpd")
        
        assert result == []


class TestElasticsearchClientHealthCheck:
    """Test cases for health check functionality."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock Elasticsearch client."""
        with patch('src.api.elasticsearch_client.Elasticsearch') as mock_es:
            mock_client = Mock()
            mock_client.indices.exists.return_value = True
            mock_es.return_value = mock_client
            yield mock_client
    
    def test_health_check_success(self, mock_client):
        """Test successful health check."""
        mock_client.cluster.health.return_value = {
            "status": "green",
            "number_of_nodes": 1
        }
        mock_client.indices.exists.return_value = True
        
        client = ElasticsearchClient()
        result = client.health_check()
        
        assert result["connected"] is True
        assert result["cluster_status"] == "green"
        assert result["number_of_nodes"] == 1
        assert result["index_exists"] is True
    
    def test_health_check_failure(self, mock_client):
        """Test health check when Elasticsearch is unavailable."""
        mock_client.cluster.health.side_effect = Exception("Connection failed")
        
        client = ElasticsearchClient()
        result = client.health_check()
        
        assert result["connected"] is False
        assert "error" in result
        assert result["index_exists"] is False