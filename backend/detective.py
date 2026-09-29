import json
from typing import Dict, Any, List
from db import get_db

def evaluate_hypotheses(entity_id: int, event_type: str, new_value: float, mean: float, stddev: float) -> Dict[str, Any]:
    evidence = f"Entity {entity_id} triggered {event_type} with value {new_value}. Historical mean is {mean:.2f}, stddev is {stddev:.2f}."
    
    hypotheses = {
        "Normal Behavior": "The value represents normal fluctuation.",
        "System Glitch": "The data point is a reporting error.",
        "Compromise/Attack": "The entity is exhibiting malicious behavior or is compromised."
    }
    
    ruled_out = []
    verdict = ""
    reasoning_steps = []
    
    z_score = 0.0
    if stddev > 0:
        z_score = abs(new_value - mean) / stddev
        
    if z_score > 3.0 or stddev == 0:
        ruled_out.append({"hypothesis": "Normal Behavior", "reason": f"Value is statistically significant ({z_score:.1f} standard deviations away)."})
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT count(*) FROM events 
            WHERE entity_id = ? AND event_type = ? AND timestamp > datetime('now', '-1 hour')
        ''', (entity_id, event_type))
        recent_count = cursor.fetchone()[0]
        conn.close()
        
        if recent_count > 5:
             ruled_out.append({"hypothesis": "System Glitch", "reason": "Consistent repeated anomalous events within a short timeframe."})
             verdict = "Compromise/Attack"
             reasoning_steps.append("Multiple high-deviation events point to sustained anomalous activity.")
        else:
             verdict = "Held"
             reasoning_steps.append("Single anomaly detected. Waiting on further evidence to rule out System Glitch.")
             
    elif z_score > 2.0:
        ruled_out.append({"hypothesis": "Normal Behavior", "reason": "Value is outside 2 standard deviations (Warning)."})
        verdict = "Held"
        reasoning_steps.append("Warning threshold exceeded. Need more data points to determine if it's a trend or glitch.")
    else:
        verdict = "Normal"
        ruled_out.append({"hypothesis": "Compromise/Attack", "reason": "Value is within normal operational bounds."})
        ruled_out.append({"hypothesis": "System Glitch", "reason": "Value is within expected range."})
        reasoning_steps.append("Evidence aligns with established baseline.")
        
    reasoning = {
        "hypotheses_considered": list(hypotheses.keys()),
        "ruled_out": ruled_out,
        "steps": reasoning_steps
    }
    
    return {
        "evidence": evidence,
        "reasoning": json.dumps(reasoning),
        "verdict": verdict
    }

def create_case(entity_id: int, event_type: str, new_value: float, mean: float, stddev: float):
    evaluation = evaluate_hypotheses(entity_id, event_type, new_value, mean, stddev)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO cases (entity_id, status, evidence, reasoning, verdict)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        entity_id, 
        "Open" if evaluation["verdict"] in ["Held", "Compromise/Attack"] else "Closed",
        evaluation["evidence"],
        evaluation["reasoning"],
        evaluation["verdict"]
    ))
    
    case_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return case_id
