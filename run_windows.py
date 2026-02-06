#!/usr/bin/env python3
"""
Skrypt uruchomieniowy dla Windows
"""
import os
import sys
import subprocess
from pathlib import Path

def print_header():
    print("=" * 50)
    print("BLOG PLATFORM - Windows Setup")
    print("=" * 50)
    print()

def check_python():
    """Sprawdź czy Python jest zainstalowany używając py"""
    try:
        result = subprocess.run(
            ["py", "--version"], 
            capture_output=True, 
            text=True, 
            shell=True
        )
        if result.returncode == 0:
            print(f"✓ Python zainstalowany: {result.stdout.strip()}")
            return True
        else:
            print("✗ Python nie znaleziony (spróbuj użyć 'py' zamiast 'python')")
            return False
    except Exception as e:
        print(f"✗ Błąd: {e}")
        return False

def setup_virtualenv():
    """Utwórz i aktywuj wirtualne środowisko w .venv"""
    venv_dir = Path(".venv")
    
    if not venv_dir.exists():
        print("Tworzenie wirtualnego środowiska w .venv...")
        subprocess.run(["py", "-m", "venv", ".venv"], shell=True)
        print("✓ Wirtualne środowisko utworzone w .venv")
    else:
        print("✓ Wirtualne środowisko .venv już istnieje")
    
    # Ścieżka do pip w venv
    if sys.platform == "win32":
        pip_path = venv_dir / "Scripts" / "pip.exe"
        python_path = venv_dir / "Scripts" / "python.exe"
    else:
        pip_path = venv_dir / "bin" / "pip"
        python_path = venv_dir / "bin" / "python"
    
    return pip_path, python_path

def install_dependencies(pip_path):
    """Zainstaluj zależności"""
    requirements = Path("requirements.txt")
    
    if not requirements.exists():
        print("✗ Brak pliku requirements.txt")
        return False
    
    print("Instalowanie zależności...")
    result = subprocess.run(
        [str(pip_path), "install", "-r", "requirements.txt"],
        capture_output=True,
        text=True,
        shell=True
    )
    
    if result.returncode == 0:
        print("✓ Zależności zainstalowane")
        return True
    else:
        print(f"✗ Błąd instalacji: {result.stderr}")
        return False

def setup_env_file():
    """Utwórz plik .env jeśli nie istnieje"""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_file.exists():
        if env_example.exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print("✓ Plik .env utworzony z .env.example")
            print("  Edytuj plik .env przed uruchomieniem aplikacji!")
        else:
            print("⚠ Brak pliku .env.example - utworzę podstawowy .env")
            with open(".env", "w") as f:
                f.write("""# Blog Platform - Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite:///blog.db
JWT_SECRET_KEY=jwt-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRES=900
JWT_REFRESH_TOKEN_EXPIRES=604800
""")
    else:
        print("✓ Plik .env już istnieje")

def setup_database(python_path):
    """Skonfiguruj bazę danych"""
    print("Konfiguracja bazy danych...")
    
    # Importujemy tutaj, bo potrzebujemy zainstalowanych zależności
    import sys
    sys.path.insert(0, str(Path.cwd()))
    
    try:
        from app import create_app
        from database import db
        
        app = create_app()
        with app.app_context():
            db.create_all()
            print("✓ Baza danych skonfigurowana")
            return True
    except Exception as e:
        print(f"✗ Błąd konfiguracji bazy: {e}")
        return False

def run_application(python_path):
    """Uruchom aplikację"""
    print("\n" + "=" * 50)
    print("URUCHAMIANIE APLIKACJI")
    print("=" * 50)
    print("\nAplikacja dostępna pod: http://localhost:5000")
    print("Endpoints:")
    print("  - http://localhost:5000/hello")
    print("  - http://localhost:5000/api/health")
    print("  - http://localhost:5000/api/auth/register")
    print("\nNaciśnij Ctrl+C aby zatrzymać")
    print("-" * 50)
    
    subprocess.run([str(python_path), "app.py"], shell=True)

def main():
    print_header()
    
    if not check_python():
        print("\nZainstaluj Python z: https://www.python.org/downloads/")
        print("Upewnij się, że podczas instalacji zaznaczysz 'Add Python to PATH'")
        return
    
    pip_path, python_path = setup_virtualenv()
    
    if not install_dependencies(pip_path):
        return
    
    setup_env_file()
    
    if not setup_database(python_path):
        print("Kontynuowanie mimo błędu bazy danych...")
    
    run_application(python_path)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAplikacja zatrzymana")
    except Exception as e:
        print(f"\n✗ Nieoczekiwany błąd: {e}")
        input("Naciśnij Enter aby zakończyć...")