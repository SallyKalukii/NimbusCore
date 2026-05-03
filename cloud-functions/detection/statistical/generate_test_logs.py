
import requests
import time
import random

URL = "https://us-central1-capstone-log-monitoring.cloudfunctions.net/ingest_log"

print("Generating test logs...")

for i in range(100):
    level = random.choice(['INFO', 'INFO', 'INFO', 'WARNING', 'WARNING', 'ERROR'])
    
    log = {
        'level': level,
        'source': 'test-generator',
        'message': f'Test log message {i}'
    }
    
    try:
        response = requests.post(URL, json=log, timeout=5)
        if response.status_code in [200, 202, 204]:
            print(f"✓ Sent log {i+1}/100", end='\r')
        else:
            print(f"✗ Failed log {i+1}/100 - Status: {response.status_code}")
    except Exception as e:
        print(f"✗ Error sending log {i+1}: {e}")
    
    time.sleep(0.1)

print("\n Generated 100 test logs")
