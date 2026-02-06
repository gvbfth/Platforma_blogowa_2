"""
Routing dla administratora (Lab 11-12)
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from services.user_service import UserService
from utils.jwt_utils import admin_required, get_current_user
import structlog

logger = structlog.get_logger(__name__)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    """
    Pobierz wszystkich użytkowników (tylko admin)
    GET /api/admin/users
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        users = UserService.get_all_users(page, per_page)
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'page': users.page,
            'per_page': users.per_page,
            'total': users.total,
            'pages': users.pages
        }), 200
        
    except Exception as e:
        logger.error("Błąd pobierania użytkowników", error=str(e))
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Wystąpił błąd podczas pobierania użytkowników'
        }), 500

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """
    Pobierz szczegóły użytkownika (tylko admin)
    GET /api/admin/users/<id>
    """
    try:
        user = UserService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({
                'error': 'Not Found',
                'message': 'Użytkownik nie znaleziony'
            }), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        logger.error("Błąd pobierania użytkownika", error=str(e), user_id=user_id)
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Wystąpił błąd podczas pobierania użytkownika'
        }), 500

@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """
    Aktywuj/deaktywuj użytkownika (tylko admin)
    POST /api/admin/users/<id>/toggle
    """
    try:
        current_admin = get_current_user()
        
        if current_admin.id == user_id:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Nie możesz deaktywować własnego konta'
            }), 400
        
        user = UserService.toggle_user_status(user_id)
        
        action = "aktywowany" if user.is_active else "deaktywowany"
        logger.info(f"Użytkownik {action}", user_id=user_id, admin_id=current_admin.id)
        
        return jsonify({
            'message': f'Użytkownik {action} pomyślnie',
            'user': user.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'Not Found',
            'message': str(e)
        }), 404
    except Exception as e:
        logger.error("Błąd zmiany statusu użytkownika", error=str(e), user_id=user_id)
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Wystąpił błąd podczas zmiany statusu użytkownika'
        }), 500

@admin_bp.route('/posts', methods=['GET'])
@admin_required
def get_all_posts_admin():
    """
    Pobierz wszystkie posty (tylko admin)
    GET /api/admin/posts
    """
    try:
        from services.post_service import PostService
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        user_id = request.args.get('user_id', type=int)
        
        posts = PostService.get_all_posts_admin(page, per_page, user_id)
        
        return jsonify({
            'posts': [post.to_dict(include_author=True) for post in posts.items],
            'page': posts.page,
            'per_page': posts.per_page,
            'total': posts.total,
            'pages': posts.pages
        }), 200
        
    except Exception as e:
        logger.error("Błąd pobierania postów (admin)", error=str(e))
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Wystąpił błąd podczas pobierania postów'
        }), 500