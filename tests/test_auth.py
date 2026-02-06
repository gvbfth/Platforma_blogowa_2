"""
Testy autoryzacji
"""
import pytest
from app import create_app
from database import db
from config import TestingConfig
import json

class TestAuth:
    """Testy endpointów autoryzacji"""
    
    @pytest.fixture
    def app(self):
        """Fixture tworzący aplikację testową"""
        app = create_app(TestingConfig)
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Fixture tworzący klienta testowego"""
        return app.test_client()
    
    def test_register_success(self, client):
        """Test udanej rejestracji"""
        data = {
            'username': 'testuser',
            'email': 'test@example.org',  # Zmieniono na example.org
            'password': 'Test123!'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data['message'] == 'Użytkownik zarejestrowany pomyślnie'
        assert 'user' in json_data
        assert 'access_token' in json_data  # Teraz tokeny są w odpowiedzi JSON
        assert 'refresh_token' in json_data
        assert json_data['user']['username'] == 'testuser'
    
    def test_register_missing_data(self, client):
        """Test rejestracji z brakującymi danymi"""
        data = {
            'username': 'testuser'
            # Brak email i hasła
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
    
    def test_register_weak_password(self, client):
        """Test rejestracji ze słabym hasłem"""
        data = {
            'username': 'testuser',
            'email': 'test@example.org',  # Zmieniono na example.org
            'password': 'weak'
        }
        
        response = client.post('/api/auth/register',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        json_data = response.get_json()
        assert 'validation_errors' in json_data
    
    def test_login_success(self, client):
        """Test udanego logowania"""
        # Najpierw zarejestruj użytkownika
        register_data = {
            'username': 'testuser',
            'email': 'test@example.org',  # Zmieniono na example.org
            'password': 'Test123!'
        }
        
        client.post('/api/auth/register',
                   data=json.dumps(register_data),
                   content_type='application/json')
        
        # Teraz spróbuj się zalogować
        login_data = {
            'username': 'testuser',
            'password': 'Test123!'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert 'access_token' in json_data  # Tokeny są w JSON
        assert 'refresh_token' in json_data
    
    def test_login_wrong_password(self, client):
        """Test logowania z błędnym hasłem"""
        # Zarejestruj użytkownika
        register_data = {
            'username': 'testuser',
            'email': 'test@example.org',  # Zmieniono na example.org
            'password': 'Test123!'
        }
        
        client.post('/api/auth/register',
                   data=json.dumps(register_data),
                   content_type='application/json')
        
        # Spróbuj zalogować się z błędnym hasłem
        login_data = {
            'username': 'testuser',
            'password': 'WrongPassword123!'
        }
        
        response = client.post('/api/auth/login',
                             data=json.dumps(login_data),
                             content_type='application/json')
        
        assert response.status_code == 401
    
    def test_refresh_token(self, client):
        """Test odświeżania tokena"""
        # Zarejestruj i zaloguj użytkownika
        register_data = {
            'username': 'testuser',
            'email': 'test@example.org',  # Zmieniono na example.org
            'password': 'Test123!'
        }
        
        client.post('/api/auth/register',
                   data=json.dumps(register_data),
                   content_type='application/json')
        
        login_data = {
            'username': 'testuser',
            'password': 'Test123!'
        }
        
        login_response = client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        tokens = login_response.get_json()
        refresh_token = tokens['refresh_token']
        
        # Odśwież token - użyj refresh token z cookies lub nagłówka
        # W aktualnej implementacji tokeny są też w JSON, więc możemy użyć tego
        headers = {
            'Authorization': f'Bearer {refresh_token}',
            'Content-Type': 'application/json'
        }
        
        response = client.post('/api/auth/refresh',
                             headers=headers)
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert 'access_token' in json_data
        assert 'refresh_token' in json_data
    
    def test_protected_endpoint_without_token(self, client):
        """Test dostępu do chronionego endpointu bez tokena"""
        response = client.get('/api/auth/me')
        
        assert response.status_code == 401
    
    def test_protected_endpoint_with_token(self, client):
        """Test dostępu do chronionego endpointu z tokenem"""
        # Zarejestruj i zaloguj użytkownika
        register_data = {
            'username': 'testuser',
            'email': 'test@example.org',  # Zmieniono na example.org
            'password': 'Test123!'
        }
        
        client.post('/api/auth/register',
                   data=json.dumps(register_data),
                   content_type='application/json')
        
        login_data = {
            'username': 'testuser',
            'password': 'Test123!'
        }
        
        login_response = client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        tokens = login_response.get_json()
        access_token = tokens['access_token']
        
        # Spróbuj uzyskać dostęp do chronionego endpointu
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = client.get('/api/auth/me',
                            headers=headers)
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['username'] == 'testuser'
