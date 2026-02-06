#!/usr/bin/env python
"""
COMPLETE LAUNCHER - All packages included
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(cmd, description):
    """Run command with feedback"""
    print(f"{description}...", end=" ", flush=True)
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("✓")
            return True
        else:
            print("✗")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print("⏱ (timeout)")
        return False
    except Exception as e:
        print(f"✗ ({e})")
        return False

def check_python():
    """Check Python installation"""
    print("Checking Python...", end=" ", flush=True)
    try:
        result = subprocess.run(
            [sys.executable, "--version"],
            capture_output=True,
            text=True
        )
        print(f"✓ {result.stdout.strip()}")
        return True
    except:
        print("✗ Python not found!")
        print("Please install Python 3.8+ from python.org")
        return False

def create_venv():
    """Create virtual environment"""
    venv_path = Path(".venv")
    
    if venv_path.exists():
        print("Cleaning old .venv...")
        try:
            # Kill Python processes on Windows
            if sys.platform == "win32":
                subprocess.run("taskkill /F /IM python.exe /T >nul 2>&1", 
                             shell=True, timeout=5)
            time.sleep(1)
            
            import shutil
            shutil.rmtree(venv_path)
            print("✓ Old .venv removed")
        except Exception as e:
            print(f"⚠ Could not remove .venv: {e}")
            print("Please close all terminals/IDEs and try again")
            return False
    
    print("Creating virtual environment...")
    if run_command(f'{sys.executable} -m venv .venv', "Creating .venv"):
        print("✓ .venv created")
        return True
    return False

def install_packages():
    """Install all required packages"""
    print("\nInstalling packages...")
    
    # All required packages
    all_packages = [
        "Flask==3.0.0",
        "Flask-SQLAlchemy==3.1.1",
        "Flask-Migrate==4.0.5",
        "Flask-CORS==4.0.0",
        "Flask-Bcrypt==1.0.1",
        "Flask-JWT-Extended==4.6.0",
        "Flask-Limiter==3.5.1",
        "python-dotenv==1.0.0",
        "PyJWT==2.8.0",
        "structlog==24.1.0",
        "email-validator==2.1.1",
        "cryptography==42.0.5",
        "redis==5.0.1",
    ]
    
    # Determine pip path
    if sys.platform == "win32":
        pip_path = ".venv\\Scripts\\pip.exe"
    else:
        pip_path = ".venv/bin/pip"
    
    # Install in batches to avoid timeouts
    batch_size = 4
    for i in range(0, len(all_packages), batch_size):
        batch = all_packages[i:i+batch_size]
        if not run_command(f'{pip_path} install {" ".join(batch)}', 
                          f"  Batch {i//batch_size + 1}"):
            print("⚠ Some packages may not have installed correctly")
    
    return True

def setup_env():
    """Setup environment file"""
    env_path = Path(".env")
    if not env_path.exists():
        print("\nCreating .env file...")
        env_content = """# Blog Platform Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite:///blog.db
JWT_SECRET_KEY=jwt-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRES=900
JWT_REFRESH_TOKEN_EXPIRES=604800
LOG_LEVEL=INFO
"""
        with open(".env", "w") as f:
            f.write(env_content)
        print("✓ .env created")
    else:
        print("✓ .env already exists")

def setup_database():
    """Setup database"""
    print("\nSetting up database...")
    
    # Add current directory to path
    sys.path.insert(0, str(Path.cwd()))
    
    try:
        from app import create_app
        from database import db
        from models.user import User
        
        app = create_app()
        with app.app_context():
            # Create tables
            db.create_all()
            print("✓ Database tables created")
            
            # Create admin user
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
                print("✓ Admin user created")
            else:
                print("✓ Admin already exists")
            
            print("✓ Database setup complete")
            return True
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_application():
    """Run the Flask application"""
    print("\n" + "=" * 50)
    print("STARTING APPLICATION")
    print("=" * 50)
    
    if sys.platform == "win32":
        python_path = ".venv\\Scripts\\python.exe"
    else:
        python_path = ".venv/bin/python"
    
    print(f"\nApplication will be available at:")
    print("  🌐 http://localhost:5000")
    print("\nUseful endpoints:")
    print("  📍 /hello                - Welcome page")
    print("  📍 /api/health           - Health check")
    print("  📍 /api/auth/register    - Register new user")
    print("\nDefault admin credentials:")
    print("  👤 Username: admin")
    print("  🔑 Password: Admin123!")
    print("\nPress Ctrl+C to stop the application")
    print("=" * 50 + "\n")
    
    # Run the app
    os.environ["FLASK_ENV"] = "development"
    subprocess.run([python_path, "app.py"])

def main():
    """Main function"""
    print("=" * 50)
    print("BLOG PLATFORM - COMPLETE SETUP & LAUNCH")
    print("=" * 50)
    
    # Check Python
    if not check_python():
        return
    
    # Create venv
    if not create_venv():
        print("Failed to create virtual environment")
        return
    
    # Install packages
    if not install_packages():
        print("Package installation had issues")
    
    # Setup environment
    setup_env()
    
    # Setup database
    if not setup_database():
        print("Database setup failed, but continuing...")
    
    # Run application
    run_application()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Application stopped by user")
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")