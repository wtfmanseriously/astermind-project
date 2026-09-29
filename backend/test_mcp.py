import pytest
from fastapi.testclient import TestClient
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app

client = TestClient(app)

def test_mcp_rank():
    response = client.post("/api/mcp/rank", json={
        "query": "What are the payment methods accepted?",
        "passages": [
            "We offer a 30 day return policy on all items.",
            "You can pay using Visa, Mastercard, or PayPal payment methods.",
            "Contact our support team for help.",
            "Our payment gateway is secure."
        ],
        "keep_top_k": 1
    })
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["ranked_passages"]) == 1
    # Should pick the second passage due to "payment methods" overlap
    assert "Visa, Mastercard" in data["ranked_passages"][0]
    
    assert data["original_tokens"] > 0
    assert data["new_tokens"] < data["original_tokens"]
    assert data["savings_percentage"] > 50.0 # Keeping 1 of 4 should save > 50%
