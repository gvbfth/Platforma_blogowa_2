"""
Narzędzia JWT - Wersja z cookies
"""
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
import jwt
from flask import request, jsonify, current_app
from flask_jwt_extended import create_access_token as flask_create_access_token
from flask_jwt_extended import create_refresh_token as flask_create_refresh_token
from flask_jwt_extended import get_jwt_identity, jwt_required
import structlog

logger = structlog.get_logger(__name__)

# Słownik do śledzenia unieważnionych tokenów (w produkcji użyj Redis)
BLACKLISTED_TOKENS = set()
REFRESH_TOKENS = {}  # token_refresh -> {user_id, expires_at}

def create_access_token(identity, user=None, additional_claims=None):
    """
    Tworzenie access tokena JWT - dla cookies
    """
    # KONWERSJA IDENTITY NA STRING - Flask-JWT wymaga stringa
    identity_str = str(identity)
    
    now = datetime.now(timezone.utc)

    claims = {
        'type': 'access',
        'iat': now,
        'exp': now + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
        'jti': f"{identity_str}_{int(time.time() * 1000)}"  # Unikalny ID tokena
    }
    
    if user:
        claims.update({
            'username': user.username,
            'role': user.role,
            'email': user.email
        })
    
    if additional_claims:
        claims.update(additional_claims)
    
    token = flask_create_access_token(
        identity=identity_str,  # UŻYJ STRINGA
        additional_claims=claims
    )
    
    logger.debug("Utworzono access token", user_id=identity_str)
    return token

def create_refresh_token(identity):
    """
    Tworzenie refresh tokena JWT - dla cookies
    """
    # KONWERSJA IDENTITY NA STRING - Flask-JWT wymaga stringa
    identity_str = str(identity)
    
    now = datetime.now(timezone.utc)
    expires_at = now + current_app.config['JWT_REFRESH_TOKEN_EXPIRES']
    
    refresh_token = flask_create_refresh_token(
        identity=identity_str,  # UŻYJ STRINGA
        additional_claims={
            'jti': f"refresh_{identity_str}_{int(time.time() * 1000)}",
            'type': 'refresh'
        }
    )
    
    # Zapisz refresh token (w produkcji w Redis)
    REFRESH_TOKENS[refresh_token] = {
        'user_id': identity_str,  # ZAPISZ JAKO STRING
        'expires_at': expires_at.timestamp(),
        'created_at': now.timestamp(),
        'jti': f"refresh_{identity_str}_{int(time.time() * 1000)}"
    }
    
    logger.debug("Utworzono refresh token", user_id=identity_str)
    return refresh_token

def revoke_token(token):
    """
    Unieważnienie tokena
    """
    BLACKLISTED_TOKENS.add(token)
    logger.info("Token unieważniony")

def is_token_revoked(token):
    """
    Sprawdzenie czy token jest unieważniony
    """
    return token in BLACKLISTED_TOKENS

def rotate_refresh_token(old_token, user_id):
    """
    Rotacja refresh tokena - dla cookies
    Zwraca nowy refresh token i unieważnia stary
    """
    if old_token not in REFRESH_TOKENS:
        logger.warning("Próba rotacji nieistniejącego tokena")
        return None
    
    token_data = REFRESH_TOKENS[old_token]
    
    # Sprawdź czy token jeszcze nie wygasł
    if token_data['expires_at'] < datetime.now(timezone.utc).timestamp():
        logger.warning("Próba rotacji wygasłego tokena")
        del REFRESH_TOKENS[old_token]
        return None
    
    # Sprawdź czy user_id się zgadza
    # token_data['user_id'] jest stringiem, więc porównujemy jako stringi
    if str(user_id) != token_data['user_id']:
        logger.warning("Próba rotacji tokena dla innego użytkownika", 
                      expected_user_id=token_data['user_id'], provided_user_id=user_id)
        return None
    
    # Unieważnij stary token
    del REFRESH_TOKENS[old_token]
    revoke_token(old_token)
    
    # Stwórz nowy refresh token - user_id może być int lub string, create_refresh_token to obsłuży
    new_refresh_token = create_refresh_token(user_id)
    
    logger.info("Rotacja refresh tokena", user_id=user_id)
    return new_refresh_token

def verify_token(token):
    """
    Weryfikacja tokena JWT
    """
    try:
        if is_token_revoked(token):
            logger.warning("Próba użycia unieważnionego tokena")
            return None
        
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=['HS256']
        )
        
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token wygasł")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning("Nieprawidłowy token", error=str(e))
        return None

def get_current_user():
    """
    Pobierz aktualnego użytkownika z JWT
    """
    from models.user import User
    
    identity = get_jwt_identity()
    if not identity:
        return None
    
    try:
        # Konwersja identity (string) na integer dla wyszukiwania w bazie
        user_id = int(identity)
    except (ValueError, TypeError):
        logger.warning("Nieprawidłowy format identyfikatora użytkownika", identity=identity)
        return None
    
    # POPRAWKA: Używaj user_id (int) zamiast identity (string) do wyszukiwania w bazie
    user = User.find_by_id(user_id)
    if not user or not user.is_active:
        return None
    
    return user

def admin_required(f):
    """
    Dekorator wymagający roli ADMIN - działa z cookies
    """
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user or user.role != 'ADMIN':
            logger.warning("Nieautoryzowany dostęp do endpointu admin", 
                          user_id=get_jwt_identity())
            return jsonify({
                'error': 'Forbidden',
                'message': 'Wymagane uprawnienia administratora'
            }), 403
        return f(*args, **kwargs)
    return decorated

def owner_or_admin_required(model_class, id_param='post_id'):
    """
    Dekorator wymagający bycia właścicielem lub administratorem - działa z cookies
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated(*args, **kwargs):
            from models.user import User
            
            user = get_current_user()
            if not user:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'Wymagane uwierzytelnienie'
                }), 401
            
            item_id = kwargs.get(id_param)
            if not item_id:
                return jsonify({
                    'error': 'Bad Request',
                    'message': f'Brak parametru {id_param}'
                }), 400
            
            item = model_class.find_by_id(item_id)
            if not item:
                return jsonify({
                    'error': 'Not Found',
                    'message': 'Nie znaleziono zasobu'
                }), 404
            
            # Sprawdź uprawnienia
            if isinstance(item, User):
                # Dla użytkownika - tylko ten sam użytkownik lub admin
                if user.id != item.id and user.role != 'ADMIN':
                    logger.warning("Próba dostępu do cudzych danych", 
                                  user_id=user.id, target_user_id=item.id)
                    return jsonify({
                        'error': 'Forbidden',
                        'message': 'Brak uprawnień do tego zasobu'
                    }), 403
            else:
                # Dla innych modeli - sprawdź właściciela
                if not hasattr(item, 'author_id') or (user.id != item.author_id and user.role != 'ADMIN'):
                    logger.warning("Próba dostępu do cudzych danych", 
                                  user_id=user.id, author_id=getattr(item, 'author_id', None))
                    return jsonify({
                        'error': 'Forbidden',
                        'message': 'Brak uprawnień do tego zasobu'
                    }), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator