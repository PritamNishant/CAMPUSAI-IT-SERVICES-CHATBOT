"""
CampusFix AI - Configuration
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'campusfix-ai-secret-key-2026')
    MONGO_URI = os.getenv('MONGO_URI')
    DATABASE_NAME = 'campusfix_ai'
    
    # JWT Configuration
    JWT_EXPIRATION_DAYS = 7
    
    # Ticket Configuration
    TICKET_PRIORITIES = ['low', 'medium', 'high', 'urgent']
    TICKET_CATEGORIES = ['wifi', 'login', 'software', 'printer', 'hardware', 'other']
    TICKET_STATUSES = ['open', 'in_progress', 'resolved', 'closed']
    
    # Department Routing
    DEPARTMENT_MAP = {
        'wifi': 'Network Support',
        'login': 'Account Services',
        'software': 'Software Support',
        'printer': 'Hardware Support',
        'hardware': 'Hardware Support',
        'other': 'General IT Support'
    }
    
    # User Types
    USER_TYPES = ['student', 'employee']

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
