"""
Model komentarza
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import validates
from database import db
import structlog

logger = structlog.get_logger(__name__)

class Comment(db.Model):
    """Model komentarza pod postem"""
    __tablename__ = 'comments'
    
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False, index=True)
    #created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def __init__(self, content, author_id, post_id):
        """Inicjalizacja komentarza"""
        self.content = content
        self.author_id = author_id
        self.post_id = post_id
        logger.info("Utworzono nowy komentarz", 
                   post_id=post_id, 
                   author_id=author_id)
    
    @validates('content')
    def validate_content(self, key, content):
        """Walidacja treści komentarza"""
        if not content or len(content.strip()) < 2:
            raise ValueError('Komentarz musi mieć co najmniej 2 znaki')
        if len(content) > 1000:
            raise ValueError('Komentarz może mieć maksymalnie 1000 znaków')
        
        # Basic XSS protection
        import re
        content = re.sub(r'<script.*?>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'on\w+=".*?"', '', content)
        
        return content.strip()
    
    def to_dict(self):
        """Konwersja do słownika"""
        from models.user import User
        author = User.find_by_id(self.author_id)
        
        return {
            'id': self.id,
            'content': self.content,
            'author_id': self.author_id,
            'author_username': author.username if author else None,
            'post_id': self.post_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }