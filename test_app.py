# test_app.py
import pytest
from app import app
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_ask_question(client):
    response = client.post('/ask', 
                           data=json.dumps({'question': 'What is Python?'}),
                           content_type='application/json')
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.data}")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'id' in data
    assert 'question' in data
    assert 'answer' in data
    assert data['question'] == 'What is Python?'