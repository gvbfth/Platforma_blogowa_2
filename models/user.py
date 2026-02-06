"""
Model użytkownika 
"""
import re
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import validates
from database import db
from flask_bcrypt import generate_password_hash, check_password_hash
import structlog

logger = structlog.get_logger(__name__)

class User(db.Model):
    """Model użytkownika"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default='USER', nullable=False)  # USER, ADMIN
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relacje
    posts = db.relationship('Post', backref='author', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, username, email, password, role='USER'):
        """Inicjalizacja użytkownika z walidacją"""
        self.username = username
        self.email = email
        self.set_password(password)  # Automatyczne hashowanie
        self.role = role
        logger.info("Utworzono nowego użytkownika", username=username, role=role)
    
    def set_password(self, password):
        """Hashowanie hasła"""
        from validators.password_validator import validate_password
        # Walidacja hasła przed hashowaniem
        validate_password(password)
        self.password_hash = generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Sprawdzenie hasła"""
        return check_password_hash(self.password_hash, password)
    
    @validates('username')
    def validate_username(self, key, username):
        """Walidacja nazwy użytkownika"""
        if not username or len(username.strip()) < 3:
            raise ValueError('Nazwa użytkownika musi mieć co najmniej 3 znaki')
        if len(username) > 50:
            raise ValueError('Nazwa użytkownika może mieć maksymalnie 50 znaków')
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValueError('Nazwa użytkownika może zawierać tylko litery, cyfry i podkreślenia')
        return username.strip()
    
    @validates('email')
    def validate_email(self, key, email):
        """Walidacja emaila"""
        if not email or '@' not in email:
            raise ValueError('Nieprawidłowy format email')
        if len(email) > 100:
            raise ValueError('Email może mieć maksymalnie 100 znaków')
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError('Nieprawidłowy format email')
        return email.strip().lower()
    
    @validates('role')
    def validate_role(self, key, role):
        """Walidacja roli"""
        allowed_roles = ['USER', 'ADMIN', 'MODERATOR']
        if role not in allowed_roles:
            raise ValueError(f'Rola musi być jedną z: {", ".join(allowed_roles)}')
        return role
    
    def to_dict(self):
        """Konwersja do słownika (bez wrażliwych danych)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_auth_dict(self):
        """Konwersja do słownika dla odpowiedzi auth (z tokenami)"""
        """from utils.jwt_utils import create_access_token, create_refresh_token
        
        data = self.to_dict()
        data.update({
            'access_token': create_access_token(identity=self.id, user=self),
            'refresh_token': create_refresh_token(identity=self.id),
            'token_type': 'Bearer'
        })
        return data"""
        """Konwersja do słownika dla odpowiedzi auth (BEZ tokenów - teraz w cookies)"""
        # Usunięto tworzenie tokenów - teraz są w cookies
        return self.to_dict()
    
    @classmethod
    def find_by_username(cls, username):
        """Znajdź użytkownika po nazwie"""
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def find_by_email(cls, email):
        """Znajdź użytkownika po emailu"""
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def find_by_id(cls, user_id):
        """Znajdź użytkownika po ID"""
        return cls.query.get(user_id)