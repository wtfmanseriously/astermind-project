import pytest
import sqlite3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from detection import calculate_mean_and_stddev, check_anomaly
from db import init_db, get_db

@pytest.fixture(autouse=True)
def setup_teardown():
    import db
    db.DB_PATH = 'test_astermind.db'
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
        
    init_db()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO entities (name, type) VALUES (?, ?)', ('test_user', 'user'))
    for i in range(10):
        cursor.execute('INSERT INTO events (entity_id, event_type, value) VALUES (?, ?, ?)', 
                      (1, 'login_attempts', 10.0))
    conn.commit()
    conn.close()
    
    yield
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)

def test_calculate_mean_and_stddev():
    values = [10.0, 10.0, 10.0, 10.0]
    mean, std = calculate_mean_and_stddev(values)
    assert mean == 10.0
    assert std == 0.0

    values = [2, 4, 4, 4, 5, 5, 7, 9]
    mean, std = calculate_mean_and_stddev(values)
    assert mean == 5.0
    assert abs(std - 2.138) < 0.01

def test_check_anomaly_normal():
    is_anomaly, mean, stddev = check_anomaly(1, 'login_attempts', 10.0)
    assert not is_anomaly
    assert mean == 10.0

def test_check_anomaly_abnormal():
    is_anomaly, mean, stddev = check_anomaly(1, 'login_attempts', 15.0)
    assert is_anomaly
    assert mean == 10.0
