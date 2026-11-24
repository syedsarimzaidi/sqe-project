"""Root pytest conftest.

Sets the environment variables InvenTree's settings.py needs *before* Django
is set up, so the vendored baseline app (mis/src/backend/InvenTree) can be
imported and tested with pytest-django, using a throwaway SQLite database
dedicated to the test run (kept separate from the manually-run dev server's
database).
"""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

os.environ.setdefault('INVENTREE_DEBUG', 'True')
os.environ.setdefault('INVENTREE_DB_ENGINE', 'sqlite3')
os.environ.setdefault('INVENTREE_DB_NAME', str(REPO_ROOT / 'data' / 'test_db.sqlite3'))
os.environ.setdefault('INVENTREE_SECRET_KEY', 'test-only-key-not-for-production')
os.environ.setdefault('INVENTREE_PLUGINS_ENABLED', 'False')
os.environ.setdefault('INVENTREE_SITE_URL', 'http://localhost:8000')
os.environ.setdefault('INVENTREE_STATIC_ROOT', str(REPO_ROOT / 'data' / 'static'))
os.environ.setdefault('INVENTREE_MEDIA_ROOT', str(REPO_ROOT / 'data' / 'media'))
os.environ.setdefault('INVENTREE_BACKUP_DIR', str(REPO_ROOT / 'data' / 'backup'))
