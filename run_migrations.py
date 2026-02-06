#!/usr/bin/env python
"""
Alternatywny skrypt migracji (używa istniejącej funkcji)
"""
import sys
import os

# Dodaj ścieżkę do projektu
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def main():
    print("=" * 50)
    print("Blog Platform - Database Migration Tool (Alternative)")
    print("=" * 50)
    
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from migrations import run_migrations
            run_migrations()
            print("\n✅ Migracje zakończone pomyślnie!")
            
    except Exception as e:
        print(f"\n❌ Błąd migracji: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()