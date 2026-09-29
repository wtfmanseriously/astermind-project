from pydantic import BaseModel
from typing import List, Dict

class MCPRankRequest(BaseModel):
    query: str
    passages: List[str]
    keep_top_k: int = 3

class MCPRankResponse(BaseModel):
    ranked_passages: List[str]
    original_tokens: int
    new_tokens: int
    savings_percentage: float
