import pytest
from unittest.mock import MagicMock, patch
from imoveis_web_multi import process_upload_task, app

@pytest.fixture
def mock_celery_task(mocker):
    # Mock the self argument of the task (which is a Celery Task instance)
    mock_self = MagicMock()
    mock_self.request.id = "test-task-id"
    return mock_self

@pytest.fixture
def mock_ocr(mocker):
    return mocker.patch("imoveis_web_multi.ocr_file_to_text", return_value="MATRÍCULA Nº 12345 TESTE")

@pytest.fixture
def mock_iago(mocker):
    return mocker.patch("imoveis_web_multi.iago.analyze", return_value={"NUMERO_REGISTRO": "12345"})

@pytest.fixture
def mock_db(mocker):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    
    # Mock get_conn to return our mock
    mocker.patch("imoveis_web_multi.get_conn", return_value=mock_conn)
    return mock_conn, mock_cur

def test_process_upload_task_success(mock_celery_task, mock_ocr, mock_iago, mock_db):
    """Test successful processing of a file."""
    mock_conn, mock_cur = mock_db
    # Mock existing check (None)
    mock_cur.fetchone.return_value = None
    # Mock insert/lastrowid
    mock_cur.lastrowid = 99
    
    # Run Task
    # Note: We call the function directly, bypassing the decorator magic if possible, 
    # but since it's decorated with bind=True, we need to pass 'self'.
    # Accessing the original function from the task object:
    # In Celery < 5, it was task.run. In Celery 5+, we might need to invoke differently or just call the decorated object.
    # If we imported the function, it's the Task object.
    # To test logic, it's often easier to extract logic or rely on .apply() if celery is eager.
    # But here we just pass our mock_self as first arg if we call it as a py function?
    # Actually, the decorated function is a Task instance. 
    # We can use process_upload_task.__wrapped__(mock_self, ...) or similar? Creates complexity.
    # Simpler: Configure Celery to be in 'always_eager' mode for tests? 
    # Or just patch the dependencies and call it.
    
    # Using the python function directly (underlying):
    # process_upload_task is a Task instance. 
    # process_upload_task.run is usually the method.
    
    res = process_upload_task.run(mock_celery_task, "file.pdf", "/tmp/file.pdf", "tenant_default")
    
    assert res['status'] == 'success'
    assert res['matricula'] == '12345'
    mock_ocr.assert_called_once()
    mock_iago.assert_called_once()
    # Check if save was called (implied by success)

def test_process_upload_task_duplicate_skip(mock_celery_task, mock_ocr, mock_iago, mock_db):
    """Test duplicate detection skips save."""
    mock_conn, mock_cur = mock_db
    # Mock existing check (Found ID 10)
    mock_cur.fetchone.return_value = (10,)
    
    res = process_upload_task.run(mock_celery_task, "file.pdf", "/tmp/file.pdf", "tenant_default", overwrite=False)
    
    assert res['status'] == 'duplicate'
    assert res['matricula'] == '12345'

def test_route_triggers_task(client, mocker):
    """Test that the upload route calls delay() on the task."""
    mock_delay = mocker.patch("imoveis_web_multi.process_upload_task.delay")
    mock_delay.return_value.id = "fake-id"
    
    # Authenticate (using fixture logic or fresh login)
    # We need a user. Using existing login logic from conftest if available, or mocking login_required.
    # For now, let's mock current_user or login
    mocker.patch("flask_login.utils._get_user", return_value=MagicMock(is_authenticated=True, role='admin'))
    
    # Mock file save
    mocker.patch("werkzeug.datastructures.FileStorage.save")
    
    data = {
        'arquivo': (b'fake content', 'test.pdf'),
        'mode': 'ajax'
    }
    
    res = client.post('/importar', data=data, content_type='multipart/form-data')
    
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data['status'] == 'success'
    
    # Verify Task was called
    mock_delay.assert_called_once()
