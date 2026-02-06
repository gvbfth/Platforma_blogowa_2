"""
Middleware dla nagłówków bezpieczeństwa HTTP 
"""
from flask import request, jsonify
import structlog

logger = structlog.get_logger(__name__)

def setup_security_headers(app):
    """
    Konfiguracja nagłówków bezpieczeństwa HTTP 
    """
    @app.after_request
    def add_security_headers(response):
        """
        Dodaj nagłówki bezpieczeństwa do odpowiedzi
        """
        # X-Content-Type-Options: zapobiega MIME sniffing 
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options: zapobiega clickjacking 
        response.headers['X-Frame-Options'] = 'DENY'
        
        # X-XSS-Protection: przestarzałe, ale dla kompatybilności
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer-Policy: kontrola referrerów 
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content-Security-Policy: podstawowa polityka 
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers['Content-Security-Policy'] = csp_policy
        
        # Strict-Transport-Security (tylko w produkcji)
        if app.config.get('ENV') == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Cache-Control dla API
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store, max-age=0'
        
        # Dodatkowe nagłówki dla JSON API
        if request.is_json or response.content_type == 'application/json':
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Robots-Tag'] = 'noindex, nofollow'
        
        logger.debug("Nagłówki bezpieczeństwa dodane", 
                    path=request.path, 
                    method=request.method,
                    status=response.status_code)
        
        return response
    
    @app.before_request
    def log_request_info():
        """
        Logowanie informacji o żądaniach (Lab 13)
        """
        # Nie loguj wrażliwych danych
        log_data = {
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr,
            'user_agent': request.user_agent.string[:100] if request.user_agent else None,
        }
        
        # Dodatkowe informacje dla POST/PUT
        if request.method in ['POST', 'PUT']:
            # Loguj tylko metadane, nie treść (mogą zawierać hasła)
            log_data['content_type'] = request.content_type
            log_data['content_length'] = request.content_length
        
        logger.info("Żądanie HTTP", **log_data)
    
    @app.after_request
    def log_response_info(response):
        """
        Logowanie informacji o odpowiedziach
        """
        # Loguj tylko status i rozmiar odpowiedzi
        logger.info("Odpowiedź HTTP",
                   method=request.method,
                   path=request.path,
                   status=response.status_code,
                   content_length=response.content_length)
        
        return response
    
    @app.before_request
    def debug_cookies():
        """Debugowanie cookies"""
        if '/api/auth' in request.path:
            logger.debug("Request cookies", 
                        cookies=dict(request.cookies),
                        path=request.path,
                        method=request.method)