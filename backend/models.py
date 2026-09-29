from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class EntityBase(BaseModel):
    name: str
    type: str

class Entity(EntityBase):
    id: int

class EventBase(BaseModel):
    entity_id: int
    event_type: str
    value: float
    ip_address: Optional[str] = None

class Event(EventBase):
    id: int
    timestamp: datetime

class CaseBase(BaseModel):
    entity_id: int
    status: str
    evidence: str
    reasoning: str
    verdict: str

class Case(CaseBase):
    id: int
    created_at: datetime

class AuditLog(BaseModel):
    id: int
    action: str
    timestamp: datetime
    previous_hash: str
    hash: str
