"""
Serwis bezpieczeństwa
"""
import structlog

logger = structlog.get_logger(__name__)

class SecurityService:
    """Serwis obsługujący logikę bezpieczeństwa"""
    
    @staticmethod
    def log_security_event(event_type, ip_address, user_id=None, details=None):
        """
        Logowanie zdarzeń bezpieczeństwa
        """
        log_data = {
            'event_type': event_type,
            'ip_address': ip_address,
            'user_id': user_id,
            'details': details
        }
        
        if event_type == 'failed_login':
            logger.warning("Nieudana próba logowania", **log_data)
        elif event_type == 'brute_force_attempt':
            logger.error("Wykryto próbę ataku brute force", **log_data)
        elif event_type == 'suspicious_activity':
            logger.warning("Podejrzana aktywność", **log_data)
        else:
            logger.info(f"Zdarzenie bezpieczeństwa: {event_type}", **log_data)
    
    @staticmethod
    def check_ip_reputation(ip_address):
        """
        Sprawdź reputację adresu IP (prosta implementacja)
        """
        # W rzeczywistej aplikacji można dodać integrację z zewnętrznymi serwisami
        # Tutaj tylko logika przykładowa
        return {
            'ip': ip_address,
            'is_suspicious': False,
            'risk_level': 'low'
        }