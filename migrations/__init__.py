"""
Migracje bazy danych (analogiczne do Flyway)
"""
import os
from datetime import datetime
from database import db
from models.comment import Comment
import structlog

logger = structlog.get_logger(__name__)

def run_migrations():
    """
    Uruchom migracje bazy danych
    """
    try:
        # Utwórz tabele
        from models.user import User
        from models.post import Post
        from models.comment import Comment

        db.create_all()
        
        # Sprawdź czy istnieje admin
        admin = User.find_by_username('admin')
        if not admin:
            # Utwórz domyślnego admina
            admin_user = User(
                username='admin',
                email='admin@blog.platform',
                password='Admin123!',  # Hasło do zmiany po pierwszym logowaniu
                role='ADMIN'
            )
            db.session.add(admin_user)
            db.session.commit()
            
            logger.info("Utworzono domyślnego użytkownika admin", user_id=admin_user.id)
        
        logger.info("Migracje zakończone pomyślnie")
        
    except Exception as e:
        logger.error("Błąd migracji", error=str(e))
        raise