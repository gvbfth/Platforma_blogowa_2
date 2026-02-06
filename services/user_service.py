"""
Serwis użytkowników
"""
from database import db
from models.user import User
import structlog

logger = structlog.get_logger(__name__)

class UserService:
    """Serwis obsługujący logikę użytkowników"""
    
    @staticmethod
    def get_all_users(page=1, per_page=20):
        """
        Pobierz wszystkich użytkowników z paginacją
        """
        return User.query.order_by(User.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_user_by_id(user_id):
        """
        Pobierz użytkownika po ID
        """
        return User.find_by_id(user_id)
    
    @staticmethod
    def toggle_user_status(user_id):
        """
        Przełącz status użytkownika (aktywny/nieaktywny)
        """
        user = User.find_by_id(user_id)
        
        if not user:
            raise ValueError('Użytkownik nie znaleziony')
        
        user.is_active = not user.is_active
        db.session.commit()
        
        logger.info("Status użytkownika zmieniony", 
                   user_id=user_id, is_active=user.is_active)
        return user
    
    @staticmethod
    def update_user_role(user_id, new_role):
        """
        Aktualizuj rolę użytkownika
        """
        user = User.find_by_id(user_id)
        
        if not user:
            raise ValueError('Użytkownik nie znaleziony')
        
        user.role = new_role
        db.session.commit()
        
        logger.info("Rola użytkownika zaktualizowana", 
                   user_id=user_id, new_role=new_role)
        return user
    
    @staticmethod
    def search_users(query, page=1, per_page=20):
        """
        Wyszukaj użytkowników
        """
        search_query = f"%{query}%"
        
        return User.query.filter(
            (User.username.ilike(search_query)) |
            (User.email.ilike(search_query))
        ).order_by(User.created_at.desc())\
         .paginate(page=page, per_page=per_page, error_out=False)