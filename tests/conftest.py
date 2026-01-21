
import pytest
from unittest.mock import MagicMock
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock psycopg2
try:
    import psycopg2
except ImportError:
    print("Mocking psycopg2")
    sys.modules['psycopg2'] = MagicMock()
    sys.modules['psycopg2.pool'] = MagicMock()
    sys.modules['psycopg2.extras'] = MagicMock()

# Mock other heavy dependencies
for module in ['pandas', 'pytesseract', 'PIL', 'pdf2image']:
    try:
        __import__(module)
    except ImportError:
        print(f"Mocking {module}")
        sys.modules[module] = MagicMock()
        if module == 'PIL':
            sys.modules['PIL.Image'] = MagicMock()

from imoveis_web_multi import app, db_manager

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-key'
    app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for tests
    
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_db(mocker):
    """Mocks the database connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    # Configure cursor context manager
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    
    # Mock db_manager functions
    mocker.patch('db_manager.get_db_connection', return_value=mock_conn)
    mocker.patch('db_manager.release_db_connection')
    
    return mock_conn, mock_cursor
