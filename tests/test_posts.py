"""
Testy postów blogowych
"""
import pytest
from app import create_app
from database import db
from config import TestingConfig
import json

class TestPosts:
    """Testy endpointów postów"""
    
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
    
    @pytest.fixture
    def auth_headers(self, client):
        """Fixture tworzący nagłówki autoryzacji"""
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
        
        return {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def test_create_post_success(self, client, auth_headers):
        """Test tworzenia posta"""
        data = {
            'title': 'Testowy post',
            'content': 'To jest treść testowego posta',
            'is_published': True
        }
        
        response = client.post('/api/posts',
                             data=json.dumps(data),
                             headers=auth_headers)
        
        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data['message'] == 'Post utworzony pomyślnie'
        assert 'post' in json_data
        assert json_data['post']['title'] == 'Testowy post'
    
    def test_create_post_missing_title(self, client, auth_headers):
        """Test tworzenia posta bez tytułu"""
        data = {
            'content': 'To jest treść testowego posta',
            'is_published': True
        }
        
        response = client.post('/api/posts',
                             data=json.dumps(data),
                             headers=auth_headers)
        
        assert response.status_code == 400
    
    def test_get_public_posts(self, client):
        """Test pobierania publicznych postów"""
        response = client.get('/api/posts')
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert 'posts' in json_data
        assert 'page' in json_data
        assert 'total' in json_data
    
    def test_get_single_post(self, client, auth_headers):
        """Test pobierania pojedynczego posta"""
        # Najpierw utwórz post
        create_data = {
            'title': 'Testowy post do pobrania',
            'content': 'Treść posta do pobrania',
            'is_published': True
        }
        
        create_response = client.post('/api/posts',
                                    data=json.dumps(create_data),
                                    headers=auth_headers)
        
        post_id = create_response.get_json()['post']['id']
        
        # Teraz pobierz post
        response = client.get(f'/api/posts/{post_id}')
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['title'] == 'Testowy post do pobrania'
        assert json_data['content'] == 'Treść posta do pobrania'
    
    def test_update_post(self, client, auth_headers):
        """Test aktualizacji posta"""
        # Utwórz post
        create_data = {
            'title': 'Stary tytuł',
            'content': 'Stara treść',
            'is_published': True
        }
        
        create_response = client.post('/api/posts',
                                    data=json.dumps(create_data),
                                    headers=auth_headers)
        
        post_id = create_response.get_json()['post']['id']
        
        # Zaktualizuj post
        update_data = {
            'title': 'Nowy tytuł',
            'content': 'Nowa treść',
            'is_published': False
        }
        
        response = client.put(f'/api/posts/{post_id}',
                            data=json.dumps(update_data),
                            headers=auth_headers)
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['post']['title'] == 'Nowy tytuł'
        assert json_data['post']['content'] == 'Nowa treść'
        assert json_data['post']['is_published'] == False
    
    def test_delete_post(self, client, auth_headers):
        """Test usuwania posta"""
        # Utwórz post
        create_data = {
            'title': 'Post do usunięcia',
            'content': 'Treść posta do usunięcia',
            'is_published': True
        }
        
        create_response = client.post('/api/posts',
                                    data=json.dumps(create_data),
                                    headers=auth_headers)
        
        post_id = create_response.get_json()['post']['id']
        
        # Usuń post
        response = client.delete(f'/api/posts/{post_id}',
                               headers=auth_headers)
        
        assert response.status_code == 200
        
        # Sprawdź czy post został usunięty
        get_response = client.get(f'/api/posts/{post_id}')
        assert get_response.status_code == 404
    
    def test_get_my_posts(self, client, auth_headers):
        """Test pobierania postów zalogowanego użytkownika"""
        # Utwórz kilka postów
        for i in range(3):
            data = {
                'title': f'Post {i}',
                'content': f'Treść posta {i}',
                'is_published': True
            }
            
            client.post('/api/posts',
                       data=json.dumps(data),
                       headers=auth_headers)
        
        # Pobierz posty użytkownika
        response = client.get('/api/posts/my',
                            headers=auth_headers)
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert len(json_data['posts']) == 3
