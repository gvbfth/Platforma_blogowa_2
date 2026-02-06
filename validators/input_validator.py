"""
Walidator danych wejściowych
"""
import re
from email_validator import validate_email as email_validator, EmailNotValidError
import structlog

logger = structlog.get_logger(__name__)

class ValidationError(Exception):
    """Wyjątek walidacji danych wejściowych"""
    def __init__(self, message, field=None, value=None):
        super().__init__(message)
        self.field = field
        self.value = value
        logger.warning("Błąd walidacji", field=field, value=value, message=message)

def validate_email(email):
    """Walidacja emaila"""
    try:
        # Dla testów wyłączamy check_deliverability
        valid = email_validator(email, check_deliverability=False)
        return valid.email
    except EmailNotValidError as e:
        raise ValidationError(str(e), 'email', email)

def validate_username(username):
    """Walidacja nazwy użytkownika"""
    if not username:
        raise ValidationError("Nazwa użytkownika jest wymagana", 'username', username)
    
    if len(username) < 3:
        raise ValidationError("Nazwa użytkownika musi mieć co najmniej 3 znaki", 'username', username)
    
    if len(username) > 50:
        raise ValidationError("Nazwa użytkownika może mieć maksymalnie 50 znaków", 'username', username)
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise ValidationError("Nazwa użytkownika może zawierać tylko litery, cyfry i podkreślenia", 'username', username)
    
    return username.strip()

def validate_post_title(title):
    """Walidacja tytułu postu"""
    if not title:
        raise ValidationError("Tytuł jest wymagany", 'title', title)
    
    if len(title) < 3:
        raise ValidationError("Tytuł musi mieć co najmniej 3 znaki", 'title', title)
    
    if len(title) > 200:
        raise ValidationError("Tytuł może mieć maksymalnie 200 znaków", 'title', title)
    
    # Basic XSS protection
    if '<script>' in title.lower():
        raise ValidationError("Tytuł zawiera niedozwolone znaczniki", 'title', title)
    
    return title.strip()

def validate_post_content(content):
    """Walidacja treści postu"""
    if not content:
        raise ValidationError("Treść jest wymagana", 'content', content)
    
    if len(content) < 10:
        raise ValidationError("Treść musi mieć co najmniej 10 znaków", 'content', content)
    
    if len(content) > 10000:
        raise ValidationError("Treść może mieć maksymalnie 10000 znaków", 'content', content)
    
    return content.strip()

def sanitize_input(input_string):
    """Sanityzacja danych wejściowych (ochrona przed XSS)"""
    if not input_string:
        return input_string
    
    import html
    # Escapowanie HTML
    sanitized = html.escape(input_string)
    
    # Usuwanie niebezpiecznych znaczników
    import re
    sanitized = re.sub(r'<script.*?>.*?</script>', '', sanitized, flags=re.DOTALL | re.IGNORECASE)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'on\w+=".*?"', '', sanitized)
    sanitized = re.sub(r'on\w+=\'.*?\'', '', sanitized)
    
    return sanitized