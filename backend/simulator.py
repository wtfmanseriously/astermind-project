import requests
import time
import random
import threading

API_URL = "http://127.0.0.1:8000"

def ingest_event(entity_id, event_type, value, ip_address):
    try:
        response = requests.post(f"{API_URL}/api/events", json={
            "entity_id": entity_id,
            "event_type": event_type,
            "value": value,
            "ip_address": ip_address
        })
        if response.status_code == 200:
            data = response.json()
            if data["is_anomaly"]:
                print(f"⚠️ Anomaly Detected! Case ID: {data['case_id']}")
        else:
            print(f"Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Connection failed: {e}")

def simulate_normal_behavior():
    print("Simulating normal behavior for Entity 1...")
    for i in range(10):
        value = random.normalvariate(100, 5)
        ingest_event(1, "bytes_transferred", value, "192.168.1.100")
        time.sleep(0.5)

def simulate_anomaly():
    print("\nSimulating anomaly for Entity 1 (Data Exfiltration)...")
    ingest_event(1, "bytes_transferred", 15000.0, "93.184.216.34") 
    
def setup_db_for_simulator():
    import sqlite3
    import os
    db_path = os.path.join(os.path.dirname(__file__), 'astermind.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO entities (id, name, type) VALUES (1, "casey.morgan16", "user")')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_db_for_simulator()
    time.sleep(1)
    simulate_normal_behavior()
    time.sleep(1)
    simulate_anomaly()
    print("Simulation complete. Check the dashboard.")
