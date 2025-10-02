"""
Elasticsearch client wrapper for rbcapp1 monitoring system.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import (
    ConnectionError as ESConnectionError,
    NotFoundError,
    RequestError,
    TransportError
)


class ElasticsearchConnectionError(Exception):
    """Custom exception for Elasticsearch connection issues."""
    pass


class ElasticsearchClient:
    """
    Wrapper class for Elasticsearch operations.
    
    Provides methods for indexing and querying service monitoring data
    with proper error handling and connection management.
    """
    
    def __init__(self, url: str = "http://localhost:9200", index_name: str = "service-monitoring"):
        """
        Initialize Elasticsearch client.
        
        Args:
            url: Elasticsearch server URL
            index_name: Name of the index to use for monitoring data
        """
        self.url = url
        self.index_name = index_name
        self.logger = logging.getLogger(__name__)
        
        try:
            self.client = Elasticsearch([url])
            self._ensure_index_exists()
        except Exception as e:
            self.logger.error(f"Failed to initialize Elasticsearch client: {e}")
            raise ElasticsearchConnectionError(f"Cannot connect to Elasticsearch at {url}: {e}")
    
    def _ensure_index_exists(self):
        """
        Ensure the monitoring index exists with proper mapping.
        """
        if not self.client.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "service_name": {"type": "keyword"},
                        "service_status": {"type": "keyword"},
                        "host_name": {"type": "keyword"},
                        "timestamp": {"type": "date", "format": "strict_date_optional_time||epoch_millis"}
                    }
                }
            }
            
            try:
                self.client.indices.create(index=self.index_name, body=mapping)
                self.logger.info(f"Created index: {self.index_name}")
            except RequestError as e:
                if "resource_already_exists_exception" not in str(e):
                    raise
    
    def is_connected(self) -> bool:
        """
        Check if Elasticsearch is connected and responsive.
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            return self.client.ping()
        except Exception as e:
            self.logger.error(f"Elasticsearch connection check failed: {e}")
            return False
    
    def index_document(self, document: Dict[str, Any]) -> bool:
        """
        Index a service status document.
        
        Args:
            document: Dictionary containing service status data
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ElasticsearchConnectionError: If Elasticsearch is not available
            ValueError: If document format is invalid
        """
        try:
            # Validate required fields
            required_fields = ['service_name', 'service_status', 'host_name']
            missing_fields = [field for field in required_fields if field not in document]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            # Add timestamp if not present
            if 'timestamp' not in document:
                document['timestamp'] = datetime.utcnow().isoformat() + 'Z'
            
            # Index the document
            result = self.client.index(
                index=self.index_name,
                body=document
            )
            
            self.logger.info(f"Indexed document: {result['_id']}")
            return True
            
        except ESConnectionError:
            self.logger.error("Elasticsearch connection failed during indexing")
            raise ElasticsearchConnectionError("Elasticsearch service is unavailable")
        except ValueError as e:
            self.logger.error(f"Invalid document format: {e}")
            raise ValueError(f"Invalid document format: {e}")
        except TransportError as e:
            self.logger.error(f"Elasticsearch error during indexing: {e}")
            raise ElasticsearchConnectionError(f"Elasticsearch operation failed: {e}")
    
    def get_latest_status(self, service_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get the latest status for services.
        
        Args:
            service_name: Optional specific service name to query
            
        Returns:
            List of service status documents
            
        Raises:
            ElasticsearchConnectionError: If Elasticsearch is not available
        """
        try:
            if service_name:
                # Query for specific service
                query = {
                    "query": {
                        "term": {"service_name": service_name}
                    },
                    "sort": [{"timestamp": {"order": "desc"}}],
                    "size": 1
                }
            else:
                # Get latest status for all services
                query = {
                    "query": {"match_all": {}},
                    "aggs": {
                        "services": {
                            "terms": {"field": "service_name"},
                            "aggs": {
                                "latest": {
                                    "top_hits": {
                                        "sort": [{"timestamp": {"order": "desc"}}],
                                        "size": 1
                                    }
                                }
                            }
                        }
                    },
                    "size": 0
                }
            
            response = self.client.search(index=self.index_name, body=query)
            
            if service_name:
                # Return hits for specific service
                hits = response['hits']['hits']
                return [hit['_source'] for hit in hits]
            else:
                # Extract latest status for each service from aggregations
                results = []
                if 'aggregations' in response:
                    for bucket in response['aggregations']['services']['buckets']:
                        latest_hit = bucket['latest']['hits']['hits'][0]
                        results.append(latest_hit['_source'])
                return results
                
        except NotFoundError:
            self.logger.warning(f"Index {self.index_name} not found")
            return []
        except ESConnectionError:
            self.logger.error("Elasticsearch connection failed during query")
            raise ElasticsearchConnectionError("Elasticsearch service is unavailable")
        except TransportError as e:
            self.logger.error(f"Elasticsearch error during query: {e}")
            raise ElasticsearchConnectionError(f"Elasticsearch operation failed: {e}")
    
    def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest status for a specific service.
        
        Args:
            service_name: Name of the service to query
            
        Returns:
            Service status document or None if not found
            
        Raises:
            ElasticsearchConnectionError: If Elasticsearch is not available
        """
        results = self.get_latest_status(service_name)
        return results[0] if results else None
    
    def get_all_service_statuses(self) -> Dict[str, str]:
        """
        Get the latest status for all services in a simplified format.
        
        Returns:
            Dictionary mapping service names to their status ("UP" or "DOWN")
            
        Raises:
            ElasticsearchConnectionError: If Elasticsearch is not available
        """
        try:
            results = self.get_latest_status()
            return {doc['service_name']: doc['service_status'] for doc in results}
        except Exception as e:
            self.logger.error(f"Failed to get all service statuses: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the Elasticsearch connection.
        
        Returns:
            Dictionary containing health status information
        """
        try:
            cluster_health = self.client.cluster.health()
            return {
                'connected': True,
                'cluster_status': cluster_health['status'],
                'number_of_nodes': cluster_health['number_of_nodes'],
                'index_exists': self.client.indices.exists(index=self.index_name)
            }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e),
                'index_exists': False
            }