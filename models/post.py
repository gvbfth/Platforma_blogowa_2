"""
Model postu blogowego 
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import validates
from database import db
import structlog

logger = structlog.get_logger(__name__)

class Post(db.Model):
    """Model postu blogowego"""
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False, index=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    is_published = Column(db.Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relacja jest zdefiniowana w modelu User przez backref='author'
    # Nie trzeba jej definiować tutaj ponownie
    
    def __init__(self, title, content, author_id, is_published=True):
        """Inicjalizacja postu z walidacją"""
        self.title = title
        self.content = content
        self.author_id = author_id
        self.is_published = is_published
        logger.info("Utworzono nowy post", title=title[:50], author_id=author_id)
    
    @validates('title')
    def validate_title(self, key, title):
        """Walidacja tytułu"""
        if not title or len(title.strip()) < 3:
            raise ValueError('Tytuł musi mieć co najmniej 3 znaki')
        if len(title) > 200:
            raise ValueError('Tytuł może mieć maksymalnie 200 znaków')
        return title.strip()
    
    @validates('content')
    def validate_content(self, key, content):
        """Walidacja treści"""
        if not content or len(content.strip()) < 10:
            raise ValueError('Treść musi mieć co najmniej 10 znaków')
        if len(content) > 10000:
            raise ValueError('Treść może mieć maksymalnie 10000 znaków')
        
        # Basic XSS protection - remove script tags
        import re
        content = re.sub(r'<script.*?>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'on\w+=".*?"', '', content)
        
        return content.strip()
    
    @validates('author_id')
    def validate_author_id(self, key, author_id):
        """Walidacja autora"""
        if not author_id or author_id <= 0:
            raise ValueError('Nieprawidłowy identyfikator autora')
        return author_id
    
    def to_dict(self, include_author=False):
        """Konwersja do słownika"""
        data = {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author_id': self.author_id,
            'is_published': self.is_published,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_author and self.author:  # self.author jest dostępne przez backref z User
            data['author'] = {
                'id': self.author.id,
                'username': self.author.username
            }
        
        return data
    
    @classmethod
    def get_public_posts(cls, page=1, per_page=20):
        """Pobierz publiczne posty z paginacją"""
        return cls.query.filter_by(is_published=True)\
            .order_by(cls.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
    
    @classmethod
    def get_user_posts(cls, user_id, page=1, per_page=20):
        """Pobierz posty użytkownika"""
        return cls.query.filter_by(author_id=user_id)\
            .order_by(cls.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
    
    @classmethod
    def find_by_id(cls, post_id):
        """Znajdź post po ID"""
        return cls.query.get(post_id)
    
    def can_edit(self, user):
        """Sprawdź czy użytkownik może edytować post"""
        return user and (user.id == self.author_id or user.role in ['ADMIN', 'MODERATOR'])
    
    def can_delete(self, user):
        """Sprawdź czy użytkownik może usunąć post"""
        return self.can_edit(user)