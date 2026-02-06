"""
Główny plik aplikacji Flask - Blog Platform
"""
import os
from extensions import limiter
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import structlog

from config import Config
from database import db
from middleware.security_headers import setup_security_headers
from utils.error_handlers import register_error_handlers
from utils.logger import setup_logging

# Import routes
from routes.auth import auth_bp
from routes.posts import posts_bp
from routes.health import health_bp
from routes.admin import admin_bp

from flask import render_template
from middleware.rate_limiter import setup_rate_limiting

def create_app(config_class=Config):
    """Factory function do tworzenia aplikacji Flask"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    setup_rate_limiting(app)

    # Setup logging
    setup_logging(app)
    logger = structlog.get_logger(__name__)
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)
    bcrypt = Bcrypt(app)
    
    

    # Setup CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config.get("CORS_ORIGINS", ["http://localhost:3000"]),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "expose_headers": ["Content-Type", "Authorization"]
        }
    }, supports_credentials=True)
    
    # Setup rate limiting
    limiter.init_app(app)
    limiter.default_limits = [app.config.get("RATE_LIMIT", "200 per day, 50 per hour")]
    
    # Register middleware
    setup_security_headers(app)

    # Middleware do zapobiegania cache'owaniu dla auth endpointów
    @app.after_request
    def add_no_cache(response):
        if request.path.startswith('/api/auth/'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(posts_bp, url_prefix='/api/posts')
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Health check endpoint (Lab 10)
    @app.route('/hello')
    def hello():
        """Prosty endpoint testowy (Lab 10)"""
        return jsonify({
            "status": "OK",
            "message": "Blog Platform działa poprawnie!",
            "version": "1.0.0"
        })
    
    @app.route('/')
    def index():
        return jsonify({
            "name": "Blog Platform API",
            "version": "1.0.0",
            "docs": "/api/health",
            "endpoints": {
                "auth": "/api/auth",
                "posts": "/api/posts",
                "health": "/api/health"
            }
        })
    
    # CLI command for manual migrations
    @app.cli.command("init-db")
    def init_db_command():
        """Initialize the database with default admin user"""
        with app.app_context():
            try:
                from migrations import run_migrations
                run_migrations()
                print("✓ Database initialized successfully")
            except Exception as e:
                print(f"✗ Error initializing database: {e}")
                raise
    
    # Auto-run migrations only in development
    if app.config.get('FLASK_ENV') == 'development':
        with app.app_context():
            try:
                # Check if users table exists
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                tables = inspector.get_table_names()
                
                if not tables:  # If no tables at all
                    print("⚙️ Running initial migrations...")
                    from migrations import run_migrations
                    run_migrations()
                    print("✓ Initial migrations completed")
                elif 'users' not in tables:
                    print("⚠️ Tables exist but 'users' table is missing")
                    print("Consider running: flask init-db")
            except Exception as e:
                print(f"⚠️ Could not check/run migrations: {e}")
                if app.config.get('DEBUG'):
                    print("Debug mode: Continuing despite migration error")
    
    logger.info("Aplikacja zainicjalizowana", 
                env=app.config.get("FLASK_ENV"),
                debug=app.config.get("DEBUG"))
    
    @app.route('/web')
    def web_index():
        """Strona webowa z interfejsem HTML"""
        return render_template('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)