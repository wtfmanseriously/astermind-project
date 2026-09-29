import pytest
import sqlite3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from audit import add_audit_log, verify_audit_chain
from db import init_db, get_db

@pytest.fixture(autouse=True)
def setup_teardown():
    import db
    db.DB_PATH = 'test_astermind_audit.db'
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
        
    init_db()
    
    yield
    
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)

def test_audit_chain_valid():
    add_audit_log("User created")
    add_audit_log("Case opened")
    add_audit_log("Case updated")
    
    assert verify_audit_chain() == True

def test_audit_chain_tampered():
    add_audit_log("User created")
    add_audit_log("Case opened")
    
    assert verify_audit_chain() == True
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE audit_logs SET action = 'Tampered' WHERE id = 2")
    conn.commit()
    conn.close()
    
    assert verify_audit_chain() == False

def test_audit_chain_broken_link():
    add_audit_log("Log 1")
    add_audit_log("Log 2")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE audit_logs SET previous_hash = 'invalid' WHERE id = 3")
    conn.commit()
    conn.close()
    
    assert verify_audit_chain() == False
