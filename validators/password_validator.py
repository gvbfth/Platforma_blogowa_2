"""
Walidator hasła
"""
import re
import structlog

logger = structlog.get_logger(__name__)

class PasswordValidationError(Exception):
    """Wyjątek walidacji hasła"""
    def __init__(self, message, validation_errors=None):
        super().__init__(message)
        self.validation_errors = validation_errors or []

def validate_password(password):
    """
    Walidacja hasła zgodnie z wymaganiami
    - Minimum 8 znaków
    - Co najmniej jedna wielka litera
    - Co najmniej jedna mała litera
    - Co najmniej jedna cyfra
    - Co najmniej jeden znak specjalny
    """
    if not password:
        raise PasswordValidationError("Hasło jest wymagane")
    
    errors = []
    
    # Minimum 8 znaków
    if len(password) < 8:
        errors.append("Hasło musi mieć co najmniej 8 znaków")
    
    # Co najmniej jedna wielka litera
    if not re.search(r'[A-Z]', password):
        errors.append("Hasło musi zawierać co najmniej jedną wielką literę")
    
    # Co najmniej jedna mała litera
    if not re.search(r'[a-z]', password):
        errors.append("Hasło musi zawierać co najmniej jedną małą literę")
    
    # Co najmniej jedna cyfra
    if not re.search(r'\d', password):
        errors.append("Hasło musi zawierać co najmniej jedną cyfrę")
    
    # Co najmniej jeden znak specjalny
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Hasło musi zawierać co najmniej jeden znak specjalny (!@#$%^&*...)")
    
    # Sprawdź czy hasło nie jest zbyt proste
    common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein']
    if password.lower() in common_passwords:
        errors.append("Hasło jest zbyt proste")
    
    if errors:
        logger.warning("Nieudana walidacja hasła", errors=errors)
        raise PasswordValidationError("Hasło nie spełnia wymagań bezpieczeństwa", errors)
    
    logger.debug("Hasło zwalidowane pomyślnie")
    return True

def validate_password_strength(password):
    """
    Ocena siły hasła
    Zwraca wynik 0-100
    """
    score = 0
    
    # Długość
    if len(password) >= 8:
        score += 20
    if len(password) >= 12:
        score += 10
    if len(password) >= 16:
        score += 10
    
    # Różnorodność znaków
    if re.search(r'[A-Z]', password):
        score += 15
    if re.search(r'[a-z]', password):
        score += 15
    if re.search(r'\d', password):
        score += 15
    if re.search(r'[^A-Za-z0-9]', password):
        score += 15
    
    # Unikalność
    if len(set(password)) >= len(password) * 0.7:
        score += 10
    
    return min(score, 100)