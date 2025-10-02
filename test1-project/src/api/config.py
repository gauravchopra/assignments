"""
Configuration settings for the rbcapp1 monitoring API.
"""
import os


class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # Elasticsearch settings
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL') or 'http://localhost:9200'
    ELASTICSEARCH_INDEX = os.environ.get('ELASTICSEARCH_INDEX') or 'service-monitoring'
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = False
    TESTING = True
    ELASTICSEARCH_URL = 'http://localhost:9200'
    ELASTICSEARCH_INDEX = 'test-service-monitoring'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    def __init__(self):
        super().__init__()
        self.SECRET_KEY = os.environ.get('SECRET_KEY')
        
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable must be set in production")


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}