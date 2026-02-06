"""
Obsługa błędów
"""
from flask import jsonify, request
from sqlalchemy.exc import SQLAlchemyError
import structlog

logger = structlog.get_logger(__name__)

def register_error_handlers(app):
    """
    Rejestracja handlerów błędów
    """
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """
        Obsługa błędów 400 Bad Request
        """
        logger.warning("Bad Request", 
                      path=request.path,
                      error=str(error))
        
        return jsonify({
            'error': 'Bad Request',
            'message': 'Nieprawidłowe żądanie',
            'path': request.path
        }), 400
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        """
        Obsługa błędów 401 Unauthorized
        """
        logger.warning("Unauthorized", 
                      path=request.path,
                      remote_addr=request.remote_addr)
        
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Wymagane uwierzytelnienie',
            'path': request.path
        }), 401
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """
        Obsługa błędów 403 Forbidden
        """
        logger.warning("Forbidden", 
                      path=request.path,
                      remote_addr=request.remote_addr)
        
        return jsonify({
            'error': 'Forbidden',
            'message': 'Brak uprawnień do tego zasobu',
            'path': request.path
        }), 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        """
        Obsługa błędów 404 Not Found
        """
        logger.warning("Not Found", 
                      path=request.path,
                      method=request.method)
        
        return jsonify({
            'error': 'Not Found',
            'message': 'Zasób nie znaleziony',
            'path': request.path
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed_error(error):
        """
        Obsługa błędów 405 Method Not Allowed
        """
        logger.warning("Method Not Allowed", 
                      path=request.path,
                      method=request.method)
        
        return jsonify({
            'error': 'Method Not Allowed',
            'message': 'Metoda HTTP nie jest dozwolona dla tego zasobu',
            'path': request.path,
            'allowed_methods': getattr(error, 'valid_methods', [])
        }), 405
    
    @app.errorhandler(415)
    def unsupported_media_type_error(error):
        """
        Obsługa błędów 415 Unsupported Media Type
        """
        logger.warning("Unsupported Media Type", 
                      path=request.path,
                      content_type=request.content_type)
        
        return jsonify({
            'error': 'Unsupported Media Type',
            'message': 'Nieobsługiwany typ mediów. Użyj application/json',
            'path': request.path
        }), 415
    
    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        """
        Obsługa błędów bazy danych
        """
        logger.error("Błąd bazy danych", 
                    error=str(error),
                    path=request.path)
        
        # W produkcji nie pokazuj szczegółów błędu
        if app.config.get('ENV') == 'production':
            message = 'Wystąpił błąd bazy danych'
        else:
            message = str(error)
        
        return jsonify({
            'error': 'Database Error',
            'message': message,
            'path': request.path
        }), 500
    
    @app.errorhandler(Exception)
    def internal_server_error(error):
        """
        Obsługa błędów 500 Internal Server Error
        """
        # Loguj pełny błąd dla administratora
        logger.error("Internal Server Error", 
                    error=str(error),
                    path=request.path,
                    traceback=getattr(error, '__traceback__', None))
        
        # W produkcji nie pokazuj szczegółów błędu
        if app.config.get('ENV') == 'production':
            message = 'Wystąpił wewnętrzny błąd serwera'
        else:
            message = str(error)
        
        return jsonify({
            'error': 'Internal Server Error',
            'message': message,
            'path': request.path
        }), 500

def handle_validation_error(error):
    """
    Obsługa błędów walidacji 
    """
    logger.warning("Błąd walidacji", 
                  field=error.field,
                  value=error.value,
                  message=str(error))
    
    response = {
        'error': 'Validation Error',
        'message': str(error),
        'path': request.path
    }
    
    if error.field:
        response['field'] = error.field
    
    if error.value:
        response['value'] = error.value
    
    return jsonify(response), 400

def handle_password_validation_error(error):
    """
    Obsługa błędów walidacji hasła
    """
    logger.warning("Błąd walidacji hasła", 
                  validation_errors=error.validation_errors)
    
    return jsonify({
        'error': 'Password Validation Failed',
        'message': str(error),
        'validation_errors': error.validation_errors,
        'path': request.path
    }), 400