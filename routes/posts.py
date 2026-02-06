"""
Routing dla postów blogowych
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from flask_limiter import Limiter

from services.post_service import PostService
from validators.input_validator import validate_post_title, validate_post_content, ValidationError
from utils.error_handlers import handle_validation_error
from utils.jwt_utils import get_current_user, owner_or_admin_required
from models.post import Post
import structlog

logger = structlog.get_logger(__name__)

posts_bp = Blueprint('posts', __name__)

@posts_bp.route('', methods=['GET'])
def get_posts():
    """
    Pobierz wszystkie publiczne posty
    GET /api/posts
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        posts = PostService.get_public_posts(page, per_page)
        
        return jsonify({
            'posts': [post.to_dict(include_author=True) for post in posts.items],
            'page': posts.page,
            'per_page': posts.per_page,
            'total': posts.total,
            'pages': posts.pages
        }), 200
        
    except Exception as e:
        logger.error("Błąd pobierania postów", error=str(e))
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Wystąpił błąd podczas pobierania postów'
        }), 500

@posts_bp.route('/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """
    Pobierz pojedynczy post
    GET /api/posts/<id>
    """
    try:
        post = PostService.get_post_by_id(post_id)
        
        if not post:
            return jsonify({
                'error': 'Not Found',
                'message': 'Post nie znaleziony'
            }), 404
        
        if not post.is_published:
            # Sprawdź czy użytkownik jest autorem lub adminem
            user = get_current_user()
            if not user or (user.id != post.author_id and user.role != 'ADMIN'):
                return jsonify({
                    'error': 'Forbidden',
                    'message': 'Brak uprawnień do tego posta'
                }), 403
        
        return jsonify(post.to_dict(include_author=True)), 200
        
    except Exception as e:
        logger.error("Błąd pobierania posta", error=str(e), post_id=post_id)
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Wystąpił błąd podczas pobierania posta'
        }), 500

@posts_bp.route('', methods=['POST'])
@jwt_required()
def create_post():
    """
    Utwórz nowy post
    POST /api/posts
    """
    try:
        user = get_current_user()
        
        if not user:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Wymagane uwierzytelnienie'
            }), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Brak danych JSON'
            }), 400
        
        # Walidacja danych
        title = validate_post_title(data.get('title'))
        content = validate_post_content(data.get('content'))
        is_published = data.get('is_published', True)
        
        # Utwórz post
        post = PostService.create_post(
            title=title,
            content=content,
            author_id=user.id,
            is_published=is_published
        )
        
        logger.info("Nowy post utworzony", post_id=post.id, author_id=user.id)
        
        return jsonify({
            'message': 'Post utworzony pomyślnie',
            'post': post.to_dict()
        }), 201
        
    except ValidationError as e:
        return handle_validation_error(e)
    except Exception as e:
        logger.error("Błąd tworzenia posta", error=str(e))
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Wystąpił błąd podczas tworzenia posta'
        }), 500

@posts_bp.route('/<int:post_id>', methods=['PUT'])
@jwt_required()
@owner_or_admin_required(Post)
def update_post(post_id):
    """
    Aktualizuj post (tylko autor lub admin)
    PUT /api/posts/<id>
    """
    try:
        user = get_current_user()
        post = PostService.get_post_by_id(post_id)
        
        if not post:
            return jsonify({
                'error': 'Not Found',
                'message': 'Post nie znaleziony'
            }), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Brak danych JSON'
            }), 400
        
        # Walidacja danych
        title = validate_post_title(data.get('title', post.title))
        content = validate_post_content(data.get('content', post.content))
        is_published = data.get('is_published', post.is_published)
        
        # Aktualizuj post
        updated_post = PostService.update_post(
            post_id=post_id,
            title=title,
            content=content,
            is_published=is_published,
            user=user
        )
        
        logger.info("Post zaktualizowany", post_id=post_id, user_id=user.id)
        
        return jsonify({
            'message': 'Post zaktualizowany pomyślnie',
            'post': updated_post.to_dict(include_author=True)
        }), 200
        
    except ValidationError as e:
        return handle_validation_error(e)
    except ValueError as e:
        return jsonify({
            'error': 'Forbidden',
            'message': str(e)
        }), 403
    except Exception as e:
        logger.error("Błąd aktualizacji posta", error=str(e), post_id=post_id)
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Wystąpił błąd podczas aktualizacji posta'
        }), 500

@posts_bp.route('/<int:post_id>', methods=['DELETE'])
@jwt_required()
@owner_or_admin_required(Post)
def delete_post(post_id):
    """
    Usuń post (tylko autor lub admin)
    DELETE /api/posts/<id>
    """
    try:
        user = get_current_user()
        
        PostService.delete_post(post_id, user)
        
        logger.info("Post usunięty", post_id=post_id, user_id=user.id)
        
        return jsonify({
            'message': 'Post usunięty pomyślnie'
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'Forbidden',
            'message': str(e)
        }), 403
    except Exception as e:
        logger.error("Błąd usuwania posta", error=str(e), post_id=post_id)
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Wystąpił błąd podczas usuwania posta'
        }), 500

@posts_bp.route('/my', methods=['GET'])
@jwt_required()
def get_my_posts():
    """
    Pobierz posty zalogowanego użytkownika
    GET /api/posts/my
    """
    try:
        user = get_current_user()
        
        if not user:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Wymagane uwierzytelnienie'
            }), 401
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        posts = PostService.get_user_posts(user.id, page, per_page)
        
        return jsonify({
            'posts': [post.to_dict() for post in posts.items],
            'page': posts.page,
            'per_page': posts.per_page,
            'total': posts.total,
            'pages': posts.pages
        }), 200
        
    except Exception as e:
        logger.error("Błąd pobierania postów użytkownika", error=str(e), user_id=user.id if user else None)
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Wystąpił błąd podczas pobierania postów'
        }), 500
    
@posts_bp.route('/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(post_id):
    """
    Dodaj komentarz do posta (Lab dodatkowe)
    POST /api/posts/<id>/comments
    """
    try:
        user = get_current_user()
        
        if not user:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Wymagane uwierzytelnienie'
            }), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Brak danych JSON'
            }), 400
        
        content = data.get('content')
        if not content or len(content.strip()) < 2:
            return jsonify({
                'error': 'Bad Request',
                'message': 'Komentarz musi mieć co najmniej 2 znaki'
            }), 400
        
        # Sprawdź czy post istnieje
        post = PostService.get_post_by_id(post_id)
        if not post:
            return jsonify({
                'error': 'Not Found',
                'message': 'Post nie znaleziony'
            }), 404
        
        # Utwórz komentarz w bazie (trzeba dodać model Comment)
        from models.comment import Comment
        from database import db
        
        comment = Comment(
            content=content.strip(),
            author_id=user.id,
            post_id=post_id
        )
        
        db.session.add(comment)
        db.session.commit()
        
        logger.info("Komentarz dodany", 
                   comment_id=comment.id, 
                   post_id=post_id, 
                   user_id=user.id)
        
        return jsonify({
            'message': 'Komentarz dodany pomyślnie',
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'author': user.username,
                'created_at': comment.created_at.isoformat() if comment.created_at else None
            }
        }), 201
        
    except Exception as e:
        logger.error("Błąd dodawania komentarza", error=str(e), post_id=post_id)
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Wystąpił błąd podczas dodawania komentarza'
        }), 500


@posts_bp.route('/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """Pobierz komentarze dla posta"""
    try:
        from models.comment import Comment
        comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.asc()).all()
        
        result = []
        for comment in comments:
            from models.user import User
            author = User.query.get(comment.author_id)
            
            result.append({
                'id': comment.id,
                'content': comment.content,
                'author_username': author.username if author else 'Unknown',
                'created_at': comment.created_at.isoformat() if comment.created_at else None
            })
        
        return jsonify({'comments': result}), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500