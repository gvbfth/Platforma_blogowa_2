"""
Serwis autoryzacji
"""
from database import db
from models.user import User
import structlog

logger = structlog.get_logger(__name__)

class AuthService:
    """Serwis obsługujący logikę autoryzacji"""
    
    @staticmethod
    def register_user(username, email, password, role='USER'):
        """
        Rejestracja nowego użytkownika
        """
        # Sprawdź czy użytkownik już istnieje
        existing_user = User.find_by_username(username)
        if existing_user:
            raise ValueError(f'Nazwa użytkownika "{username}" jest już zajęta')
        
        existing_email = User.find_by_email(email)
        if existing_email:
            raise ValueError(f'Email "{email}" jest już zarejestrowany')
        
        # Utwórz nowego użytkownika
        user = User(username=username, email=email, password=password, role=role)
        
        db.session.add(user)
        db.session.commit()
        
        logger.info("Użytkownik zarejestrowany", user_id=user.id, username=username)
        return user
    
    @staticmethod
    def login_user(username, password):
        """
        Logowanie użytkownika
        """
        user = User.find_by_username(username)
        
        if not user:
            # Loguj próbę logowania z nieistniejącym użytkownikiem
            logger.warning("Próba logowania nieistniejącego użytkownika", username=username)
            return None
        
        if not user.is_active:
            logger.warning("Próba logowania deaktywowanego użytkownika", user_id=user.id)
            return None
        
        if not user.check_password(password):
            # Loguj nieudaną próbę logowania (bez hasła)
            logger.warning("Nieprawidłowe hasło dla użytkownika", username=username)
            return None
        
        logger.info("Użytkownik zalogowany", user_id=user.id, username=username)
        return user
    
    @staticmethod
    def logout_user(user_id, token_jti):
        """
        Wylogowanie użytkownika
        """
        from utils.jwt_utils import revoke_token
        revoke_token(token_jti)
        
        logger.info("Użytkownik wylogowany", user_id=user_id)
        return True
    
    @staticmethod
    def change_password(user_id, current_password, new_password):
        """
        Zmiana hasła użytkownika
        """
        user = User.find_by_id(user_id)
        
        if not user:
            raise ValueError('Użytkownik nie znaleziony')
        
        if not user.check_password(current_password):
            raise ValueError('Nieprawidłowe obecne hasło')
        
        user.set_password(new_password)
        db.session.commit()
        
        logger.info("Hasło zmienione", user_id=user_id)
        return user