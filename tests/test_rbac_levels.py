import pytest
from unittest.mock import MagicMock
from werkzeug.security import generate_password_hash

# We use the 'client' and 'mock_db' fixtures from conftest.py

def configure_mock_user(mock_cursor, username, role, password="123"):
    """Helper to mock DB response for a user."""
    # The app expects: id, username, role, password_hash, whatsapp, is_temporary_password, profile_image, email, nome_completo, cpf, last_seen
    # User.get_by_username query: SELECT id, ... FROM users WHERE username = %s
    
    password_hash = generate_password_hash(password)
    
    # Return a dict-like object or tuple depending on how the app fetches it.
    # The app uses `user['id']` so it expects a dict-like row or RealDictCursor.
    # conftest.py mocks the cursor. We can make fetchone return a dict.
    
    user_data = {
        'id': 1,
        'username': username,
        'role': role,
        'password_hash': password_hash,
        'whatsapp': None,
        'is_temporary_password': 0,
        'profile_image': None,
        'email': f"{username}@test.com",
        'nome_completo': f"User {username}",
        'cpf': '000.000.000-00',
        'last_seen': None
    }
    
    
    def smart_fetchone():
        # Inspect the last execute call to determine what to return
        # mock_cursor.execute is a Mock. call_args gives (args, kwargs) of last call.
        if mock_cursor.execute.call_args:
            args, _ = mock_cursor.execute.call_args
            sql = args[0]
            
            # User Fetch (Login or load_user)
            if "SELECT id, username" in sql or "FROM users" in sql:
                 return user_data
            
            # Dashboard Stats or CP
            if "SELECT COUNT" in sql:
                 return (10,)
                 
            # Tenants (fetched via fetchall, but if fetchone used)
            if "FROM tenants" in sql:
                 return {'id': 1, 'name': 'Tes', 'slug': 'test', 'schema_name': 'test'}
                 
        return None

    mock_cursor.fetchone.side_effect = smart_fetchone
    
    class MockRow(dict):
        def __init__(self, data_dict, data_tuple):
            super().__init__(data_dict)
            self.tuple = data_tuple
        def __getitem__(self, key):
            if isinstance(key, int):
                return self.tuple[key]
            return super().__getitem__(key)
            
    # Also handle fetchall for tenants & online users replacement
    # Tenants: index access. Online users: dict() access.
    # Tenant: (1, 'Cartorio Teste', 'teste', 'tenant_default')
    # Online User: {'username': 'admin', 'role': 'admin', 'last_seen': '...'}
    
    # We need to provide a side_effect for fetchall too if we want to be precise,
    # or just return a list that works for both (safe).
    # But Tenants query columns != Online Users query columns.
    # Tenants: id, name, slug, schema
    # Online: username, role, last_seen
    
    # Let's make fetchall smart too.
    def smart_fetchall():
        if mock_cursor.execute.call_args:
            args, _ = mock_cursor.execute.call_args
            sql = args[0]
            if "FROM tenants" in sql:
                d = {'id': 1, 'name': 'Cartorio Teste', 'slug': 'teste', 'schema_name': 'tenant_default'}
                t = (1, 'Cartorio Teste', 'teste', 'tenant_default')
                return [MockRow(d, t)]
            if "FROM users" in sql and "last_seen" in sql:
                d = {'username': 'admin', 'role': 'admin', 'last_seen': '2025-01-01'}
                t = ('admin', 'admin', '2025-01-01')
                return [MockRow(d, t)]
        return []

    mock_cursor.fetchall.side_effect = smart_fetchall

@pytest.mark.parametrize("username, password, role, should_access_dashboard", [
    ("admin", "admin", "admin", True),
    ("supervisor", "123", "supervisor", True),
    ("colaborador", "123", "colaborador", False),
])
def test_login_and_dashboard_access(client, mock_db, username, password, role, should_access_dashboard):
    mock_conn, mock_cursor = mock_db
    
    # 1. Setup Mock for Login
    configure_mock_user(mock_cursor, username, role, password)
    
    # 2. Login
    response = client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)
    assert response.status_code == 200
    
    # 3. Try Accessing Dashboard
    response = client.get('/dashboard')
    
    if should_access_dashboard:
        assert response.status_code == 200
        # Check for meaningful content
        assert b"Dashboard" in response.data or b"Total" in response.data
    else:
        # Colaborador might be redirected
        assert response.status_code != 200 or b"Dashboard" not in response.data
