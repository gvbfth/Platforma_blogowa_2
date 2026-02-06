"""
Middleware do ograniczania liczby żądań (rate limiting) 
"""
import time
from flask import request, jsonify, make_response
import structlog

logger = structlog.get_logger(__name__)

def setup_rate_limiting(app):
    """
    Prosty rate limiting bez Redis (dla Windows/development)
    """
    # W pamięci przechowujemy licznik żądań
    request_counts = {}
    
    @app.before_request
    def check_rate_limit():
        # Endpointy zwolnione z rate limitingu
        exempt_paths = ['/api/health', '/hello', '/', '/web']
        if request.path in exempt_paths:
            return None
        
        # Identyfikator klienta (adres IP)
        client_ip = request.remote_addr or '127.0.0.1'
        
        # Klucz: IP + ścieżka
        key = f"{client_ip}:{request.path}"
        
        # Bieżąca minuta (uproszczone okno czasowe)
        current_minute = int(time.time() / 60)
        
        # Inicjalizacja licznika
        if key not in request_counts:
            request_counts[key] = {'count': 0, 'minute': current_minute}
        
        # Reset licznika jeśli nowa minuta
        if request_counts[key]['minute'] != current_minute:
            request_counts[key] = {'count': 0, 'minute': current_minute}
        
        # Zwiększ licznik
        request_counts[key]['count'] += 1
        
        # Sprawdź limit (np. 10 żądań na minutę dla login)
        limit = 10 if '/login' in request.path else 100
        
        if request_counts[key]['count'] > limit:
            logger.warning("Przekroczono limit żądań", 
                          ip=client_ip, 
                          path=request.path,
                          count=request_counts[key]['count'])
            
            # POPRAWIONE: Użyj make_response
            response = make_response(jsonify({
                'error': 'Too Many Requests',
                'message': 'Przekroczono dopuszczalną liczbę żądań. Spróbuj ponownie później.',
                'retry_after': 60
            }), 429)
            
            return response  # Zwróć response z ustawionym statusem
        
        return None
    
    logger.info("Rate limiting skonfigurowany (w pamięci)")