"""
Serwis postów blogowych
"""
from database import db
from models.post import Post
from models.user import User
import structlog

logger = structlog.get_logger(__name__)

class PostService:
    """Serwis obsługujący logikę postów"""
    
    @staticmethod
    def get_public_posts(page=1, per_page=20):
        """
        Pobierz publiczne posty z paginacją
        """
        return Post.get_public_posts(page, per_page)
    
    @staticmethod
    def get_post_by_id(post_id):
        """
        Pobierz post po ID
        """
        return Post.find_by_id(post_id)
    
    @staticmethod
    def create_post(title, content, author_id, is_published=True):
        """
        Utwórz nowy post
        """
        user = User.find_by_id(author_id)
        if not user:
            raise ValueError('Użytkownik nie znaleziony')
        
        post = Post(
            title=title,
            content=content,
            author_id=author_id,
            is_published=is_published
        )
        
        db.session.add(post)
        db.session.commit()
        
        logger.info("Post utworzony", post_id=post.id, author_id=author_id)
        return post
    
    @staticmethod
    def update_post(post_id, title, content, is_published, user):
        """
        Aktualizuj istniejący post
        """
        post = Post.find_by_id(post_id)
        
        if not post:
            raise ValueError('Post nie znaleziony')
        
        # Sprawdź uprawnienia
        if not post.can_edit(user):
            logger.warning("Nieautoryzowana próba edycji posta", 
                          user_id=user.id, post_id=post_id, author_id=post.author_id)
            raise ValueError('Brak uprawnień do edycji tego posta')
        
        post.title = title
        post.content = content
        post.is_published = is_published
        
        db.session.commit()
        
        logger.info("Post zaktualizowany", post_id=post_id, user_id=user.id)
        return post
    
    @staticmethod
    def delete_post(post_id, user):
        """
        Usuń post
        """
        post = Post.find_by_id(post_id)
        
        if not post:
            raise ValueError('Post nie znaleziony')
        
        # Sprawdź uprawnienia
        if not post.can_delete(user):
            logger.warning("Nieautoryzowana próba usunięcia posta", 
                          user_id=user.id, post_id=post_id, author_id=post.author_id)
            raise ValueError('Brak uprawnień do usunięcia tego posta')
        
        db.session.delete(post)
        db.session.commit()
        
        logger.info("Post usunięty", post_id=post_id, user_id=user.id)
        return True
    
    @staticmethod
    def get_user_posts(user_id, page=1, per_page=20):
        """
        Pobierz posty użytkownika
        """
        return Post.get_user_posts(user_id, page, per_page)
    
    @staticmethod
    def get_all_posts_admin(page=1, per_page=20, user_id=None):
        """
        Pobierz wszystkie posty (dla admina)
        """
        query = Post.query
        
        if user_id:
            query = query.filter_by(author_id=user_id)
        
        return query.order_by(Post.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)