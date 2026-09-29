import pytest
from fastapi.testclient import TestClient
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app
from db import init_db, get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown():
    import db
    db.DB_PATH = 'test_astermind_api.db'
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
        
    init_db()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO entities (name, type) VALUES (?, ?)', ('api_user', 'user'))
    conn.commit()
    conn.close()
    
    yield
    
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "AsterMind AI Console" in response.text

def test_ingest_event_normal():
    values = [1000.0, 1010.0, 990.0, 1005.0, 995.0] 
    for v in values:
        client.post("/api/events", json={
            "entity_id": 1,
            "event_type": "bytes_transferred",
            "value": v,
            "ip_address": "192.168.1.5"
        })
        
    response = client.post("/api/events", json={
        "entity_id": 1,
        "event_type": "bytes_transferred",
        "value": 1002.0,
        "ip_address": "192.168.1.5"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_anomaly"] == False
    assert data["case_id"] is None

def test_ingest_event_anomaly():
    for _ in range(5):
        client.post("/api/events", json={
            "entity_id": 1,
            "event_type": "login_failures",
            "value": 0.0,
            "ip_address": "10.0.0.1"
        })
        
    response = client.post("/api/events", json={
        "entity_id": 1,
        "event_type": "login_failures",
        "value": 10.0, 
        "ip_address": "8.8.8.8"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_anomaly"] == True
    assert data["case_id"] is not None
    
    cases_response = client.get("/api/cases")
    assert cases_response.status_code == 200
    cases = cases_response.json()
    assert len(cases) > 0
    assert cases[0]["id"] == data["case_id"]
    
    geoip_response = client.get(f"/api/cases/{data['case_id']}/geoip")
    assert geoip_response.status_code == 200
    geo_data = geoip_response.json()
    assert "lat" in geo_data
    assert geo_data["ip_address"] == "8.8.8.8"

def test_verify_audit_api():
    response = client.get("/api/audit/verify")
    assert response.status_code == 200
    assert response.json() == {"is_valid": True}
