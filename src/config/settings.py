import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///insurance_chatbot.db')
    API_KEY = os.environ.get('API_KEY') or 'your_api_key'
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Export DATABASE_URI directly for easier access
DATABASE_URI = Config.DATABASE_URI