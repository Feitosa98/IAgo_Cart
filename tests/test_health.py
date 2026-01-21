
def test_health_check_success(client, mock_db):
    """Test health check returns 200 and connected status."""
    mock_conn, mock_cursor = mock_db
    # Mock successful query
    mock_cursor.execute.return_value = None
    
    response = client.get('/health')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert data['database'] == 'connected'

def test_health_check_db_failure(client, mock_db):
    """Test health check returns 500 when DB fails."""
    mock_conn, mock_cursor = mock_db
    # Mock exception on execute
    mock_cursor.execute.side_effect = Exception("DB Connection Failed")
    
    response = client.get('/health')
    
    assert response.status_code == 500
    data = response.get_json()
    assert data['status'] == 'error'
    assert "DB Connection Failed" in data['database']
