"""
Configuration settings for the e-commerce application
Contains all configurable parameters and environment-specific settings
"""

import os
from datetime import timedelta


class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Application settings
    DISCOUNT_ORDER_FREQUENCY = int(os.environ.get('DISCOUNT_ORDER_FREQUENCY', '3'))
    DISCOUNT_PERCENTAGE = float(os.environ.get('DISCOUNT_PERCENTAGE', '10.0'))
    
    # Discount code settings
    DISCOUNT_CODE_EXPIRY_DAYS = int(os.environ.get('DISCOUNT_CODE_EXPIRY_DAYS', '30'))
    MAX_DISCOUNT_CODES_PER_USER = int(os.environ.get('MAX_DISCOUNT_CODES_PER_USER', '1'))
    
    # Cart settings
    CART_EXPIRY_HOURS = int(os.environ.get('CART_EXPIRY_HOURS', '24'))
    MAX_ITEMS_PER_CART = int(os.environ.get('MAX_ITEMS_PER_CART', '100'))
    MAX_QUANTITY_PER_ITEM = int(os.environ.get('MAX_QUANTITY_PER_ITEM', '10'))
    
    # API settings
    MAX_PAGE_SIZE = int(os.environ.get('MAX_PAGE_SIZE', '100'))
    DEFAULT_PAGE_SIZE = int(os.environ.get('DEFAULT_PAGE_SIZE', '10'))
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Rate limiting (if implemented)
    RATE_LIMIT_STORAGE_URL = os.environ.get('RATE_LIMIT_STORAGE_URL', 'memory://')
    DEFAULT_RATE_LIMIT = os.environ.get('DEFAULT_RATE_LIMIT', '100 per hour')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Ensure secret key is set in production
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set in production")


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # Override settings for testing
    DISCOUNT_ORDER_FREQUENCY = 2  # Every 2nd order for easier testing
    DISCOUNT_CODE_EXPIRY_DAYS = 1
    CART_EXPIRY_HOURS = 1


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment"""
    return config[os.environ.get('FLASK_ENV', 'default')]