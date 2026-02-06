"""Konfiguracja aplikacji Flask"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Podstawowa konfiguracja"""
    
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database - domyślnie SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///blog.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT - zmienione na cookies
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 900))  # 15 minut
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 604800))  # 7 dni
    )
    
    # ZMIANA: Tokeny w cookies zamiast headers
    JWT_TOKEN_LOCATION = ['cookies']
    JWT_ACCESS_COOKIE_NAME = 'access_token'
    JWT_REFRESH_COOKIE_NAME = 'refresh_token'
    JWT_COOKIE_SECURE = False  # True tylko w produkcji z HTTPS
    JWT_COOKIE_CSRF_PROTECT = False  # Dla prostoty
    JWT_COOKIE_SAMESITE = 'Lax'
    JWT_COOKIE_PATH = '/'
    JWT_COOKIE_DOMAIN = None
    JWT_ACCESS_COOKIE_PATH = '/'  
    JWT_REFRESH_COOKIE_PATH = '/' 
    JWT_COOKIE_MAX_AGE = None 

    JWT_SESSION_COOKIE = False #odświeżanie przy każdej odpowiedzi
    
    # Bcrypt
    BCRYPT_LOG_ROUNDS = int(os.environ.get('BCRYPT_LOG_ROUNDS', 12))
    
    # Rate limiting (w pamięci zamiast Redis)
    RATE_LIMIT = os.environ.get('RATE_LIMIT', '200 per day, 50 per hour')
    
    # Security
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

class DevelopmentConfig(Config):
    """Konfiguracja deweloperska"""
    """
    DEBUG = True
    SQLALCHEMY_ECHO = False
    JWT_COOKIE_SECURE = False  # W dev pozwól na HTTP
    JWT_COOKIE_CSRF_PROTECT = False  # Wyłącz CSRF dla łatwiejszego testowania
    JWT_REFRESH_JSON_KEY = 'refresh_token' #do odświeżania
    JWT_ACCESS_JSON_KEY = 'access_token' #do odświeżania
    JWT_SESSION_COOKIE = False
    """
    class DevelopmentConfig(Config):
        DEBUG = True
        SQLALCHEMY_ECHO = False
        JWT_COOKIE_SECURE = False  
        JWT_COOKIE_CSRF_PROTECT = False  
        JWT_COOKIE_SAMESITE = 'Lax'  
        JWT_ACCESS_COOKIE_PATH = '/'  
        JWT_REFRESH_COOKIE_PATH = '/'  
        JWT_COOKIE_DOMAIN = None  
        JWT_SESSION_COOKIE = False  
    
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    JWT_REFRESH_JSON_KEY = 'refresh_token'  
    JWT_ACCESS_JSON_KEY = 'access_token'  

class ProductionConfig(Config):
    """Konfiguracja produkcyjna"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    JWT_COOKIE_SECURE = True  # Wymaga HTTPS
    JWT_COOKIE_HTTPONLY = True
    JWT_COOKIE_SAMESITE = 'Strict'
    JWT_COOKIE_CSRF_PROTECT = True  # Włącz CSRF w produkcji
    JWT_SESSION_COOKIE = False

class TestingConfig(Config):
    """Konfiguracja testowa"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_SESSION_COOKIE = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}