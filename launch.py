import os
import sys
import subprocess

def check_and_install():
    """Sprawdź i zainstaluj jeśli potrzeba"""
    
    # Sprawdź czy venv istnieje
    if not os.path.exists(".venv"):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", ".venv"])
    
    # Ścieżki
    if sys.platform == "win32":
        pip = ".venv\\Scripts\\pip.exe"
        python = ".venv\\Scripts\\python.exe"
    else:
        pip = ".venv/bin/pip"
        python = ".venv/bin/python"
    
    # Sprawdź czy Flask jest zainstalowany
    try:
        subprocess.run([python, "-c", "import flask"], check=True, capture_output=True)
    except:
        print("Installing dependencies...")
        packages = ["Flask", "Flask-SQLAlchemy", "Flask-Migrate", "Flask-CORS", 
                   "Flask-Bcrypt", "Flask-JWT-Extended", "python-dotenv", 
                   "PyJWT", "structlog"]
        subprocess.run([pip, "install"] + packages)
    
    # Utwórz .env jeśli nie istnieje
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("FLASK_APP=app.py\nFLASK_ENV=development\nDATABASE_URL=sqlite:///blog.db\n")
    
    # Uruchom migracje
    if not os.path.exists("blog.db"):
        print("Creating database...")
        subprocess.run([python, "-c", """
import sys
sys.path.insert(0, '.')
from app import create_app
from database import db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database created')
"""])
    
    return python

def main():
    """Uruchom aplikację"""
    print("=" * 50)
    print("LAUNCHING BLOG PLATFORM")
    print("=" * 50)
    
    python_path = check_and_install()
    
    print("\nApp starting at: http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    
    os.environ["FLASK_ENV"] = "development"
    subprocess.run([python_path, "app.py"])

if __name__ == "__main__":
    main()