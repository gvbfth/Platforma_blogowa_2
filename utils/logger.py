"""
Konfiguracja logowania
"""
import os
import logging
import structlog
from datetime import datetime

def setup_logging(app):
    """
    Konfiguracja systemu logowania
    """
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
    
    # Konfiguracja structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()  # JSON dla łatwej integracji
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Konfiguracja standardowego logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ustaw poziom logowania dla bibliotek zewnętrznych
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # Utwórz katalog logów jeśli nie istnieje
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # File handler dla logów aplikacji
    log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m")}.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Dodaj handler do głównego logera
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    
    # Security log file (oddzielny dla zdarzeń bezpieczeństwa)
    security_log_file = os.path.join(log_dir, f'security_{datetime.now().strftime("%Y%m")}.log')
    security_handler = logging.FileHandler(security_log_file)
    security_handler.setLevel(logging.WARNING)
    security_handler.setFormatter(logging.Formatter(
        '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
    ))
    
    # Filtrowanie logów bezpieczeństwa
    class SecurityFilter(logging.Filter):
        def filter(self, record):
            return 'SECURITY' in record.getMessage() or \
                   'auth' in record.name or \
                   'security' in record.name
    
    security_handler.addFilter(SecurityFilter())
    root_logger.addHandler(security_handler)
    
    # Log startup
    logger = structlog.get_logger(__name__)
    logger.info("Logowanie skonfigurowane", 
                log_level=app.config.get('LOG_LEVEL'),
                log_file=log_file,
                security_log_file=security_log_file)

def log_security_event(event_type, **kwargs):
    """
    Logowanie zdarzeń bezpieczeństwa
    """
    logger = structlog.get_logger('security')
    
    # Usuń wrażliwe dane z kwargs
    safe_kwargs = {}
    for key, value in kwargs.items():
        if isinstance(value, str):
            # Maskuj wrażliwe dane
            if 'password' in key.lower() or 'token' in key.lower():
                safe_kwargs[key] = '***MASKED***'
            elif 'email' in key.lower():
                # Zachowaj domenę emaila, maskuj nazwę użytkownika
                if '@' in value:
                    user, domain = value.split('@', 1)
                    safe_kwargs[key] = f'{user[0]}***@{domain}'
                else:
                    safe_kwargs[key] = '***MASKED***'
            else:
                safe_kwargs[key] = value
        else:
            safe_kwargs[key] = value
    
    if event_type == 'login_failed':
        logger.warning("Nieudana próba logowania", event='login_failed', **safe_kwargs)
    elif event_type == 'login_success':
        logger.info("Udane logowanie", event='login_success', **safe_kwargs)
    elif event_type == 'unauthorized_access':
        logger.warning("Nieautoryzowany dostęp", event='unauthorized_access', **safe_kwargs)
    elif event_type == 'rate_limit_exceeded':
        logger.warning("Przekroczony limit żądań", event='rate_limit_exceeded', **safe_kwargs)
    elif event_type == 'suspicious_activity':
        logger.warning("Podejrzana aktywność", event='suspicious_activity', **safe_kwargs)
    else:
        logger.info(f"Zdarzenie bezpieczeństwa: {event_type}", event=event_type, **safe_kwargs)

def log_http_request(request, user_id=None):
    """
    Logowanie żądań HTTP (bez wrażliwych danych)
    """
    logger = structlog.get_logger('http')
    
    log_data = {
        'method': request.method,
        'path': request.path,
        'remote_addr': request.remote_addr,
        'user_agent': request.user_agent.string[:100] if request.user_agent else None,
    }
    
    if user_id:
        log_data['user_id'] = user_id
    
    # Nie loguj ciał żądań POST/PUT (mogą zawierać hasła)
    if request.method in ['POST', 'PUT']:
        log_data['content_type'] = request.content_type
        log_data['content_length'] = request.content_length
    
    logger.info("Żądanie HTTP", **log_data)