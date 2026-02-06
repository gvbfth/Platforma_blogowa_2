"""
Plik na rozszerzenia Flask, które muszą być dostępne w różnych częściach aplikacji
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

#Obiekt limiter bez aplikacji (zostanie zainicjalizowany później)
limiter = Limiter(key_func=get_remote_address)