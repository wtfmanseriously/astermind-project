import pytest
import sqlite3
import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from detective import evaluate_hypotheses, create_case
from db import init_db, get_db

@pytest.fixture(autouse=True)
def setup_teardown():
    import db
    db.DB_PATH = 'test_astermind_detective.db'
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
        
    init_db()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO entities (name, type) VALUES (?, ?)', ('test_user_2', 'user'))
    conn.commit()
    conn.close()
    
    yield
    
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)

def test_evaluate_hypotheses_normal():
    result = evaluate_hypotheses(1, 'login_attempts', 10.0, 10.0, 1.0)
    assert result['verdict'] == 'Normal'
    reasoning = json.loads(result['reasoning'])
    assert len(reasoning['ruled_out']) == 2
    
def test_evaluate_hypotheses_warning():
    result = evaluate_hypotheses(1, 'login_attempts', 12.5, 10.0, 1.0)
    assert result['verdict'] == 'Held'
    reasoning = json.loads(result['reasoning'])
    assert reasoning['ruled_out'][0]['hypothesis'] == 'Normal Behavior'

def test_create_case():
    case_id = create_case(1, 'login_attempts', 15.0, 10.0, 1.0)
    assert case_id is not None
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM cases WHERE id = ?', (case_id,))
    case = cursor.fetchone()
    conn.close()
    
    assert case['entity_id'] == 1
    assert case['status'] == 'Open'
    assert case['verdict'] == 'Held'
