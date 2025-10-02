"""
Flask application factory for rbcapp1 monitoring system.
"""
from flask import Flask, jsonify, request
import logging
from datetime import datetime
from .elasticsearch_client import ElasticsearchClient, ElasticsearchConnectionError


def create_app(config=None):
    """
    Application factory function that creates and configures Flask app.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Default configuration
    app.config.update({
        'JSON_SORT_KEYS': False,
        'JSONIFY_PRETTYPRINT_REGULAR': True,
    })
    
    # Configure JSON settings (Flask 2.3+ style)
    app.json.sort_keys = False
    app.json.compact = False
    
    # Apply custom configuration if provided
    if config:
        app.config.update(config)
    
    # Set up logging
    if not app.debug and not app.testing:
        logging.basicConfig(level=logging.INFO)
        app.logger.setLevel(logging.INFO)
    
    # Initialize Elasticsearch client
    try:
        es_client = ElasticsearchClient()
        app.es_client = es_client
    except ElasticsearchConnectionError as e:
        app.logger.error(f"Failed to initialize Elasticsearch: {e}")
        app.es_client = None
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register API routes
    register_routes(app)
    
    return app


def register_error_handlers(app):
    """
    Register error handlers for the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        return jsonify({
            'error': 'bad_request',
            'message': 'Invalid request data',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        return jsonify({
            'error': 'not_found',
            'message': 'Resource not found',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error."""
        app.logger.error(f'Internal server error: {error}')
        return jsonify({
            'error': 'internal_server_error',
            'message': 'An internal server error occurred',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500
    
    @app.errorhandler(503)
    def service_unavailable(error):
        """Handle 503 Service Unavailable errors."""
        return jsonify({
            'error': 'service_unavailable',
            'message': 'Service temporarily unavailable',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503


def register_routes(app):
    """
    Register API routes for the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/add', methods=['POST'])
    def add_status():
        """
        POST /add endpoint to accept JSON payload and store in Elasticsearch.
        
        Expected JSON format:
        {
            "service_name": "string",
            "service_status": "string",
            "host_name": "string",
            "timestamp": "string" (optional)
        }
        
        Returns:
            JSON response with success/error status
        """
        try:
            # Check if Elasticsearch client is available
            if not app.es_client:
                app.logger.error("Elasticsearch client not available")
                return jsonify({
                    'error': 'service_unavailable',
                    'message': 'Elasticsearch service is not available',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }), 503
            
            # Validate request content type
            if not request.is_json:
                return jsonify({
                    'error': 'bad_request',
                    'message': 'Request must be JSON',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }), 400
            
            # Get JSON data
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'error': 'bad_request',
                    'message': 'Empty JSON payload',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }), 400
            
            # Validate required fields
            required_fields = ['service_name', 'service_status', 'host_name']
            missing_fields = [field for field in required_fields if field not in data or not data[field]]
            
            if missing_fields:
                return jsonify({
                    'error': 'bad_request',
                    'message': f'Missing required fields: {", ".join(missing_fields)}',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }), 400
            
            # Validate service_status values
            valid_statuses = ['UP', 'DOWN']
            if data['service_status'] not in valid_statuses:
                return jsonify({
                    'error': 'bad_request',
                    'message': f'service_status must be one of: {", ".join(valid_statuses)}',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }), 400
            
            # Index the document in Elasticsearch
            success = app.es_client.index_document(data)
            
            if success:
                return jsonify({
                    'message': 'Status data successfully stored',
                    'service_name': data['service_name'],
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }), 201
            else:
                return jsonify({
                    'error': 'internal_server_error',
                    'message': 'Failed to store status data',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }), 500
                
        except ElasticsearchConnectionError:
            app.logger.error("Elasticsearch connection failed during add operation")
            return jsonify({
                'error': 'service_unavailable',
                'message': 'Elasticsearch service is unavailable',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 503
        except ValueError as e:
            app.logger.error(f"Invalid data format: {e}")
            return jsonify({
                'error': 'bad_request',
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 400
        except Exception as e:
            app.logger.error(f"Unexpected error in add endpoint: {e}")
            return jsonify({
                'error': 'internal_server_error',
                'message': 'An unexpected error occurred',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 500
    
    @app.route('/healthcheck', methods=['GET'])
    def healthcheck():
        """
        GET /healthcheck endpoint to return all application statuses.
        
        Returns:
            JSON response with all service statuses
        """
        try:
            # Check if Elasticsearch client is available
            if not app.es_client:
                app.logger.error("Elasticsearch client not available")
                return jsonify({
                    'error': 'service_unavailable',
                    'message': 'Elasticsearch service is not available',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }), 503
            
            # Get all service statuses from Elasticsearch
            service_statuses = app.es_client.get_all_service_statuses()
            
            # Format response
            response_data = {
                'services': service_statuses,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
            return jsonify(response_data), 200
            
        except ElasticsearchConnectionError:
            app.logger.error("Elasticsearch connection failed during healthcheck")
            return jsonify({
                'error': 'service_unavailable',
                'message': 'Elasticsearch service is unavailable',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 503
        except Exception as e:
            app.logger.error(f"Unexpected error in healthcheck endpoint: {e}")
            return jsonify({
                'error': 'internal_server_error',
                'message': 'An unexpected error occurred',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 500
    
    @app.route('/healthcheck/<service_name>', methods=['GET'])
    def healthcheck_service(service_name):
        """
        GET /healthcheck/{serviceName} endpoint for specific service status queries.
        
        Args:
            service_name: Name of the service to query
            
        Returns:
            JSON response with specific service status
        """
        try:
            # Check if Elasticsearch client is available
            if not app.es_client:
                app.logger.error("Elasticsearch client not available")
                return jsonify({
                    'error': 'service_unavailable',
                    'message': 'Elasticsearch service is not available',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }), 503
            
            # Validate service name parameter
            if not service_name or not service_name.strip():
                return jsonify({
                    'error': 'bad_request',
                    'message': 'Service name cannot be empty',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }), 400
            
            # Get specific service status from Elasticsearch
            service_status_doc = app.es_client.get_service_status(service_name.strip())
            
            if not service_status_doc:
                return jsonify({
                    'error': 'not_found',
                    'message': f'Service "{service_name}" not found',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }), 404
            
            # Format response
            response_data = {
                'service_name': service_status_doc['service_name'],
                'service_status': service_status_doc['service_status'],
                'host_name': service_status_doc['host_name'],
                'last_updated': service_status_doc.get('timestamp'),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
            return jsonify(response_data), 200
            
        except ElasticsearchConnectionError:
            app.logger.error("Elasticsearch connection failed during service healthcheck")
            return jsonify({
                'error': 'service_unavailable',
                'message': 'Elasticsearch service is unavailable',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 503
        except Exception as e:
            app.logger.error(f"Unexpected error in service healthcheck endpoint: {e}")
            return jsonify({
                'error': 'internal_server_error',
                'message': 'An unexpected error occurred',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 500


# For development/testing purposes
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)