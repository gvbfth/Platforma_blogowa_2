"""
Konfiguracja bazy danych SQLAlchemy
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Base class dla wszystkich modeli"""
    pass

db = SQLAlchemy(model_class=Base)