import hashlib
from db import get_db

def add_audit_log(action: str):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT hash FROM audit_logs ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    previous_hash = row['hash'] if row else "0"
    
    data_to_hash = f"{action}|{previous_hash}".encode('utf-8')
    new_hash = hashlib.sha256(data_to_hash).hexdigest()
    
    cursor.execute('''
        INSERT INTO audit_logs (action, previous_hash, hash)
        VALUES (?, ?, ?)
    ''', (action, previous_hash, new_hash))
    
    conn.commit()
    conn.close()

def verify_audit_chain() -> bool:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM audit_logs ORDER BY id ASC')
    logs = cursor.fetchall()
    conn.close()
    
    if not logs:
        return True
        
    for i in range(1, len(logs)):
        prev_log = logs[i-1]
        current_log = logs[i]
        
        if current_log['previous_hash'] != prev_log['hash']:
            return False
            
        data_to_hash = f"{current_log['action']}|{current_log['previous_hash']}".encode('utf-8')
        expected_hash = hashlib.sha256(data_to_hash).hexdigest()
        
        if current_log['hash'] != expected_hash:
            return False
            
    return True
