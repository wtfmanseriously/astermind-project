from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List, Dict, Any

from models import EventBase, Event, Case, AuditLog
from mcp_models import MCPRankRequest, MCPRankResponse
from db import get_db, init_db
from detection import check_anomaly
from detective import create_case
from audit import add_audit_log, verify_audit_chain
from geoip import lookup_ip

app = FastAPI(title="Astermind AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.post("/api/events", response_model=Dict[str, Any])
def ingest_event(event: EventBase, background_tasks: BackgroundTasks):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM entities WHERE id = ?', (event.entity_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Entity not found")
        
    is_anomaly, mean, stddev = check_anomaly(event.entity_id, event.event_type, event.value)
    
    cursor.execute('''
        INSERT INTO events (entity_id, event_type, value, ip_address)
        VALUES (?, ?, ?, ?)
    ''', (event.entity_id, event.event_type, event.value, event.ip_address))
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    background_tasks.add_task(add_audit_log, f"Event {event_id} ingested for Entity {event.entity_id}")
    
    case_id = None
    if is_anomaly:
        case_id = create_case(event.entity_id, event.event_type, event.value, mean, stddev)
        background_tasks.add_task(add_audit_log, f"Case {case_id} created due to anomaly in Event {event_id}")
        
    return {
        "event_id": event_id,
        "is_anomaly": is_anomaly,
        "case_id": case_id
    }

@app.get("/api/cases", response_model=List[Case])
def get_cases():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM cases ORDER BY created_at DESC')
    cases = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return cases

@app.get("/api/cases/{case_id}/geoip", response_model=Dict[str, Any])
def get_case_geoip(case_id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT entity_id, created_at FROM cases WHERE id = ?', (case_id,))
    case = cursor.fetchone()
    if not case:
        conn.close()
        raise HTTPException(status_code=404, detail="Case not found")
        
    cursor.execute('''
        SELECT ip_address FROM events 
        WHERE entity_id = ? AND ip_address IS NOT NULL 
        ORDER BY id DESC LIMIT 1
    ''', (case['entity_id'],))
    event = cursor.fetchone()
    conn.close()
    
    if not event or not event['ip_address']:
        return {"error": "No IP address associated with this case's entity."}
        
    geo_data = lookup_ip(event['ip_address'])
    geo_data['ip_address'] = event['ip_address']
    return geo_data

@app.get("/api/audit/verify", response_model=Dict[str, bool])
def verify_audit():
    is_valid = verify_audit_chain()
    add_audit_log(f"Audit chain verified. Result: {'Valid' if is_valid else 'Invalid'}")
    return {"is_valid": is_valid}

@app.post("/api/mcp/rank", response_model=MCPRankResponse)
def mcp_rank(request: MCPRankRequest):
    """
    Simulates the AsterMind MCP local token reduction logic.
    Ranks passages against a query using a basic keyword overlap heuristic
    and returns the top K passages, calculating token savings.
    """
    def tokenize(text: str) -> List[str]:
        # Very basic whitespace tokenizer for keyword overlap
        return [w.lower() for w in text.split() if w.isalnum()]

    def estimate_tokens(text: str) -> int:
        # OpenAI rough estimate: ~4 chars per token
        return max(1, len(text) // 4)

    query_tokens = set(tokenize(request.query))
    
    scored_passages = []
    for passage in request.passages:
        p_tokens = set(tokenize(passage))
        # Simple overlap score
        score = len(query_tokens.intersection(p_tokens))
        scored_passages.append((score, passage))
        
    # Sort descending by score
    scored_passages.sort(key=lambda x: x[0], reverse=True)
    
    # Keep top K
    top_k = request.keep_top_k
    ranked_passages = [p for score, p in scored_passages[:top_k]]
    
    # Calculate savings
    original_tokens = sum(estimate_tokens(p) for p in request.passages)
    new_tokens = sum(estimate_tokens(p) for p in ranked_passages)
    
    savings = 0.0
    if original_tokens > 0:
        savings = ((original_tokens - new_tokens) / original_tokens) * 100.0
        
    return MCPRankResponse(
        ranked_passages=ranked_passages,
        original_tokens=original_tokens,
        new_tokens=new_tokens,
        savings_percentage=round(savings, 1)
    )

@app.get("/api/entities/{entity_id}/chart/{event_type}")
def get_chart_data(entity_id: int, event_type: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT value, timestamp FROM events 
        WHERE entity_id = ? AND event_type = ?
        ORDER BY timestamp ASC
    ''', (entity_id, event_type))
    rows = cursor.fetchall()
    conn.close()
    
    labels = [row['timestamp'] for row in rows]
    data = [row['value'] for row in rows]
    
    return {
        "labels": labels,
        "data": data
    }
