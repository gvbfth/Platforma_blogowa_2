# init.py
import sys
sys.path.insert(0, '.')
from app import create_app
from database import db
from models.user import User

app = create_app()
with app.app_context():
    db.create_all()
    print('Database tables created')
    
    admin = User.find_by_username('admin')
    if not admin:
        admin_user = User(
            username='admin',
            email='admin@blog.platform',
            password='Admin123!',
            role='ADMIN'
        )
        db.session.add(admin_user)
        db.session.commit()
        print('Admin created')
    
    print('Database ready')