import os
from pathlib import Path
from datetime import timedelta

# Create base directory path
basedir = Path(__file__).parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    # Create instance directory if it doesn't exist
    INSTANCE_PATH = basedir / 'instance'
    INSTANCE_PATH.mkdir(exist_ok=True)
    
    # Set database path
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{INSTANCE_PATH}/crm.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_SECURE = True  # Enable in production
    SESSION_COOKIE_HTTPONLY = True
    
    # Security headers
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=14) 