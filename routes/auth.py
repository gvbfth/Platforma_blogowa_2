"""
Routing dla autoryzacji - Wersja z cookies
"""
from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, get_jwt,
    create_access_token, create_refresh_token,
    set_access_cookies, set_refresh_cookies,
    unset_jwt_cookies, get_csrf_token
)
from datetime import datetime, timezone

from services.auth_service import AuthService
from validators.input_validator import validate_email, validate_username, ValidationError
from validators.password_validator import validate_password, PasswordValidationError
from utils.error_handlers import handle_validation_error
from utils.jwt_utils import rotate_refresh_token, revoke_token, get_current_user
from extensions import limiter
import structlog

logger = structlog.get_logger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """
    Rejestracja użytkownika
    POST /api/auth/register
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Brak danych JSON'
            }), 400
        
        # Walidacja danych wejściowych
        username = validate_username(data.get('username'))
        email = validate_email(data.get('email'))
        password = data.get('password')
        
        # Walidacja hasła
        validate_password(password)
        
        # Rejestracja użytkownika
        user = AuthService.register_user(username, email, password)
        
        logger.info("Nowy użytkownik zarejestrowany", username=username, email=email)
        
        # Tworzenie tokenów z dodatkowymi claimami
        current_time = datetime.now(timezone.utc).isoformat()

        # Tworzenie tokenów
        access_token = create_access_token(
            identity=str(user.id),  # KONWERSJA NA STRING
            additional_claims={
                'username': user.username,
                'role': user.role,
                'email': user.email,
                'login_time': current_time
            }
        )
        refresh_token = create_refresh_token(identity=str(user.id))  # KONWERSJA NA STRING
        
        # Tworzenie odpowiedzi
        response = jsonify({
            'message': 'Użytkownik zarejestrowany pomyślnie',
            'user': user.to_dict(),
            'login_time': current_time,
            'access_token': access_token, 
            'refresh_token': refresh_token 
        })
        
        # Ustawienie tokenów w cookies
        set_access_cookies(response, access_token, max_age=15*60)
        set_refresh_cookies(response, refresh_token, max_age=7*24*60*60)
        
        return response, 201
        
    except ValidationError as e:
        return handle_validation_error(e)
    except PasswordValidationError as e:
        return jsonify({
            'error': 'Password Validation Failed',
            'message': str(e),
            'validation_errors': e.validation_errors
        }), 400
    except ValueError as e:
        return jsonify({
            'error': 'Bad Request',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error("Błąd rejestracji", error=str(e))
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Wystąpił błąd podczas rejestracji'
        }), 500

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """
    Logowanie użytkownika
    POST /api/auth/login
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Brak danych JSON'
            }), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Nazwa użytkownika i hasło są wymagane'
            }), 400
        
        # Logowanie
        user = AuthService.login_user(username, password)
        
        if not user:
            logger.warning("Nieudana próba logowania", username=username)
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Nieprawidłowa nazwa użytkownika lub hasło'
            }), 401
        
        # Tworzenie UNIKALNEGO tokenu z timestamp
        current_time = datetime.now(timezone.utc).isoformat()

        # Tworzenie tokenów
        access_token = create_access_token(
            identity=str(user.id),  # KONWERSJA NA STRING
            additional_claims={
                'username': user.username,
                'role': user.role,
                'email': user.email,
                'login_time': current_time,
                'session_id': f"{user.id}_{int(datetime.now(timezone.utc).timestamp())}"
            }
        )
        refresh_token = create_refresh_token(identity=str(user.id))  # KONWERSJA NA STRING
        
        # Tworzenie odpowiedzi
        response = jsonify({
            'message': 'Zalogowano pomyślnie',
            'user': user.to_dict(),
            'login_time': current_time,
            'access_token': access_token, 
            'refresh_token': refresh_token 
        })
        
        # Ustawienie tokenów w cookies
        set_access_cookies(response, access_token, max_age=15*60)
        set_refresh_cookies(response, refresh_token, max_age=7*24*60*60)
        
        logger.info("Użytkownik zalogowany", username=username)
        
        return response, 200
        
    except Exception as e:
        logger.error("Błąd logowania", error=str(e))
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Wystąpił błąd podczas logowania'
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Odświeżanie tokena JWT - wersja z cookies
    POST /api/auth/refresh
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Sprawdź czy current_user_id jest prawidłowym stringiem
        if not current_user_id or not isinstance(current_user_id, str):
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Nieprawidłowy identyfikator użytkownika'
            }), 401
        
        # Pobierz stary refresh token z cookies
        old_refresh_token = request.cookies.get('refresh_token')
        if not old_refresh_token:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Brak refresh token w cookies'
            }), 401
        
        # Konwertuj string na int dla rotacji tokena
        try:
            user_id_int = int(current_user_id)
        except (ValueError, TypeError):
            logger.warning("Nieprawidłowy format identyfikatora użytkownika", user_id=current_user_id)
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Nieprawidłowy format identyfikatora użytkownika'
            }), 401
        
        # Rotacja refresh tokena 
        new_refresh_token = rotate_refresh_token(old_refresh_token, user_id_int)
        
        if not new_refresh_token:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Nieprawidłowy lub wygasły refresh token'
            }), 401
        
        # Utwórz nowy access token - identity jako string
        new_access_token = create_access_token(identity=current_user_id)
        
        # Utwórz odpowiedź
        response = jsonify({
            'message': 'Token odświeżony',
            'access_token': new_access_token,  
            'refresh_token': new_refresh_token  
        })
        
        # Ustaw nowe tokeny w cookies
        set_access_cookies(response, new_access_token)
        set_refresh_cookies(response, new_refresh_token)
        
        logger.info("Token odświeżony", user_id=current_user_id)
        
        return response, 200
        
    except Exception as e:
        logger.error("Błąd odświeżania tokena", error=str(e))
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Wystąpił błąd podczas odświeżania tokena'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Wylogowanie użytkownika - wersja z cookies
    POST /api/auth/logout
    """
    try:
        jti = get_jwt()['jti']
        revoke_token(jti)
        
        # Tworzenie odpowiedzi
        response = jsonify({
            'message': 'Wylogowano pomyślnie'
        })
        
        # Usunięcie tokenów z cookies
        unset_jwt_cookies(response)
        
        logger.info("Użytkownik wylogowany", user_id=get_jwt_identity())
        
        return response, 200
        
    except Exception as e:
        logger.error("Błąd wylogowania", error=str(e))
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Wystąpił błąd podczas wylogowania'
        }), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user_info():
    """
    Pobierz informacje o aktualnym użytkowniku
    GET /api/auth/me
    """
    try:
        # DEBUG: Sprawdź co jest w JWT
        current_identity = get_jwt_identity()
        logger.debug("JWT Identity", identity=current_identity, type=type(current_identity))
        
        user = get_current_user()
        
        if not user:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Użytkownik nie znaleziony'
            }), 401
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        logger.error("Błąd pobierania danych użytkownika", error=str(e))
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Wystąpił błąd podczas pobierania danych użytkownika'
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Zmiana hasła
    POST /api/auth/change-password
    """
    try:
        user = get_current_user()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Brak danych JSON'
            }), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Obecne i nowe hasło są wymagane'
            }), 400
        
        # Sprawdź obecne hasło
        if not user.check_password(current_password):
            logger.warning("Nieprawidłowe obecne hasło przy próbie zmiany", user_id=user.id)
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Nieprawidłowe obecne hasło'
            }), 401
        
        # Walidacja nowego hasła
        validate_password(new_password)
        
        # Zmiana hasła
        user.set_password(new_password)
        from database import db
        db.session.commit()
        
        logger.info("Hasło zmienione", user_id=user.id)
        
        return jsonify({
            'message': 'Hasło zmienione pomyślnie'
        }), 200
        
    except PasswordValidationError as e:
        return jsonify({
            'error': 'Password Validation Failed',
            'message': str(e),
            'validation_errors': e.validation_errors
        }), 400
    except Exception as e:
        logger.error("Błąd zmiany hasła", error=str(e))
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Wystąpił błąd podczas zmiany hasła'
        }), 500