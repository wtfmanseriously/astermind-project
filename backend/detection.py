import math
import sqlite3
from typing import List, Tuple
from db import get_db

def calculate_mean_and_stddev(values: List[float]) -> Tuple[float, float]:
    if not values:
        return 0.0, 0.0
    
    n = len(values)
    mean = sum(values) / n
    
    if n == 1:
        return mean, 0.0
        
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    stddev = math.sqrt(variance)
    return mean, stddev

def check_anomaly(entity_id: int, event_type: str, new_value: float) -> Tuple[bool, float, float]:
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT value FROM events 
        WHERE entity_id = ? AND event_type = ?
        ORDER BY timestamp DESC
        LIMIT 100
    ''', (entity_id, event_type))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return False, new_value, 0.0
        
    values = [row['value'] for row in rows]
    
    if not values:
        return False, new_value, 0.0

    mean, stddev = calculate_mean_and_stddev(values)
    
    if stddev == 0:
        if abs(new_value - mean) > 0.01:
            return True, mean, stddev
        return False, mean, stddev
        
    z_score = abs(new_value - mean) / stddev
    
    is_anomaly = z_score > 2.0
    
    return is_anomaly, mean, stddev
