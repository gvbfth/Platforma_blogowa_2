"""
Blueprint routes package
"""
from .auth import auth_bp
from .posts import posts_bp
from .admin import admin_bp
from .health import health_bp

__all__ = ['auth_bp', 'posts_bp', 'admin_bp', 'health_bp']