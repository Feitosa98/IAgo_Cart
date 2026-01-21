import pytest
import io
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
    mock_cur.fetchone.return_value = None
    mock_cur.lastrowid = 99
    
    # Use .apply() to execute synchronously
    res = process_upload_task.apply(args=("file.pdf", "/tmp/file.pdf", "tenant_default")).result
    
    assert res['status'] == 'success'
    assert res['matricula'] == '12345'
    mock_ocr.assert_called_once()
    mock_iago.assert_called_once()

def test_process_upload_task_duplicate_skip(mock_celery_task, mock_ocr, mock_iago, mock_db):
    """Test duplicate detection skips save."""
    mock_conn, mock_cur = mock_db
    mock_cur.fetchone.return_value = (10,)
    
    res = process_upload_task.apply(args=("file.pdf", "/tmp/file.pdf", "tenant_default"), kwargs={'overwrite': False}).result
    
    assert res['status'] == 'duplicate'
    assert res['matricula'] == '12345'

def test_route_triggers_task(client, mocker):
    """Test that the upload route calls delay() on the task."""
    mock_delay = mocker.patch("imoveis_web_multi.process_upload_task.delay")
    mock_delay.return_value.id = "fake-id"
    
    user_mock = MagicMock(is_authenticated=True, role='admin', is_temporary_password=False)
    mocker.patch("flask_login.utils._get_user", return_value=user_mock)
    
    mocker.patch("werkzeug.datastructures.FileStorage.save")
    
    with client.session_transaction() as sess:
        sess['csrf_token'] = 'test-token'
    
    data = {
        'arquivo': (io.BytesIO(b'fake content'), 'test.pdf'),
        'mode': 'ajax',
        'csrf_token': 'test-token'
    }
    
    # Remove content_type, let client infer boundary
    res = client.post('/importar', data=data) 
    
    if res.status_code == 200:
        json_data = res.get_json()
        if json_data.get('status') == 'error':
             print(f"Route Error: {json_data}")
    elif res.status_code == 302:
        print(f"Redirecting to: {res.location}")
        
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data['status'] == 'success'
    mock_delay.assert_called_once()
