"""
Simplified statistical detector
"""
import functions_framework
from google.cloud import pubsub_v1, firestore
import json
import base64
from datetime import datetime

db = firestore.Client()
publisher = pubsub_v1.PublisherClient()
alerts_topic = publisher.topic_path('capstone-log-monitoring', 'alerts')

@functions_framework.cloud_event
def detect_statistical(cloud_event):
    """Statistical anomaly detection"""
    try:
        # Decode message
        message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode()
        log_data = json.loads(message_data)
        
        source_ip = log_data.get('source_ip', 'unknown')
        print(f" Processing {source_ip}")
        
        # Simple check: Is attack_type not BENIGN?
        attack_type = log_data.get('attack_type', 'BENIGN')
        
        if attack_type.upper() != 'BENIGN':
            print(f" Attack detected: {attack_type}")
            
            alert = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'source_ip': source_ip,
                'detector': 'statistical',
                'severity': 'HIGH',
                'attack_type': attack_type,
                'confidence': 0.90,
                'description': f"{attack_type} detected",
                'source': log_data.get('source', 'unknown')
            }
            
            db.collection('alerts').add(alert)
            print(f" Alert created!")
            
            publisher.publish(alerts_topic, json.dumps(alert).encode('utf-8')).result()
            print(f" Published to alerts")
        else:
            print(f" No anomaly (BENIGN)")
        
        return 'OK'
    except Exception as e:
        print(f" Error: {e}")
        import traceback
        traceback.print_exc()
        return str(e)